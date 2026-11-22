"""Game logic area 0x2c4e0..0x2efd0 (docs/subsystems/game_2c4e0.md).

1. Every C file with `src =` in the symbol database (analysis/symbols/
   game_2c4e0.toml) still reproduces the original bytes, relocation targets
   and module-local data (T3, wc1.match).
2. The reference files (draw-list sort/insert, the one-argument order setter,
   PathPeekStep) are known near misses. If one starts matching, it must be
   promoted to the built file.
3. T4: the same four functions are behaviour-checked as compiled C. `cemu.load`
   compiles the reference file with its codegen-flags and relocates it against
   the symbol database; `cemu.run_pair` runs the original and the compiled C on
   identical inputs (watched memory restored between the two) and compares the
   result registers and the memory the function writes.
"""
import os
import struct

import pytest

from wc1 import cemu, codegen_sweep, match, path, symbols, t4spec
from wc1.emu import Emu

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "game_2c4e0")
MATCHED = ["draw_list_remove.c", "unit_reset_path.c", "unit_damage_frame.c", "unit_orders.c",
           "unit_set_next_order.c"]   # T3 under Watcom 10.0a (was reference C under OW2)
REFERENCE = ["draw_list_reference.c", "path_reference.c"]


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


def _flags(src):
    """Full wcc flags, and the codegen-flags tail that codegen_sweep prepends BASE_CFLAGS to."""
    full = match.file_cflags(src)
    prefix = match.BASE_CFLAGS + " "
    assert full.startswith(prefix), full
    return full, full[len(prefix):]


@pytest.mark.parametrize("name", MATCHED)
def test_matched_c(name, prog):
    src = os.path.join(AREA, name)
    out = path("build", "game_2c4e0", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    full, _ = _flags(src)
    mod = match.compile_c(src, full, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad


@pytest.mark.parametrize("name", REFERENCE)
def test_reference_is_still_a_near_miss(name):
    src = os.path.join(AREA, name)
    _, codegen = _flags(src)
    _, rows, err = codegen_sweep.sweep(src, [codegen], quiet=True)[0]
    assert rows is not None, err
    assert rows
    t4spec.assert_ref_results(src, t4spec.sweep_results(rows), name)


# ---------------------------------------------------------------- T4 difftests
# The originals of the four reference functions (analysis/symbols/
# game_2c4e0.toml: `ref_verified_by`) and the unit record / draw list layout
# they use (src/include/game_2c4e0.h, docs/subsystems/game_2c4e0.md).
PATH_PEEK = 0x2C4E0
DRAW_LIST_SORT = 0x2CED0
DRAW_LIST_INSERT = 0x2CFD8
UNIT_SET_NEXT_ORDER = 0x2EEAC
UNIT_SIZE = 0x5C
DRAW_LIST = 0x5A490


def _unit(emu, ty=0, flags=0, order=0, path_idx=0, path=(), tx=0):
    """Write one 0x5c-byte unit record into the emulator; return its address."""
    rec = bytearray(UNIT_SIZE)
    struct.pack_into("<h", rec, 0x0A, tx)        # tx
    struct.pack_into("<h", rec, 0x0C, ty)        # ty (draw key, tile row)
    struct.pack_into("<H", rec, 0x10, flags)     # flags word
    rec[0x1F] = order                            # current order
    rec[0x4C] = path_idx                         # path index
    rec[0x22:0x22 + len(path)] = bytes(path)     # path[20], 0xfe = end marker
    addr = emu.alloc(UNIT_SIZE)
    emu.write(addr, rec)
    return addr


def _set_draw_list(emu, units):
    """Fill draw_list (0x5a490) with unit pointers and the null terminator."""
    emu.write(DRAW_LIST, struct.pack("<%dI" % (len(units) + 1),
                                     *(list(units) + [0])))


def _draw_entries(emu):
    """The unit pointers currently in draw_list, up to the terminator."""
    out = []
    for i in range(201):
        u = emu.u32(DRAW_LIST + 4 * i)
        if not u:
            return out
        out.append(u)
    raise AssertionError("draw_list is not null-terminated")


def _draw_keys(emu):
    """The draw keys (0 for flags & 0x207, else the unsigned tile row)."""
    keys = []
    for u in _draw_entries(emu):
        flags = struct.unpack("<H", emu.read(u + 0x10, 2))[0]
        ty = struct.unpack("<H", emu.read(u + 0x0C, 2))[0]
        keys.append(0 if flags & 0x207 else ty)
    return keys


def test_t4_path_peek_step():
    """0x2c4e0 PathPeekStep: all three spellings in path_reference.c behave
    like the original - every direction 0..7, the index boundaries 0/19/20 and
    the 0xfe end marker, with the out Point and the unit record compared."""
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "path_reference.c"))
    dx = struct.unpack("<8b", emu.read(0x50F80, 8))     # dir_dx
    dy = struct.unpack("<8b", emu.read(0x50F88, 8))     # dir_dy
    out = emu.alloc(4)
    # the fixture is meaningful: a valid step writes tile + direction delta
    u = _unit(emu, tx=0x14, ty=0x23, path_idx=0, path=[0])
    assert emu.call(PATH_PEEK, u, out) == 1
    assert emu.read(out, 4) == struct.pack("<hh", 0x14 + dx[0], 0x23 + dy[0])
    names = ("PathPeekStep_a_", "PathPeekStep_b_", "PathPeekStep_c_")
    for tx, ty in ((0x14, 0x23), (0, 0), (0x3F, 0x3F)):
        for idx in (0, 1, 19, 20, 21, 0xFF):
            for d in list(range(8)) + [0xFE]:
                path = [0xAA] * 20          # bytes past the step are never read
                if idx < 20:
                    path[idx] = d
                u = _unit(emu, tx=tx, ty=ty, path_idx=idx, path=path)
                for name in names:
                    diffs = cemu.run_pair(emu, PATH_PEEK, cm, name, u, out,
                                          watch=[(u, UNIT_SIZE), (out, 4)],
                                          out_regs=("eax",))
                    assert diffs == [], (hex(tx), hex(ty), idx, hex(d), name, diffs)


def test_t4_draw_list_sort():
    """0x2ced0 DrawListSort: the compiled draw_list_reference.c reorders the
    list exactly like the original on empty, single-entry, sorted, reversed,
    duplicate-key, flagged-key-0, shuffled and negative-tile-row lists; the
    list contents including the terminator are compared."""
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "draw_list_reference.c"))
    cases = [
        [],                                             # empty: immediate return
        [(5, 0)],                                       # single entry
        [(1, 0), (2, 0), (3, 4)],                       # already ordered
        [(3, 0), (2, 0), (1, 0)],                       # reversed
        [(4, 0), (4, 0), (4, 0)],                       # equal keys
        [(0x200, 0), (1, 0), (2, 0)],                   # key-0 unit in front
        [(2, 0), (0x201, 0), (1, 0), (3, 0)],           # mixed keys
        [(11, 0), (3, 0), (9, 0), (0, 0), (7, 0), (3, 0), (15, 0), (1, 0)],
        [(-1, 0), (1, 0), (1, 0), (-0x8000, 0), (0, 0)],  # high-bit tile rows
        [(7, 0x100), (6, 0x4), (5, 0x200), (4, 0x1), (3, 0), (2, 0x207)],
    ]
    for case in cases:
        units = [_unit(emu, ty=ty, flags=flags) for ty, flags in case]
        _set_draw_list(emu, units)
        diffs = cemu.run_pair(emu, DRAW_LIST_SORT, cm, "DrawListSort_",
                              watch=[(DRAW_LIST, 4 * 20)] +
                                    [(u, UNIT_SIZE) for u in units],
                              out_regs=())
        assert diffs == [], (case, diffs)
    # sanity: the original bubbles the largest key to the end of a reversed list
    # (one pass per call - the tick calls it again; the list is a permutation)
    units = [_unit(emu, ty=t) for t in (5, 4, 3, 2, 1)]
    _set_draw_list(emu, units)
    emu.call(DRAW_LIST_SORT)
    assert sorted(_draw_entries(emu)) == sorted(units)
    assert _draw_keys(emu)[-1] == 5


def test_t4_draw_list_insert():
    """0x2cfd8 DrawListInsert: the compiled draw_list_reference.c keeps the same
    order as the original inserting into an empty list, at the front, middle and
    end, for duplicate keys, key-0 (flagged) units and high-bit tile rows."""
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "draw_list_reference.c"))
    cases = [
        ([], (4, 0)),                                   # empty list
        ([(1, 0)], (2, 0)),                             # after the only entry
        ([(2, 0)], (1, 0)),                             # before it
        ([(1, 0)], (1, 0)),                             # equal key
        ([(1, 0), (3, 0)], (2, 0)),                     # middle
        ([(1, 0), (3, 0)], (4, 0)),                     # end
        ([(1, 0), (3, 0)], (0, 0)),                     # front
        ([(1, 0), (2, 0), (2, 0), (3, 0)], (2, 0)),     # duplicate keys
        ([(0x200, 0), (1, 0)], (0, 0)),                 # key-0 list entry
        ([(0, 0), (1, 0)], (0x200, 0)),                 # inserted key-0 unit
        ([(5, 0), (6, 0), (7, 0), (8, 0)], (6, 0)),
        ([(1, 0), (3, 0)], (-1, 0)),                    # high-bit tile row
        ([(-1, 0)], (1, 0)),
    ]
    for keys, new in cases:
        units = [_unit(emu, ty=ty, flags=flags) for ty, flags in keys]
        u = _unit(emu, ty=new[0], flags=new[1])
        _set_draw_list(emu, units)
        diffs = cemu.run_pair(emu, DRAW_LIST_INSERT, cm, "DrawListInsert_", u,
                              watch=[(DRAW_LIST, 4 * 20)] +
                                    [(x, UNIT_SIZE) for x in units + [u]],
                              out_regs=())
        assert diffs == [], (keys, new, diffs)
    # sanity: [1, 5] + 3 is [1, 3, 5] with the inserted pointer in place
    units = [_unit(emu, ty=t) for t in (1, 5)]
    u = _unit(emu, ty=3)
    _set_draw_list(emu, units)
    emu.call(DRAW_LIST_INSERT, u)
    assert _draw_keys(emu) == [1, 3, 5]
    assert _draw_entries(emu)[1] == u


def test_t4_unit_set_next_order():
    """0x2eeac UnitSetNextOrder: the compiled unit_set_next_order.c runs the
    same guard (flags & 0x207, current order 0xc) and writes the same
    order_next/order_next2 bytes and flag bit; the whole unit record is
    compared."""
    emu = Emu()
    cm = cemu.load(emu, os.path.join(AREA, "unit_set_next_order.c"))
    cases = [
        (0x0, 0x0, 5),          # accepted: both next-order bytes and bit 7
        (0x0, 0x1, 0),          # accepted, order byte 0
        (0x0, 0xB, 0x1F),       # accepted, last normal order
        (0x80, 0x0, 0xFF),      # accepted, clears flag bit 7
        (0x207, 0x0, 5),        # rejected: flags & 0x207
        (0x200, 0x0, 5),        # rejected: 0x200 bit
        (0x7, 0x0, 5),          # rejected: low flag bits
        (0x100, 0x0, 0),        # accepted (0x100 is not in the mask)
        (0x180, 0x3, 0x1F),     # accepted
        (0x201, 0x0, 0),        # rejected
        (0x0, 0xC, 5),          # rejected: current order 0xc
        (0x80, 0xC, 5),         # rejected: order 0xc, bit 7 left set
        (0xFFFF, 0x0, 5),       # rejected: every flag bit set
    ]
    for flags, order, new in cases:
        u = _unit(emu, flags=flags, order=order)
        diffs = cemu.run_pair(emu, UNIT_SET_NEXT_ORDER, cm,
                              "UnitSetNextOrder_", u, new,
                              watch=[(u, UNIT_SIZE)], out_regs=())
        assert diffs == [], (hex(flags), order, new, diffs)
    # sanity: accepted stores the order + 0x1f and clears bit 7; rejected is a no-op
    u = _unit(emu, flags=0x80, order=0x2)
    emu.call(UNIT_SET_NEXT_ORDER, u, 5)
    assert emu.read(u + 0x1F, 3) == bytes((0x2, 5, 0x1F))
    assert emu.read(u + 0x11, 1) == b"\x00"
    u = _unit(emu, flags=0x200, order=0x2)
    before = emu.read(u, UNIT_SIZE)
    emu.call(UNIT_SET_NEXT_ORDER, u, 5)
    assert emu.read(u, UNIT_SIZE) == before

