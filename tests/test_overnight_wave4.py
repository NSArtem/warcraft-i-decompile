"""Wave 4 integration in wc1.overnight: queue, command, success predicate, rollback, CLI (fakes only)."""
import os
import subprocess
import sys

import pytest

from wc1 import live, overnight, path, wave4


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
    a = ap.parse_args(["--headless", "--wave", "wave4", "--wave4-max-calls", "3", "--max-modules", "1"])
    assert a.wave == "wave4" and a.wave4_max_calls == 3 and a.max_modules == 1
    base = {"window_budget": 1.0, "window_capacity": 35.0, "max_modules": 1, "wave": "wave4",
            "wave4_max_calls": 3, "chunk_size": 10, "module_budget": 1.0, "module_calls": 8,
            "repair_budget": 0.3, "skip": (), "only": (), "sleep_on_limit": False, "rate_limit_sleep": 600}
    args = overnight.build_cli_args(base)
    p = ap.parse_args(args)
    assert p.wave == "wave4" and p.wave4_max_calls == 3
    assert "--wave4-max-calls" not in overnight.build_cli_args(dict(base, wave="all"))
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
        self.cmds, self.verify_rc = [], 0
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
        monkeypatch.setattr(overnight, "_run_subprocess_logged", self.subproc)
        self.behaviour = lambda: None

    def subproc(self, cmd, log_fh, cwd=None, controller=None, worker_id=None, event_kind="info", **_kw):
        if cmd[0] == sys.executable:
            self.cmds.append(list(cmd))
            self.behaviour()
            return 0, "ok\n"
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


def test_verify_without_identical_build_is_not_committed(tmp_path, monkeypatch):
    e = Env(tmp_path, monkeypatch)
    e.behaviour = e.promote
    orig = e.subproc
    monkeypatch.setattr(overnight, "_run_subprocess_logged",
                        lambda cmd, *a, **k: (0, "100 passed\n") if cmd[0] != sys.executable else orig(cmd, *a, **k))
    e.run()
    assert e.log() == ["init"]
    assert (e.repo / "src" / "mod_x" / "f.c").read_text() == REF0


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
