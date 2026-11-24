"""Unit tests for Wave 4A deterministic dependency inventory, ABI checks, and C rewriter."""
import types

import pytest

from wc1 import wave4_deps


# ---------------------------------------------------------------------------
# Syntax-aware C lexer & rewriter
# ---------------------------------------------------------------------------

def test_rewrite_c_symbol_preserves_comments_strings_preproc_and_members():
    src = """/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
#include "foo.h"
#define foo_macro(x) (x)
/* fn_12345 in block comment */
// fn_12345 in line comment
extern int fn_12345(int a);
struct S { int fn_12345; };
int caller(struct S *s, struct S v)
{
    const char *msg = "fn_12345";
    char c = 'x';
    return fn_12345(s->fn_12345 + v.fn_12345) + (int)msg[0] + c;
}
"""
    out, count = wave4_deps.rewrite_c_symbol(src, "fn_12345", "CanonicalFunc")
    assert count == 2
    assert "/* codegen-compiler: 10.0a */" in out
    assert "/* codegen-flags: -s -ot -ol -4r -zp2 */" in out
    assert "/* fn_12345 in block comment */" in out
    assert "// fn_12345 in line comment" in out
    assert 'const char *msg = "fn_12345";' in out
    assert "s->fn_12345 + v.fn_12345" in out
    assert "extern int CanonicalFunc(int a);" in out
    assert "return CanonicalFunc(" in out


def test_rewrite_c_symbol_drops_redundant_extern_decl_only():
    src = """/* codegen-compiler: 10.0a */
#include "mod.h"
extern void fn_1b48c(void); /* stale */
void Caller(void)
{
    fn_1b48c();
}
"""
    out, count = wave4_deps.rewrite_c_symbol(
        src, "fn_1b48c", "RealFunc", drop_redundant_decl=True,
    )
    assert count == 2
    assert "extern void" not in out
    assert "RealFunc();" in out
    assert "/* codegen-compiler: 10.0a */" in out


def test_rewrite_c_symbol_rejects_local_macro_typedef_collisions_and_trigraphs():
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("void f(void) { int Real = 1; fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("void f(int Real) { fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("void f(void) { Rect Real; fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("void f(void) { int a, Real; fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("typedef int Real;\nvoid f(void) { fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("static int Real;\nvoid f(void) { fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="collision"):
        wave4_deps.rewrite_c_symbol("#define Real 1\nvoid f(void) { fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="trigraph"):
        wave4_deps.rewrite_c_symbol("/* ??= */\nvoid f(void) { fn_10000(); }", "fn_10000", "Real")
    with pytest.raises(ValueError, match="unterminated"):
        wave4_deps.rewrite_c_symbol("/* unterminated\nvoid f(void) { fn_10000(); }", "fn_10000", "Real")


def test_drop_redundant_decl_does_not_delete_multi_decls_initializers_or_unrelated_protos():
    src = (
        "extern short old_v, keep_v;\n"
        "int (*cb)(void) = old_v;\n"
        "extern void Other(int old_v);\n"
        "void f(void) { old_v = 1; }\n"
    )
    out, _ = wave4_deps.rewrite_c_symbol(src, "old_v", "new_v", drop_redundant_decl=True)
    assert "keep_v" in out
    assert "int (*cb)(void) = new_v;" in out
    assert "extern void Other(int new_v);" in out


# ---------------------------------------------------------------------------
# ABI & data declaration compatibility
# ---------------------------------------------------------------------------

def test_prototypes_compatible_conservative_checks():
    assert wave4_deps.prototypes_compatible(
        "extern void fn_100(unsigned short a, void *p);",
        "void Real(unsigned short flags, struct Unit *u)",
        "watcall",
        expected_ident="fn_100",
    )
    # Unnamed primitive parameters must parse without splitting mid-token
    assert wave4_deps.prototypes_compatible("extern void fn(int);", "void Real(int x)", "watcall", expected_ident="fn")
    assert not wave4_deps.prototypes_compatible("extern void fn(short);", "void Real(signed)", "watcall", expected_ident="fn")
    assert not wave4_deps.prototypes_compatible("extern void fn(struct Unit);", "void Real(struct Unit *u)", "watcall", expected_ident="fn")
    # Unrelated prototype whose parameter happens to share `ident` must be rejected
    assert not wave4_deps.prototypes_compatible(
        "extern void Other(int old_fn);", "void Real(int x)", "watcall", expected_ident="old_fn",
    )
    assert wave4_deps.prototypes_compatible(
        "extern int __cdecl fn_200(const char *fmt, ...);",
        "int __cdecl Fatal(const char *fmt, ...)",
        "cdecl",
    )
    # Calling convention mismatch -> rejected
    assert not wave4_deps.prototypes_compatible(
        "extern int fn_200(int a);",
        "int Real(int a)",
        "cdecl",
    )
    # Argument count mismatch -> rejected
    assert not wave4_deps.prototypes_compatible(
        "extern void fn_100(int a);",
        "void Real(int a, int b)",
        "watcall",
    )
    # K&R empty parens -> rejected
    assert not wave4_deps.prototypes_compatible(
        "extern void fn_100();",
        "void Real(void)",
        "watcall",
    )
    # Distinct concrete pointer types -> rejected
    assert not wave4_deps.prototypes_compatible(
        "extern void fn_100(short *p);",
        "void Real(unsigned char *p)",
        "watcall",
    )


def test_data_decls_compatible_rejects_pointer_vs_array_and_const_mismatch():
    assert wave4_deps.data_decls_compatible("extern unsigned short *old_ptr;", "old_ptr", "unsigned short *")
    assert wave4_deps.data_decls_compatible("extern unsigned char old_tbl[];", "old_tbl", "unsigned char[16]")
    assert wave4_deps.data_decls_compatible("extern long game_rng_seed;", "game_rng_seed", "long")
    # Pointer vs array on extern data changes indirection -> MUST reject!
    assert not wave4_deps.data_decls_compatible("extern unsigned char *old_tbl;", "old_tbl", "unsigned char[16]")
    # const mismatch -> rejected
    assert not wave4_deps.data_decls_compatible("extern char old_str[11];", "old_str", "const char[11]")
    # width mismatch -> rejected
    assert not wave4_deps.data_decls_compatible("extern short old_w;", "old_w", "unsigned short")


# ---------------------------------------------------------------------------
# Generic struct layout & containing data owner detection
# ---------------------------------------------------------------------------

def test_parse_header_structs_and_containing_owner(tmp_path):
    inc = tmp_path / "inc"
    inc.mkdir()
    (inc / "sample.h").write_text("""
typedef struct Rect {
    short x, y;
    short w, h;
} Rect;
typedef struct Layer {
    unsigned short flags;
    Rect box;
    void (*draw)(void);
} Layer;
""")
    structs, aliases = wave4_deps.parse_header_structs(str(inc))
    assert structs["Rect"]["size"] == 8
    assert structs["Layer"]["size"] == 14
    datas = {
        0x59000: {"addr": 0x59000, "name": "layers", "link_name": "_layers", "type": "Layer[32]", "_file": "a.toml"},
        # Bogus oversized heap pointer annotated as huge array overlapping 35 globals
        0x58580: {"addr": 0x58580, "name": "object_map", "link_name": "_object_map", "type": "void *[4096]", "_file": "b.toml"},
        0x58584: {"addr": 0x58584, "name": "other_global", "link_name": "_other_global", "type": "unsigned long", "_file": "b.toml"},
    }
    for i in range(35):
        a = 0x58590 + i * 4
        datas[a] = {"addr": a, "name": f"g_{i}", "link_name": f"_g_{i}", "type": "unsigned long", "_file": "b.toml"}

    owner = wave4_deps.find_containing_owner(0x59000 + 14 * 2 + 2, datas, structs, aliases)
    assert owner is not None
    assert owner["name"] == "layers"
    assert owner["element_index"] == 2
    assert owner["field_offset"] == 2
    assert owner["field_name"] == "box"

    # Must NOT treat oversized pointer `object_map` as containing owner of 0x58600
    assert wave4_deps.find_containing_owner(0x58600, datas, structs, aliases) is None


# ---------------------------------------------------------------------------
# Dependency inventory, corroboration, grouping & prioritization
# ---------------------------------------------------------------------------

def _fake_prog(funcs_spec, insns_map=None, fix_at=None):
    return types.SimpleNamespace(
        functions=funcs_spec,
        insns=insns_map or {},
        fix_at=fix_at or {},
        le=types.SimpleNamespace(obj_at=lambda a: types.SimpleNamespace(index=0 if a < 0x50000 else 1, base=0x10000 if a < 0x50000 else 0x50000)),
    )


def _insn(mnemonic, op_str, size=5):
    return types.SimpleNamespace(mnemonic=mnemonic, op_str=op_str, size=size)


def test_inventory_never_trusts_spelling_alone_and_respects_best_attempt(tmp_path):
    ref_dir = tmp_path / "src" / "m"
    ref_dir.mkdir(parents=True)
    ref = ref_dir / "caller_reference.c"
    ref.write_text(
        "extern void fn_20000(void);\n"
        "extern void fn_20100(void);\n"
        "void Caller(void) { fn_20000(); fn_20100(); }\n"
    )
    # Original function 0x10000 actually calls 0x20000 ONLY (NOT 0x20100!)
    p = _fake_prog(
        [{"start": 0x10000, "end": 0x10020}, {"start": 0x20000, "end": 0x20010}, {"start": 0x20100, "end": 0x20110}],
        insns_map={0x10004: _insn("call", "0x20000")},
    )
    funcs = {
        0x20000: {"addr": 0x20000, "name": "RealTarget", "link_name": "RealTarget_", "conv": "watcall", "proto": "void RealTarget(void)", "_file": "t.toml"},
        0x20100: {"addr": 0x20100, "name": "OtherTarget", "link_name": "OtherTarget_", "conv": "watcall", "proto": "void OtherTarget(void)", "_file": "t.toml"},
    }
    best_att = {
        "index": 0, "score": [0, 0, 0, 0, 0],
        "unresolved": [
            {"symbol": "fn_20000_", "self_relative": True, "loc": 9, "operand": "0x0", "addend": 0, "original_candidate": 0x20000},
            {"symbol": "fn_20100_", "self_relative": True, "loc": 9, "operand": "0x0", "addend": 0, "original_candidate": None},
        ],
    }
    bad_att = {
        "index": 1, "score": [10, 0, 0, 0, 0],
        # Misaligned non-best attempt points fn_20100_ at 0x20000 — must be ignored!
        "unresolved": [
            {"symbol": "fn_20100_", "self_relative": True, "loc": 9, "operand": "0x0", "addend": 0, "original_candidate": 0x20000},
        ],
    }
    rep = {"results": [{
        "addr": 0x10000, "tier": "T4", "name": "Caller", "link_name": "Caller_",
        "ref": "src/m/caller_reference.c", "toml": "analysis/symbols/m.toml", "module": "M.C",
        "best": best_att, "attempts": [best_att, bad_att],
    }]}
    inv = wave4_deps.build_dependency_inventory(rep, p, funcs, {}, {e["link_name"]: e for e in funcs.values()}, repo_root=str(tmp_path))
    by_sym = {d["symbol"]: d for d in inv["dependencies"]}
    assert by_sym["fn_20000_"]["classification"] == wave4_deps.MECHANICAL_FUNC_RENAME
    assert by_sym["fn_20000_"]["expected_address"] == 0x20000
    # Spelling `fn_20100_` is NOT corroborated in original binary and non-best attempt was ignored -> AMBIGUOUS!
    assert by_sym["fn_20100_"]["classification"] == wave4_deps.AMBIGUOUS
    assert by_sym["fn_20100_"]["expected_address"] is None


def test_inventory_groups_shared_callers_interior_fields_and_reuses_established_mappings(tmp_path):
    (tmp_path / "src" / "include").mkdir(parents=True)
    (tmp_path / "src" / "include" / "tbl.h").write_text("typedef struct Entry { short a; short b; } Entry;\n")
    (tmp_path / "src" / "m").mkdir(parents=True)
    (tmp_path / "src" / "m" / "c1_reference.c").write_text(
        "extern void old_alias(void);\nextern short field_a;\nvoid C1(void) { old_alias(); field_a = 1; }\n"
    )
    (tmp_path / "src" / "m" / "c2_reference.c").write_text(
        "extern void old_alias(void);\nextern short field_b;\nvoid C2(void) { old_alias(); field_b = 2; }\n"
    )
    p = _fake_prog(
        [{"start": 0x10000, "end": 0x10020}, {"start": 0x10040, "end": 0x10060}, {"start": 0x20000, "end": 0x20010}],
        insns_map={
            0x10004: _insn("call", "0x20000"),
            0x1000a: _insn("mov", "word ptr [0x52004], 1", size=6),
            0x10044: _insn("call", "0x20000"),
            0x1004a: _insn("mov", "word ptr [0x52006], 2", size=6),
        },
        fix_at={0x1000c: (0, 0x52004), 0x1004c: (0, 0x52006)},
    )
    funcs = {
        0x20000: {"addr": 0x20000, "name": "SharedFn", "link_name": "SharedFn_", "conv": "watcall", "proto": "void SharedFn(void)", "_file": "t.toml"},
    }
    datas = {
        0x52000: {"addr": 0x52000, "name": "entries", "link_name": "_entries", "type": "Entry[8]", "_file": "t.toml"},
    }
    att1 = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [
        {"symbol": "old_alias_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": None},
        {"symbol": "_field_a", "self_relative": False, "loc": 9, "addend": 0, "original_candidate": 0x52004},
    ]}
    att2 = {"index": 0, "score": [1, 0, 0, 0, 0], "unresolved": [
        {"symbol": "old_alias_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": None},
        {"symbol": "_field_b", "self_relative": False, "loc": 9, "addend": 0, "original_candidate": 0x52006},
    ]}
    rep = {"results": [
        {"addr": 0x10000, "tier": "T4", "name": "C1", "link_name": "C1_", "ref": "src/m/c1_reference.c", "toml": "t.toml", "module": "M", "best": att1, "attempts": [att1]},
        {"addr": 0x10040, "tier": "T4", "name": "C2", "link_name": "C2_", "ref": "src/m/c2_reference.c", "toml": "t.toml", "module": "M", "best": att2, "attempts": [att2]},
    ]}
    # Without established mappings, non-addr `old_alias_` with candidate=None is AMBIGUOUS
    inv0 = wave4_deps.build_dependency_inventory(rep, p, funcs, datas, {}, repo_root=str(tmp_path))
    g_by_id0 = {g["group_id"]: g for g in inv0["groups"]}
    assert g_by_id0["sym_old_alias"]["classification"] == wave4_deps.AMBIGUOUS
    # Both interior fields 0x52004 and 0x52006 share ONE `owner_52000` group across both callers!
    assert "owner_52000" in g_by_id0
    assert g_by_id0["owner_52000"]["classification"] == wave4_deps.CONTAINING_OWNER_FIELD
    assert set(g_by_id0["owner_52000"]["symbols"]) == {"_field_a", "_field_b"}
    assert len(g_by_id0["owner_52000"]["affected_functions"]) == 2

    # With established mapping `old_alias_ -> 0x20000` (corroborated against actual calls in C1 & C2!),
    # both callers collapse into ONE mechanical group `func_20000` prioritized ahead of research!
    est = {"old_alias_": {"target_addr": 0x20000, "canonical_link": "SharedFn_", "canonical_name": "SharedFn"}}
    inv1 = wave4_deps.build_dependency_inventory(rep, p, funcs, datas, {}, repo_root=str(tmp_path), established_mappings=est)
    assert inv1["groups"][0]["group_id"] == "func_20000"
    assert inv1["groups"][0]["classification"] == wave4_deps.MECHANICAL_FUNC_RENAME
    assert len(inv1["groups"][0]["affected_functions"]) == 2


def test_inventory_extracts_test_extra_and_detects_conflicts(tmp_path):
    (tmp_path / "src" / "m").mkdir(parents=True)
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "src" / "m" / "a_reference.c").write_text("extern void old_fn(void);\nvoid A(void) { old_fn(); }\n")
    (tmp_path / "src" / "m" / "b_reference.c").write_text("extern void old_fn(void);\nvoid B(void) { old_fn(); }\n")
    (tmp_path / "tests" / "test_m.py").write_text('TARGET = 0x20000\nEXTRA = {"old_fn_": TARGET}\ndef test_a(): pass\ndef test_b(): pass\n')
    p = _fake_prog(
        [{"start": 0x10000, "end": 0x10020}, {"start": 0x10040, "end": 0x10060},
         {"start": 0x20000, "end": 0x20010}, {"start": 0x20020, "end": 0x20030}],
        insns_map={0x10004: _insn("call", "0x20000"), 0x10044: _insn("call", "0x20020")},
    )
    att_a = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [{"symbol": "old_fn_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": None}]}
    att_b = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [{"symbol": "old_fn_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": 0x20020}]}
    rep = {"results": [
        {"addr": 0x10000, "tier": "T4", "name": "A", "link_name": "A_", "ref": "src/m/a_reference.c", "toml": "t.toml", "module": "M", "ref_verified_by": "difftest: tests/test_m.py::test_a", "best": att_a, "attempts": [att_a]},
        {"addr": 0x10040, "tier": "T4", "name": "B", "link_name": "B_", "ref": "src/m/b_reference.c", "toml": "t.toml", "module": "M", "ref_verified_by": "difftest: tests/test_m.py::test_b", "best": att_b, "attempts": [att_b]},
    ]}
    inv = wave4_deps.build_dependency_inventory(rep, p, {}, {}, {}, repo_root=str(tmp_path))
    dep = inv["dependencies"][0]
    # Caller A corroborates 0x20000 via EXTRA, Caller B corroborates 0x20020 -> conflict -> AMBIGUOUS!
    assert dep["classification"] == wave4_deps.AMBIGUOUS
    assert dep["conflict_addresses"] == ["0x20000", "0x20020"]


def test_inventory_requires_per_caller_corroboration_and_skips_matched_rows(tmp_path):
    (tmp_path / "src" / "m").mkdir(parents=True)
    (tmp_path / "src" / "m" / "c1.c").write_text("extern void fn_20000(void);\nvoid C1(void) { fn_20000(); }\n")
    (tmp_path / "src" / "m" / "c2.c").write_text("extern void fn_20000(void);\nvoid C2(void) { fn_20000(); }\n")
    # C1 actually calls 0x20000, C2 does NOT call 0x20000 in the original binary!
    p = _fake_prog(
        [{"start": 0x10000, "end": 0x10020}, {"start": 0x10040, "end": 0x10060}, {"start": 0x20000, "end": 0x20010}],
        insns_map={0x10004: _insn("call", "0x20000")},
    )
    funcs = {0x20000: {"addr": 0x20000, "name": "Real", "link_name": "Real_", "conv": "watcall", "proto": "void Real(void)", "_file": "t.toml"}}
    att = {"index": 0, "score": [0, 0, 0, 0, 0], "unresolved": [{"symbol": "fn_20000_", "self_relative": True, "loc": 9, "addend": 0, "original_candidate": 0x20000}]}
    rep = {"results": [
        {"addr": 0x10000, "tier": "T4", "status": "MISMATCH", "name": "C1", "link_name": "C1_", "ref": "src/m/c1.c", "toml": "t.toml", "module": "M", "best": att, "attempts": [att]},
        {"addr": 0x10040, "tier": "T4", "status": "MISMATCH", "name": "C2", "link_name": "C2_", "ref": "src/m/c2.c", "toml": "t.toml", "module": "M", "best": att, "attempts": [att]},
        # Already MATCH_BUILDABLE row with a stale non-best unresolved must be ignored completely!
        {"addr": 0x10080, "tier": "T4", "status": "MATCH_BUILDABLE", "name": "C3", "link_name": "C3_", "ref": "src/m/c3.c", "toml": "t.toml", "module": "M", "best": {"score": [0, 0, 0, 0, 0], "unresolved": []}, "attempts": [att]},
    ]}
    inv = wave4_deps.build_dependency_inventory(rep, p, funcs, {}, {e["link_name"]: e for e in funcs.values()}, repo_root=str(tmp_path))
    dep = inv["dependencies"][0]
    assert len(dep["affected_functions"]) == 2  # C3 skipped!
    # C2 lacks independent binary corroboration -> MUST NOT be mechanical!
    assert not dep["mechanical"] and dep["classification"] == wave4_deps.AMBIGUOUS
