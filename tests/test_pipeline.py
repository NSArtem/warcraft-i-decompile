"""Regression tests for the analysis/rebuild pipeline (need original/)."""
import os
import subprocess
import sys

import pytest

from wc1 import analysis, le, path, symbols

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="original files not extracted (make extract)")


def test_le_layout():
    e = le.load()
    assert [(o.base, o.vsize) for o in e.objects] == [(0x10000, 0x3212B), (0x50000, 0x155F0)]
    assert e.entry == 0x34584 and e.initial_esp == 0x655F0
    assert len(e.fixups_unique) == 8770


def test_code_coverage():
    p = analysis.run()
    cov = p.coverage()
    # at least 97% of the code object is decoded instructions or jump tables
    assert (cov["insn_bytes"] + cov["table_bytes"]) / cov["code_size"] > 0.97
    # every fixup inside the code object is either an instruction operand or table data
    for s in p.fix_at:
        if p.in_code(s):
            assert s in p.owner or s in p.table_bytes


def test_symbols_valid():
    funcs, datas, errors = symbols.load(strict=False)
    assert not errors, "\n".join(errors)


def test_symbol_addresses_are_function_starts():
    p = analysis.run()
    starts = {f["start"] for f in p.functions}
    funcs, _, _ = symbols.load()
    bad = [hex(a) for a in funcs if a not in starts]
    assert not bad, f"func entries not at discovered function starts: {bad}"


def test_identical_relink(tmp_path):
    """The wlink build (make build) must equal the original: C objects are
    linked in place, so this holds with C replacements too, unless a C file
    fell back to the legacy layout (then the build says so)."""
    r = subprocess.run([sys.executable, "-m", "wc1.compare", path("original", "install", "war.exe"),
                        path("build", "war.exe")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_omfpatch(tmp_path):
    """BYTE alignment, segment rename and zero-length anchors on a wcc386 object."""
    from wc1 import match, omf, omfpatch
    o = str(tmp_path / "init.obj")
    match.compile_c(path("src", "init.c"), None, o)
    m = omf.parse_object(o)
    assert m.seg("_TEXT")[1].align == 3 and m.seg("CONST")[1].length == 9
    q = str(tmp_path / "init_p.obj")
    omfpatch.patch(o, q, align="byte", rename={"CONST": "_DATA"}, empty={"CONST"})
    m2 = omf.parse_object(q)
    assert all(s.align == 1 for s in m2.segments)
    assert [s.name for s in m2.segments].count("_DATA") == 2
    assert all(s.length == 0 for s in m2.segments if s.cls == "DATA")
    t1, t2 = m.seg("_TEXT")[1], m2.seg("_TEXT")[1]
    assert t1.data == t2.data and len(t1.fixups) == len(t2.fixups)
    assert m.publics == m2.publics


def test_module_fields_checked():
    """`module =` must name the analysis/modules.toml range containing the function."""
    ok = {0x1d7cc: {"module": "INIT.C", "_file": "t"}}
    bad = {0x1d798: {"module": "FOO.C", "_file": "t"}}
    assert symbols.check_modules(ok) == []
    assert "INIT.C" in symbols.check_modules(bad)[0]


# ---------------------------------------------------------------------------
# Discovery plausibility: data tables and lifted mid-function blocks are not
# function starts (docs/subsystems/discovery.md).

def test_discovery_drops_data_and_lifted_blocks():
    p = analysis.run()
    starts = {f["start"] for f in p.functions}
    # a 12-byte data table that used to swallow the callback at 0x187a4
    assert 0x18798 not in starts
    assert 0x187a4 in starts, "the callback at 0x187a4 must be discovered"
    # a save-file template table decoded as code
    assert 0x24860 not in starts
    # shared epilogues / lifted blocks of neighbouring functions
    for a in (0x1e3ac, 0x2c1b3, 0x3c461):
        assert a not in starts, hex(a)
    # ... while genuine starts are untouched, including the two exemptions
    # of the stack check: a direct call target (_hardresume, which switches
    # stacks with lss) and an AIL function
    for a in (0x24ee0, 0x3d01e, 0x38aa8, 0x41819):
        assert a in starts, hex(a)


def test_discovery_audit_has_no_unexplained_underflow():
    """Every start except the AIL exemption passes the stack-balance veto."""
    from wc1 import discovery_audit
    rows = discovery_audit.rows_of()
    bad = [(r["start"], r["module"], r["frag"]) for r in rows
           if r["frag"] and r["kind"] != "ail"]
    assert not bad, bad


def test_runtime_pieces_are_classified_out_of_scope():
    """0x3d920/0x401bd/0x41819 are Watcom runtime pieces, recorded in
    clib.toml with explicit evidence (not a discovery change)."""
    funcs, _, _ = symbols.load()
    for a in (0x3D920, 0x401BD, 0x41819):
        assert a in funcs, hex(a)
        assert funcs[a]["_file"].endswith("clib.toml"), (hex(a), funcs[a]["_file"])
