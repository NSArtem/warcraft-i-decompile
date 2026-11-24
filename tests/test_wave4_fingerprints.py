"""Focused regression & integration tests for per-unit Wave 4A & Wave 4B dependency fingerprints.

Covers the complete preservation / invalidation matrix for both stages, OMF dependency
extraction, multi-caller Wave 4A groups, ambiguous -> resolvable transitions, fail-open
bypass behavior, legacy schema v1 rejection without deletion, in-run dependency-aware
retry eligibility (bounded), cross-invocation persistence, incremental audit consistency,
and structured cache diagnostics in `build/wave4/metrics.json`.
"""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import types

import pytest

from wc1 import live, match, oldcc, omf, overnight, symbols, t3_audit, wave4, wave4_deps, wave4_fp, wave4a


def _write(root, rel, text):
    fn = root / rel
    fn.parent.mkdir(parents=True, exist_ok=True)
    fn.write_text(text)
    return fn


def _insn(mnemonic, op_str, size=5):
    return types.SimpleNamespace(mnemonic=mnemonic, op_str=op_str, size=size)


def _fake_prog(funcs_spec, insns_map=None, fix_at=None):
    return types.SimpleNamespace(
        functions=list(funcs_spec),
        insns=dict(insns_map or {}),
        fix_at=dict(fix_at or {}),
        le=types.SimpleNamespace(
            obj_at=lambda a: types.SimpleNamespace(
                index=0 if a < 0x50000 else 1,
                base=0x10000 if a < 0x50000 else 0x50000,
            ),
        ),
    )


def _make_miss_4b(addr, max_calls=2, **overrides):
    rec = {
        "addr": f"{addr:#x}",
        "outcome": wave4.NO_IMPROVEMENT,
        "complete_search": True,
        "llm_calls": max_calls,
        "ts": "2026-11-24T12:00:00Z",
        "history": (
            [{"call": 0, "status": "MISMATCH"}]
            + [{"call": i, "diagnosis": "d", "applied": 0} for i in range(1, max_calls + 1)]
        ),
    }
    rec.update(overrides)
    return rec


def _make_miss_4a(group_id, outcome=wave4a.NO_IMPROVEMENT, max_calls=2, **overrides):
    rec = {
        "group_id": group_id,
        "outcome": outcome,
        "complete_search": True,
        "llm_calls": 1 if outcome == wave4a.AMBIGUOUS else max_calls,
        "ts": "2026-11-24T12:00:00Z",
        "history": [{"call": 1, "decision": "ambiguous" if outcome == wave4a.AMBIGUOUS else "defer"}],
    }
    rec.update(overrides)
    return rec


@pytest.fixture
def fp_repo(tmp_path, monkeypatch):
    """Isolated disposable repository with fake Watcom 10.0a binaries and war.exe."""
    repo = tmp_path / "repo"
    repo.mkdir()
    compiler = repo / "original" / "watcom" / "10.0a"
    for rel in ("binnt/wcc386.exe", "binb/wcc386.exe"):
        fn = compiler / rel
        fn.parent.mkdir(parents=True, exist_ok=True)
        fn.write_bytes(b"watcom10a-" + rel.encode())
    (compiler / "h").mkdir(parents=True, exist_ok=True)
    war = repo / "original" / "install" / "war.exe"
    war.parent.mkdir(parents=True, exist_ok=True)
    war.write_bytes(b"original-war-exe")
    (repo / "src" / "include").mkdir(parents=True, exist_ok=True)
    (repo / "tests").mkdir(parents=True, exist_ok=True)

    join = lambda *parts: os.path.join(str(repo), *parts)
    for mod in (wave4, wave4a, wave4_deps, wave4_fp, overnight, t3_audit, symbols):
        monkeypatch.setattr(mod, "path", join)
    monkeypatch.setattr(oldcc, "root", lambda: str(compiler))
    monkeypatch.delenv("INCLUDE", raising=False)
    monkeypatch.delenv("WCC386", raising=False)
    return repo


# ---------------------------------------------------------------------------
# 1. OMF dependency extraction (`t3_audit.extract_omf_deps` / `merge_omf_deps`)
# ---------------------------------------------------------------------------

def test_extract_omf_deps_captures_resolved_unresolved_relocs_and_data_anchors():
    text_data = bytearray(16)
    struct.pack_into("<i", text_data, 1, 0)       # call rel32 addend=0
    struct.pack_into("<i", text_data, 8, 12)      # data ref addend=+12
    text_seg = omf.Segment(
        name="_TEXT", cls="CODE", align=1, length=16, data=text_data,
        fixups=[
            omf.Fixup(offset=1, loc=9, self_rel=True, target_kind="ext", target="Callee_", disp=0),
            omf.Fixup(offset=8, loc=9, self_rel=False, target_kind="ext", target="_table", disp=0),
        ],
    )
    const_seg = omf.Segment(name="CONST", cls="DATA", align=1, length=4, data=bytearray(b"abc\0"), fixups=[])
    mod = omf.Module(
        name="foo",
        segments=[text_seg, const_seg],
        externs=["Callee_", "_table", "__STK"],
        publics={"Foo_": (1, 0)},
        statics={"helper_": (1, 12)},
    )
    d = t3_audit.extract_omf_deps(mod)
    assert d is not None
    assert d["external_symbols"] == ["Callee_", "__STK", "_table"]
    assert d["text_symbols"] == ["Foo_", "helper_"]
    assert d["has_data_anchors"] is True
    assert d["external_relocs"] == [
        {"symbol": "Callee_", "self_relative": True, "loc": 9, "addend": 0},
        {"symbol": "_table", "self_relative": False, "loc": 9, "addend": 12},
    ]

    merged_incomplete = t3_audit.merge_omf_deps([d], complete=False)
    assert merged_incomplete["complete"] is False

    # Lightweight fake without OMF metadata returns None (never claims 0 externals!)
    fake_mod = types.SimpleNamespace(publics={"Foo_": (1, 0)}, seg=lambda n: (1, object()))
    assert t3_audit.extract_omf_deps(fake_mod) is None


# ---------------------------------------------------------------------------
# 2. Wave 4B dependency-scoped fingerprint matrix (all preservation & invalidation cases)
# ---------------------------------------------------------------------------

def _build_4b_fixture(repo):
    _write(repo, "src/include/inner.h", "typedef struct Box { short x; short y; } Box;\n")
    _write(repo, "src/include/unit_hdr.h", '#include "inner.h"\ntypedef struct Item { short flags; Box box; } Item;\n')
    _write(repo, "src/include/other_hdr.h", "extern int completely_unrelated;\n")
    ref = "src/mod_a/target_reference.c"
    _write(
        repo, ref,
        '/* codegen-compiler: 10.0a */\n/* codegen-flags: -s -ot -ol -4r -zp2 */\n'
        '#include "unit_hdr.h"\n'
        'extern void Helper(void);\n'
        'extern Item items[8];\n'
        'extern int missing_sym;\n'
        'void Target(void) { Helper(); items[1].box.x = missing_sym; }\n',
    )
    _write(repo, "src/mod_b/unrelated.c", "void Unrelated(void) {}\n")
    _write(repo, "tests/test_target.py", "def test_target():\n    assert True\n")
    _write(repo, "tests/test_unrelated.py", "def test_other():\n    assert True\n")

    funcs = {
        0x10000: {
            "addr": 0x10000, "name": "Target", "link_name": "Target_",
            "conv": "watcall", "proto": "void Target(void)", "module": "MOD_A",
            "ref": ref, "ref_verified_by": "difftest: tests/test_target.py::test_target",
            "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        },
        0x10040: {
            "addr": 0x10040, "name": "Helper", "link_name": "Helper_",
            "conv": "watcall", "proto": "void Helper(void)", "module": "MOD_A",
            "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        },
        0x20000: {
            "addr": 0x20000, "name": "UnrelatedFn", "link_name": "UnrelatedFn_",
            "conv": "watcall", "proto": "void UnrelatedFn(void)", "module": "MOD_B",
            "_file": "analysis/symbols/mod_b.toml", "_kind": "func",
        },
    }
    datas = {
        0x52000: {
            "addr": 0x52000, "name": "items", "link_name": "_items",
            "type": "Item[8]", "_file": "analysis/symbols/mod_a.toml", "_kind": "data",
        },
        0x59000: {
            "addr": 0x59000, "name": "unrelated_data", "link_name": "_unrelated_data",
            "type": "long", "_file": "analysis/symbols/mod_b.toml", "_kind": "data",
        },
    }
    p = _fake_prog(
        [
            {"start": 0x10000, "end": 0x10030, "limit": 0x10030},
            {"start": 0x10030, "end": 0x10040, "limit": 0x10040},
            {"start": 0x10040, "end": 0x10060, "limit": 0x10060},
            {"start": 0x20000, "end": 0x20020, "limit": 0x20020},
        ],
        insns_map={
            0x10004: _insn("call", "0x10040"),
            0x1000a: _insn("mov", "eax, dword ptr [0x52008]", size=6),
            0x10010: _insn("mov", "edx, dword ptr [0x53000]", size=6),
        },
        fix_at={0x1000c: (0, 0x52008), 0x10012: (0, 0x53000)},
    )
    cand = {
        "addr": 0x10000, "addr_hex": "0x10000", "name": "Target", "link_name": "Target_",
        "module": "MOD_A", "ref": ref, "toml": "analysis/symbols/mod_a.toml",
        "declared_cc": "10.0a", "declared_cflags": "-s -ot -ol -4r -zp2",
        "ref_verified_by": "difftest: tests/test_target.py::test_target",
    }
    omf_deps = {
        "complete": True,
        "external_symbols": ["Helper_", "_items", "_missing_sym"],
        "text_symbols": ["Target_"],
        "external_relocs": [
            {"symbol": "Helper_", "self_relative": True, "loc": 9, "addend": 0},
            {"symbol": "_items", "self_relative": False, "loc": 9, "addend": 8},
            {"symbol": "_missing_sym", "self_relative": False, "loc": 9, "addend": 0},
        ],
        "has_data_anchors": False,
    }
    return ref, cand, funcs, datas, p, omf_deps


def _ctx_from(repo, p, funcs, datas, omf_by_ref, audit_rows=None, est=None):
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    msig = wave4.matcher_signature(p.functions, by_link)
    return wave4_fp.DependencyContext(
        p, funcs, datas, by_link,
        repo_root=str(repo),
        audit_rows=audit_rows,
        unit_omf_deps=omf_by_ref,
        established_mappings=est,
        repo_matcher_sig=msig,
        load_disk_omf_deps=False,
    ), msig


@pytest.mark.parametrize("change", [
    "add_unrelated_func",
    "add_unrelated_func_same_toml",
    "add_unrelated_data",
    "rename_unrelated_symbol",
    "change_unrelated_source",
    "change_unrelated_header",
    "change_unrelated_test",
    "edit_relevant_prose_evidence",
])
def test_wave4b_cache_preserved_across_unrelated_changes(fp_repo, change):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    ctx1, msig1 = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    cache = wave4.RetryCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    fp1 = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx1)
    assert fp1.key is not None and fp1.mode == "dependency_scoped"
    cache.remember(cand["addr"], fp1, _make_miss_4b(cand["addr"]), repo_state_hint={"matcher_sig": msig1})

    repo_changed = True
    if change == "add_unrelated_func":
        funcs[0x25000] = {
            "addr": 0x25000, "name": "BrandNewUnrelated", "link_name": "BrandNewUnrelated_",
            "conv": "watcall", "proto": "void BrandNewUnrelated(void)",
            "_file": "analysis/symbols/mod_z.toml", "_kind": "func",
        }
    elif change == "add_unrelated_func_same_toml":
        funcs[0x26000] = {
            "addr": 0x26000, "name": "SameTomlOther", "link_name": "SameTomlOther_",
            "conv": "watcall", "proto": "void SameTomlOther(void)",
            "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        }
    elif change == "add_unrelated_data":
        datas[0x5a000] = {
            "addr": 0x5a000, "name": "new_unrelated_var", "link_name": "_new_unrelated_var",
            "type": "short", "_file": "analysis/symbols/mod_z.toml", "_kind": "data",
        }
    elif change == "rename_unrelated_symbol":
        funcs[0x20000]["name"] = "RenamedUnrelatedFn"
        funcs[0x20000]["link_name"] = "RenamedUnrelatedFn_"
    elif change == "change_unrelated_source":
        _write(fp_repo, "src/mod_b/unrelated.c", "void Unrelated(void) { /* edited */ }\n")
        repo_changed = False
    elif change == "change_unrelated_header":
        _write(fp_repo, "src/include/other_hdr.h", "extern long completely_unrelated;\n")
        repo_changed = False
    elif change == "change_unrelated_test":
        _write(fp_repo, "tests/test_unrelated.py", "def test_other():\n    assert 1 == 1\n")
        repo_changed = False
    elif change == "edit_relevant_prose_evidence":
        funcs[0x10040]["evidence"] = ["brand new prose note"]
        repo_changed = False

    ctx2, msig2 = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    fp2 = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx2)
    assert fp2.key == fp1.key
    lk = cache.lookup(cand["addr"], fp2, repo_state_hint={"matcher_sig": msig2})
    assert lk.hit is True
    if repo_changed:
        assert msig2 != msig1
        assert lk.status == "hit_preserved_unrelated"
    else:
        assert lk.status == "hit"


@pytest.mark.parametrize("change", [
    "ext_addr",
    "ext_name",
    "ext_abi",
    "resolve_missing_by_link",
    "resolve_missing_orig_target_addr",
    "data_owner_type",
    "struct_field_layout",
    "reloc_addend",
    "func_extent",
    "neighbor_func_extent",
    "candidate_source",
    "direct_header",
    "recursive_header",
    "sibling_added",
    "compiler_binary",
    "declared_cflags",
    "presets",
    "model",
    "effort",
    "budget",
    "cost",
    "cited_test",
])
def test_wave4b_cache_invalidated_on_relevant_changes(fp_repo, monkeypatch, change):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    cfg = ["claude", ("sonnet", "medium"), 2, 1.1]
    ctx1, msig1 = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    cache1 = wave4.RetryCache(*cfg)
    fp1 = cache1.compute_fingerprint(cand, [cand], dep_ctx=ctx1)
    assert fp1.key is not None
    cache1.remember(cand["addr"], fp1, _make_miss_4b(cand["addr"]), repo_state_hint={"matcher_sig": msig1})

    siblings = [cand]
    if change == "ext_addr":
        funcs[0x10040]["addr"] = 0x10044
        funcs[0x10044] = funcs.pop(0x10040)
    elif change == "ext_name":
        funcs[0x10040]["name"] = "HelperRenamed"
        funcs[0x10040]["link_name"] = "HelperRenamed_"
    elif change == "ext_abi":
        funcs[0x10040]["proto"] = "int Helper(int x)"
        funcs[0x10040]["conv"] = "cdecl"
    elif change == "resolve_missing_by_link":
        datas[0x53000] = {
            "addr": 0x53000, "name": "missing_sym", "link_name": "_missing_sym",
            "type": "int", "_file": "analysis/symbols/mod_a.toml", "_kind": "data",
        }
    elif change == "resolve_missing_orig_target_addr":
        # Even under a different link name, adding a DB symbol at orig target 0x53000 MUST invalidate!
        datas[0x53000] = {
            "addr": 0x53000, "name": "canonical_53000", "link_name": "_canonical_53000",
            "type": "int", "_file": "analysis/symbols/mod_a.toml", "_kind": "data",
        }
    elif change == "data_owner_type":
        datas[0x52000]["type"] = "Item[16]"
    elif change == "struct_field_layout":
        # Change field layout in nested header `inner.h` (without changing `unit_hdr.h` directly)
        _write(fp_repo, "src/include/inner.h", "typedef struct Box { short y; short x; } Box;\n")
    elif change == "reloc_addend":
        omf_deps = dict(omf_deps, external_relocs=[
            {"symbol": "Helper_", "self_relative": True, "loc": 9, "addend": 0},
            {"symbol": "_items", "self_relative": False, "loc": 9, "addend": 10},
            {"symbol": "_missing_sym", "self_relative": False, "loc": 9, "addend": 0},
        ])
    elif change == "func_extent":
        p.functions[0]["end"] = 0x10034
    elif change == "neighbor_func_extent":
        p.functions[1]["end"] = 0x10044
    elif change == "candidate_source":
        _write(fp_repo, ref, (fp_repo / ref).read_text().replace("box.x", "box.y"))
    elif change == "direct_header":
        _write(fp_repo, "src/include/unit_hdr.h", (fp_repo / "src/include/unit_hdr.h").read_text() + "/* edit */\n")
    elif change == "recursive_header":
        _write(fp_repo, "src/include/inner.h", (fp_repo / "src/include/inner.h").read_text() + "/* edit */\n")
    elif change == "sibling_added":
        sib = dict(cand, addr=0x10020, addr_hex="0x10020", name="Sib", link_name="Sib_")
        siblings.append(sib)
        funcs[0x10020] = {
            "addr": 0x10020, "name": "Sib", "link_name": "Sib_", "conv": "watcall",
            "proto": "void Sib(void)", "ref": ref, "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        }
    elif change == "compiler_binary":
        (Path(oldcc.root()) / "binb/wcc386.exe").write_bytes(b"different-compiler")
    elif change == "declared_cflags":
        cand = dict(cand, declared_cflags="-s -od -4r -zp2")
    elif change == "presets":
        monkeypatch.setattr(t3_audit, "attempt_plan", lambda flags: [("declared", flags)])
    elif change == "model":
        cfg[1] = ("opus", "medium")
    elif change == "effort":
        cfg[1] = ("sonnet", "high")
    elif change == "budget":
        cfg[2] = 3
    elif change == "cost":
        cfg[3] = 2.2
    elif change == "cited_test":
        _write(fp_repo, "tests/test_target.py", "def test_target():\n    assert 2 == 2\n")

    ctx2, msig2 = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    cache2 = wave4.RetryCache(*cfg)
    fp2 = cache2.compute_fingerprint(cand, siblings, dep_ctx=ctx2)
    assert fp2.key is not None and fp2.key != fp1.key
    lk = cache2.lookup(cand["addr"], fp2, repo_state_hint={"matcher_sig": msig2})
    assert lk.hit is False
    assert lk.status == "miss_dep_changed"


# ---------------------------------------------------------------------------
# 3. Wave 4A multi-caller group & ambiguous -> resolvable matrix
# ---------------------------------------------------------------------------

def _build_4a_multicaller_fixture(repo):
    _write(repo, "src/include/shared_types.h", "typedef struct Entry { short a; short b; } Entry;\n")
    _write(repo, "src/include/target_api.h", "extern void TargetApi(int x);\n")
    _write(repo, "src/include/unrelated_hdr.h", "extern void Nothing(void);\n")
    ref1 = "src/mod_a/caller1_reference.c"
    ref2 = "src/mod_b/caller2_reference.c"
    _write(
        repo, ref1,
        '/* codegen-compiler: 10.0a */\n#include "shared_types.h"\n'
        'extern void old_api(void);\nextern short field_a;\n'
        'void Caller1(void) { old_api(); field_a = 1; }\n',
    )
    _write(
        repo, ref2,
        '/* codegen-compiler: 10.0a */\n'
        'extern void old_api(void);\nextern short field_b;\n'
        'void Caller2(void) { old_api(); field_b = 2; }\n',
    )
    _write(repo, "src/mod_c/other.c", "void Other(void) {}\n")
    _write(repo, "tests/test_c1.py", 'EXTRA = {"_field_a": 0x52004}\ndef test_c1(): pass\n')
    _write(repo, "tests/test_c2.py", 'EXTRA = {"_field_b": 0x52006}\ndef test_c2(): pass\n')

    funcs = {
        0x10000: {
            "addr": 0x10000, "name": "Caller1", "link_name": "Caller1_", "conv": "watcall",
            "proto": "void Caller1(void)", "module": "MOD_A", "ref": ref1,
            "ref_verified_by": "difftest: tests/test_c1.py::test_c1",
            "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        },
        0x10040: {
            "addr": 0x10040, "name": "Caller2", "link_name": "Caller2_", "conv": "watcall",
            "proto": "void Caller2(void)", "module": "MOD_B", "ref": ref2,
            "ref_verified_by": "difftest: tests/test_c2.py::test_c2",
            "_file": "analysis/symbols/mod_b.toml", "_kind": "func",
        },
        0x15000: {
            "addr": 0x15000, "name": "TargetApi", "link_name": "TargetApi_", "conv": "watcall",
            "proto": "void TargetApi(int x)", "module": "API",
            "_file": "analysis/symbols/api.toml", "_kind": "func",
        },
        0x15040: {
            "addr": 0x15040, "name": "ApiCallee", "link_name": "ApiCallee_", "conv": "watcall",
            "proto": "void ApiCallee(void)", "module": "API",
            "_file": "analysis/symbols/api.toml", "_kind": "func",
        },
        0x28000: {
            "addr": 0x28000, "name": "UnrelatedFn", "link_name": "UnrelatedFn_", "conv": "watcall",
            "proto": "void UnrelatedFn(void)", "module": "MOD_C",
            "_file": "analysis/symbols/mod_c.toml", "_kind": "func",
        },
    }
    datas = {
        0x52000: {
            "addr": 0x52000, "name": "entries", "link_name": "_entries",
            "type": "Entry[8]", "_file": "analysis/symbols/mod_a.toml", "_kind": "data",
        },
        0x5a000: {
            "addr": 0x5a000, "name": "unrelated_global", "link_name": "_unrelated_global",
            "type": "long", "_file": "analysis/symbols/mod_c.toml", "_kind": "data",
        },
    }
    p = _fake_prog(
        [
            {"start": 0x10000, "end": 0x10020, "limit": 0x10020},
            {"start": 0x10040, "end": 0x10060, "limit": 0x10060},
            {"start": 0x15000, "end": 0x15020, "limit": 0x15020},
            {"start": 0x15040, "end": 0x15050, "limit": 0x15050},
            {"start": 0x28000, "end": 0x28020, "limit": 0x28020},
        ],
        insns_map={
            0x10004: _insn("call", "0x15000"),
            0x1000a: _insn("mov", "word ptr [0x52004], 1", size=6),
            0x10044: _insn("call", "0x15000"),
            0x1004a: _insn("mov", "word ptr [0x52006], 2", size=6),
            0x15004: _insn("call", "0x15040"),
        },
        fix_at={0x1000c: (0, 0x52004), 0x1004c: (0, 0x52006)},
    )
    omf_by_ref = {
        ref1: {
            "complete": True,
            "external_symbols": ["old_api_", "_field_a"],
            "text_symbols": ["Caller1_"],
            "external_relocs": [
                {"symbol": "old_api_", "self_relative": True, "loc": 9, "addend": 0},
                {"symbol": "_field_a", "self_relative": False, "loc": 9, "addend": 0},
            ],
            "has_data_anchors": False,
        },
        ref2: {
            "complete": True,
            "external_symbols": ["old_api_", "_field_b"],
            "text_symbols": ["Caller2_"],
            "external_relocs": [
                {"symbol": "old_api_", "self_relative": True, "loc": 9, "addend": 0},
                {"symbol": "_field_b", "self_relative": False, "loc": 9, "addend": 0},
            ],
            "has_data_anchors": False,
        },
    }
    att1 = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [
        {"symbol": "old_api_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": 0x15000},
        {"symbol": "_field_a", "self_relative": False, "loc": 9, "addend": 0, "original_candidate": 0x52004},
    ]}
    att2 = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [
        {"symbol": "old_api_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": 0x15000},
        {"symbol": "_field_b", "self_relative": False, "loc": 9, "addend": 0, "original_candidate": 0x52006},
    ]}
    rep = {"results": [
        {"addr": 0x10000, "tier": "T4", "status": "MISMATCH", "name": "Caller1", "link_name": "Caller1_",
         "ref": ref1, "toml": "analysis/symbols/mod_a.toml", "module": "MOD_A",
         "ref_verified_by": "difftest: tests/test_c1.py::test_c1", "best": att1, "attempts": [att1]},
        {"addr": 0x10040, "tier": "T4", "status": "MISMATCH", "name": "Caller2", "link_name": "Caller2_",
         "ref": ref2, "toml": "analysis/symbols/mod_b.toml", "module": "MOD_B",
         "ref_verified_by": "difftest: tests/test_c2.py::test_c2", "best": att2, "attempts": [att2]},
    ]}
    return ref1, ref2, funcs, datas, p, omf_by_ref, rep


def _group_by_id(repo, rep, p, funcs, datas, omf_by_ref, gid, est=None):
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    inv = wave4_deps.build_dependency_inventory(
        rep, p, funcs, datas, by_link, repo_root=str(repo), established_mappings=est or {},
    )
    ctx, msig = _ctx_from(repo, p, funcs, datas, omf_by_ref, audit_rows=rep["results"], est=est or {})
    g = next(x for x in inv["groups"] if x["group_id"] == gid)
    return g, ctx, msig


@pytest.mark.parametrize("change", [
    "add_unrelated_func",
    "add_unrelated_data",
    "rename_unrelated",
    "change_unrelated_source",
    "change_unrelated_header",
    "add_unrelated_mapping",
])
def test_wave4a_multicaller_cache_preserved_on_unrelated_changes(fp_repo, change):
    ref1, ref2, funcs, datas, p, omf_by_ref, rep = _build_4a_multicaller_fixture(fp_repo)
    est = {}
    g1, ctx1, msig1 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, "func_15000", est=est)
    assert set(g1["affected_refs"]) == {ref1, ref2}
    cache = wave4a.ReconcileCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    fp1 = cache.compute_fingerprint(g1, dep_ctx=ctx1)
    assert fp1.key is not None and fp1.mode == "dependency_scoped"
    cache.remember("func_15000", fp1, _make_miss_4a("func_15000"), repo_state_hint={"matcher_sig": msig1})

    repo_changed = True
    if change == "add_unrelated_func":
        funcs[0x29000] = {
            "addr": 0x29000, "name": "OtherNewFn", "link_name": "OtherNewFn_",
            "conv": "watcall", "proto": "void OtherNewFn(void)",
            "_file": "analysis/symbols/mod_z.toml", "_kind": "func",
        }
    elif change == "add_unrelated_data":
        datas[0x5b000] = {
            "addr": 0x5b000, "name": "far_away_var", "link_name": "_far_away_var",
            "type": "int", "_file": "analysis/symbols/mod_z.toml", "_kind": "data",
        }
    elif change == "rename_unrelated":
        funcs[0x28000]["name"] = "UnrelatedRenamed"
        funcs[0x28000]["link_name"] = "UnrelatedRenamed_"
    elif change == "change_unrelated_source":
        _write(fp_repo, "src/mod_c/other.c", "void Other(void) { /* changed */ }\n")
        repo_changed = False
    elif change == "change_unrelated_header":
        _write(fp_repo, "src/include/unrelated_hdr.h", "extern int Nothing(void);\n")
        repo_changed = False
    elif change == "add_unrelated_mapping":
        est["_some_unrelated_sym"] = {"target_addr": 0x5a000, "canonical_link": "_unrelated_global"}
        repo_changed = False

    g2, ctx2, msig2 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, "func_15000", est=est)
    fp2 = cache.compute_fingerprint(g2, dep_ctx=ctx2)
    assert fp2.key == fp1.key
    lk = cache.lookup("func_15000", fp2, repo_state_hint={"matcher_sig": msig2})
    assert lk.hit is True
    assert lk.status == ("hit_preserved_unrelated" if repo_changed else "hit")


@pytest.mark.parametrize("gid,change", [
    ("func_15000", "caller2_source"),
    ("func_15000", "caller1_header"),
    ("func_15000", "canonical_target_header"),
    ("func_15000", "target_abi"),
    ("func_15000", "target_extent"),
    ("func_15000", "target_callee_renamed"),
    ("func_15000", "nearby_toml_scope_change"),
    ("func_15000", "cited_test_change"),
    ("func_15000", "established_mapping_for_sym"),
    ("func_15000", "ow2_compiler_changed"),
    ("func_15000", "budget_changed"),
    ("owner_52000", "owner_struct_layout"),
    ("owner_52000", "nearby_data_within_0x60"),
    ("owner_52000", "reloc_addend_change"),
])
def test_wave4a_multicaller_cache_invalidated_on_relevant_changes(fp_repo, monkeypatch, gid, change):
    ref1, ref2, funcs, datas, p, omf_by_ref, rep = _build_4a_multicaller_fixture(fp_repo)
    est = {}
    g1, ctx1, msig1 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, gid, est=est)
    cfg = ["codex", ("gpt-6.2-sol", "low"), 2]
    cache1 = wave4a.ReconcileCache(*cfg)
    fp1 = cache1.compute_fingerprint(g1, dep_ctx=ctx1)
    assert fp1.key is not None
    cache1.remember(gid, fp1, _make_miss_4a(gid), repo_state_hint={"matcher_sig": msig1})

    if change == "caller2_source":
        _write(fp_repo, ref2, (fp_repo / ref2).read_text() + "/* modified caller2 */\n")
    elif change == "caller1_header":
        _write(fp_repo, "src/include/shared_types.h", (fp_repo / "src/include/shared_types.h").read_text() + "/* hdr */\n")
    elif change == "canonical_target_header":
        # Like real `func_1dda0` / `mod_1dca0.h`: NOT included by callers, only in canonical_header_decls!
        _write(fp_repo, "src/include/target_api.h", "extern void TargetApi(int x);\nextern short FixedOther(void);\n")
    elif change == "target_abi":
        funcs[0x15000]["proto"] = "int TargetApi(int x, int y)"
    elif change == "target_extent":
        p.functions[2]["end"] = 0x15028
    elif change == "target_callee_renamed":
        funcs[0x15040]["name"] = "ApiCalleeRenamed"
        funcs[0x15040]["link_name"] = "ApiCalleeRenamed_"
    elif change == "nearby_toml_scope_change":
        # New func within ±0x400 of 0x15000 in a new TOML expands allowed edit scope!
        funcs[0x15100] = {
            "addr": 0x15100, "name": "NeighborInNewToml", "link_name": "NeighborInNewToml_",
            "conv": "watcall", "proto": "void NeighborInNewToml(void)",
            "_file": "analysis/symbols/api_extra.toml", "_kind": "func",
        }
    elif change == "cited_test_change":
        _write(fp_repo, "tests/test_c2.py", 'EXTRA = {"_field_b": 0x52006}\ndef test_c2():\n    assert 1\n')
    elif change == "established_mapping_for_sym":
        est["old_api_"] = {"target_addr": 0x15000, "canonical_link": "TargetApi_", "canonical_name": "TargetApi"}
    elif change == "ow2_compiler_changed":
        monkeypatch.setattr(wave4_fp, "ow2_compiler_digest", lambda: "different-ow2-sha256")
    elif change == "budget_changed":
        cfg[2] = 3
    elif change == "owner_struct_layout":
        _write(fp_repo, "src/include/shared_types.h", "typedef struct Entry { int a; short b; } Entry;\n")
    elif change == "nearby_data_within_0x60":
        datas[0x52020] = {
            "addr": 0x52020, "name": "near_field", "link_name": "_near_field",
            "type": "short", "_file": "analysis/symbols/mod_a.toml", "_kind": "data",
        }
    elif change == "reloc_addend_change":
        omf_by_ref = dict(omf_by_ref)
        omf_by_ref[ref1] = dict(omf_by_ref[ref1], external_relocs=[
            {"symbol": "old_api_", "self_relative": True, "loc": 9, "addend": 0},
            {"symbol": "_field_a", "self_relative": False, "loc": 9, "addend": 2},
        ])

    g2, ctx2, msig2 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, gid, est=est)
    cache2 = wave4a.ReconcileCache(*cfg)
    fp2 = cache2.compute_fingerprint(g2, dep_ctx=ctx2)
    assert fp2.key is not None and fp2.key != fp1.key
    lk = cache2.lookup(gid, fp2, repo_state_hint={"matcher_sig": msig2})
    assert lk.hit is False and lk.status == "miss_dep_changed"


def test_ambiguous_group_invalidated_when_candidate_symbol_added_at_orig_target(fp_repo):
    ref = "src/mod_a/ambig_reference.c"
    _write(fp_repo, ref, "/* codegen-compiler: 10.0a */\nextern void mystery(void);\nvoid Caller(void) { mystery(); }\n")
    _write(fp_repo, "tests/test_ambig.py", "def test_a(): pass\n")
    funcs = {
        0x10000: {
            "addr": 0x10000, "name": "Caller", "link_name": "Caller_", "conv": "watcall",
            "proto": "void Caller(void)", "module": "MOD_A", "ref": ref,
            "ref_verified_by": "difftest: tests/test_ambig.py::test_a",
            "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
        },
    }
    datas = {}
    p = _fake_prog(
        [{"start": 0x10000, "end": 0x10020}, {"start": 0x20000, "end": 0x20010}, {"start": 0x30000, "end": 0x30010}],
        insns_map={0x10004: _insn("call", "0x20000")},
    )
    omf_by_ref = {
        ref: {
            "complete": True,
            "external_symbols": ["mystery_"],
            "text_symbols": ["Caller_"],
            "external_relocs": [{"symbol": "mystery_", "self_relative": True, "loc": 9, "addend": 0}],
            "has_data_anchors": False,
        },
    }
    att = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [
        {"symbol": "mystery_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": None},
    ]}
    rep = {"results": [
        {"addr": 0x10000, "tier": "T4", "status": "MISMATCH", "name": "Caller", "link_name": "Caller_",
         "ref": ref, "toml": "analysis/symbols/mod_a.toml", "module": "MOD_A",
         "ref_verified_by": "difftest: tests/test_ambig.py::test_a", "best": att, "attempts": [att]},
    ]}
    cache = wave4a.ReconcileCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    g1, ctx1, msig1 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, "sym_mystery")
    assert g1["classification"] == wave4_deps.AMBIGUOUS
    fp1 = cache.compute_fingerprint(g1, dep_ctx=ctx1)
    assert fp1.key is not None
    cache.remember("sym_mystery", fp1, _make_miss_4a("sym_mystery", outcome=wave4a.AMBIGUOUS),
                   repo_state_hint={"matcher_sig": msig1})

    # Unrelated symbol at 0x30000 (NOT referenced by Caller) -> CACHE HIT preserved!
    funcs[0x30000] = {
        "addr": 0x30000, "name": "TotallyUnrelated", "link_name": "TotallyUnrelated_",
        "conv": "watcall", "proto": "void TotallyUnrelated(void)",
        "_file": "analysis/symbols/other.toml", "_kind": "func",
    }
    g2, ctx2, msig2 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, "sym_mystery")
    fp2 = cache.compute_fingerprint(g2, dep_ctx=ctx2)
    lk2 = cache.lookup("sym_mystery", fp2, repo_state_hint={"matcher_sig": msig2})
    assert lk2.hit is True and lk2.status == "hit_preserved_unrelated"

    # Candidate symbol added at 0x20000 (which Caller ACTUALLY calls in original binary!) -> CACHE MISS!
    funcs[0x20000] = {
        "addr": 0x20000, "name": "MysteryReal", "link_name": "MysteryReal_",
        "conv": "watcall", "proto": "void MysteryReal(void)",
        "_file": "analysis/symbols/mod_a.toml", "_kind": "func",
    }
    g3, ctx3, msig3 = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, "sym_mystery")
    fp3 = cache.compute_fingerprint(g3, dep_ctx=ctx3)
    lk3 = cache.lookup("sym_mystery", fp3, repo_state_hint={"matcher_sig": msig3})
    assert lk3.hit is False and lk3.status == "miss_dep_changed"


# ---------------------------------------------------------------------------
# 4. Fail-open bypasses & legacy schema v1 rejection without deletion
# ---------------------------------------------------------------------------

def test_fail_open_bypasses_on_uncertain_dependencies(fp_repo, monkeypatch):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    cache = wave4.RetryCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)

    # Missing OMF deps -> bypass_uncertain
    ctx_no_omf, _ = _ctx_from(fp_repo, p, funcs, datas, {})
    fp = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx_no_omf)
    assert fp.key is None and fp.mode == "bypass" and "missing_omf_deps" in fp.bypass_reason
    lk = cache.lookup(cand["addr"], fp)
    assert lk.hit is False and lk.status == "bypass_uncertain"

    # Incomplete OMF deps (e.g. a compile error on one preset) -> bypass_uncertain
    ctx_inc, _ = _ctx_from(fp_repo, p, funcs, datas, {ref: dict(omf_deps, complete=False)})
    fp_inc = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx_inc)
    assert fp_inc.key is None and "incomplete_omf_deps" in fp_inc.bypass_reason

    # Stale OMF source digest -> bypass_uncertain
    ctx_stale, _ = _ctx_from(fp_repo, p, funcs, datas, {ref: dict(omf_deps, source_digest="old-digest")})
    fp_stale = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx_stale)
    assert fp_stale.key is None and "stale_omf_source_digest" in fp_stale.bypass_reason

    # Unsafe compiler include flag -> bypass_uncertain
    ctx_ok, _ = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    bad_cand = dict(cand, declared_cflags="-s -i=/tmp/extra")
    assert cache.compute_fingerprint(bad_cand, [bad_cand], dep_ctx=ctx_ok).key is None

    # Trigraph in source -> bypass_uncertain
    orig_txt = (fp_repo / ref).read_text()
    _write(fp_repo, ref, "/* ??/ */\n" + orig_txt)
    ctx_tri, _ = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
    assert cache.compute_fingerprint(cand, [cand], dep_ctx=ctx_tri).key is None
    _write(fp_repo, ref, orig_txt)

    # Environment override (INCLUDE / WCC386) -> bypass_uncertain
    monkeypatch.setenv("INCLUDE", "/custom/inc")
    fp_env = cache.compute_fingerprint(cand, [cand], dep_ctx=ctx_ok)
    assert fp_env.key is None and fp_env.bypass_reason == "env_override:INCLUDE"
    cache_env = wave4.RetryCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    assert cache_env.settings is None and cache_env.init_bypass_reason == "env_override:INCLUDE"


def test_legacy_v1_cache_entries_are_rejected_reported_and_preserved_on_disk(fp_repo):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    ctx, msig = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})

    # Plant a realistic legacy schema v1 Wave 4B entry (no `cache_schema`, `version: 4`)
    legacy_4b = fp_repo / "build/wave4/retry/10000/deadbeef.json"
    legacy_4b.parent.mkdir(parents=True, exist_ok=True)
    legacy_4b_payload = json.dumps({
        "fingerprint": "deadbeef",
        "settings": {"version": 4, "provider": "codex", "max_calls": 2},
        "result": _make_miss_4b(0x10000),
    })
    legacy_4b.write_text(legacy_4b_payload)

    cache_4b = wave4.RetryCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    fp_4b = cache_4b.compute_fingerprint(cand, [cand], dep_ctx=ctx)
    lk_4b = cache_4b.lookup(0x10000, fp_4b, repo_state_hint={"matcher_sig": msig})
    assert lk_4b.hit is False and lk_4b.status == "miss_legacy_schema"
    msg = cache_4b.diag.record("0x10000", lk_4b)
    assert "INVALIDATED legacy/invalid cache schema" in msg
    assert cache_4b.diagnostics_summary()["invalidated_legacy_schema"] == 1
    # Legacy entry is NOT deleted or modified!
    assert legacy_4b.read_text() == legacy_4b_payload

    # Same for legacy schema v1 Wave 4A entry (no `cache_schema`, `version: 1`)
    ref1, ref2, funcs4a, datas4a, p4a, omf4a, rep4a = _build_4a_multicaller_fixture(fp_repo)
    g1, ctx4a, msig4a = _group_by_id(fp_repo, rep4a, p4a, funcs4a, datas4a, omf4a, "func_15000")
    legacy_4a = fp_repo / "build/wave4/reconcile_cache/func_15000/cafebabe.json"
    legacy_4a.parent.mkdir(parents=True, exist_ok=True)
    legacy_4a_payload = json.dumps({
        "fingerprint": "cafebabe",
        "settings": {"version": 1, "provider": "codex", "max_calls": 2},
        "result": _make_miss_4a("func_15000"),
    })
    legacy_4a.write_text(legacy_4a_payload)

    cache_4a = wave4a.ReconcileCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    fp_4a = cache_4a.compute_fingerprint(g1, dep_ctx=ctx4a)
    lk_4a = cache_4a.lookup("func_15000", fp_4a, repo_state_hint={"matcher_sig": msig4a})
    assert lk_4a.hit is False and lk_4a.status == "miss_legacy_schema"
    assert legacy_4a.read_text() == legacy_4a_payload


# ---------------------------------------------------------------------------
# 5. In-run retry eligibility, bounded retries, cross-invocation persistence & metrics
# ---------------------------------------------------------------------------

def test_in_run_retry_eligibility_respects_relevant_vs_unrelated_changes_and_cap(fp_repo):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    cache = wave4.RetryCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    key = (overnight.WAVE4_MODE, cand["module"], (cand["addr"],))

    def build_once(failed_keys, failed_fps, retry_misses=False):
        ctx, msig = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
        disc = lambda: ([dict(cand, group=1, ninsns=10, unresolved_count=0)],
                        {"report": "fresh", "eligible": 1, "matcher_signature": msig, "dep_ctx": ctx})
        logs = []
        items = overnight.wave4_items(
            discover=disc, retry_cache=cache, failed_keys=failed_keys,
            failed_fingerprints=failed_fps, retry_misses=retry_misses, cache_log=logs.append,
        )
        return items, logs

    # Attempt 1 fails under fp1
    items0, _ = build_once(set(), {})
    assert len(items0) == 1
    fp1 = items0[0]["retry_key"]
    assert fp1 is not None
    failed_keys = {key}
    failed_fps = {key: {"fingerprints": {fp1}, "attempts": 1, "unconditional": False}}

    # Unrelated symbol added during the same run -> STILL suppressed (no redundant retry!)
    funcs[0x29990] = {
        "addr": 0x29990, "name": "UnrelatedMidRun", "link_name": "UnrelatedMidRun_",
        "conv": "watcall", "proto": "void UnrelatedMidRun(void)",
        "_file": "analysis/symbols/other.toml", "_kind": "func",
    }
    items_unrel, _ = build_once(failed_keys, failed_fps)
    assert items_unrel == []

    # Relevant dependency changes during the same run -> RE-ENABLED!
    funcs[0x10040]["addr"] = 0x10048
    funcs[0x10048] = funcs.pop(0x10040)
    items_rel, logs_rel = build_once(failed_keys, failed_fps)
    assert len(items_rel) == 1
    fp2 = items_rel[0]["retry_key"]
    assert fp2 != fp1
    assert any("REQUEUED IN-RUN" in m for m in logs_rel)
    assert cache.diagnostics_summary()["in_run_requeued"] == 1

    # Bounded cap: after MAX_IN_RUN_WAVE4_ATTEMPTS, even another dependency change stops retrying in-run!
    failed_fps[key]["fingerprints"].add(fp2)
    failed_fps[key]["attempts"] = overnight.MAX_IN_RUN_WAVE4_ATTEMPTS
    funcs[0x10048]["proto"] = "int Helper(int z)"
    items_capped, _ = build_once(failed_keys, failed_fps)
    assert items_capped == []


def test_wave4a_in_run_retry_eligibility_for_ambiguous_group(fp_repo):
    ref1, ref2, funcs, datas, p, omf_by_ref, rep = _build_4a_multicaller_fixture(fp_repo)
    cache = wave4a.ReconcileCache("codex", ("gpt-6.2-sol", "low"), max_calls=2)
    gid = "func_15000"
    key = (overnight.WAVE4A_MODE, gid)

    def build_once(failed_keys, failed_fps):
        g, ctx, msig = _group_by_id(fp_repo, rep, p, funcs, datas, omf_by_ref, gid)
        disc = lambda: ([dict(g, task_kind="reconcile")],
                        {"matcher_signature": msig, "dep_ctx": ctx})
        logs = []
        items = overnight.wave4a_items(
            discover=disc, reconcile_cache=cache, failed_keys=failed_keys,
            failed_fingerprints=failed_fps, cache_log=logs.append,
        )
        return items, logs

    items0, _ = build_once(set(), {})
    assert len(items0) == 1
    fp1 = items0[0]["retry_key"]
    assert fp1 is not None
    failed_keys = {key}
    failed_fps = {key: {"fingerprints": {fp1}, "attempts": 1, "unconditional": False}}

    # Unrelated symbol change during the same run -> stays suppressed
    funcs[0x2c000] = {
        "addr": 0x2c000, "name": "UnrelInRun4a", "link_name": "UnrelInRun4a_",
        "conv": "watcall", "proto": "void UnrelInRun4a(void)",
        "_file": "analysis/symbols/other.toml", "_kind": "func",
    }
    assert build_once(failed_keys, failed_fps)[0] == []

    # Relevant dependency change (target ABI updated) during the same run -> eligible again!
    funcs[0x15000]["proto"] = "int TargetApi(int x, int y)"
    items_rel, logs_rel = build_once(failed_keys, failed_fps)
    assert len(items_rel) == 1 and items_rel[0]["retry_key"] != fp1
    assert any("REQUEUED IN-RUN" in m for m in logs_rel)
    assert cache.diagnostics_summary()["in_run_requeued"] == 1


def test_cross_invocation_persistence_and_metrics_diagnostics(fp_repo, monkeypatch):
    # Set up minimal git repo for run_overnight
    git = lambda *a: subprocess.run(["git", *a], cwd=fp_repo, check=True, capture_output=True)
    git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    _write(fp_repo, "analysis/symbols/mod_a.toml", '[[func]]\naddr = 0x10000\nname = "Target"\nconfidence = "high"\nevidence = ["x"]\n')
    git("add", "src", "tests", "analysis")
    git("commit", "-qm", "init")

    monkeypatch.setattr(live, "live_dir", lambda root=None: os.path.join(root or str(fp_repo), "build", "live"))
    monkeypatch.setattr(overnight, "_reset_wine", lambda: None)
    monkeypatch.setattr(overnight, "progress_done_count", lambda: (500, 1000, 300, 200))
    monkeypatch.setattr(overnight, "_snapshot_symbol_state", lambda: {
        0x10000: {"done": True, "name": "Target", "c": "T4", "src": None, "ref": ref,
                  "ref_verified_by": cand["ref_verified_by"], "file": "analysis/symbols/mod_a.toml"},
    })
    monkeypatch.setattr(overnight, "_wave4_is_real_discover", lambda fn: False)

    def fake_discover():
        ctx, msig = _ctx_from(fp_repo, p, funcs, datas, {ref: omf_deps})
        return ([dict(cand, group=1, ninsns=10, unresolved_count=0)],
                {"report": "fresh", "eligible": 1, "matcher_signature": msig, "dep_ctx": ctx})

    monkeypatch.setattr(wave4, "discover", fake_discover)
    worker_calls = []

    def fake_subproc(cmd, log_fh, **_kw):
        worker_calls.append(cmd)
        payload = {k: v for k, v in _make_miss_4b(0x10000).items() if k != "addr"}
        wave4.write_outcome(0x10000, **payload)
        return 0, "ok\n"

    monkeypatch.setattr(overnight, "_run_subprocess_logged", fake_subproc)

    # Invocation 1: cold miss -> runs worker and caches v2 entry
    assert overnight.run_overnight(window_budget=1.0, wave="wave4b", repair_budget=0.0) == 0
    assert len(worker_calls) == 1

    # Add unrelated symbol & unrelated git commit -> Invocation 2: preserved cache hit (0 worker calls!)
    funcs[0x2a000] = {
        "addr": 0x2a000, "name": "OtherUnrel", "link_name": "OtherUnrel_",
        "conv": "watcall", "proto": "void OtherUnrel(void)",
        "_file": "analysis/symbols/other.toml", "_kind": "func",
    }
    git("commit", "--allow-empty", "-qm", "unrelated")
    assert overnight.run_overnight(window_budget=1.0, wave="wave4b", repair_budget=0.0) == 0
    assert len(worker_calls) == 1
    m2 = json.loads((fp_repo / "build/wave4/metrics.json").read_text())
    assert m2["wave4b"]["cache_hits_skipped"] == 1
    assert m2["wave4b"]["cache"]["hits"] == 1
    assert m2["wave4b"]["cache"]["preserved_unrelated"] == 1
    assert m2["wave4b"]["cache"]["schema_version"] == wave4_fp.CACHE_SCHEMA_VERSION

    # Explicit --wave4-retry bypasses persistent cache
    assert overnight.run_overnight(window_budget=1.0, wave="wave4b", repair_budget=0.0, wave4_retry=True) == 0
    assert len(worker_calls) == 2

    # Change relevant dependency (Helper's address) -> Invocation 4 invalidates cache and runs worker!
    funcs[0x10040]["addr"] = 0x1004c
    funcs[0x1004c] = funcs.pop(0x10040)
    assert overnight.run_overnight(window_budget=1.0, wave="wave4b", repair_budget=0.0) == 0
    assert len(worker_calls) == 3
    m4 = json.loads((fp_repo / "build/wave4/metrics.json").read_text())
    assert m4["wave4b"]["cache"]["invalidated_dep_change"] == 1


# ---------------------------------------------------------------------------
# 6. Incremental audit state consistency (`load_audit_report_incremental`)
# ---------------------------------------------------------------------------

def test_incremental_audit_tracks_resolved_omf_deps_and_extents_and_fails_open(fp_repo, monkeypatch):
    ref, cand, funcs, datas, p, omf_deps = _build_4b_fixture(fp_repo)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    rows = [{"addr": 0x10000, "scope": "in", "c": "T4", "module": "MOD_A"}]
    monkeypatch.setattr(t3_audit, "discover", lambda f, r: ([dict(cand, tier="T4", skip_reason=None)], []))

    audited_calls = []

    def fake_audit_unit(ctx, unit):
        audited_calls.append(unit["ref"])
        return [dict(
            cand, tier="T4", status="MISMATCH", audited=True,
            best={"index": 0, "cflags": cand["declared_cflags"], "score": [1, 0, 0, 0, 0], "unresolved": []},
            attempts=[{"index": 0, "cflags": cand["declared_cflags"], "result": "MISMATCH", "unresolved": []}],
            omf_deps=omf_deps,
        )]

    monkeypatch.setattr(t3_audit, "audit_unit", fake_audit_unit)
    inputs = (p, funcs, by_link, rows, [])

    # 1. Initial audit populates unit_meta with omf_deps + resolved `Helper_` + extents
    rep1 = wave4a.load_audit_report_incremental(inputs=inputs, refresh_stale=True)
    assert audited_calls == [ref]
    state = json.loads((fp_repo / "build/wave4/audit_state.json").read_text())
    assert state["unit_meta"][ref]["omf_deps"]["external_symbols"] == ["Helper_", "_items", "_missing_sym"]
    assert state["unit_meta"][ref]["deps"]["Helper_"] == 0x10040

    # 2. Adding an unrelated symbol does NOT re-audit `ref`!
    funcs[0x2b000] = {
        "addr": 0x2b000, "name": "NoTouch", "link_name": "NoTouch_",
        "conv": "watcall", "proto": "void NoTouch(void)",
        "_file": "analysis/symbols/other.toml", "_kind": "func",
    }
    by_link2 = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    rep2 = wave4a.load_audit_report_incremental(inputs=(p, funcs, by_link2, rows, []), refresh_stale=True)
    assert rep2["meta"]["refreshed_units"] == 0 and len(audited_calls) == 1

    # 3. Changing resolved external `Helper_`'s address DOES re-audit `ref`!
    funcs[0x10040]["addr"] = 0x10048
    by_link3 = {e["link_name"]: e for t in (funcs, datas) for e in t.values() if e.get("link_name")}
    rep3 = wave4a.load_audit_report_incremental(inputs=(p, funcs, by_link3, rows, []), refresh_stale=True)
    assert rep3["meta"]["refreshed_units"] == 1 and len(audited_calls) == 2

    # 4. Changing function extent in `p.functions` DOES re-audit `ref`!
    p.functions[0]["end"] = 0x10034
    rep4 = wave4a.load_audit_report_incremental(inputs=(p, funcs, by_link3, rows, []), refresh_stale=True)
    assert rep4["meta"]["refreshed_units"] == 1 and len(audited_calls) == 3
