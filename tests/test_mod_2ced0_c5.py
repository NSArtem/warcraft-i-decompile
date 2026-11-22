import os
import struct

import pytest

from wc1 import t4spec
from wc1 import path

pytestmark = pytest.mark.skipif(not (os.path.exists(path('original', 'install', 'war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')

REF = 'src/mod_2ced0/units_draw_reference.c'

SCROLL_X = 0x500d0
SCROLL_Y = 0x500d2
DRAW_LIST = 0x5a490
FIRE_HEAVY = 0x5a7b4
FIRE_LIGHT = 0x5a7b8
OBJ_ARRAY = 0x59644
CURSOR_FLAGS = 0x5a7c9
DRAW_COLOR = 0x5ad30
BLITTERS = 0x55288
GRP_TABLE = 0x522d8
UNIT_SZ = 0x60
NUNITS = 4

BLIT_STUBS = [0x7f0000 + 0x20 * i for i in range(8)]

state = {}
bitmap_vals = {"v": (20, 20, 20, 20)}


def _init_emu(emu, watch):
    emu.uc.mem_map(0x7f0000, 0x1000)
    units = emu.alloc(UNIT_SZ * NUNITS, 16)
    links = emu.alloc(UNIT_SZ * NUNITS, 16)
    objs = emu.alloc(0x26 * 100, 16)
    heavy = emu.alloc(16, 16)
    light = emu.alloc(16, 16)
    state.update(units=units, links=links, objs=objs, heavy=heavy, light=light)
    watch[:] = [(units, UNIT_SZ * NUNITS), (links, UNIT_SZ * NUNITS),
                (objs, 0x26 * 100), (heavy, 16), (light, 16), (DRAW_COLOR, 1)]


def _fill_shorts(emu, rng, addr, n, lo, hi):
    emu.write(addr, b"".join(struct.pack("<h", rng.randint(lo, hi)) for _ in range(n)))


def _make_case(rng, label=""):
    seed = rng.getrandbits(32)

    def setup(emu):
        import random
        r = random.Random(seed)
        emu.write(SCROLL_X, struct.pack("<HH", r.randint(0, 20), r.randint(0, 20)))
        emu.write(CURSOR_FLAGS, bytes([r.randint(0, 1)]))
        emu.write(0x51808, bytes(r.randint(0, 255) for _ in range(8)))
        emu.write(0x552a8, bytes(r.randint(0, 4) for _ in range(16)))
        _fill_shorts(emu, r, 0x51aba, 0xd2 // 2, -20, 40)
        _fill_shorts(emu, r, 0x51b9a, 0xd8 // 2, 4, 40)
        _fill_shorts(emu, r, 0x59530, 0xd8 // 2, -20, 40)
        emu.write(GRP_TABLE, struct.pack("<4I", 0, 0, 0, 0))
        for i in range(8):
            emu.write(BLITTERS + 4 * i, struct.pack("<I", BLIT_STUBS[i]))
        emu.write(state["objs"], bytes(r.getrandbits(8) for _ in range(0x26 * 100)))
        emu.write(state["heavy"], bytes(16))
        emu.write(state["light"], bytes(16))
        emu.write(FIRE_HEAVY, struct.pack("<I", state["heavy"]))
        emu.write(FIRE_LIGHT, struct.pack("<I", state["light"]))
        emu.write(OBJ_ARRAY, struct.pack("<I", state["objs"]))
        n = r.randint(0, NUNITS)
        ptrs = []
        for k in range(NUNITS):
            base = state["units"] + k * UNIT_SZ
            b = bytearray(r.getrandbits(8) for _ in range(UNIT_SZ))
            b[0:4] = struct.pack("<hh", r.randint(0, 600), r.randint(0, 400))
            b[8] = r.randint(0, 7)
            flags = r.choice([0, 0x10, 0x40, 0x200, 0x4, 0x50])
            b[0x10:0x12] = struct.pack("<H", flags)
            b[0x0e:0x10] = struct.pack("<H", r.choice([0, 0x100, 0x0]))
            b[0x1b] = r.randint(0, 51)
            b[0x1d] = r.randint(0, 3)
            b[0x1e] = r.choice([0, 0, 1, 7])
            b[0x36:0x3a] = struct.pack("<HH", r.choice([0, 5, 0x300]), r.choice([0, 9, 0x100]))
            if r.random() < 0.6:
                b[0x58:0x5c] = struct.pack("<I", state["links"] + k * UNIT_SZ)
            else:
                b[0x58:0x5c] = bytes(4)
            emu.write(base, bytes(b))
            if k < n:
                ptrs.append(base)
        emu.write(state["links"], bytes(r.getrandbits(8) for _ in range(UNIT_SZ * NUNITS)))
        emu.write(DRAW_LIST, b"".join(struct.pack("<I", p) for p in ptrs) + struct.pack("<I", 0))
        bitmap_vals["v"] = (r.randint(4, 40), r.randint(4, 40), r.randint(-5, 30), r.randint(-5, 30))

    return t4spec.T4Case(args=(), setup=setup, label=label)


def _grp_info(e, log):
    log(e.reg("eax"), e.reg("edx"))
    w, h, r0, r1 = bitmap_vals["v"]
    e.write(e.reg("ebx"), struct.pack("<hhhh", w, h, r0, r1))
    e.write(e.reg("ecx"), struct.pack("<h", 3))
    esp = e.reg("esp")
    for off, val in ((4, 2), (8, 30), (12, 20)):
        p = struct.unpack("<I", e.read(esp + off, 4))[0]
        e.write(p, struct.pack("<h", val))
    return 0


def test_t3_nothing():
    pass


def test_ref_mismatch():
    t4spec.assert_ref_mismatch(path('src/mod_2ced0'), ['units_draw_reference.c'])


def test_units_draw():
    watch = []
    stubs = [
        t4spec.T4Stub(0x3abb0, fn=_grp_info, stack_pop=12),
        t4spec.T4Stub(0x2d704, log_regs=("eax", "edx", "ebx")),
        t4spec.T4Stub(0x32970, log_regs=("eax", "edx", "ebx")),
        t4spec.T4Stub(0x3ac10, log_regs=("eax", "edx", "ebx")),
    ] + [t4spec.T4Stub(a, log_regs=("eax", "edx")) for a in BLIT_STUBS]

    import random
    seeder = random.Random(1)
    cases = [_make_case(seeder, "fixed[%d]" % i) for i in range(4)]

    t4spec.run_spec(REF, "UnitsDraw_", 0x2d8c8, cases=cases, watch=watch, stubs=stubs,
                    out_regs=(), init_emu=lambda emu: _init_emu(emu, watch),
                    rand_cases=60, rand_gen=_make_case, log_cap=4096)
