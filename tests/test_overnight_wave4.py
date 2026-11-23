"""Wave 4 integration in wc1.overnight: queue, command, success predicate, rollback, CLI (fakes only)."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from wc1 import live, oldcc, overnight, path, wave4


@pytest.fixture(autouse=True)
def wine_resets(monkeypatch):
    calls = []
    monkeypatch.setattr(overnight, "_reset_wine", lambda: calls.append(1))
    return calls


def c(addr, module="mod_x", ref="src/mod_x/f.c", group=2):
    return {"addr": addr, "addr_hex": f"{addr:#x}", "name": f"F{addr:x}", "module": module, "ref": ref,
            "group": group, "audit_status": None, "ninsns": 12}


def fake_discover(cs, state="stale"):
    return lambda: (list(cs), {"report": state, "eligible": len(cs), "issues": []})


# 1/4/5 -----------------------------------------------------------------------------------------
def test_wave4_items_one_function_per_task(tmp_path, monkeypatch):
    monkeypatch.setattr(overnight, "path", lambda *p: os.path.join(str(tmp_path), *p))
    items = overnight.wave4_items(discover=fake_discover([c(0x10), c(0x20), c(0x30, module="mod_y")]))
    assert [it["addrs"] for it in items] == [[0x10], [0x20], [0x30]]      # same ref file, still one task each
    for it in items:
        assert it["mode"] == overnight.WAVE4_MODE == "t3-recovery"
        assert it["count"] == 1 and it["module_total"] == 1
        assert it["header"] is None and it["limit"] is None and it["src_subdir"] is None
        assert it["key"] == (overnight.WAVE4_MODE, it["module"], (it["addrs"][0],))
    assert len({it["area"] for it in items}) == 3 and items[0]["area"] == "w4_10"
    assert items[0]["report_state"] == "stale"


def test_wave4_items_filters_and_failed_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(overnight, "path", lambda *p: os.path.join(str(tmp_path), *p))
    d = fake_discover([c(0x10), c(0x20), c(0x30, module="mod_y")])
    k10 = (overnight.WAVE4_MODE, "mod_x", (0x10,))
    assert [i["addrs"][0] for i in overnight.wave4_items(discover=d, failed_keys={k10})] == [0x20, 0x30]
    assert [i["addrs"][0] for i in overnight.wave4_items(discover=d, only=["mod_y"])] == [0x30]
    assert [i["addrs"][0] for i in overnight.wave4_items(discover=d, only=["0x20"])] == [0x20]
    assert [i["addrs"][0] for i in overnight.wave4_items(discover=d, skip=["mod_x"])] == [0x30]


def test_wave4_queue_is_separate_from_wave2_and_3(monkeypatch):
    monkeypatch.setattr(wave4, "discover", fake_discover([c(0x10)]))
    items, nh = overnight.build_queue_with_needs_human(wave="wave4")
    assert [i["mode"] for i in items] == ["t3-recovery"] and nh == []


# 2/3 -------------------------------------------------------------------------------------------
def test_wave_all_and_wave2_3_never_include_wave4(monkeypatch):
    if not os.path.exists(path("original", "install", "war.exe")):
        pytest.skip("needs original/install/war.exe")
    monkeypatch.setattr(wave4, "discover", lambda *a, **k: pytest.fail("wave4 discovery ran"))
    monkeypatch.setattr(overnight, "wave4_items", lambda *a, **k: pytest.fail("wave4 queue built"))
    allq, _ = overnight.build_queue_with_needs_human(wave="all")
    assert allq and {i["mode"] for i in allq} <= {"c-only", "full"}
    for w, mode in (("wave2", "c-only"), ("wave3", "full")):
        q, _ = overnight.build_queue_with_needs_human(wave=w)
        assert {i["mode"] for i in q} <= {mode}


# 13 --------------------------------------------------------------------------------------------
def test_cli_wave4_flags_and_forwarding():
    ap = overnight._build_parser()
    assert ap.parse_args([]).wave == "all" and ap.parse_args([]).wave4_max_calls == 2
    a = ap.parse_args(["--headless", "--wave", "wave4", "--wave4-max-calls", "3", "--max-modules", "1",
                       "--wave4-retry"])
    assert a.wave == "wave4" and a.wave4_max_calls == 3 and a.max_modules == 1 and a.wave4_retry
    base = {"window_budget": 1.0, "window_capacity": 35.0, "max_modules": 1, "wave": "wave4",
            "wave4_max_calls": 3, "wave4_retry": True, "chunk_size": 10, "module_budget": 1.0, "module_calls": 8,
            "repair_budget": 0.3, "skip": (), "only": (), "sleep_on_limit": False, "rate_limit_sleep": 600}
    args = overnight.build_cli_args(base)
    p = ap.parse_args(args)
    assert p.wave == "wave4" and p.wave4_max_calls == 3 and p.wave4_retry
    assert not {"--wave4-max-calls", "--wave4-retry"} & set(overnight.build_cli_args(dict(base, wave="all")))
    with pytest.raises(SystemExit):
        ap.parse_args(["--wave", "wave5"])


def test_run_overnight_validates_wave4_args():
    with pytest.raises(ValueError):
        overnight.run_overnight(wave="wave9")
    with pytest.raises(ValueError):
        overnight.run_overnight(wave="wave4", wave4_max_calls=0)


def test_wave4_path_allowlist():
    out = {"ref": "src/mod_x/f.c", "tomls": ["analysis/symbols/m.toml"]}
    assert overnight._check_wave4_paths({"src/mod_x/f.c", "analysis/symbols/m.toml"}, out, cwd="/nonexistent") == []
    bad = overnight._check_wave4_paths({"src/mod_x/f.c", "Makefile", "tests/test_new.py", "src/mod_x/g.c"},
                                       out, cwd="/nonexistent")
    assert bad == ["Makefile", "src/mod_x/g.c", "tests/test_new.py"]
    assert overnight._check_wave4_paths({"src/mod_x/f.c"}, {}, cwd="/nonexistent") == ["src/mod_x/f.c"]


# 7/8/10/11/12 end to end -----------------------------------------------------------------------
TOML = "[[func]]\naddr = 0x10\nname = \"F\"\nconfidence = \"high\"\nevidence = [\n  \"x\",\n]\n"
REF0 = "int f(void) { return 1; }\n"


class Env:
    def __init__(self, tmp_path, monkeypatch):
        self.repo = repo = tmp_path / "repo"
        repo.mkdir()
        git = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)
        git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
        (repo / "Makefile").write_text("all:\n\t@true\n")
        (repo / "analysis" / "symbols").mkdir(parents=True)
        (repo / "analysis" / "symbols" / "m.toml").write_text(TOML)
        (repo / "src" / "mod_x").mkdir(parents=True)
        (repo / "src" / "mod_x" / "f.c").write_text(REF0)
        git("add", "Makefile", "analysis/symbols/m.toml", "src/mod_x/f.c")
        git("commit", "-q", "-m", "init")
        join = lambda *p: os.path.join(str(repo), *p)
        monkeypatch.setattr(overnight, "path", join)
        monkeypatch.setattr(wave4, "path", join)
        monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(repo), "build", "live"))
        self.cmds, self.verify_rc, self.worker_rc = [], 0, 0
        self.t3 = 300
        self.failed_seen = []
        self.item = {"key": (overnight.WAVE4_MODE, "mod_x", (0x10,)), "mode": overnight.WAVE4_MODE,
                     "module": "mod_x", "area": "w4_10", "src_subdir": None, "header": None, "limit": None,
                     "count": 1, "addrs": [0x10], "module_total": 1, "total_insns": 12, "avg_insns": 12.0,
                     "name": "F", "ref": "src/mod_x/f.c", "wave4_group": 2, "audit_status": None,
                     "report_state": "missing"}

        def queue(**kw):
            self.failed_seen.append(set(kw.get("failed_keys") or ()))
            return [] if self.item["key"] in (kw.get("failed_keys") or ()) or self.cmds else [self.item]
        monkeypatch.setattr(overnight, "build_queue", queue)
        monkeypatch.setattr(overnight, "progress_done_count", lambda: (600, 1010, self.t3, 600 - self.t3))
        monkeypatch.setattr(overnight, "_snapshot_symbol_state", self.snapshot)
        monkeypatch.setattr(overnight, "_run_subprocess_logged", self.subproc)
        self.behaviour = lambda: None

    def snapshot(self):
        ref = self.item["ref"]
        promoted = self.t3 > 300
        return {0x10: {"done": True, "name": "F", "c": "T3" if promoted else "T4",
                       "src": ref if promoted else None, "ref": None if promoted else ref,
                       "ref_verified_by": None if promoted else "difftest: tests/test_x.py::test_f",
                       "file": "analysis/symbols/m.toml"}}

    def subproc(self, cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info", **_kw):
        if cmd[0] == sys.executable:
            self.cmds.append(list(cmd))
            self.behaviour()
            return self.worker_rc, "ok\n"
        return (self.verify_rc, "IDENTICAL\n100 passed\n" if self.verify_rc == 0 else "FAILED\n")

    def promote(self):
        (self.repo / "src" / "mod_x" / "f.c").write_text("/* codegen-compiler: 10.0a */\n" + REF0)
        (self.repo / "analysis" / "symbols" / "m.toml").write_text(TOML + "# promoted\n")
        self.t3 = 301
        wave4.write_outcome(0x10, wave4.PROMOTED, promoted=["0x10"], ref="src/mod_x/f.c",
                            tomls=["analysis/symbols/m.toml"])

    def run(self, **kw):
        kw.setdefault("repair_budget", 0.0)
        return overnight.run_overnight(window_budget=1.0, wave="wave4", **kw)

    def log(self):
        return subprocess.run(["git", "log", "--format=%s"], cwd=self.repo, capture_output=True, text=True).stdout.split("\n")[:-1]

    def state(self):
        return live.read_json(live.state_path())


def test_promoted_commits_even_though_done_is_unchanged(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour = e.promote
    assert e.run(wave4_max_calls=2) == 0
    cmd = e.cmds[0]
    assert cmd[3:5] == ["t3-recovery", "0x10"] and cmd[cmd.index("--max-calls") + 1] == "2"
    assert not {"--addrs", "--header", "--limit", "--src-subdir"} & set(cmd)
    assert e.log()[0] == "T3: F 0x10 (built from C, via wc1.overnight wave4)" and len(e.log()) == 2
    st = e.state()
    assert st["completed"][0]["status"] == "COMMITTED" and st["completed"][0]["delta"] == 1
    assert "promoted" in (e.repo / "analysis" / "symbols" / "m.toml").read_text()


def test_wave4_max_calls_is_forwarded_to_the_driver(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour = e.promote
    e.run(wave4_max_calls=3)
    assert e.cmds[0][e.cmds[0].index("--max-calls") + 1] == "3"


def test_unchanged_t3_count_is_not_success(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)

    def beh():
        e.promote()
        e.t3 = 300                       # files changed but the T3 count did not move
    e.behaviour = beh
    e.run()
    assert e.log() == ["init"]
    assert e.state()["completed"][0]["status"] == "FAILED"
    assert "delta_t3=0" in e.state()["completed"][0]["note"]
    assert (e.repo / "src" / "mod_x" / "f.c").read_text() == REF0


def test_matching_counts_without_the_target_receipt_are_not_success(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)

    def beh():
        e.promote()
        wave4.write_outcome(0x10, wave4.PROMOTED, promoted=["0x20"], ref=e.item["ref"],
                            tomls=["analysis/symbols/m.toml"])
    e.behaviour = beh
    e.run()
    assert e.log() == ["init"]
    assert "invalid Wave 4 transition" in e.state()["completed"][0]["note"]


def test_wrong_toml_owner_in_receipt_is_rejected(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)

    def beh():
        e.promote()
        # The edited TOML passes a receipt-only allowlist, but the extra
        # claimant is not actually an owner of any promoted entry.
        wave4.write_outcome(0x10, wave4.PROMOTED, promoted=["0x10"], ref=e.item["ref"],
                            tomls=["analysis/symbols/m.toml", "analysis/symbols/unrelated.toml"])

    e.behaviour = beh
    e.run()
    assert e.log() == ["init"]
    assert "invalid Wave 4 transition" in e.state()["completed"][0]["note"]


def test_nonzero_worker_exit_cannot_commit_a_promotion(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour, e.worker_rc = e.promote, 1
    e.run()
    assert e.log() == ["init"]
    assert "did not finish a clean promotion" in e.state()["completed"][0]["note"]
    assert (e.repo / e.item["ref"]).read_text() == REF0


def test_no_improvement_is_noop_and_not_retried(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour = lambda: wave4.write_outcome(0x10, wave4.NO_IMPROVEMENT, reason="still differs at 0x4")
    e.run()
    assert len(e.cmds) == 1
    rec = e.state()["completed"][0]
    assert rec["status"] == "NOOP" and "NO_IMPROVEMENT" in rec["note"] and "0x4" in rec["note"]
    assert e.log() == ["init"]
    assert overnight.WAVE4_MODE in {k[0] for k in e.failed_seen[-1]}     # excluded for the rest of the run


def test_unbuildable_outcome_with_changes_is_rolled_back(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)

    def beh():
        (e.repo / "src" / "mod_x" / "f.c").write_text("garbage\n")
        wave4.write_outcome(0x10, wave4.UNBUILDABLE, reason="sibling mismatches")
    e.behaviour = beh
    e.run()
    assert len(e.cmds) == 1 and e.log() == ["init"]
    assert (e.repo / "src" / "mod_x" / "f.c").read_text() == REF0
    rec = e.state()["completed"][0]
    assert rec["status"] == "FAILED" and "UNBUILDABLE" in rec["note"]


def test_make_verify_failure_rolls_back_promotion(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour, e.verify_rc = e.promote, 1
    e.run()
    assert e.log() == ["init"] and len(e.cmds) == 1
    assert (e.repo / "src" / "mod_x" / "f.c").read_text() == REF0
    assert (e.repo / "analysis" / "symbols" / "m.toml").read_text() == TOML
    assert e.state()["completed"][0]["status"] == "FAILED"


def test_verify_failure_never_enters_the_generic_repair_loop(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour, e.verify_rc = e.promote, 1
    called = []
    for name in ("run_bounded_repair", "run_codex_structured_repair"):
        if hasattr(overnight, name):
            monkeypatch.setattr(overnight, name, lambda *a, **k: called.append(name) or (_ for _ in ()).throw(AssertionError(name)))
    e.run(repair_budget=5.0)
    assert not called and e.log() == ["init"] and len(e.cmds) == 1
    assert e.state()["completed"][0]["status"] == "FAILED"


@pytest.mark.parametrize("out", ["100 passed\n", "NOT IDENTICAL\n100 passed\n"])
def test_verify_without_identical_build_is_not_committed(tmp_path, monkeypatch, out):
    e = Env(tmp_path, monkeypatch)
    e.behaviour = e.promote
    orig = e.subproc
    monkeypatch.setattr(overnight, "_run_subprocess_logged",
                        lambda cmd, *a, **k: (0, out) if cmd[0] != sys.executable else orig(cmd, *a, **k))
    e.run()
    assert e.log() == ["init"]
    assert (e.repo / "src" / "mod_x" / "f.c").read_text() == REF0
    assert "did not report Build A IDENTICAL" in e.state()["completed"][0]["note"]


def test_stray_edit_outside_ref_and_tomls_is_rejected(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)

    def beh():
        e.promote()
        (e.repo / "Makefile").write_text("all:\n\t@false\n")
    e.behaviour = beh
    e.run()
    assert e.log() == ["init"]
    assert "disallowed paths" in e.state()["completed"][0]["note"]
    assert (e.repo / "Makefile").read_text() == "all:\n\t@true\n"


def test_stale_outcome_from_a_previous_run_is_ignored(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    wave4.write_outcome(0x10, wave4.PROMOTED, promoted=["0x10"], ref="src/mod_x/f.c", tomls=[])
    e.behaviour = lambda: None            # this run writes nothing at all
    e.run()
    rec = e.state()["completed"][0]
    assert rec["status"] == "NOOP" and "NO_OUTCOME" in rec["note"] and e.log() == ["init"]


def test_toolchain_error_stops_the_run(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    calls = []

    def subproc(cmd, log_fh, **kw):
        if cmd[0] == sys.executable:
            calls.append(cmd)
            return 78, "[TOOLCHAIN ERROR] wine timeout\n"
        return 0, "ok\n"
    monkeypatch.setattr(overnight, "_run_subprocess_logged", subproc)
    e.item2 = dict(e.item, key=(overnight.WAVE4_MODE, "mod_x", (0x20,)), addrs=[0x20], area="w4_20")
    monkeypatch.setattr(overnight, "build_queue", lambda **kw: [e.item, e.item2])
    rc = e.run()
    assert len(calls) == 1 and rc == 78       # the second function is never started
    assert e.log() == ["init"]


@pytest.fixture
def retry_env(tmp_path, monkeypatch):
    build_queue = overnight.build_queue
    e = Env(tmp_path, monkeypatch)
    monkeypatch.setattr(overnight, "build_queue", build_queue)
    compiler = e.repo / "original" / "watcom" / "10.0a"
    monkeypatch.setattr(oldcc, "root", lambda: str(compiler))
    monkeypatch.delenv("INCLUDE", raising=False)
    monkeypatch.delenv("WCC386", raising=False)
    for fn in (compiler / "binnt/wcc386.exe", compiler / "binb/wcc386.exe", e.repo / "original/install/war.exe"):
        fn.parent.mkdir(parents=True, exist_ok=True)
        fn.write_bytes(b"fixture")
    e.cand = dict(c(0x10), link_name="F_", declared_cc="10.0a", declared_cflags="-s -od")
    monkeypatch.setattr(wave4, "discover", fake_discover([e.cand]))
    return e


def miss(**overrides):
    data = dict(outcome=wave4.NO_IMPROVEMENT, llm_calls=2, complete_search=True,
                history=[{"call": 0, "status": "MISMATCH"}, {"call": 1}, {"call": 2}])
    data.update(overrides)
    return wave4.write_outcome(0x10, **data)


def test_completed_miss_is_reused_across_invocations_and_unrelated_commits(retry_env):
    e = retry_env
    e.behaviour = miss
    assert e.run() == 0 and len(e.cmds) == 1
    previous = wave4.read_outcome(0x10)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "unrelated"], cwd=e.repo, check=True)
    assert e.run() == 0 and len(e.cmds) == 1
    assert "1 cached Wave 4 misses" in e.state()["status_detail"]
    assert wave4.read_outcome(0x10) == previous
    assert e.run(wave4_retry=True) == 0 and len(e.cmds) == 2
    old, = (e.repo / "build/wave4/history/10").glob("*.json")
    assert json.loads(old.read_text()) == previous


@pytest.mark.parametrize("change", ["source", "header", "compiler", "flags", "presets", "model", "effort",
                                    "provider", "budget", "cost", "version", "function", "siblings"])
def test_cache_invalidation(retry_env, monkeypatch, change):
    e = retry_env
    src, hdr = e.repo / e.cand["ref"], e.repo / "src/include/dependency.h"
    hdr.parent.mkdir()
    hdr.write_text("#define VALUE 1\n")
    src.write_text('#include "dependency.h"\n' + src.read_text())
    config = ["claude", ("sonnet", "medium"), 2, 1.1]
    cache = wave4.RetryCache(*config)
    old_key = cache.fingerprint(e.cand, [e.cand])
    cache.remember(0x10, old_key, miss())
    assert cache.contains(0x10, old_key)
    siblings = [e.cand]
    if change == "source":
        src.write_text(src.read_text().replace("return 1", "return 2"))
    elif change == "header":
        hdr.write_text("#define VALUE 2\n")
    elif change == "compiler":
        (Path(oldcc.root()) / "binb/wcc386.exe").write_bytes(b"alternate")
    elif change == "flags":
        e.cand["declared_cflags"] = "-s -ot"
    elif change == "presets":
        monkeypatch.setattr(wave4.t3_audit, "attempt_plan", lambda flags: [("declared", flags)])
    elif change == "model":
        config[1] = ("opus", "medium")
    elif change == "effort":
        config[1] = ("sonnet", "high")
    elif change == "provider":
        config[0] = "codex"
    elif change == "budget":
        config[2] = 3
    elif change == "cost":
        config[3] = 2.2
    elif change == "version":
        monkeypatch.setattr(wave4, "RECOVERY_VERSION", wave4.RECOVERY_VERSION + 1)
    elif change == "function":
        e.cand["link_name"] = "Other_"
    elif change == "siblings":
        siblings.append(dict(e.cand, addr=0x20, link_name="Sibling_"))
    current = wave4.RetryCache(*config)
    new_key = current.fingerprint(e.cand, siblings)
    assert new_key and new_key != old_key and not current.contains(0x10, new_key)


def test_missing_inputs_and_malformed_records_are_safe(retry_env):
    e = retry_env
    cache = wave4.RetryCache("claude", ("sonnet", "medium"), 2)
    key = cache.fingerprint(e.cand, [e.cand])
    assert not cache.contains(0x10, key)
    cache.remember(0x10, key, miss())
    fn = Path(cache._file(0x10, key))
    for bad in ("{truncated", "[]", json.dumps({"fingerprint": key}),
                json.dumps({"fingerprint": key, "settings": cache.settings, "result": {"outcome": "NO_IMPROVEMENT"}})):
        fn.write_text(bad)
        assert not cache.contains(0x10, key)
    (e.repo / e.cand["ref"]).write_text('#include "not-installed.h"\n')
    assert cache.fingerprint(e.cand, [e.cand]) is None


@pytest.mark.parametrize("rc,overrides", [
    (1, {}), (overnight.batch_driver.EXIT_QUOTA_STOP, {}), (overnight.batch_driver.EXIT_RATE_LIMIT, {}),
    (78, {"outcome": wave4.TOOLCHAIN_ERROR}), (0, {"outcome": wave4.FAILED}),
    (0, {"outcome": wave4.UNBUILDABLE}), (0, {"complete_search": False}), (0, {"llm_calls": 1}),
])
def test_transient_or_incomplete_attempts_do_not_suppress_next_run(retry_env, rc, overrides):
    e = retry_env
    e.worker_rc, e.behaviour = rc, lambda: miss(**overrides)
    e.run(sleep_on_limit=False)
    assert not list((e.repo / "build/wave4/retry").glob("*/*.json"))
    e.worker_rc, e.behaviour = 0, miss
    e.run()
    assert len(e.cmds) == 2
