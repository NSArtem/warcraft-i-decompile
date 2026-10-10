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
