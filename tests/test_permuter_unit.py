"""wc1.permuter search control (no toolchain): the compile and the diff are faked.

Covers the 2026-11-22 overnight hang fix: baseline first, earliest match wins
whatever order compiles finish in, a compile timeout stops the search, a
crashing candidate is only a failed candidate, nothing leaks into the work
directory, the wall budget stops new submissions and every candidate beats
the heartbeat.
"""
import os
import threading
import time

import pytest

from wc1 import match, permuter

BASE = "/* codegen-compiler: 10.0a */\nint f(void)\n{\n    return 0;\n}\n"


class Fake:
    """Programmable compile_c/diff_function pair keyed by the candidate's flags."""

    def __init__(self, match_flags=(), timeout_flags=(), raise_flags=(), delay=None):
        self.match_flags = set(match_flags)
        self.timeout_flags = set(timeout_flags)
        self.raise_flags = set(raise_flags)
        self.delay = delay or {}
        self.calls = []
        self.lock = threading.Lock()

    def compile_c(self, src, cflags, out, cc=None, includes=(), timeout=None, quiet=False):
        short = cflags.replace(match.BASE_CFLAGS, "").strip()
        with self.lock:
            self.calls.append((cc, short))
        assert quiet, "permuter compiles must be quiet (thread-safe)"
        assert timeout == 5
        # leave the litter a real compile leaves behind
        open(out, "w").write("obj")
        open(out + ".log", "w").write("log")
        time.sleep(self.delay.get(short, 0.0))
        if short in self.timeout_flags:
            raise match.CompileTimeout("error: wcc386 timed out")
        if short in self.raise_flags:
            raise RuntimeError("boom")
        return (cc, short)

    def diff_function(self, p, mod, by_link, orig_addr=None):
        cc, short = mod
        hit = short in self.match_flags
        return {"matched": hit, "score": (0, 0, 0, 0, 0) if hit else (10, 0, 0, 0, 0),
                "first_diff": None if hit else f"diff {short}"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    work = tmp_path / "work"
    monkeypatch.setattr(permuter, "path", lambda *a: str(work.joinpath(*a)))
    monkeypatch.setattr(permuter.symbols, "load", lambda: ({}, {}, None))
    monkeypatch.setattr(permuter.analysis, "run", lambda: object())
    src = tmp_path / "f.c"
    src.write_text(BASE)

    def install(fake):
        monkeypatch.setattr(permuter.match, "compile_c", fake.compile_c)
        monkeypatch.setattr(permuter.match, "diff_function", fake.diff_function)
        return fake

    return src, work, install


def _preset(i):
    return permuter.FLAG_PRESETS[i][1]


def _leftovers(work):
    d = work / "build" / "permuter"
    return sorted(os.listdir(d)) if d.exists() else []


def test_baseline_match_is_evaluated_alone(env):
    src, work, install = env
    fake = install(Fake(match_flags={"-s -ot -ol -4r -zp2"}))
    r = permuter.permute_file(str(src), jobs=4, apply=True, timeout=5)
    assert r["matched"] and r["label"] == "baseline"
    assert r["trials"] == 1 and len(fake.calls) == 1
    assert r["env_error"] is None and r["stopped"] == "match"
    assert _leftovers(work) == []


def test_earliest_match_wins_regardless_of_finish_order(env):
    src, work, install = env
    # presets 1 and 3 match; preset 1 is slow so preset 3 finishes first
    early, late = _preset(1), _preset(3)
    for _ in range(3):
        install(Fake(match_flags={early, late}, delay={early: 0.3}))
        r = permuter.permute_file(str(src), jobs=4, rounds=0, timeout=5)
        assert r["matched"]
        assert r["label"] == f"flags(10.0a:{early})"
        assert r["cflags"] == early
    assert _leftovers(work) == []


def test_compile_timeout_stops_the_search(env):
    src, work, install = env
    stuck = _preset(2)
    fake = install(Fake(timeout_flags={stuck}))
    r = permuter.permute_file(str(src), jobs=1, max_trials=50, rounds=2, timeout=5)
    assert not r["matched"]
    assert r["stopped"] == "timeout"
    assert "timed out" in r["env_error"]
    # jobs=1: baseline, the presets before the stuck one (minus the baseline's
    # own flags), the stuck preset -- then nothing else
    base = "-s -ot -ol -4r -zp2"
    want = [base] + [_preset(i) for i in range(3) if _preset(i) != base]
    assert [c[1] for c in fake.calls] == want
    assert r["trials"] == len(want)
    assert _leftovers(work) == []


def test_timeout_never_applies_a_match(env):
    """A search cut short by a compile timeout writes nothing, even when a
    candidate matched before the timeout was seen."""
    src, work, install = env
    hit, stuck = _preset(1), _preset(2)
    install(Fake(match_flags={hit}, timeout_flags={stuck}, delay={stuck: 0.2}))
    r = permuter.permute_file(str(src), jobs=4, rounds=0, timeout=5, apply=True)
    assert r["env_error"] and r["stopped"] == "timeout"
    assert r["matched"] and r["cflags"] == hit           # the case the guard is for
    assert r["applied"] is False
    assert src.read_text() == BASE
    assert _leftovers(work) == []


def test_crashing_candidate_is_only_a_failed_candidate(env):
    src, work, install = env
    bad, good = _preset(1), _preset(4)
    install(Fake(match_flags={good}, raise_flags={bad}))
    r = permuter.permute_file(str(src), jobs=2, rounds=0, timeout=5)
    assert r["matched"] and r["cflags"] == good
    assert r["env_error"] is None
    assert _leftovers(work) == []


def test_wall_budget_stops_new_submissions(env):
    src, work, install = env
    fake = install(Fake())
    r = permuter.permute_file(str(src), jobs=4, rounds=2, timeout=5, wall_budget=0)
    assert not r["matched"]
    assert r["stopped"] == "deadline"
    assert r["env_error"] is None          # out of time is a miss, not an error
    assert len(fake.calls) == 1            # only the baseline ran


def test_heartbeat_called_per_candidate_and_errors_ignored(env):
    src, work, install = env
    install(Fake())
    seen = []

    def beat(n, label):
        seen.append((n, label))
        raise ValueError("a broken heartbeat must not stop the permuter")

    r = permuter.permute_file(str(src), jobs=3, rounds=0, timeout=5, on_progress=beat)
    assert [n for n, _ in seen] == list(range(1, r["trials"] + 1))
    assert seen[0][1] == "baseline"
    assert r["trials"] == len(permuter.FLAG_PRESETS)   # baseline + every other preset
    assert _leftovers(work) == []


def test_cli_exits_2_on_env_error(env, capsys):
    src, work, install = env
    install(Fake(timeout_flags={"-s -ot -ol -4r -zp2"}))
    assert permuter.main([str(src), "--rounds", "0", "--timeout", "5"]) == 2
    assert "timed out" in capsys.readouterr().err
