"""mod_295d0: the computer opponent's unit AI (0x295d0..0x2b1b0).

Two kinds of checks:

* T3: the files that wc1.match matches byte for byte under Watcom 10.0a are
  re-matched here through wc1.mod_295d0_match (it loads the symbol database
  leniently, so a half-written symbol file of another area does not break this
  test; the authoritative command is `python3 -m wc1.match`).
* T4: every other function's reference C is compiled and run next to the
  original under wc1.emu (wc1.cemu.run_pair).  The collaborators of each
  function are either the real original functions (their symbol-database
  entries point at the same address the original calls) or stubs with
  deterministic values; the inputs hit the branches the function is about.
  See tests/test_cemu.py for the harness.
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, symbols
from wc1.mod_295d0_match import load_lenient

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

# The tree is shared with other analysts; seed cemu's symbol cache from the
# lenient loader so a file that is mid-write elsewhere cannot fail this test.
_funcs, _datas, _ = load_lenient()
cemu._BY_LINK = {e["link_name"]: e for t in (_funcs, _datas) for e in t.values()}

SRC = path("src", "mod_295d0")
T3_FILES = ["ai_reset.c", "ai_tick.c", "ai_remove_unit.c"]

# Callees that belong to other areas and have no symbol-database entry yet.
# They are passed to cemu.load as `extra` so the compiled C resolves them to
# the addresses the original calls; naming them is a change request (their
# areas own the entries).
EXTRA = {
    "fn_21094_": 0x21094,
    "fn_210dc_": 0x210dc,
    "fn_2111c_": 0x2111c,
    "fn_21168_": 0x21168,
    "fn_13990_": 0x13990,
    "fn_2bb7c_": 0x2bb7c,
    "AiIdleUnitTick_": 0x2ab54,
}

# collaborators to stub
ORDERTARGET = 0x2e100
RNG = 0x19478
DIST = 0x13270
PAY = 0x20d74
PLACE = 0x13990
CREATE = 0x2e6f4  # UnitCreate (named in mod_20c30.toml)
WALKABLE = 0x2bb7c


# ---------------------------------------------------------------- T3 re-check

def test_t3_files_still_match():
    p = analysis.run()
    bad = []
    for name in T3_FILES:
        src = os.path.join(SRC, name)
        cc = match.file_cc(src)
        out = path("build", "mod_295d0", "match", name[:-2] + ".obj")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, None, out, cc=cc)
        for fname, status, problems in match.match_module(p, mod, by_link()):
            if status != "MATCH":
                bad.append((name, fname, problems[:2]))
    assert not bad, bad


def by_link():
    return {e["link_name"]: e for t in (_funcs, _datas) for e in t.values()}


# ---------------------------------------------------------------- the world

OFF = {
    "px": 0, "py": 2, "anim_timer": 6, "frame": 7, "facing": 8, "tx": 0xa,
    "ty": 0xc, "flags2": 0xe, "flags": 0x10, "order_flags": 0x12,
    "work_site": 0x14, "hp": 0x16, "energy": 0x1a, "type": 0x1b, "type2": 0x1c,
    "owner": 0x1e, "order": 0x1f, "order_next": 0x20, "order_next2": 0x21,
    "timer36": 0x36, "timer38": 0x38, "attacker": 0x3a, "work_x": 0x3e,
    "work_y": 0x40, "word46": 0x46, "b48": 0x48, "b49": 0x49, "word4a": 0x4a,
    "path_idx": 0x4c, "dest_x": 0x4e, "dest_y": 0x50, "target": 0x52,
    "gold": 0x54, "sprite": 0x58,
}
BYTE = {"anim_timer", "frame", "facing", "energy", "type", "type2", "owner",
        "order", "order_next", "order_next2", "b48", "b49"}
DWORD = {"attacker", "target", "gold", "sprite"}


def w16(emu, addr, v):
    emu.write(addr, struct.pack("<H", v & 0xffff))


def w32(emu, addr, v):
    emu.write(addr, struct.pack("<I", v & 0xffffffff))


def r16(emu, addr):
    return struct.unpack("<H", emu.read(addr, 2))[0]


def mkunit(emu, **kw):
    a = emu.alloc(0x5c)
    fields = dict(flags=0, flags2=0, hp=10, energy=0, type=0, owner=0, order=0,
                  order_next=0x1f, order_next2=0x1f, order_flags=0, work_site=0,
                  work_x=0, work_y=0, tx=10, ty=10, px=160, py=160,
                  timer36=0, timer38=0, attacker=0, target=0, word4a=0,
                  word46=0, b49=0, gold=0, sprite=0, type2=0, facing=0,
                  anim_timer=0, frame=0, path_idx=0, dest_x=0, dest_y=0, b48=0)
    fields.update(kw)
    for k, v in fields.items():
        size = 1 if k in BYTE else (4 if k in DWORD else 2)
        emu.write(a + OFF[k], int(v).to_bytes(size, "little", signed=False))
    return a


def world(emu, units):
    """Allocate the 200-unit array and publish it at 0x59640."""
    base = emu.alloc(0x5c * 200)
    w32(emu, 0x59640, base)
    for i, u in enumerate(units):
        emu.write(base + i * 0x5c, emu.read(u, 0x5c))
    return base


def objmap(emu, cells):
    """Allocate the 64x64 object map (a dword per tile) and place units."""
    m = emu.alloc(0x4000)
    w32(emu, 0x58580, m)
    for (x, y), u in cells.items():
        w32(emu, m + (y * 64 + x) * 4, u)
    return m


def sites(emu, words):
    t = emu.alloc(2 * len(words))
    for i, v in enumerate(words):
        w16(emu, t + 2 * i, v)
    w32(emu, 0x599c0, t)
    return t


def pair(emu, cfile, name, addr, args=(), watch=(), out=("eax",), stubs=(),
         setup=None, stack_args=()):
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
    cm = cemu.load(emu, os.path.join(SRC, cfile), extra=EXTRA)
    return cemu.run_pair(emu, addr, cm, name, *args, watch=watch, out_regs=out,
                         stack_args=stack_args)


def emu_new():
    from wc1.emu import Emu
    e = Emu()
    # AiBestTarget 0x29fec reads best->type through a null `best` on the first
    # candidate (address 0x1b), which is mapped in real mode but not here.
    try:
        e.uc.mem_map(0, 0x1000)
    except Exception:
        pass
    return e


def const(v, pops=0):
    def stub(e):
        if pops:
            e.esp += pops      # watcall callee pops stack arguments
        return v
    return stub


# ---------------------------------------------------------------- T4 tests

def test_t4_ai_choose_attack_point():
    emu = emu_new()
    u0 = mkunit(emu, type=0, owner=0, tx=1, ty=1)
    u1 = mkunit(emu, type=0, owner=0, tx=2, ty=2)
    b = mkunit(emu, type=0x22, owner=0, tx=2, ty=2)
    odd = mkunit(emu, type=0, owner=1, tx=60, ty=60)
    world(emu, [u0, u1, b, odd])
    diffs = pair(emu, "ai_choose_attack_point_reference.c", "AiChooseAttackPoint_",
                 0x29644, watch=[(0x50de8, 8)], out=())
    assert diffs == [], diffs


def test_t4_ai_work_site_advance():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, work_site=4)
    world(emu, [u])
    # records: word 4 = (kind,x,y) at 4..6, the next record at 7, the one after at 0xa
    sites(emu, [0, 0, 0, 0, 1, 11, 12, 2, 21, 22, 0xffff])
    diffs = pair(emu, "ai_work_site_advance_reference.c", "AiWorkSiteAdvance_",
                 0x29778, args=(u,), watch=[(u, 0x5c)], out=(),
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_work_site_advance_end():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, work_site=4, order_flags=0x10)
    world(emu, [u])
    sites(emu, [0, 0, 0, 0, 1, 11, 12, 0xffff, 0, 0, 0])
    diffs = pair(emu, "ai_work_site_advance_reference.c", "AiWorkSiteAdvance_",
                 0x29778, args=(u,), watch=[(u, 0x5c)], out=(),
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_work_site_step():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, work_site=0x8004, work_x=10, work_y=10,
               tx=10, ty=10)
    world(emu, [u])
    sites(emu, [0, 0, 0, 0, 1, 11, 12, 0xffff])
    w16(emu, 0x500a6, 1)                    # the site takes one worker
    diffs = pair(emu, "ai_work_site_step_reference.c", "AiWorkSiteStep_",
                 0x298a0, args=(u,), watch=[(u, 0x5c), (0x500a6, 2),
                                           (0x50e54, 0xa)], out=(),
                 stubs=[(DIST, 2), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_pick_work_site():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1)
    world(emu, [u])
    sites(emu, [30, 5, 70, 8, 0xffff])
    # table: pairs (weight, site) then the records at word 5 and 8
    diffs = pair(emu, "ai_pick_work_site_reference.c", "AiPickWorkSite_",
                 0x29c58, args=(u,), watch=[(u, 0x5c)], out=(),
                 stubs=[(RNG, 60), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_wake_unit():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=1, work_x=1, work_y=2)
    sleeper = mkunit(emu, type=0, owner=1, flags=0x200, tx=20, ty=21,
                     word46=0, work_x=30, work_y=31)
    base = world(emu, [u, sleeper])
    diffs = pair(emu, "ai_wake_unit_reference.c", "AiWakeUnit_",
                 0x29a9c, args=(u,), watch=[(u, 0x5c), (sleeper, 0x5c),
                                           (0x50e5e, 0xa), (base, 0x5c * 2)],
                 stubs=[(RNG, 0)])
    assert diffs == [], diffs


def test_t4_ai_guard_start_area():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=1, tx=20, ty=20, px=320, py=320)
    world(emu, [u])
    w32(emu, 0x58db0, 0)                    # no town hall
    w32(emu, 0x50e68, 20 | (20 << 16))      # home point (20,20)
    diffs = pair(emu, "ai_guard_start_area_reference.c", "AiGuardStartArea_",
                 0x29f40, args=(u,), watch=[(u, 0x5c), (0x50e68, 4)],
                 stubs=[(RNG, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_wander_step():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=1)
    pt = emu.alloc(4)
    w16(emu, pt, 10)
    w16(emu, pt + 2, 10)
    world(emu, [u])
    diffs = pair(emu, "ai_wander_step_reference.c", "AiWanderStep_",
                 0x29bac, args=(u, pt), watch=[(pt, 4)], out=(),
                 stubs=[(RNG, 3), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_best_target():
    emu = emu_new()
    a = mkunit(emu, type=0, owner=1, tx=12, ty=10)
    b = mkunit(emu, type=0x22, owner=1, tx=11, ty=10)
    world(emu, [a, b])
    pt = emu.alloc(4)
    w16(emu, pt, 10)
    w16(emu, pt + 2, 10)
    w32(emu, 0x51883, 0x01010101)           # every owner is an enemy
    diffs = pair(emu, "ai_best_target_reference.c", "AiBestTarget_",
                 0x29fec, args=(pt, 6, 2, 0x51883),
                 stubs=[(DIST, 2)])
    assert diffs == [], diffs


def test_t4_ai_acquire_nearby_target():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=0, tx=10, ty=10, order_flags=8)
    e = mkunit(emu, type=0, owner=1, tx=12, ty=10)
    world(emu, [u, e])
    w32(emu, 0x51883, 0x00010100)
    diffs = pair(emu, "ai_acquire_nearby_target_reference.c",
                 "AiAcquireNearbyTarget_", 0x2a0e0, args=(u,),
                 stubs=[(DIST, 1)])
    assert diffs == [], diffs


def test_t4_ai_defend_town_hall():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=0, tx=10, ty=10)
    hall = mkunit(emu, type=0x28, owner=0, hp=10)
    e = mkunit(emu, type=0, owner=1, tx=11, ty=11)
    world(emu, [u, hall, e])
    w32(emu, 0x58db0, hall)
    w32(emu, 0x50e68, 10 | (10 << 16))
    w32(emu, 0x51883, 0x00010100)
    w16(emu, 0x51978 + 2 * 0, 60)           # type 0 max hp
    diffs = pair(emu, "ai_defend_town_hall_reference.c", "AiDefendTownHall_",
                 0x2a168, args=(u,), stubs=[(DIST, 1)])
    assert diffs == [], diffs


def test_t4_ai_cast_heal():
    emu = emu_new()
    u = mkunit(emu, type=0x0c, owner=0, tx=10, ty=10)
    hurt = mkunit(emu, type=0, owner=0, tx=11, ty=10, hp=5)
    world(emu, [u, hurt])
    objmap(emu, {(11, 10): hurt})
    w32(emu, 0x51883, 0)
    w16(emu, 0x51978, 60)
    diffs = pair(emu, "ai_cast_heal_reference.c", "AiCastHeal_", 0x2a270,
                 args=(u,), watch=[(0x5a7c0, 2)], stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, 0x5a7c0) == 0x11


def test_t4_ai_cast_raise_dead():
    emu = emu_new()
    u = mkunit(emu, type=0x0d, owner=0, tx=10, ty=10)
    corpse = mkunit(emu, type=0x33, owner=4, tx=12, ty=11, flags=0x2)
    world(emu, [u, corpse])
    diffs = pair(emu, "ai_cast_raise_dead_reference.c", "AiCastRaiseDead_",
                 0x2a3cc, args=(u,), watch=[(0x5a7c0, 2)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, 0x5a7c0) == 0x14


def test_t4_ai_cast_invisibility():
    emu = emu_new()
    u = mkunit(emu, type=0x0c, owner=0, tx=10, ty=10)
    k = mkunit(emu, type=6, owner=0, tx=11, ty=10, order=3, hp=60)
    world(emu, [u, k])
    objmap(emu, {(11, 10): k})
    w16(emu, 0x50dea, 40)                    # the AI attack point
    w16(emu, 0x50dec, 40)
    w32(emu, 0x51883, 0)
    w16(emu, 0x51978 + 2 * 6, 90)
    diffs = pair(emu, "ai_cast_invisibility_reference.c", "AiCastInvisibility_",
                 0x2a48c, args=(u,), watch=[(0x5a7c0, 2), (k, 0x5c)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, 0x5a7c0) == 0x13


def test_t4_ai_cast_unholy_armor():
    emu = emu_new()
    u = mkunit(emu, type=0x0d, owner=0, tx=10, ty=10)
    v = mkunit(emu, type=0, owner=0, tx=11, ty=10, hp=5, attacker=0x1234)
    world(emu, [u, v])
    objmap(emu, {(11, 10): v})
    w32(emu, 0x51883, 0)
    w16(emu, 0x51978, 60)
    diffs = pair(emu, "ai_cast_unholy_armor_reference.c", "AiCastUnholyArmor_",
                 0x2a624, args=(u,), watch=[(0x5a7c0, 2)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, 0x5a7c0) == 0x15


def test_t4_ai_cast_point_spell():
    emu = emu_new()
    u = mkunit(emu, type=0x0a, owner=0, tx=10, ty=10)
    e = mkunit(emu, type=0, owner=1, tx=40, ty=40)
    world(emu, [u, e])
    objmap(emu, {(40, 40): e})
    w16(emu, 0x50dea, 40)
    w16(emu, 0x50dec, 40)
    w32(emu, 0x51883, 0x00010100)
    w16(emu, 0x5a7c0, 0x1a)
    diffs = pair(emu, "ai_cast_point_spell_reference.c", "AiCastPointSpell_",
                 0x2a774, args=(u,), stubs=[(DIST, 1), (RNG, 0),
                                           (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_spellcaster_tick_cleric():
    emu = emu_new()
    u = mkunit(emu, type=0x0c, owner=1, tx=10, ty=10, energy=200)
    v = mkunit(emu, type=0, owner=1, tx=11, ty=10, hp=5)
    world(emu, [u, v])
    objmap(emu, {(11, 10): v})
    w32(emu, 0x51883, 0)
    w16(emu, 0x51978, 60)
    w16(emu, 0x50030 + 1, 1)                 # row 5 (invisibility) available
    w16(emu, 0x50026 + 1, 1)                 # row 3 (healing) available
    diffs = pair(emu, "ai_spellcaster_tick_reference.c", "AiSpellcasterTick_",
                 0x2a8f4, args=(u,), watch=[(0x5a7c0, 2)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, 0x5a7c0) == 0x11


def test_t4_ai_spellcaster_tick_summon():
    emu = emu_new()
    u = mkunit(emu, type=0x0a, owner=1, tx=10, ty=10, energy=0xff)
    world(emu, [u])
    w16(emu, 0x5001c + 1, 1)                 # row 2 summon available
    diffs = pair(emu, "ai_spellcaster_tick_reference.c", "AiSpellcasterTick_",
                 0x2a8f4, args=(u,), watch=[(u, 0x5c)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_idle_unit_tick():
    emu = emu_new()
    u = mkunit(emu, type=0, owner=1, tx=10, ty=10, order_flags=4)
    world(emu, [u])
    w16(emu, 0x50dea, 30)
    w16(emu, 0x50dec, 30)
    w32(emu, 0x51883, 0)
    diffs = pair(emu, "ai_idle_unit_tick_reference.c", "AiIdleUnitTick_",
                 0x2ab54, args=(u,), watch=[(u, 0x5c)],
                 stubs=[(ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_mine_gold():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, tx=10, ty=10)
    near = mkunit(emu, type=0x32, owner=4, tx=12, ty=12, gold=500)
    far = mkunit(emu, type=0x32, owner=4, tx=50, ty=50, gold=500)
    world(emu, [u, near, far])
    w32(emu, 0x50e68, 10 | (10 << 16))
    diffs = pair(emu, "ai_mine_gold_reference.c", "AiMineGold_", 0x2ac38,
                 args=(u,), watch=[(u, 0x5c), (0x50dee, 0xa)],
                 stubs=[(DIST, 1), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs
    assert r16(emu, u + OFF["order_flags"]) & 1


def test_t4_ai_choose_building():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1)
    b = mkunit(emu, type=0x28, owner=1, flags=0x200, word4a=0, hp=500)
    world(emu, [u, b])
    w32(emu, 0x50074, 1000)
    w32(emu, 0x50060, 1000)
    # building_priority_down is addressed 0x20 before its first entry
    w16(emu, 0x55120 + 0x28, 0)
    emu.write(0x55100 + 0x28, b"\x78")
    diffs = pair(emu, "ai_choose_building_reference.c", "AiChooseBuilding_",
                 0x2ad10, args=(u,))
    assert diffs == [], diffs


def test_t4_ai_build_or_repair():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1)
    b = mkunit(emu, type=0x22, owner=1, flags=0x200, hp=500)
    world(emu, [u, b])
    diffs = pair(emu, "ai_build_or_repair_reference.c", "AiBuildOrRepair_",
                 0x2ae24, args=(u, b), watch=[(u, 0x5c), (0x50df8, 0xa)],
                 stubs=[(PAY, 0), (PLACE, 1), (CREATE, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_scout_step():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1)
    world(emu, [u])
    w16(emu, 0x50e0c, 0)                     # home point corner
    w16(emu, 0x50e0e, 0)
    w16(emu, 0x50e20, 5)
    w16(emu, 0x50e22, 5)
    diffs = pair(emu, "ai_scout_step_reference.c", "AiScoutStep_", 0x2aefc,
                 args=(u,), watch=[(0x50e0c, 0x18)],
                 stubs=[(WALKABLE, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_worker_tick():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, order_flags=1)
    world(emu, [u])
    w16(emu, 0x58dd8, 3)                     # three workers
    w32(emu, 0x50e0c, 0xffffffff)            # no sweep point
    diffs = pair(emu, "ai_worker_tick_reference.c", "AiWorkerTick_", 0x2b064,
                 args=(u,), watch=[(u, 0x5c), (0x50dee, 0xa), (0x50df8, 0xa)],
                 stubs=[(DIST, 1), (WALKABLE, 0), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_ai_reset_work_sites():
    emu = emu_new()
    a = mkunit(emu, type=2, owner=1, work_site=0x4005, order_flags=0x10)
    b = mkunit(emu, type=0x22, owner=1, work_site=0x4005)
    hero = mkunit(emu, type=0x10, owner=1, work_site=0x4005)
    admin = mkunit(emu, type=0x0f, owner=0, work_site=0x4005)
    units = [a, b, hero, admin]
    base = world(emu, units)
    sites(emu, [0, 0, 0, 0, 0, 9, 1])
    w16(emu, 0x50e54 + 2 * 1, 2)             # owner 1 has two units at sites
    w16(emu, 0x50e54 + 2 * 0, 1)
    diffs = pair(emu, "ai_reset_work_sites_reference.c", "AiResetWorkSites_",
                 0x29954, watch=[(base, 0x5c * 4), (0x50e54, 0xa),
                                (0x599c0 + 0, 0)], out=(),
                 setup=lambda e: sites(e, [0, 0, 0, 0, 0, 9, 1]))
    # the site word is reached through the pointer, so watch it indirectly
    assert diffs == [], diffs


def test_t4_ai_work_site_release():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, work_site=0x4005, work_x=10, work_y=10)
    other = mkunit(emu, type=2, owner=1, work_site=0x4006)
    base = world(emu, [u, other])
    sites(emu, [0, 0, 0, 0, 0, 9, 1, 0xffff])
    diffs = pair(emu, "ai_work_site_release_reference.c", "AiWorkSiteRelease_",
                 0x29818, args=(5,), watch=[(base, 0x5c * 2), (0x500a6, 0x20)],
                 out=(),
                 stubs=[(DIST, 1), (ORDERTARGET, 0, 4)])
    assert diffs == [], diffs


def test_t4_clip_box():
    emu = emu_new()
    x = emu.alloc(4)
    y = emu.alloc(4)
    w = emu.alloc(4)
    h = emu.alloc(4)
    w32(emu, x, 1)                            # a corner: clipped at 0
    w32(emu, y, 40)
    diffs = pair(emu, "clip_box_reference.c", "ClipBox_", 0x2a1f4,
                 args=(x, y, w, h), watch=[(x, 16)], out=(),
                 stack_args=(0x15,))
    assert diffs == [], diffs


def test_t4_ai_init_unit_order_worker():
    emu = emu_new()
    u = mkunit(emu, type=2, owner=1, flags=0x400)
    world(emu, [u])
    emu.write(0x5008c, bytes([0, 1, 2, 2, 4]))
    diffs = pair(emu, "ai_init_unit_order_reference.c", "AiInitUnitOrder_",
                 0x29cf8, args=(u,), watch=[(u, 0x5c)], out=())
    assert diffs == [], diffs


def test_t4_ai_init_unit_order_town_hall():
    emu = emu_new()
    u = mkunit(emu, type=0x28, owner=1, tx=20, ty=21)
    world(emu, [u])
    emu.write(0x5008c, bytes([0, 1, 2, 2, 4]))
    w32(emu, 0x50e68, 20 | (21 << 16))
    w16(emu, 0x50dea, 0xffff)                # attack point unset
    diffs = pair(emu, "ai_init_unit_order_reference.c", "AiInitUnitOrder_",
                 0x29cf8, args=(u,), watch=[(u, 0x5c), (0x50de8, 4),
                                           (0x50e0c, 0x18),
                                           (0x50e68, 4)], out=())
    assert diffs == [], diffs


def test_t4_ai_init_unit_order_summoned():
    emu = emu_new()
    u = mkunit(emu, type=0x14, owner=1)
    world(emu, [u])
    emu.write(0x5008c, bytes([0, 1, 2, 2, 4]))
    w16(emu, 0x5a7c2, 1)
    diffs = pair(emu, "ai_init_unit_order_reference.c", "AiInitUnitOrder_",
                 0x29cf8, args=(u,), watch=[(u, 0x5c)], out=())
    assert diffs == [], diffs
