"""mod_104b0 / mod_110a0 / mod_11530: unit combat, attack orders and
building production (0x104b0..0x119c0).

Two kinds of checks:

* T3: the files that wc1.match matches byte-for-byte under Watcom 10.0a are
  re-matched here (through wc1.mod_104b0_match, which loads the symbol
  database non-strictly so a half-written symbol file of another area does not
  break this test; the authoritative command is `python3 -m wc1.match`).
* T4: the reference C of the functions that do not match is compiled and run
  next to the original under wc1.emu (wc1.cemu.run_pair).  The collaborators
  of each function are stubbed to deterministic values so the test compares
  the function's own logic; the inputs are chosen to hit the interesting
  branches (see tests/test_cemu.py for the harness).
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, symbols

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

# Several analysts share the tree; while another area's symbol file is being
# written, wc1.symbols.load() (and therefore cemu's first external lookup)
# raises on that file.  Load the database non-strictly into cemu's cache so
# this test only depends on the entries it actually uses.  `make verify` runs
# with a consistent tree, where the result is identical.
_funcs, _datas, _ = symbols.load(strict=False)
cemu._BY_LINK = {e["link_name"]: e for t in (_funcs, _datas) for e in t.values()}

SRC = path("src", "mod_104b0")
T3_FILES = [
    "nop_callback.c", "nop_production.c", "unit_set_last_attacker.c",
    "anim_end_dispatch.c", "restart_production.c", "attack_order_human.c",
    "research_ranged.c", "research_speed.c", "train_workers.c",
    "unit_start_research.c", "unit_start_training.c",
]


# ---------------------------------------------------------------- T3 re-check

def test_t3_files_still_match():
    funcs, datas, _ = symbols.load(strict=False)
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    p = analysis.run()
    bad = []
    for name in T3_FILES:
        src = os.path.join(SRC, name)
        cc = match.file_cc(src)
        out = path("build", "mod_104b0", "match", name[:-2] + ".obj")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, None, out, cc=cc)
        for fname, status, problems in match.match_module(p, mod, by_link):
            if not status == "MATCH":
                bad.append((name, fname, problems[:2]))
    assert not bad, bad


# ---------------------------------------------------------------- T4 harness

OFF = {
    'px': 0, 'py': 2, 'facing': 8, 'tx': 0xa, 'ty': 0xc, 'flags2': 0xe,
    'flags': 0x10, 'f12': 0x12, 'hp': 0x16, 'energy': 0x1a, 'type': 0x1b,
    'owner': 0x1e, 'order': 0x1f, 'order_next': 0x20, 'order_next2': 0x21,
    'timer36': 0x36, 'timer38': 0x38, 'attacker': 0x3a, 'build_type': 0x3e,
    'b3f': 0x3f, 'b40': 0x40, 'build_time': 0x41, 'build_cost': 0x46,
    'word4a': 0x4a, 'dest_x': 0x4e, 'dest_y': 0x50, 'target': 0x52,
}
BYTE = {'facing', 'f12', 'energy', 'type', 'owner', 'order', 'order_next',
        'order_next2', 'b3f', 'b40', 'build_time', 'build_type'}
DWORD = {'attacker', 'target', 'build_cost'}


def mkunit(emu, **kw):
    a = emu.alloc(0x5c)
    fields = dict(flags2=0, flags=0, hp=10, energy=0, type=0, owner=0, order=0,
                  order_next=0x1f, order_next2=0x1f, target=0, attacker=0,
                  word4a=0, f12=0, dest_x=5, dest_y=5, timer36=0, timer38=0,
                  facing=0, tx=10, ty=10)
    fields.update(kw)
    for k, v in fields.items():
        size = 1 if k in BYTE else (4 if k in DWORD else 2)
        emu.write(a + OFF[k], int(v).to_bytes(size, 'little', signed=False))
    return a


def w16(emu, addr, v):
    emu.write(addr, struct.pack("<H", v & 0xffff))


def w32(emu, addr, v):
    emu.write(addr, struct.pack("<I", v & 0xffffffff))


def noop(_emu):
    return None


def memo(emu, addr, value, reg="edx"):
    """Stub that records a register argument in a scratch word."""
    out = emu.alloc(2)

    def stub(e):
        e.write(out, struct.pack("<H", e.reg(reg) & 0xffff))
        return value
    emu.stubs[addr] = stub
    return out


def pair(emu, cfile, name, addr, args=(), watch=(), out=("eax",), stubs=(), setup=None):
    if setup:
        setup(emu)
    for item in stubs:
        a, v = item[0], item[1]
        if len(item) > 2:
            emu.stub_pops[a] = item[2]
        if callable(v):
            emu.stubs[a] = v
        else:
            emu.stubs[a] = (lambda v: (lambda e: v))(v)
    cm = cemu.load(emu, os.path.join(SRC, cfile))
    return cemu.run_pair(emu, addr, cm, name, *args, watch=watch, out_regs=out)


def emu_new():
    from wc1.emu import Emu
    return Emu()


MFLAGS = 0x13348
RNG = 0x19478
ORDERTARGET = 0x2e100


# ---------------------------------------------------------------- combat core

def test_t4_tile_apply_damage():
    from wc1.emu import Emu
    emu = Emu()
    tile = emu.alloc(0x2000)

    def setup(e):
        w32(e, 0x58584, tile)
        w16(e, tile + (2 * 0x40 + 2) * 2, 0x1000)   # amount 2, flag bits clear
    diffs = pair(emu, "tile_apply_damage.c", "TileApplyDamage_", 0x105d0,
                 args=(2, 2, 2), watch=[(tile + (2 * 0x40 + 2) * 2, 2)],
                 out=(),
                 stubs=[(MFLAGS, 0xc), (0x2c2c4, 0)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_calc_damage():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, target=0)
    diffs = pair(emu, "unit_calc_damage.c", "UnitCalcDamage_", 0x104b0,
                 args=(u,), stubs=[(MFLAGS, 0xc), (RNG, 0)])
    assert diffs == [], diffs


def test_t4_unit_apply_damage():
    from wc1.emu import Emu
    emu = Emu()
    atk = mkunit(emu, type=0, owner=0)
    vic = mkunit(emu, type=1, owner=1, hp=5)
    diffs = pair(emu, "unit_apply_damage.c", "UnitApplyDamage_", 0x10650,
                 args=(atk, vic, 3), watch=[(vic, 0x5c), (0x50dac, 4)],
                 out=(),
                 stubs=[(0x2e14c, 0), (0x2207c, 0), (0x25198, 0), (0x2529c, 0)])
    assert diffs == [], diffs


def test_t4_unit_attack_frame():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, target=0, dest_x=4, dest_y=4)

    def setup(e):
        w32(e, 0x58584, e.alloc(0x2000))
    diffs = pair(emu, "unit_attack_frame.c", "UnitAttackFrame_", 0x106ec,
                 args=(u,), watch=[(u, 0x5c)], out=(),
                 stubs=[(0x11a10, 0), (0x11ec0, 0), (MFLAGS, 0), (RNG, 0)],
                 setup=setup)
    assert diffs == [], diffs


def test_t4_unit_approach_point():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, tx=10, ty=10)
    enemy = mkunit(emu, facing=0)
    out = emu.alloc(4)
    diffs = pair(emu, "unit_approach_point.c", "UnitApproachPoint_", 0x107a0,
                 args=(u, enemy, out), watch=[(out, 4)], out=(),
                 stubs=[(RNG, 0)])
    assert diffs == [], diffs


def test_t4_unit_consider_target():
    from wc1.emu import Emu
    emu = Emu()
    cand = mkunit(emu, type=0, owner=1, tx=12, ty=10)

    def setup(e):
        w32(e, 0x58540, 0)            # best
        w32(e, 0x58544, 0x51883)      # enemy_map: player 0's hostility row
        w32(e, 0x58548, 10 | (10 << 16))  # origin
        w16(e, 0x5854c, 0xffff)       # best score
        w16(e, 0x5854e, 1)            # flag_4e
        w16(e, 0x58550, 8)            # range
        w16(e, 0x58552, 0)            # chase
        w16(e, 0x58554, 0)            # min range
        w16(e, 0x58556, 0)            # vis mask
        w16(e, 0x58558, 999)          # best dist
    diffs = pair(emu, "unit_consider_target.c", "UnitConsiderTarget_", 0x10834,
                 args=(cand,), watch=[(0x58540, 0x1a)], out=(),
                 stubs=[(0x13270, 2)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_acquire_target():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, tx=10, ty=10)
    cand = mkunit(emu, type=0, owner=1, tx=12, ty=10)

    def setup(e):
        om = e.alloc(0x40 * 0x40 * 4)
        w32(e, 0x58580, om)
        w32(e, om + (10 * 0x40 + 12) * 4, cand)
        e.write(0x51883, bytes([0, 1, 1, 1, 0] + [1] + [0] * 19))
        e.write(0x5008c, bytes([0, 1, 2, 3, 0]))
        w16(e, 0x51de6, 0)
    diffs = pair(emu, "unit_acquire_target.c", "UnitAcquireTarget_", 0x10908,
                 args=(u, 0, 0), watch=[(u, 0x5c), (0x58540, 0x1a)], out=(),
                 stubs=[(0x2e100, 0, 4), (0x2207c, 0), (0x13270, 2)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_call_for_help():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, tx=10, ty=10)
    atk = mkunit(emu, type=0, owner=1)
    ally = mkunit(emu, type=0, owner=0, order=2, order_next=0x1f,
                  order_next2=0x1f, tx=11, ty=10)

    def setup(e):
        om = e.alloc(0x40 * 0x40 * 4)
        w32(e, 0x58580, om)
        w32(e, om + (10 * 0x40 + 11) * 4, ally)
        e.write(0x51883, bytes([0, 1, 1, 1, 0] + [1] + [0] * 19))
        w32(e, u + 0x3a, atk)
    diffs = pair(emu, "unit_call_for_help.c", "UnitCallForHelp_", 0x10b1c,
                 args=(u,), watch=[(ally, 0x5c)], out=(),
                 stubs=[(ORDERTARGET, 0, 4)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_retaliate_human_attack_target():
    from wc1.emu import Emu
    emu = Emu()
    atk = mkunit(emu, type=0, owner=1)
    u = mkunit(emu, type=0, owner=0, target=0)

    def setup(e):
        w32(e, u + 0x3a, atk)
        e.write(0x5008c, bytes([1, 2, 2, 2, 0]))
    diffs = pair(emu, "unit_retaliate.c", "UnitRetaliate_", 0x10d34,
                 args=(u, 0), watch=[(u, 0x5c)], stubs=[(ORDERTARGET, 0, 4)],
                 setup=setup)
    assert diffs == [], diffs


def test_t4_unit_idle_tick_waits():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, timer36=1)

    def setup(e):
        e.write(0x5008c, bytes([1, 2, 2, 2, 0]))
    diffs = pair(emu, "unit_idle_tick.c", "UnitIdleTick_", 0x10ee8,
                 args=(u,), watch=[(u, 0x5c)], out=(),
                 stubs=[(0x10d34, 0), (0x2ab54, 0), (0x2a8f4, 0),
                        (0x10908, 0)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_move_order_check():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, order_next2=0)

    def setup(e):
        e.write(0x5008c, bytes([2, 2, 2, 2, 0]))
    diffs = pair(emu, "unit_move_order_check.c", "UnitMoveOrderCheck_", 0x11004,
                 args=(u,), stubs=[(0x10d34, 1)], setup=setup)
    assert diffs == [], diffs


# ---------------------------------------------------------------- attack orders

def test_t4_unit_attack_strike_stops():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0xa, owner=0, energy=0)

    def setup(e):
        e.write(0x5008c, bytes([0, 1, 2, 3, 0]))
    diffs = pair(emu, "unit_attack_strike.c", "UnitAttackStrike_", 0x110a4,
                 args=(u,), watch=[(u, 0x5c)],
                 stubs=[(0x2eeac, 0)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_check_attack_crowding():
    from wc1.emu import Emu
    emu = Emu()
    t = mkunit(emu, type=0, owner=0, tx=20, ty=20)
    u = mkunit(emu, type=4, owner=0, target=t)
    ally = mkunit(emu, type=0, owner=0, tx=19, ty=19)

    def setup(e):
        om = e.alloc(0x40 * 0x40 * 4)
        w32(e, 0x58580, om)
        w32(e, om + (19 * 0x40 + 19) * 4, ally)
        e.write(0x51883, bytes([0, 1, 1, 1, 0] + [1] + [0] * 19))
        e.write(0x5008c, bytes([0, 1, 2, 3, 0]))
    diffs = pair(emu, "unit_check_attack_crowding.c", "UnitCheckAttackCrowding_",
                 0x11140, args=(u,), watch=[(u, 0x5c)],
                 stubs=[(0x13270, 10), (0x2eeac, 0)], setup=setup)
    assert diffs == [], diffs


def test_t4_unit_wander_step():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, tx=10, ty=10)
    diffs = pair(emu, "unit_wander_step.c", "UnitWanderStep_", 0x11298,
                 args=(u,), watch=[(u, 0x5c)],
                 stubs=[(0x1def0, 3), (MFLAGS, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_attack_order_at_point():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, dest_x=5, dest_y=5)
    diffs = pair(emu, "attack_order_at_point.c", "AttackOrderAtPoint_", 0x11344,
                 args=(u,), watch=[(u, 0x5c)],
                 stubs=[(0x10d34, 0), (0x222d8, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_attack_order_target():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0)
    diffs = pair(emu, "attack_order_target.c", "AttackOrderTarget_", 0x113e0,
                 args=(u,), stubs=[(0x2eefc, 1)])
    assert diffs == [], diffs


def test_t4_unit_attack_order_tick():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0)

    def setup(e):
        e.write(0x5008c, bytes([0, 1, 2, 3, 0]))
    diffs = pair(emu, "unit_attack_order_tick.c", "UnitAttackOrderTick_", 0x1143c,
                 args=(u, 0, 0), watch=[(u, 0x5c)],
                 stubs=[(0x2eefc, 1)], setup=setup)
    assert diffs == [], diffs


def test_t4_attack_order_ai():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0)
    diffs = pair(emu, "attack_order_ai.c", "AttackOrderAI_", 0x114ec,
                 args=(u,), stubs=[(0x1143c, 1)])
    assert diffs == [], diffs


# ---------------------------------------------------------------- production

def test_t4_building_auto_train():
    from wc1.emu import Emu
    emu = Emu()
    b = mkunit(emu, type=0x22, owner=0)

    def setup(e):
        w16(e, 0x50e4e, 0)
        w32(e, 0x50004, 0x1f)
        for p in range(5):
            w16(e, 0x58e14 + p * 2, 0)
            w16(e, 0x58e0a + p * 2, 0)
    rec = memo(emu, 0x115f4, 0)
    diffs = pair(emu, "building_auto_train.c", "BuildingAutoTrain_", 0x116c4,
                 args=(b,), out=(), watch=[(rec, 2)],
                 stubs=[(RNG, 0), (0x115f4, emu.stubs[0x115f4])],
                 setup=lambda e: (setup(e), None))
    assert diffs == [], diffs


def test_t4_train_family_starts_a_type():
    from wc1.emu import Emu
    for cfile, name, addr, btype, expect in (
            ("train_cavalry.c", "TrainCavalry_", 0x117f0, 0x24, 0xc),
            ("train_archers.c", "TrainArchers_", 0x11848, 0x26, 0xa),
            ("train_workers.c", "TrainWorkers_", 0x118a0, 0x28, 2)):
        emu = Emu()
        b = mkunit(emu, type=btype, owner=0)

        def setup(e):
            w16(e, 0x58dec, 4)         # cap
            w16(e, 0x58dc4, 0)         # count
            w16(e, 0x5009a, 4)         # worker cap
            w16(e, 0x58dd8, 0)         # worker count
        rec = memo(emu, 0x115f4, 0)
        diffs = pair(emu, cfile, name, addr, args=(b,), out=(),
                     watch=[(rec, 2)], stubs=[(0x115f4, emu.stubs[0x115f4])],
                     setup=setup)
        assert diffs == [], (name, diffs)
        assert struct.unpack("<H", emu.read(rec, 2))[0] == expect, name


def test_t4_research_upgrade_family():
    from wc1.emu import Emu
    for cfile, name, addr, row in (
            ("research_upgrade.c", "ResearchUpgrade_", 0x118e0, 0),
            ("research_armour.c", "ResearchArmourUpgrade_", 0x11950, 1)):
        emu = Emu()
        u = mkunit(emu, type=0x22, owner=0)

        def setup(e):
            e.write(0x50008, bytes([0, 0, 0, 0, 0]))
            e.write(0x5000d, bytes([0, 0, 0, 0, 0]))
            e.write(0x50035, bytes([0, 0, 0, 0, 0]))
        if name == "ResearchUpgrade_":
            rec = memo(emu, 0x11538, 0)
            arg = emu.alloc(1)
            emu.write(arg, b"\x00")
            diffs = pair(emu, cfile, name, addr, args=(u, 0, arg, 2), out=(),
                         watch=[(rec, 2), (u, 0x5c)],
                         stubs=[(0x11538, emu.stubs[0x11538])], setup=setup)
        else:
            rec = memo(emu, 0x118e0, 0)
            diffs = pair(emu, cfile, name, addr, args=(u,), out=(),
                         watch=[(u, 0x5c)],
                         stubs=[(0x118e0, emu.stubs[0x118e0])], setup=setup)
        assert diffs == [], (name, diffs)


def test_t4_unit_cancel_production():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, flags2=0x10)
    diffs = pair(emu, "unit_cancel_production.c", "UnitCancelProduction_",
                 0x116a8, args=(u,), watch=[(u, 0x5c)], out=())
    assert diffs == [], diffs
