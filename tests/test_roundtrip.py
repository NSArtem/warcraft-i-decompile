"""wc1.roundtrip: the one-pass proof with a converged demotion list, and the
diagnostic convergence loop from any other list."""
import os
import shutil
import types

import pytest

from wc1 import emit, path, roundtrip

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and shutil.which("nasm")),
    reason="needs original/ and nasm (nix develop)")

with open(path("analysis", "raw_insns.txt")) as _fh:
    COMMITTED = _fh.read()
HEADER = [l for l in COMMITTED.splitlines(True) if l.startswith("#")]
ENTRIES = [l for l in COMMITTED.splitlines(True) if not l.startswith("#")]


@pytest.fixture
def rt(tmp_path, monkeypatch):
    """Runs main() on a private build/ and raw_insns.txt; returns (raw list file,
    passes: the force_raw set of every NASM pass)."""
    (tmp_path / "build").mkdir()
    raw = tmp_path / "raw_insns.txt"

    def redirect(*p):
        if p[:1] == ("build",):
            return str(tmp_path.joinpath(*p))
        return str(raw) if p == ("analysis", "raw_insns.txt") else path(*p)

    passes = []
    real = emit.Emitter

    def emitter(*a, **kw):
        passes.append(set(kw["force_raw"]))
        return real(*a, **kw)

    monkeypatch.setattr(roundtrip, "path", redirect)
    monkeypatch.setattr(emit, "Emitter", emitter)
    return raw, passes


def test_converged_list_is_proven_in_one_non_diagnostic_pass(rt, capsys):
    raw, passes = rt
    raw.write_text(COMMITTED)
    os.utime(raw, (1, 1))
    roundtrip.main()
    out = capsys.readouterr().out
    assert "mismatching insns=0 image_identical=True" in out and "[diag]" not in out
    assert f"ROUND-TRIP OK: {len(ENTRIES)} raw instructions of" in out
    # exactly the listed instructions are raw: no branch is hidden from the proof
    assert passes == [{int(l.split()[0], 16) for l in ENTRIES}]
    assert raw.read_text() == COMMITTED and os.stat(raw).st_mtime == 1    # not rewritten
    # the proof is about the image just assembled
    img = raw.parent / "build" / "war_rt.bin"
    assert img.stat().st_size > 0


@pytest.mark.parametrize("start", ["empty", "incomplete"])
def test_fallback_converges_to_the_committed_list(rt, capsys, start):
    """empty: an assembler error in the first pass; incomplete: mis-encoded instructions."""
    raw, passes = rt
    raw.write_text("" if start == "empty" else "".join(HEADER + ENTRIES[:50] + ENTRIES[53:]))
    roundtrip.main()
    out = capsys.readouterr().out
    assert "[diag]: mismatching insns=0 image_identical=True" in out
    assert "[full]: mismatching insns=0 image_identical=True" in out
    assert out.splitlines()[-1].startswith("ROUND-TRIP OK:")
    assert raw.read_text() == COMMITTED
    # the last pass is the proof: no branches forced raw
    assert passes[-1] == {int(l.split()[0], 16) for l in ENTRIES}


@pytest.fixture
def scripted(rt, monkeypatch):
    """main() with attempt() replaced by scripted results (control flow only, no NASM).
    run(results) -> the force_raw set of each attempt."""
    raw, _ = rt

    def run(results):
        forced, left = [], list(results)

        def attempt(p, names, force_raw, src, out, want):
            forced.append(set(force_raw))
            stderr, bad, ok = left.pop(0)
            with open(out, "wb") as fh:
                fh.write(want if ok else b"?")
            return types.SimpleNamespace(line_addr={}), stderr, set(bad), ok

        monkeypatch.setattr(roundtrip, "attempt", attempt)
        roundtrip.main()
        assert not left, "not every scripted pass was run"
        return forced
    return raw, run


GOOD = (None, (), True)
LISTED = {int(l.split()[0], 16) for l in ENTRIES}


@pytest.mark.parametrize("defect", [
    (None, (), False),                         # only the image differs
    (None, (0x10000,), True),                  # only one instruction differs
    (None, (0x10000,), False),
    ("war_rt.asm:1: error: x", (), False),     # NASM fails
])
def test_fast_pass_defect_is_never_accepted(scripted, capsys, defect):
    """Whatever is wrong with the first pass, main() goes through the full loop;
    the first pass's own report demotes nothing."""
    raw, run = scripted
    raw.write_text(COMMITTED)
    fast, diag, full = run([defect, GOOD, GOOD])
    assert fast == full == LISTED and diag > LISTED     # diag: the branches too
    out = capsys.readouterr().out
    assert "iter 0 [diag]" in out and "iter 1 [full]" in out
    assert raw.read_text() == COMMITTED


def test_without_a_list_the_diagnostic_loop_runs_first(scripted, capsys):
    raw, run = scripted
    bad = sorted(LISTED)[:2]
    diag, diag2, full = run([(None, bad, False), GOOD, GOOD])
    assert diag and not diag & set(bad) and diag2 == diag | set(bad) and full == set(bad)
    assert "recorded list" not in capsys.readouterr().out
    assert raw.read_text() == "".join(HEADER + [l for l in ENTRIES if int(l.split()[0], 16) in bad])


def test_persistent_image_difference_fails(scripted, capsys):
    raw, run = scripted
    raw.write_text(COMMITTED)
    with pytest.raises(SystemExit) as ex:
        run([(None, (), False)] * 3)
    assert ex.value.code == 1
    out = capsys.readouterr().out
    assert "image differs at offset 0" in out and "ROUND-TRIP OK" not in out
    assert raw.read_text() == COMMITTED
