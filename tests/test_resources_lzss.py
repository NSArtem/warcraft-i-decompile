"""T4 difftest: war.exe's own archive code vs tools/wc1/resources_war.py.

The original OpenArchive (0x34480), ResourceBegin (0x31870), ResourceRead
(0x32740), LzssReset (0x417cc), LzssDecode (0x41550) and StoredRead (0x409a0)
run under Unicorn on the real DATA.WAR; only stdio (fseek/fread/slow getc) and
malloc are Python models (tools/wc1/resources_emu.py).
"""
import os
import random
import struct

import pytest

from wc1 import path

DATA = path("original", "cd", "files", "DATA", "DATA.WAR")
pytestmark = pytest.mark.skipif(
    not (os.path.exists(path("original", "install", "war.exe")) and os.path.exists(DATA)),
    reason="original files not extracted")


@pytest.fixture(scope="module")
def war():
    from wc1.resources_war import WarArchive
    return WarArchive(DATA)


def sample(war):
    lz = sorted((e.size, e.index) for e in war.entries if e.method == 1)
    st = sorted((e.size, e.index) for e in war.entries if e.method == 0)
    pick = set()
    pick.update(i for _, i in lz[:3])                 # 12-byte entries (shorter than one flag group)
    pick.update(i for _, i in lz[-3:])                # largest compressed (99855 bytes)
    pick.update(i for _, i in lz[len(lz) // 2 - 2:len(lz) // 2 + 2])
    pick.update(i for s, i in lz if s == 64004 and i in (261, 456))   # full-screen 64000+4 images
    pick.update((0, 1, 2, 3, war.count - 1))
    pick.update(i for _, i in st[:2] + st[-2:])      # stored: smallest, largest
    pick.add(war.count - 1)
    rnd = random.Random(1)
    pick.update(rnd.sample([e.index for e in war.entries if e.method == 1 and e.size < 40000], 12))
    return sorted(pick)


def test_open_archive_matches_python(war):
    from wc1.resources_emu import ArchiveEmu
    a = ArchiveEmu(war.raw)
    assert a.open() == war.count
    e = a.emu
    table = struct.unpack(f"<{war.count}I", e.read(e.u32(0x55828), 4 * war.count))
    assert list(table) == war.offsets


@pytest.mark.parametrize("inline", [False, True], ids=["slowpath", "inline-getc"])
def test_original_decoder_matches_python(war, inline):
    from wc1.resources_emu import ArchiveEmu
    a = ArchiveEmu(war.raw, getc_inline=inline)
    a.open()
    idx = sample(war)
    if inline:
        idx = idx[::3]                               # same code, different input path: fewer
    n_lz = 0
    for i in idx:
        ent = war.entries[i]
        data, packed, codec = a.read_resource(ent.id)
        assert codec == ent.method, ent
        assert len(data) == ent.size, ent
        assert data == war.read(i), f"entry {i} differs"
        if i != war.count - 1:
            # ResourceSeek result: next - start + 1. For the last entry the original
            # reads table[count], one dword past the malloc'd table (garbage), so
            # that value is not defined; the data itself does not depend on it.
            assert packed == ent.end - ent.offset + 1, ent
        n_lz += codec == 1
    assert n_lz >= 8 and len(idx) >= 10
    print(f"{len(idx)} entries ({n_lz} LZSS) identical, inline={inline}")


def test_chunked_decode_keeps_state(war):
    """LzssDecode may be called repeatedly on one stream, even in the middle of a match."""
    from wc1.resources_emu import ArchiveEmu
    a = ArchiveEmu(war.raw)
    a.open()
    rnd = random.Random(7)
    done = 0
    for i in [e.index for e in war.entries if e.method == 1 and 3000 < e.size < 30000][:6]:
        ent = war.entries[i]
        chunks = [rnd.choice((1, 2, 3, 5, 17, 100, 1000)) for _ in range(400)]
        data, _, _ = a.read_resource(ent.id, chunks=chunks)
        assert data == war.read(i), f"entry {i} differs when chunked"
        done += 1
    assert done == 6


def test_absent_entry_is_fatal(war):
    """An 0xFFFFFFFF offset makes ResourceSeek print 'demo failure %d' (0x57f48)."""
    from wc1.emu import EmuError
    from wc1.resources_emu import ArchiveEmu
    raw = bytearray(war.raw)
    struct.pack_into("<I", raw, 8 + 4 * 5, 0xFFFFFFFF)       # entry 5 -> resource id 7
    a = ArchiveEmu(bytes(raw))
    a.open()
    with pytest.raises(EmuError):
        a.read_resource(7)
    assert a.errors and a.errors[0] == b"demo failure %d"


def test_version_mismatch_is_fatal(war):
    from wc1.emu import EmuError
    from wc1.resources_emu import ArchiveEmu
    raw = bytearray(war.raw)
    struct.pack_into("<I", raw, 0, 0x17)
    a = ArchiveEmu(bytes(raw))
    with pytest.raises(EmuError):
        a.open()
    assert a.errors and a.errors[0].startswith(b"You do not have the correct data file version")


def test_lzss_python_roundtrip_is_decodable():
    """Synthetic data goes through resources_war.lzss_encode/decode (no game files needed)."""
    from wc1.resources_war import lzss_decode, lzss_encode
    rnd = random.Random(3)
    blob = bytes(rnd.choice(b"abcd\0\xff") for _ in range(5000)) + bytes(300)
    assert lzss_decode(lzss_encode(blob), len(blob))[0] == blob


# ---------------------------------------------------------------------------
# T4 of the reconstructed reference C (wc1.cemu): the compiled C and the
# original run on the same inputs.  Evidence named by ref_verified_by in
# analysis/symbols/resources.toml.  The C is src/resources/{lzss,codec}.c.

LZSS_REF = path("src", "resources", "lzss.c")
CODEC_REF = path("src", "resources", "codec.c")
LZSS_RING, LZSS_SRC, LZSS_POS = 0x5677C, 0x635D0, 0x635D2
LZSS_LEFT, LZSS_FLAGS, RES_REMAIN = 0x635D4, 0x635D6, 0x5AD40
CODEC_TABLE = 0x56524
STUB_ALLOC, STUB_FREE = 0x0FFF0800, 0x0FFF0900   # mapped scratch addresses


def load_lzss(emu):
    from wc1 import cemu
    return cemu.load(emu, LZSS_REF)


def test_lzss_reset_c_matches_original():
    """0x417cc: same zeroing of the flag/match/ring-index words and the
    4096-byte window."""
    from wc1 import cemu
    from wc1.emu import Emu
    emu = Emu()
    cm = load_lzss(emu)
    ring = emu.alloc(0x1000)
    emu.put_u32(LZSS_RING, ring)
    for _ in range(4):
        emu.write(ring, bytes((i * 7) & 0xFF for i in range(0x1000)))
        emu.write(LZSS_SRC, struct.pack("<H", 0x0123))
        emu.write(LZSS_POS, struct.pack("<H", 0x0ABC))
        emu.write(LZSS_LEFT, struct.pack("<H", 0x0007))
        emu.write(LZSS_FLAGS, struct.pack("<H", 0xFF01))
        diffs = cemu.run_pair(emu, 0x417CC, cm, "LzssReset_",
                              watch=[(ring, 0x1000), (LZSS_SRC, 8)], out_regs=())
        assert diffs == [], diffs
        emu.write(LZSS_RING, struct.pack("<I", ring))    # restore the pointer too


def test_lzss_free_ring_c_matches_original():
    """0x41800: GdsFree(the same window), then zero the pointer."""
    from wc1 import cemu
    from wc1.emu import Emu
    emu = Emu()
    cm = load_lzss(emu)
    ring = emu.alloc(0x1000)
    emu.put_u32(LZSS_RING, ring)
    freed = []
    emu.stubs[0x32780] = lambda e: freed.append(e.reg("eax")) or 0   # GdsFree
    diffs = cemu.run_pair(emu, 0x41800, cm, "LzssFreeRing_",
                          watch=[(LZSS_RING, 4)], out_regs=())
    assert diffs == [], diffs
    assert len(freed) == 2 and freed[0] == freed[1] == ring


def test_register_codec_c_matches_original():
    """0x3b980: same 17-byte descriptor copy into the table slot, same alloc
    call and same atexit registration."""
    from wc1 import cemu
    from wc1.emu import Emu
    emu = Emu()
    cm = cemu.load(emu, CODEC_REF)
    desc = emu.alloc(17)
    emu.write(desc, bytes([5]) + struct.pack("<4I", STUB_ALLOC, 0x415CC, 0x41550,
                                             STUB_FREE))
    alloc_calls, atexit_calls = [], []
    emu.stubs[STUB_ALLOC] = lambda e: alloc_calls.append(1) or 0
    emu.stubs[0x342B0] = lambda e: atexit_calls.append(e.reg("eax")) or 0
    slot = CODEC_TABLE + 5 * 17
    diffs = cemu.run_pair(emu, 0x3B980, cm, "RegisterCodec_", desc,
                          watch=[(slot, 17 * 3)], out_regs=())
    assert diffs == [], diffs
    assert emu.read(slot, 17) == bytes([5]) + struct.pack("<4I", STUB_ALLOC, 0x415CC,
                                                          0x41550, STUB_FREE)
    assert len(alloc_calls) == 2                        # once per run
    assert len(atexit_calls) == 2 and atexit_calls[0] == atexit_calls[1] == STUB_FREE


def _decode_entry(a, cm, index, chunks=None):
    """ResourceBegin (original) positions the stream and resets the decoder;
    then the original or the compiled C decodes it.  Returns everything the
    T4 comparison looks at."""
    from wc1.resources_emu import RES_BEGIN
    e = a.emu
    ent = a.war_entries[index] if hasattr(a, "war_entries") else None
    raise AssertionError("use the helper below")


def _run_decode(a, cm, ent, addr, chunks=None):
    """Decode one resource through `addr` (original or compiled C)."""
    from wc1.resources_emu import RES_BEGIN
    e = a.emu
    lenp = e.alloc(4)
    size = e.call(RES_BEGIN, ent.id, lenp)          # re-seeks, resets decode state
    assert size == ent.size
    dest = e.alloc(size + 16)
    e.write(dest, b"\xEE" * size)
    if chunks is None:
        e.call(addr, dest, size)
    else:
        done = 0
        for c in chunks:
            c = min(c, size - done)
            if c <= 0:
                break
            e.call(addr, dest + done, c)
            done += c
        if done < size:
            e.call(addr, dest + done, size - done)
    state = e.read(0x635D0, 8) + struct.pack("<I", e.u32(RES_REMAIN))
    ring = e.read(e.u32(LZSS_RING), 0x1000)
    return e.read(dest, size), state, ring, a.pos


def test_lzss_decode_c_matches_original(war):
    """0x41550: the compiled decoder and the original produce the same bytes
    from the same archive stream (real DATA.WAR entries; fixed window sizes
    keep the check quick)."""
    from wc1 import cemu
    from wc1.resources_emu import ArchiveEmu, LZSS_DECODE
    rnd = random.Random(11)
    a = ArchiveEmu(war.raw)
    a.open()
    cm = load_lzss(a.emu)
    lz = [e for e in war.entries if e.method == 1 and 200 < e.size < 20000]
    for ent in [lz[0], lz[len(lz) // 2], lz[-1]]:
        got_o = _run_decode(a, cm, ent, LZSS_DECODE)
        got_c = _run_decode(a, cm, ent, cm.fn("LzssDecode_"))
        assert got_o == got_c, f"entry {ent.index} differs between original and C"
        assert got_o[0] == war.read(ent.index)
    # a match split across calls: same chunks for both, state must carry
    ent = lz[len(lz) // 3]
    chunks = [rnd.choice((1, 2, 3, 5, 17, 100)) for _ in range(60)]
    got_o = _run_decode(a, cm, ent, LZSS_DECODE, chunks)
    got_c = _run_decode(a, cm, ent, cm.fn("LzssDecode_"), chunks)
    assert got_o == got_c, f"chunked entry {ent.index} differs"
    assert got_o[0] == war.read(ent.index)


def test_resource_seek_c_matches_original(war):
    """0x3452c: same table lookup, same FileSeek offset and same returned
    compressed length; an absent entry is fatal in both."""
    from wc1 import cemu
    from wc1.emu import EmuError
    from wc1.resources_emu import ArchiveEmu
    a = ArchiveEmu(war.raw)
    a.open()
    cm = cemu.load(a.emu, path("src", "resources", "war.c"))
    ids = [e.id for e in war.entries[:4]] + [war.entries[len(war.entries) // 2].id,
                                            war.entries[-2].id]
    for rid in ids:
        def run(addr):
            a.pos = 0
            a._sync_file()
            try:
                return ("ok", a.emu.call(addr, rid), a.pos)
            except EmuError as ex:
                return ("fatal", str(ex), a.pos)
        assert run(0x3452C) == run(cm.fn("ResourceSeek_")), hex(rid)
    # absent entry: the same 'demo failure %d' fatal in both
    raw = bytearray(war.raw)
    struct.pack_into("<I", raw, 8 + 4 * 5, 0xFFFFFFFF)
    b = ArchiveEmu(bytes(raw))
    b.open()
    cm2 = cemu.load(b.emu, path("src", "resources", "war.c"))
    def run2(addr):
        b.errors.clear()
        b.pos = 0
        b._sync_file()
        try:
            b.emu.call(addr, 7)
        except EmuError:
            return b.errors[:]
        raise AssertionError("absent entry must be fatal")
    assert run2(0x3452C) == run2(cm2.fn("ResourceSeek_")) == [b"demo failure %d"]
