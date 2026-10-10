"""DATA.WAR archive reader and LZSS decoder (re-implementation of war.exe's
resource library; see docs/formats/war_archive.md for the evidence).

Archive layout (little-endian):

    u32 version            must equal the value main() stores in 0x55824 (0x18)
    u32 count              number of entries
    u32 offset[count]      file offset of each entry, 0xFFFFFFFF = absent
                           (war.exe reports 'demo failure %d' for those)
    entry at offset[i]:
        u32 header         bits 0..28 unpacked size, bits 29..31 codec id
                           (0 = stored, 1 = LZSS)
        ...                payload

Game code addresses entries by *resource id* = archive index + 2
(fn_3452c subtracts 2 before indexing the offset table).

Only DATA.WAR is such an archive. The other *.WAR files on the CD (intros,
briefings, win/lose animations) are plain FLC animations (magic 0xAF12 at
offset 4) opened by a different routine (0x1933c).

    python3 -m wc1.resources_war list [FILE]
    python3 -m wc1.resources_war extract [FILE] [OUTDIR]   (default build/resources/data)
"""
import os
import struct
import sys

from . import path

DATA_WAR = path("original", "cd", "files", "DATA", "DATA.WAR")
VERSION = 0x18          # main() at 0x1e15e: mov [0x55824], 0x18
ID_BIAS = 2             # fn_3452c: index = id - 2
METHOD_STORED, METHOD_LZSS = 0, 1
FLC_MAGIC = 0xAF12


class WarError(Exception):
    pass


def lzss_decode(src, size, pos=0):
    """Decode `size` bytes of LZSS data starting at src[pos]. Returns
    (data, bytes_consumed). Mirrors fn_41550 (state reset by fn_417cc):

    * 4096-byte ring buffer, zero-filled, write position starts at 0
    * a flag byte governs the next 8 items, LSB first; bit 1 = literal byte,
      bit 0 = 16-bit little-endian match word: offset = w & 0xFFF (absolute
      ring position), length = (w >> 12) + 3
    * match bytes are copied one at a time (overlap allowed), each byte is
      also stored into the ring at the write position
    * decoding stops as soon as `size` bytes were produced (a match may be cut)
    """
    ring = bytearray(0x1000)
    r = 0
    out = bytearray()
    i = pos
    n = len(src)
    flags = 0
    while len(out) < size:
        flags >>= 1
        if not flags & 0x100:
            if i >= n:
                raise WarError("LZSS input exhausted (flags)")
            flags = src[i] | 0xFF00
            i += 1
        if flags & 1:
            if i >= n:
                raise WarError("LZSS input exhausted (literal)")
            c = src[i]
            i += 1
            ring[r] = c
            out.append(c)
            r = (r + 1) & 0xFFF
        else:
            if i + 1 >= n:
                raise WarError("LZSS input exhausted (match)")
            w = src[i] | (src[i + 1] << 8)
            i += 2
            off = w & 0xFFF
            for _ in range((w >> 12) + 3):
                c = ring[off]
                ring[r] = c
                out.append(c)
                r = (r + 1) & 0xFFF
                off = (off + 1) & 0xFFF
                if len(out) == size:
                    break
    return bytes(out), i - pos


def lzss_encode(data):
    """A simple greedy encoder producing streams lzss_decode accepts (used to
    build synthetic difftest inputs; not the original compressor)."""
    ring = bytearray(0x1000)
    r = 0
    out = bytearray()
    i = 0
    while i < len(data):
        flagpos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= len(data):
                break
            best_len, best_off = 0, 0
            maxlen = min(18, len(data) - i)
            if maxlen >= 3:
                # simulate the decoder's ring to find a match (incl. overlap)
                for off in range(0x1000):
                    if ring[off] != data[i]:
                        continue
                    ln = 0
                    tmp = {}
                    rr, oo = r, off
                    while ln < maxlen:
                        c = tmp.get(oo, ring[oo])
                        if c != data[i + ln]:
                            break
                        tmp[rr] = c
                        rr = (rr + 1) & 0xFFF
                        oo = (oo + 1) & 0xFFF
                        ln += 1
                    if ln > best_len:
                        best_len, best_off = ln, off
                        if ln == maxlen:
                            break
            if best_len >= 3:
                w = best_off | ((best_len - 3) << 12)
                out += bytes((w & 0xFF, w >> 8))
                off = best_off
                for _ in range(best_len):
                    ring[r] = ring[off]
                    r = (r + 1) & 0xFFF
                    off = (off + 1) & 0xFFF
                i += best_len
            else:
                flags |= 1 << bit
                out.append(data[i])
                ring[r] = data[i]
                r = (r + 1) & 0xFFF
                i += 1
        out[flagpos] = flags
    return bytes(out)


class Entry:
    def __init__(self, index, offset, end, header):
        self.index = index
        self.id = index + ID_BIAS
        self.offset = offset
        self.end = end              # next entry's offset (or file size)
        self.header = header
        self.method = header >> 29
        self.size = header & 0x1FFFFFFF
        self.stored = end - offset - 4

    def __repr__(self):
        return (f"Entry({self.index}, id={self.id}, off={self.offset:#x}, method={self.method}, "
                f"size={self.size}, stored={self.stored})")


class WarArchive:
    def __init__(self, filename=DATA_WAR):
        with open(filename, "rb") as f:
            self.raw = f.read()
        d = self.raw
        if len(d) >= 6 and struct.unpack_from("<H", d, 4)[0] == FLC_MAGIC:
            raise WarError(f"{filename}: a FLC animation, not a resource archive")
        self.version, self.count = struct.unpack_from("<II", d, 0)
        if self.version != VERSION:
            raise WarError(f"{filename}: version {self.version:#x} != {VERSION:#x}")
        self.offsets = list(struct.unpack_from(f"<{self.count}I", d, 8))
        self.entries = []
        present = sorted(o for o in self.offsets if o != 0xFFFFFFFF)
        nxt = {o: (present[k + 1] if k + 1 < len(present) else len(d)) for k, o in enumerate(present)}
        for i, o in enumerate(self.offsets):
            if o == 0xFFFFFFFF:
                self.entries.append(None)
                continue
            self.entries.append(Entry(i, o, nxt[o], struct.unpack_from("<I", d, o)[0]))

    def entry(self, index):
        return self.entries[index]

    def payload(self, index):
        e = self.entries[index]
        return self.raw[e.offset + 4:e.end]

    def read(self, index):
        """Unpacked contents of entry `index` (archive index, not resource id)."""
        e = self.entries[index]
        if e is None:
            raise WarError(f"entry {index} absent")
        p = self.payload(index)
        if e.method == METHOD_STORED:
            if len(p) < e.size:
                raise WarError(f"entry {index}: stored payload shorter than header size")
            return p[:e.size]
        if e.method == METHOD_LZSS:
            data, _ = lzss_decode(p, e.size)
            return data
        raise WarError(f"entry {index}: unknown codec {e.method}")


def guess_kind(data):
    """Cheap content classifier for listings (heuristic, not evidence)."""
    if len(data) == 768 and max(data) < 64:
        return "palette(6-bit)"
    if len(data) >= 6 and struct.unpack_from("<H", data, 4)[0] == FLC_MAGIC:
        return "flc"
    if data[:4] == b"RIFF":
        return "riff"
    if data[:4] == b"FORM":
        return "xmi"
    if data[:20] == b"Creative Voice File\x1a":
        return "voc"
    return ""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("list", "extract"):
        print(__doc__)
        return 2
    cmd = argv.pop(0)
    fn = argv.pop(0) if argv else DATA_WAR
    war = WarArchive(fn)
    if cmd == "list":
        print(f"version {war.version:#x}, {war.count} entries")
        for e in war.entries:
            if e is None:
                continue
            data = war.read(e.index)
            print(f"{e.index:4d} id={e.id:4d} off={e.offset:#9x} m={e.method} size={e.size:8d} "
                  f"stored={e.stored:8d} {guess_kind(data)}")
    else:
        out = argv.pop(0) if argv else path("build", "resources", "data")
        os.makedirs(out, exist_ok=True)
        for e in war.entries:
            if e is None:
                continue
            with open(os.path.join(out, f"{e.index:03d}.bin"), "wb") as f:
                f.write(war.read(e.index))
        print(f"extracted {sum(e is not None for e in war.entries)} entries to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
