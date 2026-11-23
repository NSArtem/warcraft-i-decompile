"""CMD.C area 0x123f0..0x12b80 (docs/subsystems/cmd_123f0.md).

1. T3 re-check: every reconstruction the symbol database marks `verified` must
   still compile byte-identical with wc1.match.  The built files are compiled by
   Watcom 10.0a (codegen-compiler header) with CMD.C's flags `-s -ot -oa -ol
   -4r -zp2` (docs/subsystems/compiler.md, cmd_123f0.md section 3), which the
   file headers carry and which the test re-asserts.
2. Near-miss guard: every *_reference.c must still NOT match; if one starts
   matching, promote it (add the `verified`/verified_by entry, and a `src =`
   entry only together with the build owner).
3. Invariants of the naming work: all 18 function starts of the range are in the
   database with module = "CMD.C", no `src =` key was added from this area, and
   the ten cheat phrases decode from the pool exactly at the offsets
   CheatCodeCommand uses (the rotating-XOR model, docs/REFERENCES.md R1 backs
   'eye of newt').
"""
import os
import random
import re
import struct

import pytest

from wc1 import analysis, cemu, codegen_sweep, match, path, symbols, t4spec

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

AREA = path("src", "cmd_123f0")
LO, HI = 0x123F0, 0x12B80
FLAGS = "-s -ot -oa -4r -zp2"          # the reference files (OW2 near misses)
BUILT_FLAGS = "-s -ot -oa -ol -4r -zp2"  # the built files (Watcom 10.0a)

# link name -> file, for the T3-verified reconstructions
MATCHED = {
    "MapViewInitLimits_": "map_view_init_limits.c",
    "MapViewScrollUp_": "map_view_scroll_up.c",
    "MapViewScrollDown_": "map_view_scroll_down.c",
    "MapViewScrollLeft_": "map_view_scroll_left.c",
    "MapViewScrollRight_": "map_view_scroll_right.c",
    "CheatCodeCommand_": "cheat_code_command.c",
    # reference C under OW2, T3 under Watcom 10.0a (2026-11-18)
    "FogMapObscure_": "fog_map_obscure.c",
    "MapViewSetScroll_": "map_view_set_scroll.c",
    "CheatCodeMatch_": "cheat_code_match.c",
    "CmdProcessText_": "cmd_process_text.c",
}

REFERENCE = [
    "fog_map_clear_reference.c",
    "terrain_tile_to_cache_reference.c",
    "terrain_cache_run_x_reference.c",
    "terrain_cache_run_y_reference.c",
    "terrain_cache_row_reference.c",
    "terrain_cache_column_reference.c",
    "set_cheat_flags_reference.c",
    "cheat_scenario_command_reference.c",
]

# offset into the pool at 0x51218 -> (phrase, flag bit toggled by CheatCodeCommand)
CHEAT_CODES = {
    0x00: (b"corwin of amber", 1 << 31),
    0x10: (b"yours truly", 1 << 8),
    0x1C: (b"crushing defeat", 1 << 7),
    0x2C: (b"there can be only one", 1 << 2),
    0x42: (b"pot of gold", 1 << 5),
    0x4E: (b"eye of newt", 1 << 3),
    0x5A: (b"iron forge", 1 << 4),
    0x65: (b"sally shears", 1 << 0),
    0x72: (b"hurry up guys", 1 << 1),
    0x80: (b"ides of march", 1 << 6),
}
POOL = 0x51218


@pytest.fixture(scope="module")
def prog():
    return codegen_sweep.program()


@pytest.fixture(scope="module")
def db():
    funcs, datas, errors = symbols.load(strict=False)
    assert not errors, errors
    return funcs, datas


@pytest.mark.parametrize("link_name,name", sorted(MATCHED.items()))
def test_matched_c_still_matches(link_name, name, prog):
    src = os.path.join(AREA, name)
    assert match.file_cflags(src) == f"{match.BASE_CFLAGS} {BUILT_FLAGS}", \
        f"{name}: expected the -oa -ol flag set this object needs"
    assert match.file_cc(src) == "10.0a", name
    out = path("build", "cmd_123f0", "t3_" + name + ".obj")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mod = match.compile_c(src, None, out)
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    res = match.match_module(prog, mod, by_link)
    bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
    assert not bad, bad
    assert link_name in [n for n, _, _ in res], [n for n, _, _ in res]


@pytest.mark.parametrize("name", REFERENCE)
def test_reference_is_still_a_near_miss(name):
    src = os.path.join(AREA, name)
    if t4spec.t3_promoted(src):      # some function promoted: its own codegen-compiler/-flags header applies
        t4spec.assert_ref_results(src, t4spec.ref_results(src), name)
        return
    _, rows, err = codegen_sweep.sweep(src, [FLAGS], quiet=True)[0]
    assert rows is not None, err
    assert rows, name
    t4spec.assert_ref_results(src, t4spec.sweep_results(rows), name)


def test_every_file_compiles():
    """No file in the area may fail to compile (a broken reference file would
    silently stop being evidence)."""
    for f in sorted(os.listdir(AREA)):
        if not f.endswith(".c"):
            continue
        _, rows, err = codegen_sweep.sweep(os.path.join(AREA, f), [FLAGS], quiet=True)[0]
        assert rows, f"{f}: {err}"


def test_range_is_fully_named(db):
    funcs, _ = db
    in_range = sorted(a for a in funcs if LO <= a < HI)
    assert len(in_range) == 18, [hex(a) for a in in_range]
    # the six match-verified functions are built from C (src =, added by the
    # build owner per AGENTS.md step 0b); everything else stays evidence-only
    built = {0x123F0: "src/cmd_123f0/map_view_init_limits.c",
             0x125C4: "src/cmd_123f0/map_view_scroll_up.c",
             0x12620: "src/cmd_123f0/map_view_scroll_down.c",
             0x12688: "src/cmd_123f0/map_view_scroll_left.c",
             0x126E4: "src/cmd_123f0/map_view_scroll_right.c",
             0x12A2C: "src/cmd_123f0/cheat_code_command.c",
             0x12438: "src/cmd_123f0/fog_map_obscure.c",
             0x1274C: "src/cmd_123f0/map_view_set_scroll.c",
             0x12800: "src/cmd_123f0/cheat_code_match.c",
             0x12B50: "src/cmd_123f0/cmd_process_text.c",
             # T3 under 10.0a since 2026-11-23 (wc1.wave4), file name kept for its difftest
             0x12404: "src/cmd_123f0/fog_map_clear_reference.c"}
    for a in in_range:
        e = funcs[a]
        assert e["module"] == "CMD.C", (hex(a), e["module"])
        assert e["evidence"], hex(a)
        if a in built:
            assert e.get("src") == built[a], (hex(a), e.get("src"))
        else:
            assert "src" not in e, (hex(a), "only the matched functions are built")


def test_verified_entries_are_mechanically_checked(db):
    """Every function of the range is `verified`, either by T3 (wc1.match) or by
    T4 (wc1.emu difftest against a model of the reconstruction)."""
    funcs, _ = db
    by_match = {0x123F0, 0x125C4, 0x12620, 0x12688, 0x126E4, 0x12A2C,
                0x12438, 0x1274C, 0x12800, 0x12B50, 0x12404}
    in_range = sorted(a for a in funcs if LO <= a < HI)
    assert len(in_range) == 18
    for a in in_range:
        e = funcs[a]
        assert e["confidence"] == "verified", (hex(a), e["confidence"])
        vb = e["verified_by"]
        if a in by_match:
            assert vb.startswith("match:"), (hex(a), vb)
            assert "src/cmd_123f0/" in vb, hex(a)
        else:
            assert vb.startswith("difftest:"), (hex(a), vb)
            assert "tests/test_cmd_123f0.py::" in vb, (hex(a), vb)


def test_cheat_codes_decode(prog):
    """CheatCodeMatch's model: byte i of an entry is plain[i] XOR (1 << (i % 8))
    with the key restarting per entry, and the terminator is a raw NUL - but an
    encoded ' ' at phase 5 is 0x00 too, which is why a naive NUL split cuts
    'yours truly' and 'there can be only one' in half.  Decoding the exact span
    up to the next address CheatCodeCommand references checks cipher and lengths
    at once."""
    d = prog.data
    img = bytes(prog.image[d.index])
    starts = sorted(CHEAT_CODES) + [0x512A6 - POOL]      # 'orc' follows the pool

    for k, off in enumerate(starts[:-1]):
        stop = starts[k + 1]
        span = img[POOL + off - d.base:POOL + stop - d.base]
        assert span[-1] == 0, (hex(POOL + off), "entry does not end on a NUL")
        plain = bytes(b ^ (1 << (i % 8)) for i, b in enumerate(span[:-1]))
        assert plain == CHEAT_CODES[off][0], (hex(POOL + off), plain)
        assert all(0x20 <= c < 0x7F for c in plain), (hex(POOL + off), plain)

    assert img[0x512A6 - d.base:0x512B0 - d.base] == b"orc\0human\0"


def test_cheat_code_command_offsets_match_the_pool():
    """The offsets CheatCodeCommand indexes, and the bits it toggles."""
    src = open(os.path.join(AREA, "cheat_code_command.c")).read()
    used = {int(m.group(1), 16) for m in re.finditer(r"cheat_code_text \+ 0x([0-9a-f]{2})", src)}
    assert used == set(CHEAT_CODES), sorted(hex(u) for u in used ^ set(CHEAT_CODES))
    assert "flags[3] ^= 0x80;" in src            # corwin of amber -> bit 31
    assert "flags[1] ^= 0x01;" in src            # yours truly     -> bit 8
    row0 = {int(m.group(1), 16) for m in re.finditer(r"flags\[0\] \^= 0x([0-9a-f]{2});", src)}
    assert row0 | {1 << 31, 1 << 8} == {b for _p, b in CHEAT_CODES.values()}, sorted(hex(x) for x in row0)


def test_terrain_cache_geometry(db):
    """15 columns x 11 rows, and the maxima are 64 minus those."""
    _, datas = db
    assert datas[0x58594]["name"] == "map_scroll_y_max"
    assert datas[0x58596]["name"] == "map_scroll_x_max"
    src = open(os.path.join(AREA, "map_view_init_limits.c")).read()
    assert "0x31" in src and "0x35" in src
    assert 64 - 15 == 49 and 64 - 11 == 53


def test_run_lengths_in_the_binary(prog):
    """0x12518 `cmp eax,0xf` (15 tiles), 0x12557 and 0x127c4 `cmp ...,0xb`
    (11 rows) - the counts the reconstruction and the docs use."""
    base = prog.code.base

    def ins(addr):
        i = next(prog.md.disasm(prog.cbytes[addr - base:addr - base + 8], addr, 1), None)
        return f"{i.mnemonic} {i.op_str}" if i else ""

    assert ins(0x12518).endswith("0xf"), ins(0x12518)
    assert ins(0x12557).endswith("0xb"), ins(0x12557)
    assert ins(0x127c4).endswith("0xb"), ins(0x127c4)


# ---------------------------------------------------------------- T4 difftests
# Functions OW2 cannot match (register allocation and the promoted loop compare,
# docs/subsystems/cmd_123f0.md section 3) are verified behaviourally: the original
# runs under wc1.emu and is compared with a Python model of the reconstruction.
# These citations are the `difftest:` entries in analysis/symbols/cmd_123f0.toml.

FOG_MAP = 0x58578           # fog_map (unsigned short *)
TILE_MAP = 0x58584          # tile_map (unsigned short *)
CELL_TABLE = 0x5858c        # fog_cell_table (tile -> 4 minitile ids)
CACHE_TOP = 0x58590         # tile_cache_top
CACHE_LEFT = 0x58592        # tile_cache_left
MAX_Y = 0x58594             # map_scroll_y_max
MAX_X = 0x58596             # map_scroll_x_max
MODEL = 0x59616             # game_mode (short)
SCROLL_X = 0x500d0          # map_scroll_x (graphics.toml)
SCROLL_Y = 0x500d2          # map_scroll_y (graphics.toml)
MINI_TILE_TO_CACHE = 0x1007C
TERRAIN_CACHE_ROW = 0x12564
TERRAIN_CACHE_RUN_X = 0x124E8
TERRAIN_CACHE_RUN_Y = 0x12524
TERRAIN_TILE_TO_CACHE = 0x1246C


@pytest.fixture()
def emu():
    from wc1.emu import Emu
    return Emu()


@pytest.mark.parametrize("addr,op", [(0x12404, lambda w: 0), (0x12438, lambda w: w | 0xa0a)],
                         ids=["FogMapClear", "FogMapObscure"])
def test_fog_map_loops(addr, op, emu):
    """FogMapClear / FogMapObscure over a scratch fog map."""
    import random
    rng = random.Random(addr)
    n = 0x1000 + 8
    buf = emu.alloc(2 * n)
    seed = bytes(rng.randrange(256) for _ in range(2 * n))
    emu.write(buf, seed)
    emu.put_u32(FOG_MAP, buf)

    emu.call(addr)

    got = emu.read(buf, 2 * n)
    for i in range(0x1000):
        w = seed[2 * i] | (seed[2 * i + 1] << 8)
        want = op(w) & 0xFFFF
        assert got[2 * i:2 * i + 2] == bytes((want & 0xFF, want >> 8)), (i, hex(w))
    assert got[2 * 0x1000:] == seed[2 * 0x1000:], "walked past the 64x64 map"


def test_terrain_tile_to_cache(emu):
    """TerrainTileToCache: the four minitiles of entry (tile & 0x7ff), painted at
    ((y*256 + x)*16) and +8, +0x800, +0x808, each truncated to 16 bits."""
    import random
    rng = random.Random(0x1246C)
    table = emu.alloc(2048 * 8)
    ids = [rng.randrange(1 << 16) for _ in range(2048 * 4)]
    emu.write(table, b"".join(struct.pack("<H", v) for v in ids))
    emu.put_u32(CELL_TABLE, table)

    seen = []
    emu.stubs[MINI_TILE_TO_CACHE] = lambda e: seen.append((e.reg("eax"), e.reg("edx"))) or 0

    for _ in range(40):
        tile = rng.randrange(1 << 16)
        x = rng.randrange(0, 64)
        y = rng.randrange(0, 64)
        seen.clear()
        emu.call(TERRAIN_TILE_TO_CACHE, tile, x, y)
        base = (((y << 8) + x) << 4) & 0xFFFF
        entry = (tile & 0x7FF) * 4
        want = [(ids[entry + j], (base + d) & 0xFFFF) for j, d in enumerate((0, 8, 0x800, 0x808))]
        assert seen == want, (hex(tile), x, y, seen, want)


def test_map_view_scroll_up_paints_the_exposed_rows(emu):
    """MapViewScrollUp: rows [new map_scroll_y, old tile_cache_top) are repainted,
    bottom-up, and tile_cache_top ends equal to map_scroll_y.  TerrainCacheRow is
    stubbed, so this checks the sliding logic itself."""
    rows = []
    emu.stubs[TERRAIN_CACHE_ROW] = lambda e: rows.append(e.reg("eax") & 0xFFFF) or 0
    emu.put_u32(MAX_Y, 53)
    emu.put_u32(MAX_X, 49)

    for start, top, n in [(20, 20, 3), (20, 20, 0), (7, 20, 5), (3, 3, 2), (0, 0, 4), (2, 2, 9)]:
        rows.clear()
        emu.write(SCROLL_Y, struct.pack("<H", start))
        emu.write(CACHE_TOP, struct.pack("<H", top))
        emu.call(0x125C4, n)
        new = max(start - n, 0)
        assert struct.unpack("<H", bytes(emu.read(SCROLL_Y, 2)))[0] == new
        assert rows == list(range(top - 1, new - 1, -1)), (start, top, n, rows)
        assert struct.unpack("<H", bytes(emu.read(CACHE_TOP, 2)))[0] == new


def test_terrain_cache_runs(emu):
    """TerrainCacheRunX/Y walk 15 tiles along a row and 11 tiles down a column of
    tile_map, carrying the constant argument unchanged."""
    import random
    rng = random.Random(0x124E8)
    tm = emu.alloc(2 * 4096)
    values = [rng.randrange(1 << 16) for _ in range(4096)]
    emu.write(tm, b"".join(struct.pack("<H", v) for v in values))
    emu.put_u32(TILE_MAP, tm)

    calls = []
    emu.stubs[TERRAIN_TILE_TO_CACHE] = lambda e: calls.append((e.reg("eax") & 0xFFFF,
                                                 e.reg("edx") & 0xFFFF,
                                                 e.reg("ebx") & 0xFFFF)) or 0
    row, x0, y0 = 7, 5, 7
    calls.clear()
    emu.call(0x124E8, tm + 2 * (row * 64 + x0), x0, y0)
    assert calls == [(values[row * 64 + x0 + i], x0 + i, y0) for i in range(15)]

    col, x1, y1 = 3, 11, 3
    calls.clear()
    emu.call(0x12524, tm + 2 * (y1 * 64 + x1), x1, y1)
    assert calls == [(values[(y1 + i) * 64 + x1], x1, y1 + i) for i in range(11)]


def test_terrain_cache_row_column_use_the_scroll_origin(emu):
    """TerrainCacheRow starts at (map_scroll_x, y); TerrainCacheColumn at
    (x, map_scroll_y)."""
    tm = emu.alloc(2 * 4096)
    emu.put_u32(TILE_MAP, tm)
    emu.write(SCROLL_X, struct.pack("<H", 9))
    emu.write(SCROLL_Y, struct.pack("<H", 6))

    got = []
    emu.stubs[TERRAIN_CACHE_RUN_X] = lambda e: got.append((e.reg("eax"), e.reg("edx") & 0xFFFF,
                                               e.reg("ebx") & 0xFFFF)) or 0
    emu.call(0x12564, 4)
    assert got == [(tm + 2 * (4 * 64 + 9), 9, 4)], got

    got.clear()
    emu.stubs[TERRAIN_CACHE_RUN_Y] = lambda e: got.append((e.reg("eax"), e.reg("edx") & 0xFFFF,
                                               e.reg("ebx") & 0xFFFF)) or 0
    emu.call(0x12594, 13)
    assert got == [(tm + 2 * (6 * 64 + 13), 13, 6)], got


def test_map_view_set_scroll_clamps_and_rebuilds(emu):
    """MapViewSetScroll: clamp to [0, max], store the origin and the cache
    position, then rebuild 11 rows of 15 tiles from the new top-left."""
    tm = emu.alloc(2 * 4096)
    emu.put_u32(TILE_MAP, tm)
    emu.put_u32(MAX_X, 49)
    emu.put_u32(MAX_Y, 53)
    emu.write(SCROLL_X, struct.pack("<H", 40))
    emu.write(SCROLL_Y, struct.pack("<H", 40))

    rows = []
    emu.stubs[TERRAIN_CACHE_RUN_X] = lambda e: rows.append((e.reg("eax"), e.reg("edx") & 0xFFFF,
                                                e.reg("ebx") & 0xFFFF)) or 0
    emu.call(0x1274C, 0xFFFFFFFF & (-3), 60)        # x = -3, y = 60
    x, y = 0, 53
    assert struct.unpack("<H", bytes(emu.read(SCROLL_X, 2)))[0] == x
    assert struct.unpack("<H", bytes(emu.read(SCROLL_Y, 2)))[0] == y
    assert struct.unpack("<H", bytes(emu.read(CACHE_TOP, 2)))[0] == y
    assert struct.unpack("<H", bytes(emu.read(CACHE_LEFT, 2)))[0] == x
    assert [r[1:] for r in rows] == [(x, y + i) for i in range(11)], rows
    assert rows[0][0] == tm + 2 * (y * 64 + x)


def test_cheat_code_match_against_the_real_pool(emu):
    """CheatCodeMatch (0x12800) run against the actual bytes at cheat_code_text:
    a phrase matches (0), a wrong character returns 1, a longer input returns 1,
    and - because an obfuscated ' ' at index 5 is a raw NUL - the prefix in
    front of that space matches too."""
    def cbuf(s):
        a = emu.alloc(len(s) + 4)
        emu.write(a, s.encode("latin-1") + b"\0")
        return a

    for off, (phrase, _bit) in sorted(CHEAT_CODES.items()):
        code = POOL + off
        assert emu.call(0x12800, cbuf(phrase.decode()), code) == 0, phrase
        bad = phrase[:-1] + bytes([phrase[-1] ^ 0x20])
        assert emu.call(0x12800, cbuf(bad.decode()), code) == 1, phrase
        assert emu.call(0x12800, cbuf(phrase.decode() + "x"), code) != 0, phrase

    # the documented prefix quirk
    assert emu.call(0x12800, cbuf("yours"), POOL + 0x10) == 0
    assert emu.call(0x12800, cbuf("there"), POOL + 0x2C) == 0
    # ... but a prefix that does not end on a space does not match
    assert emu.call(0x12800, cbuf("pot"), POOL + 0x42) != 0
    # the race words are *not* obfuscated, so they must not match as codes
    assert emu.call(0x12800, cbuf("orc"), 0x512A6) != 0


def pool_bytes(emu, n=0x98):
    return bytes(emu.read(POOL, n))


def model_match(emu, text, off):
    """Python mirror of CheatCodeMatch against the real pool bytes."""
    raw = pool_bytes(emu)
    for i, ch in enumerate(text):
        if ord(ch) != raw[off + i] ^ (1 << (i % 8)):
            return False
    return raw[off + len(text)] == 0


ORDER = [(0x00, (3, 0x80)), (0x42, (0, 0x20)), (0x4E, (0, 0x08)), (0x5A, (0, 0x10)),
         (0x65, (0, 0x01)), (0x72, (0, 0x02))]
ORDER_DEV = [(0x2C, (0, 0x04)), (0x10, (1, 0x01)), (0x1C, (0, 0x80)), (0x80, (0, 0x40))]


def _cbuf(emu, s):
    a = emu.alloc(len(s) + 4)
    emu.write(a, s.encode("latin-1") + b"\0")
    return a


def model_cmd_process_text(emu, text, flags, global_flags):
    """Python mirror of CmdProcessText -> CheatCodeCommand (0x12a2c)."""
    text = text.lower()
    out = bytearray(flags)
    for table in ([ORDER] if not (global_flags & 0x80000000) else [ORDER + ORDER_DEV]):
        for off, (idx, bit) in table:
            if model_match(emu, text, off):
                out[idx] ^= bit
                return 1, bytes(out)
    if not (global_flags & 0x80000000):
        return 0, bytes(out)
    if text.startswith("orc"):
        return 1, bytes(out)
    if text.startswith("human"):
        return 1, bytes(out)
    return 0, bytes(out)


def test_cmd_process_text_difftest(emu):
    """The typed-command entry point (0x12b50): a cheat word toggles its bit in the
    caller's copy of the flag word and returns 1, everything else returns 0."""
    cases = ["pot of gold", "eye of newt", "sally shears", "hurry up guys",
             "iron forge", "corwin of amber", "yours", "yours truly", "there",
             "there can be only one", "crushing defeat", "ides of march",
             "POT OF GOLD", "hello", "", "orc5", "human2"]
    for dev in (0, 0x80000000):
        for text in cases:
            buf = _cbuf(emu, text)
            f = emu.alloc(16)
            emu.write(f, bytes(4))
            emu.put_u32(0x51214, dev)
            got = emu.call(0x12B50, buf, f)
            exp, exp_flags = model_cmd_process_text(emu, text, bytes(4), dev)
            assert (got & 0xFFFF != 0) == (exp != 0), (hex(dev), text, got)
            assert bytes(emu.read(f, 4)) == exp_flags, (hex(dev), text)


def test_set_cheat_flags_difftest(emu):
    """0x1284c: store the word, apply the one-shot effects, and print the
    enabled/disabled message through 0x19edc (stubbed here)."""
    msgs = []

    def rec(e):
        a, b = e.reg("eax"), bytearray()
        i = 0
        while e.read(a + i, 1)[0]:
            b.append(e.read(a + i, 1)[0])
            i += 1
        msgs.append((bytes(b), e.reg("edx") & 0xFFFF, e.reg("ebx") & 0xFFFF))
        return 0

    emu.stubs[0x19EDC] = rec

    def reset():
        emu.write(0x5008C, bytes(5))              # both players "plain"
        emu.write(0x50008, bytes(50))             # the 10x5 per-player byte table
        emu.write(0x50060, bytes(0x14))           # resource array 1
        emu.write(0x50074, bytes(0x14))           # resource array 2
        emu.put_u32(0x51214, 0)
        emu.write(0x52586, struct.pack("<H", 0))  # single player
        emu.write(0x5A7C2, struct.pack("<H", 0))
        emu.put_u32(0x59614, 3 << 16)             # game_mode = 3
        msgs.clear()

    reset()
    emu.call(0x1284C, 0x20)                       # pot of gold
    assert struct.unpack("<5I", bytes(emu.read(0x50060, 20))) == (5000,) * 5
    assert struct.unpack("<5I", bytes(emu.read(0x50074, 20))) == (10000,) * 5
    assert emu.u32(0x51214) == 0                  # the bit cleared itself
    assert msgs == [(b"cheat enabled you wascally wabbit", 0, 0x24)]

    reset()
    emu.call(0x1284C, 0x08)                       # eye of newt: rows 3..8, players 0,1
    got = bytes(emu.read(0x50008, 50))
    want = bytearray(50)
    for row in range(3, 9):
        want[row * 5] = 1
        want[row * 5 + 1] = 1
    assert got == bytes(want), got
    assert emu.u32(0x51214) == 0x08

    reset()
    emu.call(0x1284C, 0x10)                       # iron forge: rows 0,1,2,9 -> 2
    got = bytes(emu.read(0x50008, 50))
    want = bytearray(50)
    for row in (0, 1, 2, 9):
        want[row * 5] = 2
        want[row * 5 + 1] = 2
    assert got == bytes(want), got

    reset()
    emu.put_u32(0x51214, 0x40)
    emu.call(0x1284C, 0x40)                       # ides of march -> game_mode 10
    assert struct.unpack("<h", bytes(emu.read(0x59616, 2)))[0] == 10
    assert msgs == []                             # no message on this path

    reset()
    emu.put_u32(0x51214, 0x40)
    emu.write(0x52586, struct.pack("<H", 1))      # link game: ides of march is inert
    emu.call(0x1284C, 0x40)
    assert struct.unpack("<h", bytes(emu.read(0x59616, 2)))[0] == 3

    reset()
    emu.put_u32(0x51214, 0x08)
    emu.call(0x1284C, 0)                          # shrinking flags -> "cheat disabled"
    assert msgs == [(b"cheat disabled", 0, 0x24)], msgs


def test_cheat_scenario_command_difftest(emu):
    """0x1295c: needs the developer bit; "orcN"/"humanN" pick the race and the
    scenario resource number, and set game_mode = 5."""
    NET, RACE, SCEN, MODE = 0x52586, 0x50088, 0x50d82, MODEL
    emu.put_u32(0x51214, 0x80000000)
    emu.write(NET, struct.pack("<H", 0))

    for text, race, num in [("orc1", 1, 120), ("orc12", 1, 142), ("human1", 0, 119),
                            ("human9", 0, 135)]:
        r = emu.call(0x1295C, _cbuf(emu, text), 0)
        assert r & 0xFFFF, text
        assert struct.unpack("<H", bytes(emu.read(RACE, 2)))[0] == race, text
        assert struct.unpack("<H", bytes(emu.read(SCEN, 2)))[0] == num, text
        assert struct.unpack("<h", bytes(emu.read(MODE, 2)))[0] == 5, text

    for text in ["orc0", "orc13"]:
        emu.write(SCEN, struct.pack("<H", 0x7777))
        assert emu.call(0x1295C, _cbuf(emu, text), 0) & 0xFFFF
        assert struct.unpack("<H", bytes(emu.read(SCEN, 2)))[0] == 0x7777, text

    emu.write(SCEN, struct.pack("<H", 0x7777))
    assert (emu.call(0x1295C, _cbuf(emu, "bogus"), 0) & 0xFFFF) == 0
    assert struct.unpack("<H", bytes(emu.read(SCEN, 2)))[0] == 0x7777

    emu.put_u32(0x51214, 0)                       # no developer bit
    assert (emu.call(0x1295C, _cbuf(emu, "orc2"), 0) & 0xFFFF) == 0

    emu.put_u32(0x51214, 0x80000000)
    emu.write(NET, struct.pack("<H", 1))          # link game: accepted, changes nothing
    emu.write(SCEN, struct.pack("<H", 0x7777))
    assert emu.call(0x1295C, _cbuf(emu, "orc2"), 0) & 0xFFFF
    assert struct.unpack("<H", bytes(emu.read(SCEN, 2)))[0] == 0x7777


# ---------------------------------------------------------------- T4: compiled C vs original
# docs/GOAL.md T4: each *_reference.c below is compiled with this object's
# codegen flags and run *against the original function* under wc1.emu on the
# same inputs (wc1.cemu.run_pair).  The compared outputs are the return
# register, the globals the function writes, and - for callees with side
# effects - the argument registers those callees receive: they are stubbed and
# the arguments recorded into scratch memory that is part of the watched
# ranges.  These citations are the `ref_verified_by` entries in
# analysis/symbols/cmd_123f0.toml.

CHEAT_FLAGS = 0x51214
DAT_50008 = 0x50008
DAT_50060 = 0x50060
DAT_50074 = 0x50074
DAT_5008C = 0x5008C
DAT_5A7C2 = 0x5A7C2
GAME_STATE = 0x59614
NET = 0x52586
RACE = 0x50088
SCEN = 0x50D82
FN_19EDC = 0x19EDC


class _ArgLog:
    """Record a stubbed callee's argument registers into watched memory.

    A Watcom caller also leaves values in the argument registers the callee
    does not use; only the actual arguments are recorded (`regs`/`masks`) so
    scratch registers are not compared.
    """

    def __init__(self, emu, regs, masks=None, cap=64):
        self.emu = emu
        self.regs = tuple(regs)
        self.masks = tuple(masks) if masks is not None else (0xFFFFFFFF,) * len(self.regs)
        self.cap = cap
        self.buf = emu.alloc(4 + cap * 4 * len(self.regs), align=4)
        emu.put_u32(self.buf, 0)

    def watch(self):
        return (self.buf, 4 + self.cap * 4 * len(self.regs))

    def reset(self):
        self.emu.put_u32(self.buf, 0)

    def stub(self):
        emu = self.emu

        def hook(e):
            n = emu.u32(self.buf)
            if n < self.cap:
                base = self.buf + 4 + n * 4 * len(self.regs)
                for k, (r, mask) in enumerate(zip(self.regs, self.masks)):
                    emu.put_u32(base + 4 * k, e.reg(r) & mask)
                emu.put_u32(self.buf, n + 1)
            return 0

        return hook


def _cbuf_bytes(emu, data):
    a = emu.alloc(len(data) + 4)
    emu.write(a, bytes(data) + b"\0")
    return a


def _t4_fog_map(emu, addr, name, ref):
    """FogMapClear/FogMapObscure: same loop, a 64x64 word map and 8 guard words."""
    cm = cemu.load(emu, os.path.join(AREA, ref))
    n = 0x1000 + 8
    buf = emu.alloc(2 * n)
    rng = random.Random(addr)
    seeds = [bytes(2 * n), b"\xff" * (2 * n)]
    seeds += [bytes(rng.randrange(256) for _ in range(2 * n)) for _ in range(3)]
    for seed in seeds:
        emu.write(buf, seed)
        emu.put_u32(FOG_MAP, buf)
        diffs = cemu.run_pair(emu, addr, cm, name, watch=[(buf, 2 * n)], out_regs=())
        assert not diffs, (hex(addr), diffs)


def test_fog_map_clear_reference_c_matches_original(emu):
    _t4_fog_map(emu, 0x12404, "FogMapClear_", "fog_map_clear_reference.c")


def test_fog_map_obscure_reference_c_matches_original(emu):
    _t4_fog_map(emu, 0x12438, "FogMapObscure_", "fog_map_obscure.c")


def test_terrain_tile_to_cache_reference_c_matches_original(emu):
    """0x1246c: four MiniTileToCache(tile, offset) calls, tile from the entry
    (arg & 0x7ff) of fog_cell_table, offsets 0/8/0x800/0x808 from
    ((y<<8)+x)<<4 - the stubbed callee's arguments are compared."""
    cm = cemu.load(emu, os.path.join(AREA, "terrain_tile_to_cache_reference.c"))
    table = emu.alloc(2048 * 8)
    rng = random.Random(0x1246C)
    ids = [rng.randrange(1 << 16) for _ in range(2048 * 4)]
    emu.write(table, b"".join(struct.pack("<H", v) for v in ids))
    emu.put_u32(CELL_TABLE, table)
    rec = _ArgLog(emu, ("eax", "edx"), masks=(0xFFFF, 0xFFFF))
    emu.stubs[MINI_TILE_TO_CACHE] = rec.stub()
    cases = [(0, 0, 0), (0xFFFF, 0xFFFF, 0xFFFF), (0x7FF, 63, 63),
             (0x800, 0, 0), (0xFFFF, 1, 1)]
    cases += [(rng.randrange(1 << 16), rng.randrange(64), rng.randrange(64))
              for _ in range(6)]
    for tile, x, y in cases:
        rec.reset()
        diffs = cemu.run_pair(emu, TERRAIN_TILE_TO_CACHE, cm, "TerrainTileToCache_",
                              tile, x, y, watch=[rec.watch()], out_regs=())
        assert not diffs, (hex(tile), x, y, diffs)


def _t4_terrain_run(emu, addr, name, ref, stride, count):
    """TerrainCacheRunX (stride 2, 15 tiles) / RunY (stride 0x80, 11 tiles):
    the stubbed TerrainTileToCache call sequence (tile, x, y) is compared."""
    cm = cemu.load(emu, os.path.join(AREA, ref))
    tm = emu.alloc(2 * 4096)
    rng = random.Random(addr)
    values = [rng.randrange(1 << 16) for _ in range(4096)]
    emu.write(tm, b"".join(struct.pack("<H", v) for v in values))
    emu.put_u32(TILE_MAP, tm)
    rec = _ArgLog(emu, ("eax", "edx", "ebx"), masks=(0xFFFFFFFF, 0xFFFF, 0xFFFF))
    emu.stubs[TERRAIN_TILE_TO_CACHE] = rec.stub()
    max_off = 4096 - count * (stride // 2)
    cases = [(0, 0, 0), (max_off, 49, 53), ((30 * 64 + 20) % (max_off + 1), 20, 30),
             (max_off, 0xFFFF, 0xFFFF)]
    cases += [(rng.randrange(max_off + 1), rng.randrange(1 << 16),
               rng.randrange(1 << 16)) for _ in range(5)]
    for off, x, y in cases:
        rec.reset()
        diffs = cemu.run_pair(emu, addr, cm, name, tm + 2 * off, x, y,
                              watch=[rec.watch()], out_regs=())
        assert not diffs, (off, x, y, diffs)


def test_terrain_cache_run_x_reference_c_matches_original(emu):
    _t4_terrain_run(emu, 0x124E8, "TerrainCacheRunX_",
                    "terrain_cache_run_x_reference.c", 2, 15)


def test_terrain_cache_run_y_reference_c_matches_original(emu):
    _t4_terrain_run(emu, 0x12524, "TerrainCacheRunY_",
                    "terrain_cache_run_y_reference.c", 0x80, 11)


def test_terrain_cache_row_reference_c_matches_original(emu):
    """0x12564: TerrainCacheRunX(tile_map + (y*64 + map_scroll_x), map_scroll_x, y)."""
    cm = cemu.load(emu, os.path.join(AREA, "terrain_cache_row_reference.c"))
    tm = emu.alloc(2 * 4096)
    emu.write(tm, bytes(2 * 4096))
    emu.put_u32(TILE_MAP, tm)
    rec = _ArgLog(emu, ("eax", "edx", "ebx"), masks=(0xFFFFFFFF, 0xFFFF, 0xFFFF))
    emu.stubs[TERRAIN_CACHE_RUN_X] = rec.stub()
    for sx in (0, 9, 49, 63, 0xFFFF):
        emu.write(SCROLL_X, struct.pack("<H", sx))
        for y in (0, 4, 30, 53, 63, 0xFFFF):
            rec.reset()
            diffs = cemu.run_pair(emu, 0x12564, cm, "TerrainCacheRow_", y,
                                  watch=[rec.watch()], out_regs=())
            assert not diffs, (sx, y, diffs)


def test_terrain_cache_column_reference_c_matches_original(emu):
    """0x12594: TerrainCacheRunY(tile_map + (map_scroll_y*64 + x), x, map_scroll_y)."""
    cm = cemu.load(emu, os.path.join(AREA, "terrain_cache_column_reference.c"))
    tm = emu.alloc(2 * 4096)
    emu.write(tm, bytes(2 * 4096))
    emu.put_u32(TILE_MAP, tm)
    rec = _ArgLog(emu, ("eax", "edx", "ebx"), masks=(0xFFFFFFFF, 0xFFFF, 0xFFFF))
    emu.stubs[TERRAIN_CACHE_RUN_Y] = rec.stub()
    for sy in (0, 6, 30, 53, 63, 0xFFFF):
        emu.write(SCROLL_Y, struct.pack("<H", sy))
        for x in (0, 13, 49, 63, 0xFFFF):
            rec.reset()
            diffs = cemu.run_pair(emu, 0x12594, cm, "TerrainCacheColumn_", x,
                                  watch=[rec.watch()], out_regs=())
            assert not diffs, (sy, x, diffs)


def test_map_view_set_scroll_reference_c_matches_original(emu):
    """0x1274c: signed clamp to [0, max], the four stored words, and the 11
    TerrainCacheRunX calls from the new top-left - all compared."""
    cm = cemu.load(emu, os.path.join(AREA, "map_view_set_scroll.c"))
    tm = emu.alloc(2 * 4096)
    emu.write(tm, bytes(2 * 4096))
    emu.put_u32(TILE_MAP, tm)
    emu.put_u32(MAX_X, 49)
    emu.put_u32(MAX_Y, 53)
    rec = _ArgLog(emu, ("eax", "edx", "ebx"), masks=(0xFFFFFFFF, 0xFFFF, 0xFFFF))
    emu.stubs[TERRAIN_CACHE_RUN_X] = rec.stub()
    watch = [rec.watch(), (SCROLL_X, 2), (SCROLL_Y, 2), (CACHE_LEFT, 2),
             (CACHE_TOP, 2), (MAX_X, 2), (MAX_Y, 2)]
    for x, y in [(0, 0), (-3, 60), (49, 53), (50, 54), (0x7FFF, -0x8000),
                 (-0x8000, 0x7FFF), (-1, -1)]:
        rec.reset()
        diffs = cemu.run_pair(emu, 0x1274C, cm, "MapViewSetScroll_",
                              x & 0xFFFFFFFF, y & 0xFFFFFFFF,
                              watch=watch, out_regs=())
        assert not diffs, (x, y, diffs)


def test_cheat_code_match_reference_c_matches_original(emu):
    """0x12800: the rotating-XOR compare and its raw-terminator return, against
    the real obfuscated pool and scratch-encoded strings."""
    cm = cemu.load(emu, os.path.join(AREA, "cheat_code_match.c"))
    raw = bytes(emu.read(POOL, 0x98))
    cases = []
    for off in sorted(CHEAT_CODES):
        end = raw.index(0, off)
        plain = bytes(b ^ (1 << (i % 8)) for i, b in enumerate(raw[off:end]))
        for text in (plain, plain[:-1], plain + b"x", b"", b"\x00"):
            cases.append((text, POOL + off))
    rng = random.Random(0x12800)
    for _ in range(6):
        cases.append((bytes(rng.randrange(32, 127) for _ in range(rng.randrange(20))),
                      POOL + rng.choice(sorted(CHEAT_CODES))))
    for plain in (b"", b"a", b"hello world"):
        enc = bytes(b ^ (1 << (i % 8)) for i, b in enumerate(plain)) + b"\0"
        code = emu.alloc(len(enc))
        emu.write(code, enc)
        for text in (plain, plain[:len(plain) // 2], plain + b"z"):
            cases.append((text, code))
    for text, code in cases:
        diffs = cemu.run_pair(emu, 0x12800, cm, "CheatCodeMatch_",
                              _cbuf_bytes(emu, text), code, out_regs=("eax",))
        assert not diffs, (text, hex(code), diffs)


def test_set_cheat_flags_reference_c_matches_original(emu):
    """0x1284c: the flag word, the four one-shot effects (spell/upgrade rows,
    resources, game_mode), and the stubbed message call - all compared."""
    cm = cemu.load(emu, os.path.join(AREA, "set_cheat_flags_reference.c"))
    rec = _ArgLog(emu, ("eax", "edx", "ebx"), masks=(0xFFFFFFFF, 0xFFFF, 0xFFFF))
    emu.stubs[FN_19EDC] = rec.stub()
    watch = [rec.watch(), (CHEAT_FLAGS, 4), (DAT_50008, 50), (DAT_50060, 20),
             (DAT_50074, 20), (DAT_5008C, 5), (NET, 2), (DAT_5A7C2, 2),
             (MODEL, 2)]

    def reset(net=0, gates=bytes(5), old=0):
        emu.write(DAT_5008C, gates)
        emu.write(DAT_50008, bytes(50))
        emu.write(DAT_50060, bytes(20))
        emu.write(DAT_50074, bytes(20))
        emu.put_u32(CHEAT_FLAGS, old)
        emu.write(NET, struct.pack("<H", net))
        emu.write(DAT_5A7C2, struct.pack("<H", 0))
        emu.put_u32(GAME_STATE, 3 << 16)
        rec.reset()

    flagsets = [0, 0x8, 0x10, 0x20, 0x40, 0x60, 0x78,
                0x80000000, 0xFFFFFFFF]
    rng = random.Random(0x1284C)
    flagsets += [rng.randrange(1 << 32) for _ in range(5)]
    for flags in flagsets:
        reset(old=0)
        diffs = cemu.run_pair(emu, 0x1284C, cm, "SetCheatFlags_", flags,
                              watch=watch, out_regs=())
        assert not diffs, (hex(flags), "single", diffs)
        reset(old=0x08)
        diffs = cemu.run_pair(emu, 0x1284C, cm, "SetCheatFlags_", flags,
                              watch=watch, out_regs=())
        assert not diffs, (hex(flags), "shrinking", diffs)
        reset(net=1)
        diffs = cemu.run_pair(emu, 0x1284C, cm, "SetCheatFlags_", flags,
                              watch=watch, out_regs=())
        assert not diffs, (hex(flags), "link", diffs)
    for flags in (0x8, 0x10):
        reset(gates=b"\x01\x00\x00\x00\x00")
        diffs = cemu.run_pair(emu, 0x1284C, cm, "SetCheatFlags_", flags,
                              watch=watch, out_regs=())
        assert not diffs, (hex(flags), "gate", diffs)


def test_cheat_scenario_command_reference_c_matches_original(emu):
    """0x1295c: the developer gate, orc/human<N> parsing (scenario_race,
    scenario_number, game_mode) and the inert link-game paths."""
    cm = cemu.load(emu, os.path.join(AREA, "cheat_scenario_command_reference.c"))
    watch = [(RACE, 2), (SCEN, 2), (MODEL, 2)]
    texts = ["orc1", "orc12", "human1", "human9", "human12", "orc0", "orc13",
             "human0", "human13", "orc", "human", "orc-1", "orc1x", "ORC1",
             "human 2", "bogus", ""]
    for dev, net in ((0x80000000, 0), (0, 0), (0x80000000, 1)):
        emu.put_u32(CHEAT_FLAGS, dev)
        emu.write(NET, struct.pack("<H", net))
        for text in texts:
            flags = emu.alloc(4)
            emu.write(flags, bytes(4))
            diffs = cemu.run_pair(emu, 0x1295C, cm, "CheatScenarioCommand_",
                                  _cbuf(emu, text), flags,
                                  watch=watch + [(flags, 4)], out_regs=("eax",))
            assert not diffs, (hex(dev), net, text, diffs)


def test_cmd_process_text_reference_c_matches_original(emu):
    """0x12b50: strlwr in place, then CheatCodeCommand/CheatScenarioCommand on
    the original callees; the returned flag, the caller's flag bytes and the
    lower-cased text are compared."""
    cm = cemu.load(emu, os.path.join(AREA, "cmd_process_text.c"))
    texts = ["pot of gold", "eye of newt", "sally shears", "hurry up guys",
             "iron forge", "corwin of amber", "yours", "yours truly", "there",
             "there can be only one", "crushing defeat", "ides of march",
             "POT OF GOLD", "Eye Of Newt", "hello", "", "orc5", "human2",
             "ORC5", "Human12", "ides of march!"]
    for dev in (0, 0x80000000):
        emu.put_u32(CHEAT_FLAGS, dev)
        for text in texts:
            buf = _cbuf(emu, text)
            flags = emu.alloc(4)
            emu.write(flags, bytes(4))
            diffs = cemu.run_pair(emu, 0x12B50, cm, "CmdProcessText_",
                                  buf, flags,
                                  watch=[(buf, len(text) + 1), (flags, 4)],
                                  out_regs=("eax",))
            assert not diffs, (hex(dev), text, diffs)
