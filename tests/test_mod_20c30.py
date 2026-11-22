"""mod_20c30: the build/placement box (PLACEBOX.C 0x21df0..0x22800), the
mod_21cf0 layer helpers (0x21cf0..0x21de4) and the PACKET.C senders at the
front of the range (0x21c20..0x21ce8).

Two kinds of checks:

* T3: every file that `python3 -m wc1.match` matches byte-for-byte under
  Watcom 10.0a is re-matched here (`wc1.match.match_module` with a non-strict
  symbol load, so a half-written file of another area cannot break this test).
* T4: the reference C of the functions that do not match is compiled and run
  next to the original under `wc1.emu` (`wc1.cemu.run_pair`); the callees that
  would touch the map, the network or the screen are stubbed so each
  function's own logic is compared.  The inputs cover the interesting branches
  (docs/subsystems/mod_20c30.md).
"""
import os
import struct

import pytest

from wc1 import analysis, cemu, match, path, symbols, t4spec

pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.environ.get("WATCOM")),
    reason="needs original/ and $WATCOM (nix develop)")

# Several analysts share the tree; load the database non-strictly.
_funcs, _datas, _ = symbols.load(strict=False)
cemu._BY_LINK = {e["link_name"]: e for t in (_funcs, _datas) for e in t.values()}

SRC = path("src", "mod_20c30")
# Matched files.  0x21c20/0x21cf0/0x2207c/0x222d8 are named by other areas'
# symbol files (status.toml, playflic.toml, mod_104b0.toml), so these files are
# the T3 evidence without a `src =` entry in this area's file.
T3_FILES = [
    "net_send_control_packet.c",
    "net_send_cheat_flags.c",
    "net_send_chat_text.c",
    "resource_free_body.c",
    "layer_add.c",
    "unit_is_passable.c",
    "unit_clear_targets.c",
    "order_arg_in_range.c",
    "place_box_init.c",
    "place_box_active.c",
    "place_box_shutdown.c",
    "order_update_move.c",
    "unit_order_target_finish.c",
]
T4_FILES = [
    "net_send_sync_message_reference.c",
    "worker_return_to_mine_reference.c",
    "tile_occupied_by_unit_reference.c",
    "move_order_tick_reference.c",
    "order_clamp_dest_reference.c",
    "order_target_in_range.c",
    "path_set_reachable_dest_reference.c",
    "place_box_check_reference.c",
    "place_box_update_reference.c",
    "place_box_start_reference.c",
]

MAP_FLAGS = 0x5857c        # pointer to the 64x64 tile-flag array
OBJECT_MAP = 0x58580       # pointer to the 64x64 unit-pointer array

OFF = {
    'tx': 0xa, 'ty': 0xc, 'flags2': 0xe, 'flags': 0x10, 'hp': 0x16,
    'energy': 0x1a, 'type': 0x1b, 'owner': 0x1e, 'order': 0x1f,
    'order_next': 0x20, 'order_next2': 0x21, 'timer36': 0x36,
    'attacker': 0x3a, 'dest_x': 0x4e, 'dest_y': 0x50, 'target': 0x52,
}
BYTE = {'energy', 'type', 'owner', 'order', 'order_next', 'order_next2'}
DWORD = {'attacker', 'target'}


def w16(emu, a, v):
    emu.write(a, struct.pack("<H", v & 0xffff))


def w32(emu, a, v):
    emu.write(a, struct.pack("<I", v & 0xffffffff))


def mkunit(emu, **kw):
    a = emu.alloc(0x5c)
    fields = dict(tx=10, ty=10, flags2=0, flags=0, hp=10, energy=0, type=0,
                  owner=0, order=0, order_next=0x1f, order_next2=0x1f,
                  timer36=0, attacker=0, dest_x=5, dest_y=5, target=0)
    fields.update(kw)
    for k, v in fields.items():
        size = 1 if k in BYTE else (4 if k in DWORD else 2)
        emu.write(a + OFF[k], int(v).to_bytes(size, 'little', signed=False))
    return a


def setup_map(emu):
    """map_flags and object_map are pointers (0x5857c/0x58580); give both a
    fresh zeroed array."""
    flags = emu.alloc(0x2000)
    objs = emu.alloc(0x4000)
    w32(emu, MAP_FLAGS, flags)
    w32(emu, OBJECT_MAP, objs)
    return flags, objs


def arg(e, reg):
    return e.reg(reg) & 0xffff


def stub(fn=None):
    """A stub for `emu.stubs[addr]`: called as stub(emu)."""
    return fn if fn is not None else (lambda e: 0)


def pair(emu, cfile, name, addr, args=(), watch=(), out=("eax",), stubs=()):
    for item in stubs:
        a, v = item[0], item[1]
        if len(item) > 2:
            emu.stub_pops[a] = item[2]
        emu.stubs[a] = v
    cm = cemu.load(emu, os.path.join(SRC, cfile))
    return cemu.run_pair(emu, addr, cm, name, *args, watch=watch, out_regs=out)


# ---------------------------------------------------------------- T3 re-check

def test_t3_files_still_match():
    p = analysis.run()
    bad = []
    for name in T3_FILES:
        src = os.path.join(SRC, name)
        out = os.path.join(path("build", "mod_20c30", "match", name[:-2] + ".obj"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, None, out)
        for fname, status, problems in match.match_module(p, mod, cemu._BY_LINK):
            if status != "MATCH":
                bad.append((name, fname, problems[:2]))
    assert not bad, bad


def test_reference_files_are_not_silently_promoted():
    """The T4 files must stay honest: none of them matches (yet)."""
    p = analysis.run()
    for name in T4_FILES:
        src = os.path.join(SRC, name)
        mod = match.compile_c(src, None,
                              os.path.join(path("build", "mod_20c30", "t4.obj")), cc=match.file_cc(src))
        results = match.match_module(p, mod, cemu._BY_LINK)
        t4spec.assert_ref_state(src, [status for _, status, _ in results], name)


# ---------------------------------------------------------------- T4 difftests

def test_t4_net_send_sync_message():
    emu_new = __import__("wc1.emu", fromlist=["Emu"]).Emu
    emu = emu_new()
    msg = emu.alloc(0x12)
    emu.write(msg, bytes(range(0x12)))
    rec = emu.alloc(0x20)

    def send(e):
        e.write(rec, struct.pack("<H", arg(e, "eax")))
        e.write(rec + 2, e.read(e.reg("edx") & 0xffffffff, 0x16))
        return None

    diffs = pair(emu, "net_send_sync_message_reference.c", "NetSendSyncMessage_",
                 0x21cb8, args=(msg,), watch=[(rec, 0x18)], out=(),
                 stubs=[(0x214d4, send)])
    assert diffs == [], diffs


def test_t4_worker_return_to_mine():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=2, order_next2=0xa, tx=20, ty=21)
    o = emu.alloc(0x40)

    def mine(e):
        e.write(e.reg("eax") & 0xffffffff, struct.pack("<hh", 30, 31))
        return 1

    def order(e):
        e.write(o, struct.pack("<hhI", arg(e, "edx"), arg(e, "ebx"),
                               e.reg("ecx")))
        return None

    def adv(e):
        w16(emu, o + 0x10, arg(e, "edx"))
        return 1

    diffs = pair(emu, "worker_return_to_mine_reference.c", "WorkerReturnToMine_",
                 0x21df0, args=(u,), watch=[(u, 0x5c), (o, 0x14)],
                 stubs=[(0x2bbe4, mine), (0x2e100, order, 4), (0x2edac, adv)])
    assert diffs == [], diffs


def test_t4_worker_return_to_mine_rejects():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=4, order_next2=0xa)   # not a worker
    diffs = pair(emu, "worker_return_to_mine_reference.c", "WorkerReturnToMine_",
                 0x21df0, args=(u,), watch=[(u, 0x5c)])
    assert diffs == [], diffs


def test_t4_tile_occupied_by_unit():
    from wc1.emu import Emu
    emu = Emu()
    flags, objs = setup_map(emu)
    u = mkunit(emu, tx=10, ty=10, owner=0)
    obj = mkunit(emu, tx=10, ty=10, owner=0, order=3)
    cell = 10 * 0x40 + 10
    w16(emu, flags + cell * 2, 0x100)
    w32(emu, objs + cell * 4, obj)
    pt = emu.alloc(4)
    emu.write(pt, struct.pack("<hh", 10, 10))
    diffs = pair(emu, "tile_occupied_by_unit_reference.c", "TileOccupiedByUnit_",
                 0x21ec0, args=(u, pt), stubs=[(0x2c4e0, stub())])
    assert diffs == [], diffs


def test_t4_tile_occupied_by_unit_flags():
    from wc1.emu import Emu
    emu = Emu()
    flags, objs = setup_map(emu)
    u = mkunit(emu, owner=0)
    obj = mkunit(emu, owner=1, flags=0x100)        # a non-map unit
    cell = 3 * 0x40 + 4
    w16(emu, flags + cell * 2, 0x100)
    w32(emu, objs + cell * 4, obj)
    pt = emu.alloc(4)
    emu.write(pt, struct.pack("<hh", 4, 3))
    diffs = pair(emu, "tile_occupied_by_unit_reference.c", "TileOccupiedByUnit_",
                 0x21ec0, args=(u, pt), stubs=[(0x2c4e0, stub())])
    assert diffs == [], diffs


def test_t4_move_order_tick():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, owner=0, flags2=0x1000, dest_x=12, dest_y=12)
    dest = emu.alloc(4)
    emu.write(dest, struct.pack("<hh", 12, 12))
    seen = emu.alloc(0x20)

    def snd(e):
        w16(emu, seen, arg(e, "edx"))
        return None

    def order(e):
        emu.write(seen + 4, struct.pack("<hh", arg(e, "edx"), arg(e, "ebx")))
        return None

    diffs = pair(emu, "move_order_tick_reference.c", "MoveOrderTick_", 0x21f90,
                 args=(u, dest), out=(), watch=[(u, 0x5c), (seen, 8)],
                 stubs=[(0x26360, snd), (0x13348, stub(lambda e: 1)),
                        (0x2e100, order, 4), (0x2cebc, stub()),
                        (0x2eeac, stub()), (0x21ec0, stub()),
                        (0x21df0, stub()), (0x20f44, stub())])
    assert diffs == [], diffs


def test_t4_order_clamp_dest():
    from wc1.emu import Emu
    for kind in (0x20, 0x2a, 0x34, 0):
        emu = Emu()
        tgt = mkunit(emu, type=kind, tx=20, ty=20)
        u = mkunit(emu, tx=20, ty=20, target=tgt)
        diffs = pair(emu, "order_clamp_dest_reference.c", "OrderClampDest_",
                     0x220e8, args=(u,), out=(), watch=[(u, 0x5c)])
        assert diffs == [], (hex(kind), diffs)


def test_t4_order_target_in_range():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, type=0, dest_x=10, dest_y=10, tx=10, ty=10, order=3)
    diffs = pair(emu, "order_target_in_range.c", "fn_2220c_", 0x2220c,
                 args=(u, 3), watch=[(u, 0x5c)],
                 stubs=[(0x13348, stub()), (0x2cebc, stub())])
    assert diffs == [], diffs


def test_t4_path_set_reachable_dest():
    from wc1.emu import Emu
    emu = Emu()
    u = mkunit(emu, tx=10, ty=10, dest_x=12, dest_y=12, target=0)

    def trace(e):
        return None

    def nxt(e):
        e.write(e.reg("edx") & 0xffffffff, struct.pack("<hh", 1, 0))
        e.write(e.reg("ebx") & 0xffffffff, struct.pack("<hh", 1, 0))
        return None

    diffs = pair(emu, "path_set_reachable_dest_reference.c", "PathSetReachableDest_",
                 0x223bc, args=(u,), out=(), watch=[(u, 0x5c)],
                 stubs=[(0x1df0c, trace), (0x1df94, nxt),
                        (0x13348, stub(lambda e: 1))])
    assert diffs == [], diffs


def test_t4_place_box_check():
    from wc1.emu import Emu
    emu = Emu()
    flags, objs = setup_map(emu)
    worker = mkunit(emu, type=2, tx=5, ty=6)
    diffs = pair(emu, "place_box_check_reference.c", "PlaceBoxCheck_", 0x2256c,
                 args=(6 | (7 << 16), 0x34), watch=[(flags, 0x2000)],
                 stubs=[(0x25cc4, stub(lambda e: worker)),
                        (0x13360, stub(lambda e: 0)),
                        (0x1346c, stub(lambda e: 3)),
                        (0x1357c, stub(lambda e: 2))])
    assert diffs == [], diffs


def test_t4_place_box_update():
    from wc1.emu import Emu
    emu = Emu()
    setup_map(emu)
    w16(emu, 0x59428, 0x48 + 3 * 16 + 5)     # ui_mouse_x
    w16(emu, 0x5942a, 0x0c + 4 * 16 + 1)     # ui_mouse_y
    w16(emu, 0x500d0, 0)                     # map_scroll_x
    w16(emu, 0x500d2, 0)
    emu.write(0x59bd2, bytes([1, 0]))        # place_active
    emu.write(0x59bd0, bytes([0x20, 0]))     # place_type (a building)
    w16(emu, 0x59bd4, 0xffff)                # place_valid: forces the redraw
    diffs = pair(emu, "place_box_update_reference.c", "PlaceBoxUpdate_", 0x2261c,
                 out=(), watch=[(0x5ac0a, 18), (0x52b24, 8), (0x5ad30, 1), (0x59bd4, 2)],
                 stubs=[(0x2256c, stub(lambda e: 0xda)), (0x34ad0, stub())])
    assert diffs == [], diffs


def test_t4_place_box_start():
    from wc1.emu import Emu
    emu = Emu()
    worker = mkunit(emu, type=2, tx=5, ty=6)
    seen = emu.alloc(0x10)

    def msg(e):
        w32(emu, seen, e.reg("eax"))
        w16(emu, seen + 4, arg(e, "edx"))
        return None

    diffs = pair(emu, "place_box_start_reference.c", "PlaceBoxStart_", 0x22798,
                 args=(0x20,), out=(),
                 watch=[(0x59bd0, 0x8), (0x5a7c9, 1), (0x52b24, 8),
                        (0x59510, 4), (0x59518, 4), (0x5ac0a, 18)],
                 stubs=[(0x25cc4, stub(lambda e: worker)),
                        (0x20d74, stub()), (0x19f70, msg),
                        (0x20cc0, stub()), (0x20c30, stub()),
                        (0x326a0, stub()), (0x348c0, stub()),
                        (0x25b6c, stub()), (0x34860, stub(lambda e: None)),
                        (0x31920, stub(lambda e: None)), (0x2261c, stub())])
    assert diffs == [], diffs
