"""Wave 4 (T4 -> T3 recovery): discovery, ordering, promotion, one-function pipeline (all fakes)."""
import json
import os
import types

import pytest

from wc1 import t3_audit, wave4

REF = "src/mod_x/f.c"
VB = "difftest: tests/test_x_t4.py::test_f"


def cand(addr, ref=REF, tier="T4", name=None, blocker=None, skip=None, vb=VB):
    return {"addr": addr, "addr_hex": f"{addr:#x}", "name": name or f"F{addr:x}", "tier": tier, "ref": ref,
            "skip_reason": skip, "ref_verified_by": vb, "t3_blocker": blocker, "toml": "analysis/symbols/m.toml",
            "declared_cflags": "-s -od"}


def inputs_for(cs):
    p = types.SimpleNamespace(functions=[{"start": c["addr"], "ninsns": 10 + i} for i, c in enumerate(cs)])
    return p, [], {}, [], []


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(wave4, "path", lambda *parts: os.path.join(str(tmp_path), *parts))
    (tmp_path / "src" / "mod_x").mkdir(parents=True)
    (tmp_path / "src" / "mod_x" / "f.c").write_text("/* codegen-compiler: ow2 */\nint f(void) { return 1; }\n")
    (tmp_path / "analysis" / "symbols").mkdir(parents=True)
    return tmp_path


def fake_discover(monkeypatch, cs):
    monkeypatch.setattr(t3_audit, "discover", lambda funcs, rows: (cs, []))


# 1 ---------------------------------------------------------------------------------------------
def test_discover_only_eligible_t4(monkeypatch):
    cs = [cand(0x10), cand(0x20, tier="T3"), cand(0x30, skip="no ref file"), cand(0x40, ref=None),
          cand(0x50, vb="garbage"), cand(0x60)]
    fake_discover(monkeypatch, cs)
    q, info = wave4.discover(inputs=inputs_for(cs), report_state="missing")
    assert [c["addr"] for c in q] == [0x10, 0x60]
    assert info["report"] == "missing" and info["eligible"] == 2
    assert q[0]["ninsns"] == 10 and q[0]["group"] == 2


def test_order_groups_with_fresh_report(monkeypatch):
    cs = [cand(0x10), cand(0x20), cand(0x30), cand(0x40, blocker="x"), cand(0x50)]
    fake_discover(monkeypatch, cs)
    rep = {"results": [
        {"addr": 0x10, "status": "MATCH_UNBUILDABLE"},
        {"addr": 0x20, "status": "MISMATCH", "best": {"score": [5, 1]}},
        {"addr": 0x30, "status": "MATCH_BUILDABLE"},
        {"addr": 0x50, "status": "MISMATCH", "best": {"score": [2, 9]}}]}
    q, info = wave4.discover(inputs=inputs_for(cs), report=rep, report_state="fresh")
    assert [c["addr"] for c in q] == [0x30, 0x50, 0x20, 0x40, 0x10]
    assert [c["group"] for c in q] == [0, 1, 1, 2, 3]
    # a stale report is ignored: deterministic fallback, never-tried (no blocker) first, then by address
    q2, info2 = wave4.discover(inputs=inputs_for(cs), report=rep, report_state="stale")
    assert [c["addr"] for c in q2] == [0x10, 0x20, 0x30, 0x50, 0x40]
    assert all(c["group"] == 2 and c["audit_status"] is None for c in q2)
    assert q2 == wave4.discover(inputs=inputs_for(cs), report=rep, report_state="stale")[0]


# 6 ---------------------------------------------------------------------------------------------
def test_load_report_states(tmp_path):
    fn = tmp_path / "report.json"
    assert wave4.load_report(str(fn), head="H", dirty=False)[0] == "missing"
    fn.write_text("{not json")
    assert wave4.load_report(str(fn), head="H", dirty=False)[0] == "invalid"
    fn.write_text(json.dumps({"meta": {}, "results": []}))
    assert wave4.load_report(str(fn), head="H", dirty=False)[0] == "invalid"

    def rep(**meta):
        m = {"git_commit": "H", "git_dirty": False, "completion": {"status": "complete"}}
        m.update(meta)
        fn.write_text(json.dumps({"meta": m, "results": []}))
        return wave4.load_report(str(fn), head="H", dirty=False)[0]
    assert rep() == "fresh"
    assert rep(git_commit="OLD") == "stale"
    assert rep(git_dirty=True) == "stale"
    assert rep(completion={"status": "partial"}) == "stale"
    assert wave4.load_report(str(fn), head="H", dirty=True)[0] == "stale"


def test_next_candidate_skips_attempted():
    q = [cand(1), cand(2), cand(3)]
    assert wave4.next_candidate(q)["addr"] == 1
    assert wave4.next_candidate(q, {1, 2})["addr"] == 3
    assert wave4.next_candidate(q, {1, 2, 3}) is None


# promotion text --------------------------------------------------------------------------------
TOML = '''[[func]]
addr = 0x10
name = "F"
confidence = "high"
ref = "src/mod_x/f.c"
ref_verified_by = "difftest: tests/test_x_t4.py::test_f"
t3_blocker = "diff at 0x4"
evidence = [
  "old line",
]

[[func]]
addr = 0x20
name = "G"
confidence = "high"
evidence = [
  "other",
]
'''


def test_promote_toml_text_rewrites_only_that_block():
    out = wave4.promote_toml_text(TOML, 0x10, REF, "match: x", "new ev")
    assert 'src = "src/mod_x/f.c"' in out and 'verified_by = "match: x"' in out
    assert 'confidence = "verified"' in out and '"new ev",' in out
    first, second = out.split("[[func]]\n")[1:]
    assert "ref =" not in first and "ref_verified_by" not in first and "t3_blocker" not in first
    assert second == TOML.split("[[func]]\n")[2]
    for bad in (out, TOML.replace("addr = 0x10", "addr = 0x99")):
        with pytest.raises(ValueError):
            wave4.promote_toml_text(bad, 0x10, REF, "m", "e")


T4_BOTH = '''[[func]]
addr = 0x30
name = "H"
ref = "src/mod_x/f.c"
conv = "watcall"
confidence = "verified"
verified_by = "difftest: tests/test_x.py::test_h (orig run)"
ref_verified_by = "difftest: tests/test_x_t4.py::test_h"
t3_blocker = "diff at 0x4"
evidence = [
  "old line",
]

[[func]]
addr = 0x40
name = "I"
confidence = "high"
evidence = [
  "other",
]
'''


def test_promote_toml_text_replaces_existing_verified_by_without_duplicate_keys():
    import tomllib
    out = wave4.promote_toml_text(T4_BOTH, 0x30, REF, "match: x", "new ev")
    doc = tomllib.loads(out)                      # raises on a duplicate key
    h, i = doc["func"]
    assert h["verified_by"] == "match: x" and h["src"] == REF and h["confidence"] == "verified"
    assert not {"ref", "ref_verified_by", "t3_blocker"} & set(h)
    ev = " | ".join(h["evidence"])
    assert "old line" in ev and "new ev" in ev
    assert "difftest: tests/test_x.py::test_h (orig run)" in ev          # old verified_by kept as evidence
    assert out.split("[[func]]\n")[2] == T4_BOTH.split("[[func]]\n")[2]


def test_full_promotion_path_with_preexisting_verified_by(repo):
    import tomllib
    (repo / "analysis" / "symbols" / "m.toml").write_text(T4_BOTH)
    row = {"addr": 0x30, "ref": REF, "toml": "analysis/symbols/m.toml", "match_flags": "-s -od",
           "ref_verified_by": "difftest: tests/test_x_t4.py::test_h"}
    assert wave4.promote([row]) == [(0x30, "analysis/symbols/m.toml")]
    doc = tomllib.loads((repo / "analysis" / "symbols" / "m.toml").read_text())
    assert doc["func"][0]["verified_by"].startswith("match: python3 -m wc1.match")
    ev = " | ".join(doc["func"][0]["evidence"])
    assert "tests/test_x_t4.py::test_h still runs" in ev and "difftest: tests/test_x.py::test_h (orig run)" in ev
    assert (repo / "src" / "mod_x" / "f.c").read_text().startswith(
        "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -od */\n")


def test_promote_is_all_or_nothing_and_handles_same_toml_rows(repo):
    import tomllib
    two = T4_BOTH.replace('addr = 0x40\nname = "I"\nconfidence = "high"', 'addr = 0x40\nname = "I"\nref = "src/mod_x/f.c"\n'
                          'ref_verified_by = "difftest: t::i"\nconfidence = "high"')
    fn = repo / "analysis" / "symbols" / "m.toml"
    fn.write_text(two)
    mk = lambda a: {"addr": a, "ref": REF, "toml": "analysis/symbols/m.toml", "match_flags": "-s",
                    "ref_verified_by": "difftest: t::x"}
    wave4.promote([mk(0x30), mk(0x40)])
    doc = tomllib.loads(fn.read_text())
    assert all(f["verified_by"].startswith("match:") and f["src"] == REF for f in doc["func"])
    fn.write_text(two)
    with pytest.raises(ValueError):
        wave4.promote([mk(0x30), mk(0x99)])
    assert fn.read_text() == two                  # first row not written


def test_set_flags_header_replaces_existing():
    t = "/* codegen-compiler: ow2 */\n/* codegen-flags: -od */\nint x;\n"
    assert wave4.set_flags_header(t, "10.0a", "-s -oa") == (
        "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -oa */\nint x;\n")
    assert wave4.set_flags_header("int x;\n", "10.0a", "-s").startswith("/* codegen-compiler: 10.0a */\n")


# pipeline --------------------------------------------------------------------------------------
def row(c, status, score=None, **kw):
    r = {"addr": c["addr"], "name": c["name"], "ref": c["ref"], "toml": c["toml"], "status": status,
         "ref_verified_by": c["ref_verified_by"], "match_flags": "-s -oa", "reason": None}
    if score is not None:
        r["best"] = {"score": score, "counts": {}, "first_diff": "mov", "diff": ["- a", "+ b"], "cflags": "-s"}
    r.update(kw)
    return r


class Audit:
    """Scripted t3_audit.audit_unit: one result list per call."""
    def __init__(self, monkeypatch, script):
        self.script, self.calls = list(script), 0
        monkeypatch.setattr(t3_audit, "audit_unit", self)

    def __call__(self, ctx, unit):
        self.calls += 1
        r = self.script.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def setup_toml(repo):
    (repo / "analysis" / "symbols" / "m.toml").write_text(TOML)


# 7 ---------------------------------------------------------------------------------------------
def test_exact_buildable_promotes_without_llm(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    Audit(monkeypatch, [[row(c, "MATCH_BUILDABLE")]])
    seen = []
    out = wave4.run_recovery(c, [], None, llm=lambda *a: pytest.fail("no LLM for an exact match"),
                             difftests=lambda nodes: (seen.append(nodes) or True, "ok"))
    assert out["outcome"] == wave4.PROMOTED and out["promoted"] == ["0x10"] and out["llm_calls"] == 0
    assert out["tomls"] == ["analysis/symbols/m.toml"] and out["patched"] is False
    assert seen == [["tests/test_x_t4.py::test_f"]]
    toml = (repo / "analysis" / "symbols" / "m.toml").read_text()
    assert 'src = "src/mod_x/f.c"' in toml and "ref_verified_by" not in toml.split("[[func]]")[1]
    ref = (repo / REF).read_text()
    assert ref.startswith("/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -oa */\n")
    assert wave4.read_outcome(0x10)["outcome"] == wave4.PROMOTED


def test_sibling_entries_promoted_together(repo, monkeypatch):
    setup_toml(repo)
    c1, c2 = cand(0x10), cand(0x20, vb="difftest: tests/test_x_t4.py::test_g")
    t = (repo / "analysis" / "symbols" / "m.toml")
    t.write_text(TOML.replace('confidence = "high"\nevidence = [\n  "other"',
                              'confidence = "high"\nref = "src/mod_x/f.c"\n'
                              'ref_verified_by = "difftest: tests/test_x_t4.py::test_g"\nevidence = [\n  "other"'))
    Audit(monkeypatch, [[row(c1, "MATCH_BUILDABLE"), row(c2, "MATCH_BUILDABLE")]])
    out = wave4.run_recovery(c1, [c2], None, difftests=lambda n: (True, ""))
    assert out["promoted"] == ["0x10", "0x20"]


# 8 ---------------------------------------------------------------------------------------------
def test_mismatch_without_llm_keeps_t4(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    toml_before = (repo / "analysis" / "symbols" / "m.toml").read_text()
    Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])]])
    out = wave4.run_recovery(c, [], None, llm=None)
    assert out["outcome"] == wave4.NO_IMPROVEMENT and out["llm_calls"] == 0
    assert (repo / REF).read_bytes() == before
    assert (repo / "analysis" / "symbols" / "m.toml").read_text() == toml_before


def test_repair_loop_bounded_and_restores(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    a = Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])], [row(c, "MISMATCH", [9, 9])],
                            [row(c, "MISMATCH", [9, 9])], [row(c, "MISMATCH", [9, 9])]])
    prompts = []

    def llm(prompt, schema, label):
        prompts.append(label)
        return {"diagnosis": "d", "patches": [{"old": "return 1;", "new": f"return {len(prompts) + 1};"}]}
    out = wave4.run_recovery(c, [], None, llm=llm, max_calls=2, difftests=lambda n: (True, ""))
    assert out["outcome"] == wave4.NO_IMPROVEMENT and out["llm_calls"] == 2 == len(prompts)
    assert a.calls == 3                     # initial audit + one per applied patch
    assert (repo / REF).read_bytes() == before


def test_repair_that_reaches_exact_match_is_promoted_and_marked_patched(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])], [row(c, "MATCH_BUILDABLE")]])
    llm = lambda p, s, l: {"patches": [{"old": "return 1;", "new": "return 2;"}]}
    out = wave4.run_recovery(c, [], None, llm=llm, difftests=lambda n: (True, ""))
    assert out["outcome"] == wave4.PROMOTED and out["patched"] is True and out["llm_calls"] == 1
    assert "return 2;" in (repo / REF).read_text()


def test_repair_rejects_header_edit_and_unmatched_patch(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    a = Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])]])
    replies = iter([{"patches": [{"old": "codegen-compiler: ow2", "new": "codegen-compiler: 10.0a"}]},
                    {"patches": [{"old": "not in file", "new": "x"}]}])
    out = wave4.run_recovery(c, [], None, llm=lambda *x: next(replies), max_calls=2)
    assert out["outcome"] == wave4.NO_IMPROVEMENT and a.calls == 1     # nothing compiled for rejected patches
    assert [h.get("rejected") for h in out["history"][1:]] == ["patch touched the codegen headers",
                                                              "no patch applied"]
    assert (repo / REF).read_bytes() == before


def test_worse_patch_returns_to_best_text(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])], [row(c, "MISMATCH", [9, 9])], [row(c, "MATCH_BUILDABLE")]])
    seen = []

    def llm(prompt, schema, label):
        seen.append(prompt)
        return {"patches": [{"old": "return 1;", "new": "return 5;"}]} if len(seen) == 1 else \
            {"patches": [{"old": "return 1;", "new": "return 7;"}]}
    out = wave4.run_recovery(c, [], None, llm=llm, max_calls=2, difftests=lambda n: (True, ""))
    assert out["outcome"] == wave4.PROMOTED
    assert "return 5" not in seen[1].split("Current file:")[1]
    text = (repo / REF).read_text()
    assert "return 7;" in text and "return 5;" not in text


# 9 ---------------------------------------------------------------------------------------------
def test_unbuildable_match_not_promoted_and_no_llm(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    Audit(monkeypatch, [[row(c, "MATCH_UNBUILDABLE", reason="sibling mismatches")]])
    out = wave4.run_recovery(c, [], None, llm=lambda *a: pytest.fail("no LLM"), difftests=lambda n: (True, ""))
    assert out["outcome"] == wave4.UNBUILDABLE and "sibling" in out["reason"]
    assert (repo / REF).read_bytes() == before
    assert "src =" not in (repo / "analysis" / "symbols" / "m.toml").read_text()


def test_difftest_failure_blocks_promotion(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    Audit(monkeypatch, [[row(c, "MATCH_BUILDABLE")]])
    out = wave4.run_recovery(c, [], None, difftests=lambda n: (False, "1 failed"))
    assert out["outcome"] == wave4.FAILED and "difftest" in out["reason"]
    assert (repo / REF).read_bytes() == before
    assert "src =" not in (repo / "analysis" / "symbols" / "m.toml").read_text()


# 11 --------------------------------------------------------------------------------------------
def test_toolchain_abort_is_toolchain_error_and_restores(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])], t3_audit.ToolchainAbort("wine timeout")])
    llm = lambda p, s, l: {"patches": [{"old": "return 1;", "new": "return 2;"}]}
    out = wave4.run_recovery(c, [], None, llm=llm)
    assert out["outcome"] == wave4.TOOLCHAIN_ERROR and "wine" in out["reason"]
    assert (repo / REF).read_bytes() == before
    Audit(monkeypatch, [t3_audit.ToolchainAbort("compile timeout")])
    assert wave4.run_recovery(c, [], None)["outcome"] == wave4.TOOLCHAIN_ERROR


def test_llm_exception_propagates_after_restore(repo, monkeypatch):
    setup_toml(repo)
    c = cand(0x10)
    before = (repo / REF).read_bytes()
    Audit(monkeypatch, [[row(c, "MISMATCH", [3, 1])], [row(c, "MISMATCH", [3, 1])]])

    class RateLimited(Exception):
        pass

    def llm(p, s, l):
        with open(repo / REF, "a") as fh:      # a half-applied edit must not survive the abort
            fh.write("// junk\n")
        raise RateLimited()
    with pytest.raises(RateLimited):
        wave4.run_recovery(c, [], None, llm=llm)
    assert (repo / REF).read_bytes() == before


# 12 --------------------------------------------------------------------------------------------
def test_outcome_roundtrip_and_clear(repo):
    assert wave4.read_outcome(0x10) is None
    wave4.write_outcome(0x10, wave4.NO_IMPROVEMENT, reason="r")
    assert wave4.read_outcome(0x10)["outcome"] == wave4.NO_IMPROVEMENT
    wave4.clear_outcome(0x10)
    assert wave4.read_outcome(0x10) is None
    wave4.clear_outcome(0x10)               # idempotent


def test_all_passed_rejects_skips_and_xfails():
    assert wave4._all_passed("..\n2 passed in 0.1s", 2)
    assert not wave4._all_passed("1 skipped in 0.1s", 1)
    assert not wave4._all_passed("1 passed, 1 skipped in 0.1s", 2)
    assert not wave4._all_passed("1 passed, 1 xfailed in 0.1s", 1)
    assert not wave4._all_passed("", 1)


def test_difftest_timeout_is_a_failure_not_a_crash(monkeypatch):
    import subprocess

    def boom(*a, **k):
        raise subprocess.TimeoutExpired("pytest", 900)
    monkeypatch.setattr(wave4.subprocess, "run", boom)
    ok, detail = wave4.run_difftests([{"ref_verified_by": "difftest: tests/test_x.py::test_a"}])
    assert not ok and "timeout" in detail
