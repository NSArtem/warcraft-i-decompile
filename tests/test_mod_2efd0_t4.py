import struct
import pytest
from wc1 import t4spec
from wc1.t4spec import T4Stub, T4Case

pytestmark = pytest.mark.skipif(
    not __import__("os").path.exists(__import__("wc1").path("analysis", "symbols")),
    reason="wc1 analysis tree not available")

SRC = "src/mod_2efd0/"


def w16(a, v):
    return {a: struct.pack("<H", v & 0xFFFF)}


def w32(a, v):
    return {a: struct.pack("<I", v & 0xFFFFFFFF)}


# ---------------------------------------------------------------- ObjectiveUnitCount
def _ouc_case(label, objectives, need, units):
    def setup(emu):
        ua = emu.alloc(200 * 0x5C, 16)
        mf = emu.alloc(64 * 64 * 2, 16)
        emu.write(ua, b"\x00" * (200 * 0x5C))
        emu.write(mf, b"\x00" * (64 * 64 * 2))
        emu.write(0x59640, struct.pack("<I", ua))
        emu.write(0x5857C, struct.pack("<I", mf))
        emu.write(0x50092, struct.pack("<H", objectives))
        emu.write(0x50096, struct.pack("<H", need))
        for i, (flags, owner, typ, on) in enumerate(units):
            b = ua + i * 0x5C
            emu.write(b + 8, struct.pack("<hh", 3, 3))
            emu.write(b + 0x10, struct.pack("<H", flags))
            emu.write(b + 0x1B, bytes([typ]))
            emu.write(b + 0x1E, bytes([owner]))
            if on:
                emu.write(mf + (3 * 64 + 3) * 2, struct.pack("<H", 0x20))
    return T4Case(setup=setup, label=label)


def test_objective_unit_count():
    cases = [
        _ouc_case("empty", 0, 0, []),
        _ouc_case("three on cell", 0, 0, [(0, 0, 1, 1)] * 3),
        _ouc_case("dead/enemy skipped", 0, 0,
                  [(1, 0, 1, 1), (0x200, 0, 1, 1), (0, 1, 1, 1), (0, 0, 1, 1)]),
        _ouc_case("special enough", 4, 2, [(0, 0, 0xF, 1), (0, 0, 0x12, 1)]),
        _ouc_case("special short", 4, 2, [(0, 0, 0xF, 1), (0, 0, 5, 1)]),
        _ouc_case("off cell", 0, 0, [(0, 0, 0xF, 0)] * 2),
    ]
    t4spec.run_spec(SRC + "objective_unit_count_reference.c",
                    "ObjectiveUnitCount_", 0x2F428, cases)


# ---------------------------------------------------------------- EndCheckObjectives
def _eco(label, pba=0, cheat=0, train=0, unit=0, men=(0, 0, 0, 0), hall_cnt=0,
         gold=0, lum=0, workers=0, hall=0, obj=0, bld=(0, 0, 0, 0, 0)):
    m = {}
    m.update(w32(0x51214, cheat))
    m.update(w16(0x50D84, train))
    m.update(w16(0x50D98, unit))
    for i, v in enumerate(men):
        m.update(w16(0x58E28 + 2 * i, v))
    m.update(w16(0x58DF6, hall_cnt))
    m.update(w32(0x50074, gold))
    m.update(w32(0x50060, lum))
    m.update(w16(0x58DD8, workers))
    m.update(w32(0x58DB0, hall))
    m.update(w16(0x50092, obj))
    for i, v in enumerate(bld):
        m.update(w16(0x58E1E + 2 * i, v))
    m.update(w32(0x5A860, 0))
    return T4Case(mem=m, label=label)


def test_end_check_objectives():
    cases = [
        _eco("cheat victory", cheat=0x100),
        _eco("cheat defeat", cheat=0x80),
        _eco("no men no hall", men=(0, 0, 0, 0)),
        _eco("men==workers no hall gold ok", men=(2, 0, 0, 0), workers=2,
             gold=0x190, lum=0x190),
        _eco("men==workers broke", men=(2, 0, 0, 0), workers=2),
        _eco("one enemy bld", unit=1, obj=0x10, bld=(0, 1, 0, 0, 0)),
        _eco("enemy men left", unit=1, obj=0x10, bld=(0, 1, 0, 0, 0),
             men=(0, 0, 1, 0)),
        _eco("wipe all", unit=1, obj=2),
        _eco("wipe fail", unit=1, obj=2, bld=(0, 0, 0, 1, 0)),
        _eco("objective zone", unit=1, obj=4),
    ]
    t4spec.run_spec(
        SRC + "end_check_objectives_reference.c", "EndCheckObjectives_", 0x2F540,
        cases, out_regs=(), watch=[(0x5A860, 4)],
        stubs=[T4Stub(0x22538, ret=0, log_regs=()),
               T4Stub(0x2F428, ret=0, log_regs=())])
    t4spec.run_spec(
        SRC + "end_check_objectives_reference.c", "EndCheckObjectives_", 0x2F540,
        [_eco("placebox active", unit=0), _eco("zone ok", unit=1, obj=0x84)],
        out_regs=(), watch=[(0x5A860, 4)],
        stubs=[T4Stub(0x22538, ret=1, log_regs=()),
               T4Stub(0x2F428, ret=1, log_regs=())])


# ---------------------------------------------------------------- EndScreenDraw
def _esd(label, seed):
    import random
    r = random.Random(seed)
    m = {}
    m[0x55326] = struct.pack("<13h", *[r.randrange(0, 200) for _ in range(13)])
    m[0x55340] = struct.pack("<13h", *[r.randrange(0, 100) for _ in range(13)])
    m[0x5A7F8] = struct.pack("<13i", *[r.randrange(-5, 99999) for _ in range(13)])
    return T4Case(mem=m, label=label)


def test_end_screen_draw():
    t4spec.run_spec(
        SRC + "end_screen_draw_reference.c", "EndScreenDraw_", 0x2F938,
        [_esd("a", 1), _esd("b", 2), _esd("c", 3)],
        out_regs=(), watch=[(0x55438, 4)],
        stubs=[T4Stub(0x31FC0, log_regs=("eax",)),
               T4Stub(0x2F878, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x2F8BC, log_regs=("eax", "edx", "ebx")),
               T4Stub(0x31F70, log_regs=("eax",))])


# ---------------------------------------------------------------- EndScreen
def _es(label, mode, race, seed):
    import random
    r = random.Random(seed)
    m = {}
    m.update(w16(0x59616, mode))
    m.update(w16(0x50088, race))
    m[0x50D8E] = struct.pack("<5H", *[r.randrange(0, 500) for _ in range(5)])
    m[0x50DA2] = struct.pack("<5H", *[r.randrange(0, 500) for _ in range(5)])
    m[0x50DC0] = struct.pack("<5I", *[r.randrange(0, 90000) for _ in range(5)])
    m[0x50DD4] = struct.pack("<5I", *[r.randrange(0, 90000) for _ in range(5)])
    m[0x50E34] = struct.pack("<4H", *[r.randrange(0, 9999) for _ in range(4)])
    m[0x58E1E] = struct.pack("<5H", *[r.randrange(0, 500) for _ in range(5)])
    m[0x58E28] = struct.pack("<4H", *[r.randrange(0, 500) for _ in range(4)])
    m.update(w16(0x552F8, 0xB8))
    m.update(w16(0x552FA, 0x6F))
    return T4Case(mem=m, label=label)


def _es_stubs(flic_ret, rewind_ret):
    # stack-local pointer args (ResourceRead dest, memcpy src, ResourceFreeBody
    # of locals, BitmapBlit src) are not logged.
    return [
        T4Stub(0x31F70, log_regs=("eax",)),
        T4Stub(0x31870, log_regs=("eax", "edx")),
        T4Stub(0x32740, log_regs=("edx",)),
        T4Stub(0x32558, ret=0x123450, log_regs=("eax",)),
        T4Stub(0x1933C, ret=flic_ret, log_regs=("eax", "edx", "ebx", "ecx"),
               stack_pop=4),
        T4Stub(0x193FC, ret=rewind_ret, log_regs=()),
        T4Stub(0x323E0, log_regs=("edx",)),
        T4Stub(0x31789, log_regs=("ebx",)),
        T4Stub(0x32410, log_regs=("eax", "edx", "ecx")),
        T4Stub(0x33150, log_regs=("eax", "edx", "ebx")),
        T4Stub(0x21D0C, log_regs=("edx", "ebx", "ecx"), stack_pop=4),
        T4Stub(0x32030, log_regs=("eax",)),
        T4Stub(0x30C50, log_regs=("edx", "ebx")),
        T4Stub(0x2F938, log_regs=()),
        T4Stub(0x24E90, log_regs=()),
        T4Stub(0x267FC, log_regs=("eax",)),
        T4Stub(0x26784, log_regs=("eax",)),
        T4Stub(0x32E80, log_regs=("eax",)),
        T4Stub(0x2FAC4, log_regs=("eax",)),
        T4Stub(0x32FB0, log_regs=("eax",)),
        T4Stub(0x267E0, log_regs=()),
        T4Stub(0x32780, log_regs=("eax",)),
        T4Stub(0x21CF0, log_regs=()),
        T4Stub(0x32940, log_regs=()),
    ]


@pytest.mark.xfail(reason="end_screen_reference.c diverges from 0x2fcfc: LayerAdd id/res args swapped and missing LayerInvalidate(0xd)/PaletteSet before LayerAdd")
def test_end_screen():
    watch = [(0x5A7F0, 8), (0x5A82C, 52), (0x5A7F8, 52),
             (0x552F8, 12), (0x55438, 4), (0x5ACF0, 4), (0x5AA78, 1),
             (0x58F23, 0x26D)]
    cases = [_es("win race0", 6, 0, 1), _es("win race1", 6, 1, 2),
             _es("lose race0", 7, 0, 3), _es("lose race1", 7, 1, 4)]
    for flic, rew in ((0, 0),):
        t4spec.run_spec(SRC + "end_screen_reference.c", "EndScreen_", 0x2FCFC,
                        cases, out_regs=(), watch=watch,
                        stubs=_es_stubs(flic, rew), log_cap=4096)
