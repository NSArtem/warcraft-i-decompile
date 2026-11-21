import os
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_3aac0/bitmap_blit_transparent_fliph_reference.c')

M = {}
STATE = {"ret": 0, "shrink": False}


def _addr(*names):
    by = t4spec.by_link_lenient()
    for n in names:
        if n in by:
            return by[n]["addr"]
    raise AssertionError("symbol missing: %r" % (names,))


def init_emu(emu):
    M["sbmp"] = emu.alloc(16, 16)
    M["rect"] = emu.alloc(16, 16)
    M["cbmp"] = emu.alloc(16, 16)
    M["spix"] = emu.alloc(0x400, 16)
    M["cpix"] = emu.alloc(0x400, 16)


def _rd(e, a, n):
    return struct.unpack("<" + "I" * (n // 4), e.read(a, n))


def _clip_fn(e, log):
    esp = e.reg("esp")
    ps, pd = _rd(e, esp + 4, 8)
    log(*_rd(e, ps, 12))
    log(*_rd(e, pd, 12))
    if STATE["shrink"]:
        x, y, a, b, w, h = struct.unpack("<6h", e.read(ps, 12))
        if w > 0:
            e.write(ps, struct.pack("<6h", x + 1, y + 1, a, b, w - 1, h))
    return STATE["ret"]


def _copy_fn(e, log):
    esp = e.reg("esp")
    v = list(_rd(e, esp + 4, 24))
    for i in range(2, 6):
        v[i] &= 0xFFFF
    log(0)
    return 0


def _stubs():
    return [
        T4Stub(_addr("_RectClip"), fn=_clip_fn, log_regs=()),
        T4Stub(_addr("_RectCopyTransparentFlipH"), fn=_copy_fn, log_regs=()),
    ]


def _case(label, x, y, sw, sh, rx, ry, cw, ch, ret=0, shrink=False):
    def setup(e):
        STATE["ret"] = ret
        STATE["shrink"] = shrink
        e.write(M["sbmp"], struct.pack("<hhI", sw, sh, M["spix"]))
        e.write(M["cbmp"], struct.pack("<hhI", cw, ch, M["cpix"]))
        e.write(M["rect"], struct.pack("<6h", rx, ry, 3, 4, 5, 6))
        e.write(_addr("_cur_bitmap"), struct.pack("<I", M["cbmp"]))
    c = T4Case(label=label, setup=setup)
    c.args = (x & 0xFFFF, y & 0xFFFF, None, None)
    return c, x, y


def test_bitmap_blit_transparent_fliph():
    specs = [
        ("basic", 10, 20, 16, 8, 2, 3, 320, 200, 0, False),
        ("clipfail", 10, 20, 16, 8, 2, 3, 320, 200, 1, False),
        ("neg", -5, -7, 32, 16, 0, 0, 64, 64, 0, True),
        ("shrunk", 7, 9, 20, 10, 5, 4, 100, 50, 0, True),
        ("zero", 0, 0, 0, 0, 0, 0, 10, 10, 0, False),
    ]
    cases = []
    for s in specs:
        c, _, _ = _case(*s)
        cases.append(c)

    def fix(cs):
        for c in cs:
            c.args = (c.args[0], c.args[1], M["sbmp"], M["rect"])
    # addresses are only known after init_emu: patch lazily via setup wrapper
    for c in cases:
        orig = c.setup

        def wrapped(e, orig=orig, c=c):
            orig(e)
            c.args = (c.args[0], c.args[1], M["sbmp"], M["rect"])
        c.setup = wrapped
        c.args = (c.args[0], c.args[1], 0, 0)
    _run(cases)


def _run(cases):
    # args must be resolved after init_emu; run each case with a fresh emu
    for c in cases:
        def init(emu, c=c):
            init_emu(emu)
            c.args = (c.args[0], c.args[1], M["sbmp"], M["rect"])
        t4spec.run_spec(SRC, "BitmapBlitTransparentFlipH_", 0x3aac0, [c],
                        stubs=_stubs(), out_regs=(), init_emu=init)


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3aac0'), [])


def test_reference_still_mismatches():
    t4spec.assert_ref_mismatch(path('src/mod_3aac0'), ['bitmap_blit_transparent_fliph_reference.c'])
