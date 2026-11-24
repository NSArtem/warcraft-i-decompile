"""Differential and structural tests for the mod_24860 area.

Area = the save-file loader/writer object 0x24860..0x24e50: RefRelocate, the
stream helpers over the loaded image, the file loader SaveLoadImage, the three
record rebasing helpers and the writer SaveWriteImage.  Names/evidence:
analysis/symbols/mod_24860.toml; prose: docs/subsystems/save_format.md.

Kinds of test here:
  * T3 re-check of the byte-matched C files (src/mod_24860/ref_relocate.c,
    src/mod_24860/save_read_stream.c): every
    function must stay MATCH under `wc1.match`.
  * T4 difftests: the original functions run under wc1.emu against the
    compiled reference C (wc1.cemu.run_pair) on identical inputs - the same
    stubbed library calls, the same globals and record buffers, watching the
    memory effects named in the TOML `ref_verified_by` entries.
  * structural checks of the documented save-image layout (block order and
    sizes from the writer, the 0x11170 loader bound, the mode word, the
    unreferenced 0x24860 block).
"""
import os
import random
import struct

import pytest

from wc1 import cemu, codegen_sweep, match, path, symbols, t4spec

HAVE = os.path.exists(path("original", "install", "war.exe")) and bool(os.environ.get("WATCOM"))
pytestmark = pytest.mark.skipif(not HAVE, reason="needs original/ and $WATCOM (nix develop)")

MATCHED = [path("src", "mod_24860", "ref_relocate.c"),
           path("src", "mod_24860", "save_read_stream.c")]
REF_IO = path("src", "mod_24860", "save_io_reference.c")
# T3 under Watcom 10.0a since 2026-11-18 (split out of save_io_reference.c)
SKIP_SRC = path("src", "mod_24860", "save_skip_stream.c")
FREE_SRC = path("src", "mod_24860", "save_free_image.c")
REF_RELOC = path("src", "mod_24860", "save_reloc_reference.c")
REF_IMAGE = path("src", "mod_24860", "save_image_reference.c")

# addresses (evidence in analysis/symbols/mod_24860.toml)
SAVE_LEFT = 0x5A0B0             # dword: image bytes not yet consumed
RELOC_STATE = 0x5A0B2           # dword read, mode word at +2 (0x5A0B4)
SAVE_IMAGE = 0x5313C            # GdsAlloc'd loaded image
UNIT_ARRAY = 0x59640            # 200 x 0x5c unit records
OBJECT_ARRAY = 0x59644          # 100 x 0x26 object records
OBJECT_MAP = 0x58580            # 64x64 tile -> unit pointer
TILE_MAP = 0x58584
MAP_FLAGS = 0x5857C
FOG_MAP = 0x58578
GAME_STATE = 0x50D7C            # RNG seed + scenario state, 0x200 bytes
SCENARIO = 0x50004              # scenario block, 0xbb8 bytes
PREFS = 0x532B4                 # 0x14-byte prefs block
NET_RING = 0x58848              # 0x550-byte message ring
RING_STATE = 0x58D98            # 2 words
SEND_STATE = 0x58D9C            # 3 words
NET_ENEMY = 0x5A084             # 12-byte identity block
DAT_516AE = 0x516AE             # second header word

GDS_ALLOC, GDS_FREE = 0x32558, 0x32780
FILE_TELL, FILE_SEEK, FILE_READ = 0x319C4, 0x31A80, 0x31ADC
FPUTC = 0x33F90
VALIDATE = 0x241A4
WRITE_BYTES = 0x249F8
FINISH = 0x146CC
NET_ERROR = 0x21C20

# externals the reference C has and the symbol DB does not (yet)
# (the scenario block's symbol is named scenario_unit_mask by the status area;
#  it is added here so this test does not depend on that TOML)
EXTRA = {"fn_146cc_": FINISH,
         "_scenario_unit_mask": SCENARIO}

# the complete image the writer produces (sum of the block sizes,
# docs/subsystems/save_format.md section 2)
IMAGE_SIZE = 0x109EE
IMAGE_LIMIT = 0x11170


def emu_mod():
    from wc1.emu import Emu
    return Emu()


def u16(emu, a):
    return struct.unpack("<H", emu.read(a, 2))[0]


def put_u32(emu, a, v):
    emu.put_u32(a, v)


def _flags(src):
    full = match.file_cflags(src)
    assert full.startswith(match.BASE_CFLAGS + " "), full
    return full, full[len(match.BASE_CFLAGS) + 1:]


# ---------------------------------------------------------------- T3

def test_t3_matched_c():
    """RefRelocate and SaveReadStream stay byte-identical (T3), including all
    relocation targets and the module-local data.  One function per file:
    SaveLoadImage 0x24900 between them is reference C, so the two built
    functions cannot share one object."""
    funcs, datas, _ = symbols.load()
    by_link = {e["link_name"]: e for t in (funcs, datas) for e in t.values()}
    seen = []
    for src in MATCHED:
        out = path("build", "mod_24860",
                   "t3_" + os.path.splitext(os.path.basename(src))[0] + ".obj")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        mod = match.compile_c(src, _flags(src)[0], out)
        res = match.match_module(codegen_sweep.program(), mod, by_link)
        assert res, f"no functions found in {src}"
        bad = [(n, s, p) for n, s, p in res if s != "MATCH"]
        assert not bad, bad
        seen += [n for n, _, _ in res]
    assert sorted(seen) == ["RefRelocate_", "SaveReadStream_"]


@pytest.mark.parametrize("src", [REF_IO, REF_RELOC, REF_IMAGE])
def test_reference_c_stays_a_near_miss(src):
    """The reference files model the logic correctly but are not byte-matches;
    if one starts matching it has to be promoted (src = ... in the TOML)."""
    _, codegen = _flags(src)
    _, rows, err = codegen_sweep.sweep(src, [codegen], quiet=True)[0]
    assert rows is not None, err
    assert rows
    t4spec.assert_ref_results(src, t4spec.sweep_results(rows), src)


# ---------------------------------------------------------------- T4 helpers

def _load(emu, src):
    return cemu.load(emu, src, extra=EXTRA)


def _same_calls(calls):
    """The stubs record both runs back to back; the two halves must agree."""
    assert len(calls) % 2 == 0, calls
    half = len(calls) // 2
    assert calls[:half] == calls[half:], (calls[:half], calls[half:])


def test_t4_save_skip_stream():
    """0x249c8: same new position and same bytes-left counter."""
    emu = emu_mod()
    cm = _load(emu, SKIP_SRC)
    rnd = random.Random(2498)
    buf = emu.alloc(0x10000)
    for count in [0, 1, 2, 0x566, 0xFFFF, 0x10000, 0x10001] + \
                 [rnd.randrange(0x20000) for _ in range(20)]:
        pos = buf + rnd.randrange(0x1000)
        put_u32(emu, SAVE_LEFT, rnd.randrange(0x1000, 0x20000))
        diffs = cemu.run_pair(emu, 0x249C8, cm, "SaveSkipStream_", count, pos,
                              watch=[(SAVE_LEFT, 4)])
        assert diffs == [], (count, diffs)


def test_t4_save_free_image():
    """0x249e0: frees the pointer in save_image and clears it."""
    emu = emu_mod()
    cm = _load(emu, FREE_SRC)
    freed = []
    emu.stubs[GDS_FREE] = lambda e: freed.append(e.reg("eax")) or 0
    target = emu.alloc(16)
    put_u32(emu, SAVE_IMAGE, target)
    diffs = cemu.run_pair(emu, 0x249E0, cm, "SaveFreeImage_",
                          watch=[(SAVE_IMAGE, 4)], out_regs=())
    assert diffs == [], diffs
    assert freed == [target, target], freed


def _install_file(emu, content, pos0, size, pos_addr):
    """A tiny stdio file model: FileTell/FileSeek/FileRead over `content`."""
    put_u32(emu, pos_addr, pos0)

    def tell(e):
        return e.u32(pos_addr)

    def seek(e):
        whence = e.reg("ebx")
        off = e.reg("edx")
        if whence == 0:
            pos = off
        elif whence == 2:
            pos = size + off
        else:
            pos = e.u32(pos_addr) + off
        e.put_u32(pos_addr, pos & 0xFFFFFFFF)
        return 0

    def read(e):
        buf, sz, n = e.reg("eax"), e.reg("edx"), e.reg("ebx")
        pos = e.u32(pos_addr)
        total = (sz * n) & 0xFFFFFFFF
        if pos + total > size:
            e.put_u32(pos_addr, size)
            return 0
        if total:
            e.write(buf, e.read(content + pos, total))
        e.put_u32(pos_addr, pos + total)
        return n

    emu.stubs[FILE_TELL] = tell
    emu.stubs[FILE_SEEK] = seek
    emu.stubs[FILE_READ] = read


def test_t4_save_load_image():
    """0x24900: same validation result, same bytes-left counter, same image
    pointer, same stub-call sequence (the file model keeps its position in
    watched memory so the two runs start from the same state)."""
    rnd = random.Random(2490)
    cases = [
        # (file size, start, read ok, validate ok, outcome)
        (0x2000, 0x2C, True, True, "ok"),
        (0x2000, 0x2C + 0x100, True, False, "header"),   # header rejected
        (0x2000, 0x2C, False, None, "short"),            # short read
        (IMAGE_LIMIT + 0x2C, 0x2C, True, True, "ok"),    # exactly at the limit
        (IMAGE_LIMIT + 0x2D, 0x2C, True, True, "big"),   # one over: rejected
    ]
    for size, pos0, read_ok, validate_ok, outcome in cases:
        emu = emu_mod()
        cm = _load(emu, REF_IO)
        content = emu.alloc(size + 0x100)
        emu.write(content, bytes(rnd.randrange(256) for _ in range(size)))
        pos_addr = emu.alloc(4)
        savebuf = emu.alloc(IMAGE_LIMIT + 0x100)
        sentinel = emu.alloc(16)
        put_u32(emu, SAVE_IMAGE, sentinel)
        allocs, frees, calls = [], [], []
        _install_file(emu, content, pos0, size, pos_addr)
        if outcome == "short":
            emu.stubs[FILE_READ] = lambda e: calls.append(("read", e.reg("eax"))) or 0
        emu.stubs[GDS_ALLOC] = lambda e: allocs.append(e.reg("eax")) or savebuf
        emu.stubs[GDS_FREE] = lambda e: frees.append(e.reg("eax")) or 0

        def validate(e, ok=validate_ok):
            p = e.reg("eax")
            calls.append(("validate", p))
            return (p + 0x56A) if (ok and p) else 0

        emu.stubs[VALIDATE] = validate
        watch = [(pos_addr, 4), (SAVE_LEFT, 4), (RELOC_STATE, 4),
                 (SAVE_IMAGE, 4), (savebuf, size), (sentinel, 16)]
        diffs = cemu.run_pair(emu, 0x24900, cm, "SaveLoadImage_", watch=watch)
        assert diffs == [], (outcome, diffs)
        ret = emu.reg("eax")
        if calls:
            _same_calls(calls)
        if outcome == "big":
            assert allocs == [] and frees == [], (allocs, frees, calls)
            assert ret == 0
            assert emu.u32(SAVE_IMAGE) == sentinel
            assert emu.u32(SAVE_LEFT) == size - pos0
            continue
        assert allocs == [size - pos0] * 2, allocs
        assert u16(emu, RELOC_STATE + 2) == 0
        if outcome == "ok":
            assert frees == []
            assert ret == savebuf + 0x56A
            assert emu.u32(SAVE_IMAGE) == savebuf
            assert emu.u32(SAVE_LEFT) == size - pos0
        elif outcome == "header":
            assert frees == [savebuf, savebuf]
            assert ret == 0
            assert emu.u32(SAVE_IMAGE) == 0
        else:                                  # short read
            assert frees == [savebuf, savebuf]
            assert ret == 0
            assert emu.u32(SAVE_IMAGE) == 0
            assert calls == [("read", savebuf), ("validate", 0)] * 2, calls


def test_t4_save_write_bytes():
    """0x249f8: same buffer bytes, same FILE fields and same return value for
    the fast path, the line-buffered path, the newline path, a nearly full
    buffer and an fputc error."""
    FILE = 0x0
    rnd = random.Random(2498)
    for mode, cnt, bufsiz, data, fail_from in [
        (0, 0, 0x400, b"hello", None),
        (0, 0, 0x400, b"abc\ndef", None),
        (0, 0x3FF, 0x400, b"abc", None),          # one byte free
        (4, 0, 0x400, b"abc", None),              # line buffered
        (0, 0, 0x400, b"ab\ncd\n", 1),            # fputc error at the 2nd call
        (0, 0, 0x400, b"", None),
    ]:
        emu = emu_mod()
        cm = _load(emu, REF_IO)
        fp = emu.alloc(0x20)
        out = emu.alloc(0x100)
        src = emu.alloc(len(data) + 1)
        emu.write(src, data)
        # the 1994 FILE: cnt is the number of characters in the buffer
        emu.write(fp, struct.pack("<Ii", out + cnt, cnt) + bytes(4) +
                  bytes([0, mode]) + bytes(6) + struct.pack("<I", bufsiz))
        fcalls_addr = emu.alloc(4)
        put_u32(emu, fcalls_addr, 0)
        fcalls = []

        def fputc_stub(e, fail_from=fail_from, cnt_addr=fcalls_addr):
            n = e.u32(cnt_addr)
            e.put_u32(cnt_addr, n + 1)
            c = e.reg("eax")
            fcalls.append((c, e.reg("edx")))
            if fail_from is not None and n >= fail_from:
                return 0xFFFFFFFF
            return c

        emu.stubs[FPUTC] = fputc_stub
        watch = [(fp, 0x18), (out, 0x100), (fcalls_addr, 4)]
        diffs = cemu.run_pair(emu, 0x249F8, cm, "SaveWriteBytes_", src, len(data), fp,
                              watch=watch)
        assert diffs == [], (data, mode, cnt, diffs)
        _same_calls(fcalls)
        # the fast path stored the non-newline bytes directly in the buffer
        if mode == 0 and cnt == 0 and fail_from is None:
            fast = bytes(b for b in data if b != 0x0A)
            assert emu.read(out, len(fast)) == fast[:len(fast)], data


def test_t4_save_reloc_object_map():
    """0x24a68: same rebased 64x64 object map in both directions."""
    emu = emu_mod()
    cm = _load(emu, REF_RELOC)
    base = emu.alloc(0x47E0)
    put_u32(emu, UNIT_ARRAY, base)
    rnd = random.Random(2468)
    for mode in (0, 1):
        cells = []
        for _ in range(0x1000):
            r = rnd.random()
            if r < 0.1:
                cells.append(0)
            elif r < 0.2:
                cells.append(0xFFFFFFFF)
            else:
                cells.append((base + rnd.randrange(200) * 0x5C) & 0xFFFFFFFF)
        buf = emu.alloc(0x4000)
        emu.write(buf, struct.pack("<4096I", *cells))
        put_u32(emu, RELOC_STATE, (mode << 16) | rnd.randrange(0x10000))
        diffs = cemu.run_pair(emu, 0x24A68, cm, "SaveRelocObjectMap_", buf,
                              watch=[(buf, 0x4000)], out_regs=())
        assert diffs == [], (mode, diffs)


def _unit_record(rnd, base, obj_base, mode):
    rec = bytearray(0x5C)
    flags = rnd.choice([0, 0, 1])
    struct.pack_into("<H", rec, 0x10, flags)
    rec[0x11] = rnd.randrange(256)
    rec[0x1B] = rnd.choice([0, 5, 0x1F, 0x20, 0x26, 0x32, 0x33, 0x35])
    rec[0x1C] = rnd.randrange(256)
    for off, basep in ((0x3A, base), (0x42, base), (0x52, base),
                       (0x46, 0x50008), (0x58, obj_base)):
        r = rnd.random()
        if r < 0.15:
            struct.pack_into("<I", rec, off, 0)
        elif r < 0.3:
            struct.pack_into("<I", rec, off, 0xFFFFFFFF)
        else:
            struct.pack_into("<I", rec, off, (basep + rnd.randrange(0x100)) & 0xFFFFFFFF)
    return bytes(rec)


def test_t4_save_reloc_units():
    """0x24aa8: same rebasing of the 200 unit records (both directions, all
    type branches, free slots skipped)."""
    emu = emu_mod()
    cm = _load(emu, REF_RELOC)
    base = emu.alloc(0x47E0)
    obj_base = emu.alloc(0xED8)
    put_u32(emu, UNIT_ARRAY, base)
    put_u32(emu, OBJECT_ARRAY, obj_base)
    rnd = random.Random(24 * 0xA8)
    for mode in (0, 1):
        buf = emu.alloc(0x47E0)
        emu.write(buf, b"".join(_unit_record(rnd, base, obj_base, mode)
                                for _ in range(200)))
        put_u32(emu, RELOC_STATE, (mode << 16))
        diffs = cemu.run_pair(emu, 0x24AA8, cm, "SaveRelocUnits_", buf,
                              watch=[(buf, 0x47E0)], out_regs=())
        assert diffs == [], (mode, diffs)


def test_t4_save_reloc_objects():
    """0x24b88: same rebasing of the 100 object records."""
    emu = emu_mod()
    cm = _load(emu, REF_RELOC)
    base = emu.alloc(0x47E0)
    put_u32(emu, UNIT_ARRAY, base)
    rnd = random.Random(0x24B88)
    for mode in (0, 1):
        recs = []
        for _ in range(100):
            rec = bytearray(0x26)
            rec[0] = rnd.randrange(4)
            rec[1] = rnd.choice([0, 0, 1])
            for off in (0x1E, 0x22):
                r = rnd.random()
                if r < 0.15:
                    struct.pack_into("<I", rec, off, 0)
                elif r < 0.3:
                    struct.pack_into("<I", rec, off, 0xFFFFFFFF)
                else:
                    struct.pack_into("<I", rec, off,
                                     (base + rnd.randrange(200) * 0x5C) & 0xFFFFFFFF)
            recs.append(bytes(rec))
        buf = emu.alloc(0xED8)
        emu.write(buf, b"".join(recs))
        put_u32(emu, RELOC_STATE, (mode << 16))
        diffs = cemu.run_pair(emu, 0x24B88, cm, "SaveRelocObjects_", buf,
                              watch=[(buf, 0xED8)], out_regs=())
        assert diffs == [], (mode, diffs)


def _writer_world(emu, rnd, fail_block=None):
    """Fill the globals the writer serialises, stub the library calls and
    return the watched addresses.  SaveWriteBytes is modelled as 'append the
    block to the image buffer', with the cursor in emu memory so the two runs
    start identical."""
    unit_base = emu.alloc(0x47E0)
    obj_base = emu.alloc(0xED8)
    put_u32(emu, UNIT_ARRAY, unit_base)
    put_u32(emu, OBJECT_ARRAY, obj_base)
    emu.write(unit_base, b"".join(_unit_record(rnd, unit_base, obj_base, 1)
                                  for _ in range(200)))
    objrecs = []
    for _ in range(100):
        rec = bytearray(0x26)
        rec[0] = rnd.randrange(4)
        rec[1] = rnd.choice([0, 0, 1])
        for off in (0x1E, 0x22):
            struct.pack_into("<I", rec, off,
                             (unit_base + rnd.randrange(200) * 0x5C) & 0xFFFFFFFF)
        objrecs.append(bytes(rec))
    emu.write(obj_base, b"".join(objrecs))

    objmap = emu.alloc(0x4000)
    cells = [0 if rnd.random() < 0.2 else
             (unit_base + rnd.randrange(200) * 0x5C) & 0xFFFFFFFF
             for _ in range(0x1000)]
    emu.write(objmap, struct.pack("<4096I", *cells))
    put_u32(emu, OBJECT_MAP, objmap)
    for addr, size in ((TILE_MAP, 0x2000), (MAP_FLAGS, 0x2000), (FOG_MAP, 0x2000)):
        p = emu.alloc(size)
        emu.write(p, bytes(rnd.randrange(256) for _ in range(size)))
        put_u32(emu, addr, p)
    emu.write(GAME_STATE, bytes(rnd.randrange(256) for _ in range(0x200)))
    emu.write(SCENARIO, bytes(rnd.randrange(256) for _ in range(0xBB8)))
    emu.write(PREFS, bytes(rnd.randrange(256) for _ in range(0x14)))
    emu.write(NET_ENEMY, bytes(rnd.randrange(256) for _ in range(0xC)))
    emu.write(NET_RING, bytes(rnd.randrange(256) for _ in range(0x550)))
    emu.write(RING_STATE, bytes(rnd.randrange(256) for _ in range(4)))
    emu.write(SEND_STATE, bytes(rnd.randrange(256) for _ in range(6)))
    emu.write(DAT_516AE, bytes(rnd.randrange(256) for _ in range(2)))

    image = emu.alloc(IMAGE_SIZE + 0x100)
    cursor = emu.alloc(4)
    put_u32(emu, cursor, 0)
    block_cnt = emu.alloc(4)
    put_u32(emu, block_cnt, 0)
    scratch = emu.alloc(0x47E0)
    fp = emu.alloc(0x20)
    fin = []
    net_err = []
    blocks = []

    def write_bytes(e):
        data, n = e.reg("eax"), e.reg("edx")
        cur = e.u32(cursor)
        k = e.u32(block_cnt)
        e.put_u32(block_cnt, k + 1)
        blocks.append((cur, n, bytes(e.read(data, n))))
        if n:
            e.write(image + cur, e.read(data, n))
        e.put_u32(cursor, cur + n)
        if fail_block is not None and k + 1 == fail_block:
            return 1
        return 0

    emu.stubs[WRITE_BYTES] = write_bytes
    emu.stubs[GDS_ALLOC] = lambda e: scratch
    emu.stubs[GDS_FREE] = lambda e: 0
    emu.stubs[FINISH] = lambda e: fin.append((e.reg("eax"), e.reg("edx"))) or 0
    emu.stubs[NET_ERROR] = lambda e: net_err.append(e.reg("eax")) or 0
    watch = [(cursor, 4), (block_cnt, 4), (image, IMAGE_SIZE), (RELOC_STATE, 4),
             (unit_base, 0x47E0), (obj_base, 0xED8), (objmap, 0x4000)]
    return image, cursor, watch, blocks, fin, net_err, fp


def test_t4_save_write_image():
    """0x24bf0: the original and the compiled C build the same 0x109ee-byte
    image block for block (same header, same order, same rebased copies)."""
    rnd = random.Random(0x24BF0)
    emu = emu_mod()
    cm = _load(emu, REF_IMAGE)
    image, cursor, watch, blocks, fin, net_err, fp = _writer_world(emu, rnd)
    diffs = cemu.run_pair(emu, 0x24BF0, cm, "SaveWriteImage_", fp,
                          watch=watch, out_regs=())
    assert diffs == [], diffs
    assert len(blocks) % 2 == 0
    half = len(blocks) // 2
    assert [b[1] for b in blocks[:half]] == [b[1] for b in blocks[half:]]
    assert [b[2] for b in blocks[:half]] == [b[2] for b in blocks[half:]]
    assert fin == [(fp, 0), (fp, 0)], fin
    assert net_err == [], net_err
    # the image is exactly the documented size and starts with the header
    assert struct.unpack("<I", emu.read(cursor, 4))[0] == IMAGE_SIZE
    img = emu.read(image, IMAGE_SIZE)
    assert img[0:2] == b"C\x00"                   # the 0x43 'C' record word
    assert img[2:4] == emu.read(DAT_516AE, 2)      # second header word
    assert img[4:0x10] == emu.read(NET_ENEMY, 0xC)
    assert img[0x10:0x16] == emu.read(SEND_STATE, 6)
    assert img[0x16:0x566] == emu.read(NET_RING, 0x550)
    assert img[0x566:0x56A] == emu.read(RING_STATE, 4)
    assert img[0x56A:0x57E] == emu.read(PREFS, 0x14)
    assert img[0x57E:0x1136] == emu.read(SCENARIO, 0xBB8)
    assert img[0x1136:0x1336] == emu.read(GAME_STATE, 0x200)
    assert img[0x1336:0x3336] == emu.read(emu.u32(TILE_MAP), 0x2000)
    assert img[0x3336:0x5336] == emu.read(emu.u32(MAP_FLAGS), 0x2000)
    assert img[0x9336:0xB336] == emu.read(emu.u32(FOG_MAP), 0x2000)
    # the object map was rebased to offsets from unit_array (not copied)
    unit_base = emu.u32(UNIT_ARRAY)
    for cell in (0, 5, 0x40 * 7 + 9, 0x1000 - 1):
        got = struct.unpack("<i", img[0x5336 + 4 * cell:0x5336 + 4 * cell + 4])[0]
        old = struct.unpack("<i", emu.read(emu.u32(OBJECT_MAP) + 4 * cell, 4))[0]
        want = -1 if old == 0 else old - unit_base
        assert got == want, (cell, old, got)
    # and the unit records were rebased the same way (+0x3a of record 1)
    rec = img[0xB336 + 0x5C + 0x3A:0xB336 + 0x5C + 0x3E]
    old = struct.unpack("<i", emu.read(unit_base + 0x5C + 0x3A, 4))[0]
    assert struct.unpack("<i", rec)[0] == (-1 if old == 0 else old - unit_base)
    # the mode word was set for the record rebasing and the live state kept
    assert u16(emu, RELOC_STATE + 2) == 1


def test_t4_save_write_image_failure():
    """0x24bf0: a failed block aborts the image, reports the network error and
    finishes the slot with the error flag (both implementations)."""
    rnd = random.Random(0x24BF1)
    emu = emu_mod()
    cm = _load(emu, REF_IMAGE)
    # fail the 12th block (the unit array write, after two scratch blocks)
    image, cursor, watch, blocks, fin, net_err, fp = _writer_world(
        emu, rnd, fail_block=12)
    diffs = cemu.run_pair(emu, 0x24BF0, cm, "SaveWriteImage_", fp,
                          watch=watch, out_regs=())
    assert diffs == [], diffs
    assert fin == [(fp, 1), (fp, 1)], fin
    assert net_err == [0xE, 0xE], net_err
    assert len(blocks) == 2 * 12, len(blocks)
    # the failure comes after the unit block was copied and rebased, so the
    # partial image is 12 blocks long
    assert struct.unpack("<I", emu.read(cursor, 4))[0] < IMAGE_SIZE


# ---------------------------------------------------------------- structure

def test_block_order_and_image_size():
    """The writer's block list (from the call sites) sums to 0x109ee, which is
    what the loader accepts under the 0x11170 limit."""
    sizes = [2, 2, 0xC, 6, 0x550, 4, 0x14, 0xBB8, 0x200,
             0x2000, 0x2000, 0x4000, 0x2000, 0x47E0, 0xED8]
    assert sum(sizes) == IMAGE_SIZE
    assert 0x56A == sum(sizes[:6])        # the link header SaveStreamValidate skips
    prog = codegen_sweep.program()
    # SaveLoadImage's size limit (0x24949: cmp edx,0x11170)
    off = 0x24949 - prog.code.base
    assert prog.cbytes[off:off + 6] == b"\x81\xfa\x70\x11\x01\x00"


def test_unreferenced_block_at_0x24860():
    """0x24860 is data, not a function: discovery no longer starts a function
    there (2026-11-18 stack-balance veto), nothing references the block, and
    the decode is the XOR-0x64 text buffer plus 0x44 filler."""
    prog = codegen_sweep.program()
    starts = [f["start"] for f in prog.functions]
    assert 0x24860 not in starts
    base = prog.code.base
    block = prog.cbytes[0x24860 - base:0x248E0 - base]
    assert len(block) == 0x80
    text = bytes(b ^ 0x64 for b in block[:0x1A])
    assert text.startswith(b"warcraft\x00cd\x00version\x00")
    assert set(block[0x1A:]) == {0x44}
    for src, (fix, target) in prog.fix_at.items():
        assert not (0x24860 <= target < 0x248E0), (hex(src), hex(target))
    # the preceding function ends at 0x2485c and the next start is 0x248e0
    assert max(a for a in starts if a < 0x24860) == 0x247D0
    assert min(a for a in starts if a > 0x24860) == 0x248E0
