"""Unit & runner-integration tests for Wave 4A reconciliation, Wave 4B routing, and caching."""
import json
import os
import subprocess
import types

import pytest

from wc1 import batch_driver, overnight, symbols, t3_audit, wave4, wave4_deps, wave4a


def _write(root, rel, text):
    fn = root / rel
    fn.parent.mkdir(parents=True, exist_ok=True)
    fn.write_text(text)
    return fn


def _row(addr, name, ref, toml, status="MISMATCH", unres=(), score=(0, 0, 0, 0, 0), flags="-s -ot -ol -4r -zp2"):
    best = {"index": 0, "cflags": flags, "score": list(score), "unresolved": list(unres)}
    return {
        "addr": addr, "addr_hex": f"{addr:#x}", "tier": "T4",
        "name": name, "link_name": f"{name}_", "ref": ref, "toml": toml,
        "module": "MOD.C", "status": status, "match_flags": flags if status == "MATCH_BUILDABLE" else None,
        "ref_verified_by": "difftest: tests/test_mod.py::test_fn",
        "best": best, "attempts": [best],
    }


def _patch_root(monkeypatch, root):
    monkeypatch.setattr(wave4a, "path", lambda *p: os.path.join(str(root), *p))
    monkeypatch.setattr(wave4, "path", lambda *p: os.path.join(str(root), *p))
    monkeypatch.setattr(wave4_deps, "path", lambda *p: os.path.join(str(root), *p))
    monkeypatch.setattr(symbols, "path", lambda *p: os.path.join(str(root), *p))


# ---------------------------------------------------------------------------
# Wave 4A mechanical reconciliation (0 LLM) & auto-promotion
# ---------------------------------------------------------------------------

def test_mechanical_func_rename_promotes_without_llm_and_records_mapping(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/caller_reference.c"
    toml = "analysis/symbols/m.toml"
    _write(tmp_path, ref, "/* codegen-compiler: 10.0a */\nextern void fn_20000(void);\nvoid Caller(void) { fn_20000(); }\n")
    _write(tmp_path, toml, f"""[[func]]
addr = 0x10000
name = "Caller"
conv = "watcall"
proto = "void Caller(void)"
module = "CMD.C"
confidence = "high"
ref = "{ref}"
ref_verified_by = "difftest: tests/test_mod.py::test_fn"
t3_blocker = "codegen: unresolved fn_20000_"
evidence = ["test"]
""")
    _write(tmp_path, "tests/test_mod.py", "def test_fn(): pass\n")
    item = {
        "group_id": "func_20000", "task_kind": "reconcile", "mechanical": True,
        "classification": wave4_deps.MECHANICAL_FUNC_RENAME, "kind": "function",
        "symbols": ["fn_20000_"], "affected_refs": [ref], "target_address": 0x20000,
        "dependencies": [{
            "symbol": "fn_20000_", "ident": "fn_20000", "kind": "function",
            "expected_address": 0x20000,
            "db_entry": {"addr": 0x20000, "name": "RealCallee", "link_name": "RealCallee_"},
            "affected_functions": [{"addr": 0x10000, "addr_hex": "0x10000", "ref": ref,
                                    "decls": [{"file": ref, "line": 2, "text": "extern void fn_20000(void);", "in_ref": True}]}],
        }],
    }
    calls = {"aud": 0}

    def fake_audit(refs, inputs=None, objdir=None):
        calls["aud"] += 1
        if calls["aud"] == 1:
            r = _row(0x10000, "Caller", ref, toml, "MISMATCH", unres=[{"symbol": "fn_20000_"}])
        else:
            assert "RealCallee();" in (tmp_path / ref).read_text()
            r = _row(0x10000, "Caller", ref, toml, "MATCH_BUILDABLE", unres=[])
        return {ref: [r]}, [r]

    llm_called = []
    out = wave4a.run_reconciliation(
        item,
        llm=lambda *a: llm_called.append(a),
        max_calls=2,
        compile_checker=lambda files: (True, ""),
        audit_runner=fake_audit,
        difftest_runner=lambda nodes: (True, "1 passed"),
    )
    assert out["outcome"] == wave4a.PROMOTED, out
    assert out["method"] == "mechanical" and out["llm_calls"] == 0
    assert not llm_called
    assert out["promoted"] == ["0x10000"]
    assert f'src = "{ref}"' in (tmp_path / toml).read_text()
    # Mapping is emitted in receipt, NOT persisted to mappings.json until commit!
    assert wave4a.load_mappings()["mappings"] == {}
    assert wave4a.persist_outcome_mappings(out) == 1
    maps = wave4a.load_mappings()["mappings"]
    assert maps["fn_20000_"]["canonical_name"] == "RealCallee"
    assert maps["fn_20000_"]["target_addr"] == 0x20000


def test_mechanical_data_rename_reconciles_intermediate_without_immediate_t3(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/a_reference.c"
    toml = "analysis/symbols/m.toml"
    _write(tmp_path, ref, "/* codegen-compiler: 10.0a */\nextern long old_seed;\nvoid Set(long x) { old_seed = x; }\n")
    _write(tmp_path, "tests/test_mod.py", "def test_fn(): pass\n")
    item = {
        "group_id": "data_50d7c", "task_kind": "reconcile", "mechanical": True,
        "classification": wave4_deps.MECHANICAL_DATA_RENAME, "kind": "data",
        "symbols": ["_old_seed"], "affected_refs": [ref], "target_address": 0x50d7c,
        "dependencies": [{
            "symbol": "_old_seed", "ident": "old_seed", "kind": "data",
            "expected_address": 0x50d7c,
            "db_entry": {"addr": 0x50d7c, "name": "dat_50d7c", "link_name": "_dat_50d7c"},
            "affected_functions": [{"addr": 0x19470, "addr_hex": "0x19470", "ref": ref,
                                    "decls": [{"file": ref, "line": 2, "text": "extern long old_seed;", "in_ref": True}]}],
        }],
    }
    step = {"n": 0}

    def fake_audit(refs, inputs=None, objdir=None):
        step["n"] += 1
        if step["n"] == 1:
            r = _row(0x19470, "Set", ref, toml, "MISMATCH", unres=[{"symbol": "_old_seed"}], score=(3, 0, 0, 0, 0))
        else:
            # Unresolved count dropped 1 -> 0, but genuine regalloc codegen diff remains!
            r = _row(0x19470, "Set", ref, toml, "MISMATCH", unres=[], score=(3, 0, 0, 0, 0))
        return {ref: [r]}, [r]

    out = wave4a.run_reconciliation(
        item, llm=None, max_calls=0,
        compile_checker=lambda files: (True, ""),
        audit_runner=fake_audit,
        difftest_runner=lambda nodes: (True, "1 passed"),
    )
    assert out["outcome"] == wave4a.RECONCILED
    assert out["method"] == "mechanical" and out["llm_calls"] == 0
    assert out["unresolved_before"] == 1 and out["unresolved_after"] == 0
    assert out["promoted"] == []
    assert "dat_50d7c = x;" in (tmp_path / ref).read_text()


def test_auto_promote_promotes_already_buildable_with_zero_llm(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/ok_reference.c"
    toml = "analysis/symbols/m.toml"
    _write(tmp_path, ref, "/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -ol -4r -zp2 */\nvoid Ok(void) {}\n")
    _write(tmp_path, toml, f"""[[func]]
addr = 0x10000
name = "Ok"
conv = "watcall"
proto = "void Ok(void)"
module = "CMD.C"
confidence = "high"
ref = "{ref}"
ref_verified_by = "difftest: tests/test_mod.py::test_fn"
t3_blocker = "stale"
evidence = ["test"]
""")
    item = {"group_id": "promote_10000", "task_kind": "auto_promote", "affected_refs": [ref]}
    r = _row(0x10000, "Ok", ref, toml, "MATCH_BUILDABLE", unres=[])
    out = wave4a.run_reconciliation(
        item, llm=None, max_calls=0,
        audit_runner=lambda refs, **kw: ({ref: [r]}, [r]),
        difftest_runner=lambda nodes: (True, "1 passed"),
    )
    assert out["outcome"] == wave4a.PROMOTED, out
    assert out["method"] == "auto_promote" and out["llm_calls"] == 0
    assert out["promoted"] == ["0x10000"]


# ---------------------------------------------------------------------------
# Wave 4A bounded LLM research, proposal safety, reprocessing & rollback
# ---------------------------------------------------------------------------

def test_research_adds_missing_symbol_reprocesses_extra_caller_and_promotes(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref1 = "src/m/a_reference.c"
    ref2 = "src/m/b_reference.c"
    toml = "analysis/symbols/m.toml"
    _write(tmp_path, ref1, "/* codegen-compiler: 10.0a */\nextern const char missing_str[11];\nvoid A(void) {}\n")
    _write(tmp_path, ref2, "/* codegen-compiler: 10.0a */\nextern const char order_err[11];\nvoid B(void) {}\n")
    _write(tmp_path, toml, f"""[[func]]
addr = 0x10000
name = "A"
conv = "watcall"
proto = "void A(void)"
confidence = "high"
ref = "{ref1}"
ref_verified_by = "difftest: tests/test_mod.py::test_fn"
t3_blocker = "codegen: missing data"
evidence = ["test"]

[[func]]
addr = 0x10020
name = "B"
conv = "watcall"
proto = "void B(void)"
confidence = "high"
ref = "{ref2}"
ref_verified_by = "difftest: tests/test_mod.py::test_fn"
t3_blocker = "codegen: missing data"
evidence = ["test"]
""")
    _write(tmp_path, "tests/test_mod.py", "# a_reference.c b_reference.c\ndef test_fn():\n    assert True\n")
    # Pre-seed audit_state.json so ref2 is known to depend on `_order_err`
    _write(tmp_path, "build/wave4/audit_state.json", json.dumps({
        "version": 1, "results": {},
        "unit_meta": {ref2: {"source_digest": "x", "deps": {"_order_err": None}}},
    }))

    fake_p = types.SimpleNamespace(functions=[], insns={}, fix_at={})
    monkeypatch.setattr(t3_audit, "load_inputs", lambda: (fake_p, {}, {}, [], []))
    item = {
        "group_id": "data_56b10", "task_kind": "reconcile", "mechanical": False,
        "classification": wave4_deps.MISSING_DATA, "kind": "data",
        "symbols": ["_missing_str"], "affected_refs": [ref1], "target_address": 0x56b10,
        "target_address_hex": "0x56b10",
        "affected_functions": [{"addr": 0x10000, "addr_hex": "0x10000", "name": "A", "ref": ref1, "toml": toml,
                                "ref_verified_by": "difftest: tests/test_mod.py::test_fn"}],
        "dependencies": [{"symbol": "_missing_str", "ident": "missing_str", "kind": "data",
                          "classification": wave4_deps.MISSING_DATA, "expected_address": 0x56b10,
                          "expected_address_hex": "0x56b10", "addends": [0], "relocation_kinds": []}],
    }
    seen_reprocess = []
    step = {"n": 0}

    def fake_audit(refs, inputs=None, objdir=None):
        step["n"] += 1
        if step["n"] == 1:
            r1 = _row(0x10000, "A", ref1, toml, "MISMATCH", unres=[{"symbol": "_missing_str"}])
            return {ref1: [r1]}, [r1]
        seen_reprocess.extend(refs)
        r1 = _row(0x10000, "A", ref1, toml, "MATCH_BUILDABLE", unres=[])
        r2 = _row(0x10020, "B", ref2, toml, "MATCH_BUILDABLE", unres=[])
        return {ref1: [r1], ref2: [r2]}, [r1, r2]

    def fake_llm(prompt, schema, label):
        return {
            "decision": "apply",
            "summary": "Add order_err at 0x56b10 and update ref1",
            "uncertainties": [],
            "toml_entries": [{
                "toml_file": toml,
                "toml_block": '[[data]]\naddr = 0x56b10\nname = "order_err"\ntype = "const char[11]"\nconfidence = "high"\nevidence = ["0x56b10 string"]\n',
            }],
            "file_patches": [{"path": ref1, "old": "missing_str", "new": "order_err"}],
        }

    out = wave4a.run_reconciliation(
        item, llm=fake_llm, max_calls=2,
        compile_checker=lambda files: (True, ""),
        audit_runner=fake_audit,
        difftest_runner=lambda nodes: (True, "2 passed"),
    )
    assert out["outcome"] == wave4a.PROMOTED, out
    assert out["method"] == "research" and out["llm_calls"] == 1
    # Dependency-driven reprocessing picked up ref2 automatically and promoted BOTH!
    assert ref2 in seen_reprocess
    assert set(out["promoted"]) == {"0x10000", "0x10020"}
    assert "order_err" in (tmp_path / toml).read_text()


def test_research_rejects_unsafe_proposals_and_restores_disk(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/a_reference.c"
    toml = "analysis/symbols/m.toml"
    orig_c = "/* codegen-compiler: 10.0a */\nextern void bad_fn(void);\nvoid A(void) { bad_fn(); }\n"
    orig_t = (
        f'[[func]]\naddr = 0x10000\nname = "A"\nconv = "watcall"\nproto = "void A(void)"\n'
        f'confidence = "high"\nref = "{ref}"\nref_verified_by = "difftest: tests/test_mod.py::test_fn"\n'
        f't3_blocker = "codegen: bad_fn"\nevidence = ["e"]\n\n'
        f'[[data]]\naddr = 0x59000\nname = "table"\ntype = "unsigned long[8]"\nconfidence = "high"\nevidence = ["tbl"]\n'
    )
    _write(tmp_path, ref, orig_c)
    _write(tmp_path, toml, orig_t)
    _write(tmp_path, "src/include/war.h", "/* protected */\n")
    _write(tmp_path, "analysis/symbols/clib.toml", "# clib\n")
    _write(tmp_path, "tests/test_mod.py", "# a_reference.c\ndef test_fn():\n    assert 1 == 1\n")
    scope = {"refs": [ref], "headers": [], "tests": ["tests/test_mod.py"], "tomls": [toml]}

    bad_proposals = [
        # Forbidden war.h
        {"toml_entries": [], "file_patches": [{"path": "src/include/war.h", "old": "protected", "new": "hacked"}]},
        # Protected clib.toml (must never allow runtime reclassification!)
        {"toml_entries": [{"toml_file": "analysis/symbols/clib.toml", "toml_block": '[[func]]\naddr = 0x20000\nname = "X"\nconv = "watcall"\nproto = "void X(void)"\nconfidence = "high"\nevidence = ["e"]\n'}], "file_patches": []},
        # Setting src= in toml_entries
        {"toml_entries": [{"toml_file": toml, "toml_block": '[[func]]\naddr = 0x20000\nname = "X"\nconv = "watcall"\nproto = "void X(void)"\nsrc = "src/x.c"\nconfidence = "high"\nevidence = ["e"]\n'}], "file_patches": []},
        # Setting verified_by= in toml_entries
        {"toml_entries": [{"toml_file": toml, "toml_block": '[[data]]\naddr = 0x56000\nname = "x"\ntype = "int"\nconfidence = "high"\nverified_by = "manual"\nevidence = ["e"]\n'}], "file_patches": []},
        # Promoting confidence to verified
        {"toml_entries": [{"toml_file": toml, "toml_block": '[[data]]\naddr = 0x56000\nname = "x"\ntype = "int"\nconfidence = "verified"\nevidence = ["e"]\n'}], "file_patches": []},
        # Duplicate interior [[data]] inside existing `table` (0x59000..0x59020)
        {"toml_entries": [{"toml_file": toml, "toml_block": '[[data]]\naddr = 0x59008\nname = "table_2"\ntype = "unsigned long"\nconfidence = "high"\nevidence = ["interior"]\n'}], "file_patches": []},
        # Modifying codegen-compiler header
        {"toml_entries": [], "file_patches": [{"path": ref, "old": "/* codegen-compiler: 10.0a */", "new": "/* codegen-compiler: ow2 */"}]},
        # Deleting an existing [[func]] via file_patches
        {"toml_entries": [], "file_patches": [{"path": toml, "old": orig_t, "new": "# empty\n"}]},
        # Test weakening (adding pytest.skip)
        {"toml_entries": [], "file_patches": [{"path": "tests/test_mod.py", "old": "assert 1 == 1", "new": "import pytest; pytest.skip('no')"}]},
    ]
    for prop in bad_proposals:
        txn = wave4a._FileTxn(repo_root=str(tmp_path))
        ok, _syms, err = wave4a._validate_and_apply_proposal(prop, scope, txn, repo_root=str(tmp_path))
        assert not ok, f"should have rejected {prop}"
        txn.restore()
        assert (tmp_path / ref).read_text() == orig_c
        assert (tmp_path / toml).read_text() == orig_t


def test_research_ambiguous_decision_is_cached_and_invalidated_on_input_change(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/a_reference.c"
    _write(tmp_path, ref, "/* codegen-compiler: 10.0a */\nvoid A(void) {}\n")
    fake_p = types.SimpleNamespace(functions=[], insns={}, fix_at={})
    monkeypatch.setattr(t3_audit, "load_inputs", lambda: (fake_p, {}, {}, [], []))
    item = {
        "group_id": "sym_mystery", "task_kind": "reconcile", "mechanical": False,
        "classification": wave4_deps.AMBIGUOUS, "kind": "function",
        "symbols": ["mystery_"], "affected_refs": [ref], "target_address": None,
        "affected_functions": [{"addr": 0x10000, "addr_hex": "0x10000", "name": "A", "ref": ref, "toml": "analysis/symbols/m.toml"}],
        "dependencies": [{"symbol": "mystery_", "ident": "mystery", "kind": "function", "classification": wave4_deps.AMBIGUOUS}],
    }
    r = _row(0x10000, "A", ref, "analysis/symbols/m.toml", "MISMATCH", unres=[{"symbol": "mystery_"}])
    out = wave4a.run_reconciliation(
        item,
        llm=lambda *a: {"decision": "ambiguous", "summary": "two candidates", "uncertainties": ["0x20 vs 0x30"], "toml_entries": [], "file_patches": []},
        max_calls=2,
        audit_runner=lambda refs, **kw: ({ref: [r]}, [r]),
    )
    assert out["outcome"] == wave4a.AMBIGUOUS and out["complete_search"] is True

    # Build a ReconcileCache with fake tool settings and verify hit + invalidation on source edit
    cache = wave4a.ReconcileCache("codex", ("gpt-x", "high"), max_calls=2)
    cache.settings = {"version": 1, "provider": "codex", "max_calls": 2}
    cache.system_headers = tmp_path / "sys_h"
    cache.system_headers.mkdir()
    fp1 = cache.fingerprint(item, "msig-1")
    assert fp1 is not None
    cache.remember("sym_mystery", fp1, out)
    assert cache.contains("sym_mystery", fp1)
    # Changing the C file invalidates the fingerprint
    _write(tmp_path, ref, "/* codegen-compiler: 10.0a */\nvoid A(void) { /* updated */ }\n")
    fp2 = cache.fingerprint(item, "msig-1")
    assert fp2 != fp1 and not cache.contains("sym_mystery", fp2)
    # Changing matcher signature (e.g. a symbol was added to DB) invalidates too
    assert cache.fingerprint(item, "msig-2") != fp2


# ---------------------------------------------------------------------------
# Wave 4B routing & prioritization
# ---------------------------------------------------------------------------

def test_wave4b_routes_unresolved_to_4a_and_ranks_pure_codegen_first(monkeypatch):
    c_pure = {
        "addr": 0x10000, "addr_hex": "0x10000", "name": "Pure", "ref": "src/a.c", "module": "M",
        "ninsns": 20, "tier": "T4", "skip_reason": None, "ref_verified_by": "difftest: tests/test_x.py::test_a",
    }
    c_unres = {
        "addr": 0x10040, "addr_hex": "0x10040", "name": "Unres", "ref": "src/b.c", "module": "M",
        "ninsns": 5, "tier": "T4", "skip_reason": None, "ref_verified_by": "difftest: tests/test_x.py::test_b",
    }
    rep = {
        "meta": {"completion": {"status": "complete"}},
        "results": [
            # Pure codegen near-miss with score [2, 0, 0, 0, 0]
            {"addr": 0x10000, "tier": "T4", "status": "MISMATCH", "best": {"score": [2, 0, 0, 0, 0], "unresolved": []}, "attempts": []},
            # Unresolved relocation with misleading [0, 0, 0, 0, 0] score!
            {"addr": 0x10040, "tier": "T4", "status": "MISMATCH", "best": {"score": [0, 0, 0, 0, 0], "unresolved": [{"symbol": "fn_99_"}]}, "attempts": []},
        ],
    }
    monkeypatch.setattr(t3_audit, "discover", lambda funcs, rows: ([c_pure, c_unres], []))
    fake_p = types.SimpleNamespace(functions=[{"start": 0x10000, "end": 0x10020, "ninsns": 20}, {"start": 0x10040, "end": 0x10050, "ninsns": 5}])
    inputs = (fake_p, {}, {}, [], [])

    # With exclude_unresolved=True (Wave 4B default): unresolved candidate is routed to 4A!
    q_clean, info_clean = wave4.discover(inputs=inputs, report=rep, report_state="fresh", exclude_unresolved=True)
    assert [c["addr"] for c in q_clean] == [0x10000]
    assert info_clean["routed_to_4a"] == 1

    # Even with exclude_unresolved=False: pure codegen (group 1) MUST rank ahead of unresolved (group 2)!
    q_all, _ = wave4.discover(inputs=inputs, report=rep, report_state="fresh", exclude_unresolved=False)
    assert [c["addr"] for c in q_all] == [0x10000, 0x10040]
    assert q_all[0]["group"] == 1 and q_all[1]["group"] == 2


# ---------------------------------------------------------------------------
# overnight.py Wave 4A progress policy, rollback & metrics
# ---------------------------------------------------------------------------

def test_overnight_wave4a_progress_policy_accepts_reconciled_and_rejects_zero_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(overnight, "path", lambda *p: os.path.join(str(tmp_path), *p))
    _write(tmp_path, "src/m/a.c", "void A(void) {}\n")
    before = {0x10000: {"c": "T4", "ref": "src/m/a.c", "src": None, "file": "analysis/symbols/m.toml"}}
    after_t4 = dict(before)
    after_t3 = {0x10000: {"c": "T3", "ref": None, "src": "src/m/a.c", "file": "analysis/symbols/m.toml"}}

    # 1. Verified intermediate RECONCILED (unresolved 2 -> 1, delta_t3 == 0) -> ACCEPTED
    assert overnight._wave4a_progress_ok(
        {}, {"outcome": "RECONCILED", "unresolved_before": 2, "unresolved_after": 1},
        before, after_t4, {"src/m/a.c"}, delta_done=0, delta_t3=0, delta_t4=0,
    )
    # 2. Zero-progress RECONCILED (unresolved 2 -> 2) -> REJECTED!
    assert not overnight._wave4a_progress_ok(
        {}, {"outcome": "RECONCILED", "unresolved_before": 2, "unresolved_after": 2},
        before, after_t4, {"src/m/a.c"}, delta_done=0, delta_t3=0, delta_t4=0,
    )
    # 3. TOML-only PROMOTED (C file untouched because flags already matched!) -> ACCEPTED
    assert overnight._wave4a_progress_ok(
        {}, {"outcome": "PROMOTED", "promoted": ["0x10000"]},
        before, after_t3, {"analysis/symbols/m.toml"}, delta_done=0, delta_t3=1, delta_t4=-1,
    )
    # 4. Dishonest PROMOTED (claims 0x10000 but TOML didn't transition) -> REJECTED
    assert not overnight._wave4a_progress_ok(
        {}, {"outcome": "PROMOTED", "promoted": ["0x10000"]},
        before, after_t4, {"analysis/symbols/m.toml"}, delta_done=0, delta_t3=0, delta_t4=0,
    )


def test_overnight_rollback_cleans_staged_new_files_in_git(tmp_path, monkeypatch):
    monkeypatch.setattr(overnight, "path", lambda *p: os.path.join(str(tmp_path), *p))

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()
    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "t@example.test")
    _write(tmp_path, "tracked.txt", "orig\n")
    git("add", "tracked.txt")
    git("commit", "-qm", "init")
    base = git("rev-parse", "HEAD")

    _write(tmp_path, "tracked.txt", "modified\n")
    _write(tmp_path, "src/include/new_hdr.h", "extern int x;\n")
    git("add", "src/include/new_hdr.h")

    # Exercise the real `_wave4_status()` -> `_rollback_tree()` pipeline (not manual sets!)
    tracked_now, untracked_now, staged_now = overnight._wave4_status()
    assert "src/include/new_hdr.h" in untracked_now and "src/include/new_hdr.h" in staged_now
    assert "src/include/new_hdr.h" not in tracked_now
    overnight._rollback_tree(tracked_now, untracked_now, cwd=str(tmp_path), restore_from=base)
    assert (tmp_path / "tracked.txt").read_text() == "orig\n"
    assert not (tmp_path / "src/include/new_hdr.h").exists()
    assert git("status", "--porcelain") == ""


def test_skipped_audit_status_does_not_count_as_improvement(tmp_path, monkeypatch):
    _patch_root(monkeypatch, tmp_path)
    ref = "src/m/a_reference.c"
    toml = "analysis/symbols/m.toml"
    orig_c = "/* codegen-compiler: 10.0a */\nextern long old_v;\nvoid A(void) { old_v = 1; }\n"
    _write(tmp_path, ref, orig_c)
    item = {
        "group_id": "data_50000", "task_kind": "reconcile", "mechanical": True,
        "classification": wave4_deps.MECHANICAL_DATA_RENAME, "kind": "data",
        "symbols": ["_old_v"], "affected_refs": [ref], "target_address": 0x50000,
        "dependencies": [{
            "symbol": "_old_v", "ident": "old_v", "kind": "data", "expected_address": 0x50000,
            "db_entry": {"addr": 0x50000, "name": "new_v", "link_name": "_new_v"},
            "affected_functions": [{"addr": 0x10000, "addr_hex": "0x10000", "ref": ref,
                                    "decls": [{"file": ref, "line": 2, "text": "extern long old_v;", "in_ref": True}]}],
        }],
    }
    step = {"n": 0}

    def fake_audit(refs, inputs=None, objdir=None):
        step["n"] += 1
        if step["n"] == 1:
            r = _row(0x10000, "A", ref, toml, "MISMATCH", unres=[{"symbol": "_old_v"}])
        else:
            # SKIPPED has best=None (0 unresolved) — MUST NOT falsely count as improved!
            r = {"addr": 0x10000, "status": "SKIPPED", "best": None, "attempts": []}
        return {ref: [r]}, [r]

    out = wave4a.run_reconciliation(
        item, llm=None, max_calls=0,
        compile_checker=lambda files: (True, ""),
        audit_runner=fake_audit,
    )
    assert out["outcome"] == wave4a.NO_IMPROVEMENT
    assert (tmp_path / ref).read_text() == orig_c


def test_toolchain_abort_propagates_through_wave4_discovery(monkeypatch):
    monkeypatch.setattr(overnight, "_wave4_is_real_discover", lambda fn: True)
    monkeypatch.setattr(wave4a, "load_audit_report_incremental", lambda **kw: (_ for _ in ()).throw(t3_audit.ToolchainAbort("wine hung")))
    with pytest.raises(t3_audit.ToolchainAbort):
        overnight.wave4_items()
    monkeypatch.setattr(overnight, "wave4a_items", lambda **kw: (_ for _ in ()).throw(t3_audit.ToolchainAbort("wine hung")))
    with pytest.raises(t3_audit.ToolchainAbort):
        overnight.build_queue_with_needs_human(wave="wave4")


def test_overnight_combined_wave4_runs_4a_then_transitions_to_4b(monkeypatch):
    # When wave4a has items, combined `wave4` returns them first; when 4a drains, returns 4b!
    w4a_state = {"items": [{"group_id": "func_100", "mode": overnight.WAVE4A_MODE}]}
    w4b_items = [{"addrs": [0x200], "mode": overnight.WAVE4_MODE}]
    monkeypatch.setattr(overnight, "_wave4_is_real_discover", lambda fn: True)
    monkeypatch.setattr(overnight, "wave4a_items", lambda **kw: list(w4a_state["items"]))
    monkeypatch.setattr(overnight, "wave4_items", lambda **kw: list(w4b_items))

    q1, _ = overnight.build_queue_with_needs_human(wave="wave4")
    assert len(q1) == 1 and q1[0]["mode"] == overnight.WAVE4A_MODE

    w4a_state["items"] = []
    q2, _ = overnight.build_queue_with_needs_human(wave="wave4")
    assert len(q2) == 1 and q2[0]["mode"] == overnight.WAVE4_MODE


def test_write_wave4_metrics_computes_efficiency_from_observed_telemetry(tmp_path, monkeypatch):
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (885, 1010, 500, 385))
    out_fn = tmp_path / "metrics.json"
    results = [
        {"mode": overnight.WAVE4A_MODE, "area": "w4a_1", "status": "COMMITTED", "w4_outcome": "PROMOTED",
         "method": "mechanical", "delta": 2, "delta_t3": 2, "calls": 0, "cost": 0.0,
         "unresolved_delta": 2, "worker_s": 3.0, "verify_s": 12.0, "addrs": [0x10, 0x20]},
        {"mode": overnight.WAVE4A_MODE, "area": "w4a_2", "status": "COMMITTED", "w4_outcome": "RECONCILED",
         "method": "research", "delta": 0, "delta_t3": 0, "calls": 1, "cost": 0.0,
         "unresolved_delta": 1, "worker_s": 8.0, "verify_s": 11.0, "addrs": [0x30, 0x40]},
        {"mode": overnight.WAVE4_MODE, "area": "w4_50", "status": "COMMITTED", "w4_outcome": "PROMOTED",
         "method": "recovery", "delta": 1, "delta_t3": 1, "calls": 1, "cost": 0.0,
         "worker_s": 10.0, "verify_s": 12.0, "addrs": [0x50]},
    ]
    m = overnight.write_wave4_metrics(
        results, (885, 1010, 497, 388), started_at=100.0, wave="wave4", provider="claude",
        stop_reason="done", metrics_path=str(out_fn),
    )
    assert out_fn.is_file()
    assert m["wave4a"]["t3_promotions"] == 2
    assert m["wave4a"]["zero_llm_t3_promotions"] == 2
    assert m["wave4a"]["reconciled_only_commits"] == 1
    assert m["wave4a"]["resolved_mechanically"] == 1
    assert m["wave4a"]["resolved_via_llm"] == 1
    assert m["wave4a"]["unresolved_relocs_eliminated"] == 3
    assert m["wave4b"]["t3_promotions"] == 1
    assert m["efficiency"]["t3_promotions_per_llm_call"] == 1.5
    assert m["efficiency"]["zero_llm_t3_proportion"] == round(2 / 3, 3)


def test_compile_check_files_handles_two_tuple_failures_and_captures_diagnostics(tmp_path, monkeypatch, capsys):
    c_file = tmp_path / "src" / "area" / "foo_reference.c"
    c_file.parent.mkdir(parents=True)
    c_file.write_text("int foo(void) { return 0; }\n", encoding="utf-8")

    def fake_compile_check(fulls, jobs=1):
        src = fulls[0]
        print(f"DOES NOT COMPILE  {src} (ow2): {src}(1): Error! E1062: Inconsistent return type")
        print("")
        print(f"{src}(1): Note! N2003: source conversion type is 'unsigned int'")
        print("compile check: 1 files x 2 compilers, 1 failures")
        return [(src, "ow2")]

    monkeypatch.setattr(wave4a.match, "compile_check", fake_compile_check)
    ok, err = wave4a._compile_check_files(["src/area/foo_reference.c"], repo_root=str(tmp_path))
    assert ok is False
    assert "ow2" in err
    assert "Error! E1062: Inconsistent return type" in err
    assert "Note! N2003" in err
    assert "compile check:" not in err
    assert "DOES NOT COMPILE" in capsys.readouterr().out

    def fake_timeout(fulls, jobs=1):
        print(f"DOES NOT COMPILE  {fulls[0]} (ow2): earlier error")
        raise wave4a.match.CompileTimeout("hung")

    monkeypatch.setattr(wave4a.match, "compile_check", fake_timeout)
    with pytest.raises(t3_audit.ToolchainAbort):
        wave4a._compile_check_files(["src/area/foo_reference.c"], repo_root=str(tmp_path))
    assert "earlier error" in capsys.readouterr().out

