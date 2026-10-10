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
    """With no C replacements the wlink build must equal the original."""
    env = dict(os.environ)
    r = subprocess.run([sys.executable, "-m", "wc1.compare", path("original", "install", "war.exe"),
                        path("build", "war.exe")], capture_output=True, text=True, env=env)
    funcs, _, _ = symbols.load()
    if any(e.get("src") for e in funcs.values()):
        pytest.skip("build contains C replacements; identity not expected")
    assert r.returncode == 0, r.stdout
