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
    src = tmp_path / "probe.c"
    src.write_text('/* codegen-flags: -s -ot -ol -4r -zp2 */\n'
                   'extern int g(void);\n'
                   'const char probe_text[] = "path.war";\n'
                   'int Probe(int x) { return g() + x + probe_text[0]; }\n')
    o = str(tmp_path / "probe.obj")
    match.compile_c(str(src), None, o)
    m = omf.parse_object(o)
    # the literal lands in CONST (or CONST2 with -s), 9 bytes with the NUL
    cseg = next(s for s in m.segments if bytes(s.data) == b"path.war\0")
    assert m.seg("_TEXT")[1].align == 3
    q = str(tmp_path / "probe_p.obj")
    omfpatch.patch(o, q, align="byte", rename={cseg.name: "_DATA"}, empty={cseg.name})
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


def test_link_names_must_be_nasm_labels(tmp_path):
    """A `link` field becomes a NASM label in the generated asm, so a library's
    synthetic unit label (e.g. `<_TEXT+0>`) must stay in the evidence text.
    Regression: such a link name broke `make roundtrip` on 2026-11-19."""
    (tmp_path / "x.toml").write_text(
        '[[func]]\naddr = 0x40900\nname = "_init_stk"\nconv = "asm"\n'
        'link = "<_TEXT+0>"\nproto = "void _init_stk(void)"\n'
        'confidence = "high"\nevidence = ["test fixture"]\n')
    _, _, errors = symbols.load(str(tmp_path), strict=False)
    assert any("not a NASM label" in e for e in errors), errors


def test_ref_verified_by_validation(tmp_path):
    """wc1.symbols validates ref_verified_by test node existence, path hygiene,
    ref-file mention, and absence of skip/xfail cheats."""
    tdir = tmp_path / "tests"
    tdir.mkdir()
    (tdir / "test_good.py").write_text(
        "import os, pytest\n"
        "pytestmark = pytest.mark.skipif(not os.path.exists('war.exe'), reason='env')\n"
        "def test_ok():\n"
        "    assert 'foo_reference.c'\n"
        "def test_ok2():\n"
        "    assert 'foo_reference.c'\n"
        "class TestSuite:\n"
        "    def test_method(self):\n"
        "        assert 'foo_reference.c'\n"
    )
    (tdir / "test_cheats.py").write_text(
        "import pytest as pt\n"
        "import unittest as ut\n"
        "from pytest import skip as pskip, xfail as pxfail, importorskip\n"
        "def test_inline_skip():\n"
        "    assert 'foo_reference.c'\n"
        "    pt.skip('nope')\n"
        "def test_alias_skip():\n"
        "    assert 'foo_reference.c'\n"
        "    pskip('nope')\n"
        "def test_inline_xfail():\n"
        "    assert 'foo_reference.c'\n"
        "    pxfail('nope')\n"
        "def test_importorskip():\n"
        "    assert 'foo_reference.c'\n"
        "    importorskip('missing')\n"
        "def test_raise_skip_exc():\n"
        "    assert 'foo_reference.c'\n"
        "    raise pt.skip.Exception('nope')\n"
        "def test_raise_skiptest():\n"
        "    assert 'foo_reference.c'\n"
        "    raise ut.SkipTest('nope')\n"
        "@pt.mark.skip(reason='x')\n"
        "def test_dec_skip():\n"
        "    assert 'foo_reference.c'\n"
        "@pt.mark.xfail\n"
        "def test_dec_xfail():\n"
        "    assert 'foo_reference.c'\n"
        "@pt.mark.skipif(True, reason='always')\n"
        "def test_dec_skipif_true():\n"
        "    assert 'foo_reference.c'\n"
        "@ut.skip('always')\n"
        "def test_dec_ut_skip():\n"
        "    assert 'foo_reference.c'\n"
    )
    (tdir / "test_bad_pm.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.skip(reason='all')\n"
        "def test_ok():\n"
        "    assert 'foo_reference.c'\n"
    )

    root = str(tmp_path)
    ref = "src/demo/foo_reference.c"

    # Valid citations: plain, parenthetical note, multi-node, parametrized, Class::method
    for rvb in (
        "difftest: tests/test_good.py::test_ok",
        "difftest: tests/test_good.py::test_ok (extra note here)",
        "difftest: tests/test_good.py::test_ok, tests/test_good.py::test_ok2",
        "difftest: tests/test_good.py::test_ok[param0]",
        "difftest: tests/test_good.py::TestSuite::test_method",
    ):
        assert symbols.validate_ref_verified_by_entry(rvb, ref_rel=ref, repo_root=root) == [], rvb

    # Path / existence / format / ref-mention failures
    bad_cases = [
        ("difftest: tests/test_good.py", "must cite"),
        ("difftest: ../escape.py::test_ok", "relative 'tests/*.py'"),
        ("difftest: tools/test_good.py::test_ok", "relative 'tests/*.py'"),
        ("difftest: tests/missing.py::test_ok", "does not exist"),
        ("difftest: tests/test_good.py::test_missing", "not found"),
        ("difftest: tests/test_good.py::test_ok, tests/test_good.py::test_missing", "not found"),
        ("difftest: tests/test_good.py::TestSuite::test_missing", "not found"),
        ("difftest: tests/test_bad_pm.py::test_ok", "pytestmark"),
    ]
    for rvb, expect in bad_cases:
        errs = symbols.validate_ref_verified_by_entry(rvb, ref_rel=ref, repo_root=root)
        assert errs and any(expect in e for e in errs), (rvb, errs)

    # Missing ref basename mention in test file
    errs_ref = symbols.validate_ref_verified_by_entry(
        "difftest: tests/test_good.py::test_ok", ref_rel="src/demo/other_reference.c", repo_root=root,
    )
    assert errs_ref and "other_reference.c" in errs_ref[0], errs_ref

    # Every cheat variant in test_cheats.py must be rejected
    for fn in (
        "test_inline_skip", "test_alias_skip", "test_inline_xfail", "test_importorskip",
        "test_raise_skip_exc", "test_raise_skiptest", "test_dec_skip", "test_dec_xfail",
        "test_dec_skipif_true", "test_dec_ut_skip",
    ):
        rvb = f"difftest: tests/test_cheats.py::{fn}"
        errs = symbols.validate_ref_verified_by_entry(rvb, ref_rel=ref, repo_root=root)
        assert errs and "forbidden" in errs[0], (fn, errs)

    # check_ref_verified_by formats errors with file + hex addr
    funcs = {
        0x1000: {"_file": "analysis/symbols/demo.toml", "ref": ref,
                 "ref_verified_by": "difftest: tests/missing.py::test_x"},
    }
    errs_all = symbols.check_ref_verified_by(funcs, repo_root=root)
    assert len(errs_all) == 1 and "0x1000" in errs_all[0], errs_all


def test_ref_verified_by_rejects_oracle_suppression_and_tampering(tmp_path):
    """Shared AST prefilter rejects pytest.raises / suppress / try-except / finally-return /
    monkeypatch / shadow cheats while allowing legitimate mem_map/read try-except helpers."""
    tdir = tmp_path / "tests"
    tdir.mkdir()
    ref = "src/demo/foo_reference.c"
    root = str(tmp_path)

    (tdir / "test_legit.py").write_text(
        "from wc1 import t4spec\n"
        "def init_emu(emu):\n"
        "    try:\n"
        "        emu.uc.mem_map(0x6f0000, 0x1000)\n"
        "    except Exception:\n"
        "        pass\n"
        "def _probe(e):\n"
        "    try:\n"
        "        return bytes(e.read(0x1000, 4))\n"
        "    except Exception:\n"
        "        return b''\n"
        "def test_ok():\n"
        "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [], init_emu=init_emu)\n"
    )
    assert symbols.validate_ref_verified_by_entry(
        "difftest: tests/test_legit.py::test_ok", ref_rel=ref, repo_root=root,
    ) == []
    assert symbols.check_t4_test_source((tdir / "test_legit.py").read_text(), strict_pytestmark=True) is None

    cheats = {
        "expect_mismatch_helper": (
            "import pytest\nfrom wc1 import t4spec\n"
            "def _expect_mismatch(*a, **k):\n"
            "    with pytest.raises(AssertionError):\n"
            "        t4spec.run_spec(*a, **k)\n"
            "def test_bad():\n"
            "    _expect_mismatch('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "aliased_raises": (
            "import pytest\nfrom wc1 import t4spec\n"
            "r = pytest.raises\n"
            "def test_bad():\n"
            "    with r(AssertionError):\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "contextlib_suppress": (
            "import contextlib\nfrom wc1 import t4spec\n"
            "def test_bad():\n"
            "    with contextlib.suppress(AssertionError):\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "try_except_assertion": (
            "from wc1 import t4spec\n"
            "def test_bad():\n"
            "    try:\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
            "    except (AssertionError,):\n"
            "        pass\n"
        ),
        "try_bare_except_indirect": (
            "from wc1 import t4spec\n"
            "def _run():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
            "def test_bad():\n"
            "    try:\n"
            "        _run()\n"
            "    except:\n"
            "        pass\n"
        ),
        "finally_return": (
            "from wc1 import t4spec\n"
            "def test_bad():\n"
            "    try:\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
            "    finally:\n"
            "        return\n"
        ),
        "local_shadow": (
            "def run_spec(*a, **k): pass\n"
            "def test_bad():\n"
            "    run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "monkeypatch_attr": (
            "from wc1 import t4spec\n"
            "t4spec.run_spec = lambda *a, **k: None\n"
            "def test_bad():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "mock_patch_oracle": (
            "from unittest import mock\nfrom wc1 import t4spec\n"
            "def test_bad():\n"
            "    with mock.patch('wc1.t4spec.run_spec'):\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "except_specific_ucerror": (
            "from wc1 import t4spec\n"
            "def test_bad():\n"
            "    try:\n"
            "        t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
            "    except RuntimeError:\n"
            "        pass\n"
        ),
        "emu_call_override": (
            "from wc1 import t4spec\n"
            "def init(emu):\n"
            "    emu.call = lambda *a, **k: 0\n"
            "def test_bad():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [], init_emu=init)\n"
        ),
        "audit_forging_call": (
            "from wc1 import cemu, t4spec\n"
            "def test_bad():\n"
            "    cemu.record_t4_audit({'kind': 'run_pair'})\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "audit_env_tamper": (
            "import os\nfrom wc1 import t4spec\n"
            "def test_bad():\n"
            "    os.environ.pop('WC1_T4_AUDIT_LOG', None)\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "deep_attr_monkeypatch": (
            "from wc1 import t4spec\n"
            "t4spec.cemu.run_pair = lambda *a, **k: []\n"
            "def test_bad():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "builtin_setattr": (
            "from wc1 import cemu, t4spec\n"
            "def test_bad():\n"
            "    setattr(cemu, 'run_pair', lambda *a, **k: [])\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "alias_oracle_try": (
            "import functools\nfrom wc1 import t4spec\n"
            "go = functools.partial(t4spec.run_spec, 'src/demo/foo_reference.c')\n"
            "def test_bad():\n"
            "    try:\n"
            "        go('Foo_', 0x1000, [])\n"
            "    except ValueError:\n"
            "        pass\n"
        ),
        "skipif_not_false": (
            "import pytest\nfrom wc1 import t4spec\n"
            "@pytest.mark.skipif(not False, reason='always')\n"
            "def test_bad():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
        "skipif_true_or_x": (
            "import pytest\nfrom wc1 import t4spec\n"
            "@pytest.mark.skipif(True or (1 == 2), reason='always')\n"
            "def test_bad():\n"
            "    t4spec.run_spec('src/demo/foo_reference.c', 'Foo_', 0x1000, [])\n"
        ),
    }
    for name, src in cheats.items():
        p = tdir / f"test_{name}.py"
        p.write_text(src)
        errs = symbols.validate_ref_verified_by_entry(
            f"difftest: tests/test_{name}.py::test_bad", ref_rel=ref, repo_root=root,
        )
        assert errs, f"validate_ref_verified_by_entry missed {name}"
        assert symbols.check_t4_test_source(src, strict_pytestmark=True) is not None, name

    # Non-env pytestmark condition must be rejected in strict mode
    bad_pm_env = (
        "import sys, pytest\n"
        "pytestmark = pytest.mark.skipif(sys.platform != 'zzz', reason='fake')\n"
        "def test_ok(): assert True\n"
    )
    assert symbols.check_t4_test_source(bad_pm_env, strict_pytestmark=True) is not None
