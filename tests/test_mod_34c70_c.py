import functools
import os
import random
import struct

import pytest

from wc1 import path, t4spec
from wc1.t4spec import T4Case, T4Stub

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

SRC = path('src/mod_34c70', 'palette_lerp_reference.c')


@functools.cache
def _addr(name):
    by = t4spec.by_link_lenient()
    for k in ("_" + name, name):
        if k in by:
            return by[k]["addr"]
    raise KeyError(name)


@functools.cache
def _fn_addr(name):
    by = t4spec.by_link_lenient()
    for k in (name + "_", name):
        if k in by:
            return by[k]["addr"]
    cands = sorted(k for k in by if "setpalette" in k.lower().replace("_", "") and "addr" in by[k])
    if cands:
        return by[cands[0]]["addr"]
    raise KeyError(name)


def _vga_stub(e, log):
    esp = e.reg("esp")
    rgb, first, count = struct.unpack("<III", e.read(esp + 4, 12))
    log(rgb, first, count)
    return 0


def _case(rng, first, last, step, steps, label=""):
    base = bytes(rng.randrange(64) for _ in range(768))
    targ = bytes(rng.randrange(64) for _ in range(768))

    def setup(emu):
        emu.write(_addr("palette_base"), base)
        emu.write(_addr("palette_target"), targ)
        emu.write(_addr("palette_cur"), bytes(768))
    return T4Case(args=(first, last, step, steps), setup=setup, label=label)


def test_t3_files_match():
    pass


def test_palette_lerp():
    rng = random.Random(1234)
    cases = [
        _case(rng, 0, 0, 0, 1, "single0"),
        _case(rng, 0, 255, 5, 10, "full"),
        _case(rng, 10, 20, 10, 10, "end"),
        _case(rng, 5, 5, 1, 3, "one"),
        _case(rng, 250, 255, 7, 16, "top"),
        _case(rng, 3, 9, 0, 4, "zerostep"),
    ]
    for i in range(10):
        first = rng.randrange(256)
        last = rng.randrange(first, 256)
        steps = rng.randrange(1, 64)
        cases.append(_case(rng, first, last, rng.randrange(steps + 1), steps, "r%d" % i))
    t4spec.run_spec(
        SRC, "PaletteLerp_", 0x34c70, cases,
        watch=[(_addr("palette_cur"), 768)],
        stubs=[T4Stub(_fn_addr("VgaSetPaletteRange"), fn=_vga_stub)],
        out_regs=(),
        extra={"VgaSetPaletteRange_": _fn_addr("VgaSetPaletteRange")},
    )


def test_ref_guard():
    t4spec.assert_ref_mismatch(path('src/mod_34c70'), ['palette_lerp_reference.c'])
