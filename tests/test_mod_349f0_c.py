import os
import random
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_349f0', 'dirty_rect_add_layer_reference.c')

TBL = 0x5aa92
DX1, DY1, DX2, DY2, DW, DH = 0x5aa80, 0x5aa82, 0x5aa84, 0x5aa86, 0x5aa88, 0x5aa8a


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_349f0'), [])


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_349f0'), ['dirty_rect_add_layer_reference.c'])


def _sym_addrs():
    by = t4spec.by_link_lenient()
    return by


def _mk(id_, layer, rect):
    def setup(emu):
        by = t4spec.by_link_lenient()

        def a(n, d):
            e = by.get(n)
            return e["addr"] if e else d
        emu.write(a("_dat_5aa92", TBL) + id_ * 18, struct.pack("<9h", *layer))
        for n, v in zip(("_dirty_x1", "_dirty_y1", "_dirty_x2", "_dirty_y2"), rect):
            emu.write(a(n, 0), struct.pack("<h", v))
    return setup


def test_dirty_rect_add_layer():
    by = t4spec.by_link_lenient()
    addrs = [by[n]["addr"] for n in ("_dirty_x1", "_dirty_y1", "_dirty_x2",
                                     "_dirty_y2", "_dirty_w", "_dirty_h")
             if n in by]
    watch = [(a, 2) for a in addrs]
    tb = by.get("_dat_5aa92", {}).get("addr", TBL)
    watch.append((tb, 18 * 4))
    cases = []
    layers = [
        (10, 20, 30, 40, 0, 0, 0, 0, 0),
        (-5, -6, 100, 100, 0, 0, 0, 0, 0),
        (0, 0, 1, 1, 0, 0, 0, 0, 0),
        (300, 200, 50, 60, 0, 0, 0, 0, 0),
    ]
    rects = [(100, 100, 50, 50), (0, 0, 500, 500), (30000, 30000, -30000, -30000), (5, 5, 5, 5)]
    for i, L in enumerate(layers):
        for j, R in enumerate(rects):
            cases.append(T4Case(args=(i,), setup=_mk(i, L, R), label=f"l{i}r{j}"))

    def gen(rng):
        i = rng.randrange(4)
        L = tuple(rng.randint(-200, 600) for _ in range(4)) + (0,) * 5
        R = (rng.randint(-200, 600), rng.randint(-200, 600),
             rng.randint(-200, 600), rng.randint(-200, 600))
        return T4Case(args=(i,), setup=_mk(i, L, R))

    t4spec.run_spec(SRC, "DirtyRectAddLayer_", 0x349f0, cases, watch=watch,
                    out_regs=(), rand_cases=32, rand_gen=gen)
