"""analysis/modules.toml is well-formed, sorted, contiguous, inside the code
object, aligned to discovered function starts, and consistent with the scan."""
import os
import tomllib

import pytest

from wc1 import analysis, path

pytestmark = pytest.mark.skipif(not os.path.exists(path("original", "install", "war.exe")),
                                reason="needs original/ (make extract)")
CONF = {"verified", "high", "medium", "low", "speculative"}
KINDS = {"game", "gfx", "asm", "asm-shared", "runtime", "ail", "resource"}


@pytest.fixture(scope="module")
def prog():
    return analysis.run()


@pytest.fixture(scope="module")
def mods():
    with open(path("analysis", "modules.toml"), "rb") as fh:
        return tomllib.load(fh)["module"]


def test_schema(mods):
    names = set()
    for m in mods:
        for k in ("name", "start", "end", "kind", "confidence", "name_confidence", "evidence"):
            assert k in m, (m.get("name"), k)
        assert m["kind"] in KINDS and m["confidence"] in CONF and m["name_confidence"] in CONF
        assert m["evidence"] and all(isinstance(x, str) and x for x in m["evidence"])
        assert m["name"] not in names
        names.add(m["name"])


def test_sorted_contiguous_in_code(mods, prog):
    lo, hi = prog.code.base, prog.code.base + prog.code.vsize
    assert mods[0]["start"] == lo and mods[-1]["end"] == hi
    for m in mods:
        assert m["start"] < m["end"]
    for a, b in zip(mods, mods[1:]):
        assert a["end"] == b["start"]


def test_boundaries_on_function_starts(mods, prog):
    starts = {f["start"] for f in prog.functions}
    for m in mods:
        assert m["start"] in starts, hex(m["start"])


def test_zero_fill_rule(mods, prog):
    fs = prog.functions
    prev = {f["start"]: fs[i - 1]["end"] for i, f in enumerate(fs) if i}
    for m in mods:
        if any("(zero16)" in e or "(zero4)" in e or "(zero2)" in e for e in m["evidence"]):
            s = m["start"]
            gap = prog.cbytes[prev[s] - prog.code.base:s - prog.code.base]
            assert gap and not any(gap), hex(s)
            if any("(zero16)" in e for e in m["evidence"]):
                assert s % 16 == 0
