"""Parser for the 32-bit Linear Executable (LE) format as produced by
WATCOM wlink for DOS/4GW.

Reference: "IBM OS/2 16/32-bit Object Module Format (OMF) and Linear eXecutable
Module Format (LX)" plus the LE deviations (3-byte page numbers in the object
page table, explicit last-page size).
"""
import struct
from dataclasses import dataclass, field

HDR_FMT = "<2sBBIHHIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII"
HDR_NAMES = ("sig bo wo fmtlvl cpu os modver modflags npages eip_obj eip esp_obj esp "
             "pagesize lastpage fixupsize fixupcksum loadersize loadercksum objtab nobj "
             "objpagetab objiterpages rsrctab nrsrc resname entrytab moddir nmoddir "
             "fixpagetab fixrectab impmod nimpmod impproc perpagecksum datapages npreload "
             "nonresname nonreslen nonrescksum autods").split()

OBJ_READ, OBJ_WRITE, OBJ_EXEC, OBJ_BIG = 0x1, 0x2, 0x4, 0x2000

# Fixup source types (low nibble of the source byte).
SRC_BYTE, SRC_SEL16, SRC_PTR1616, SRC_OFF16, SRC_PTR1632, SRC_OFF32, SRC_REL32 = 0, 2, 3, 5, 6, 7, 8
SRC_NAMES = {0: "byte", 2: "sel16", 3: "ptr16:16", 5: "off16", 6: "ptr16:32", 7: "off32", 8: "rel32"}


@dataclass
class Obj:
    index: int        # 1-based
    vsize: int
    base: int         # preferred (relocation) base address
    flags: int
    page_index: int   # 1-based first entry in the object page table
    npages: int
    data: bytes = b""

    @property
    def is_code(self):
        return bool(self.flags & OBJ_EXEC)

    @property
    def end(self):
        return self.base + self.vsize


@dataclass
class Fixup:
    obj: int          # source object (1-based)
    src_off: int      # offset within source object of the patched field
    src_type: int
    target_obj: int   # 1-based
    target_off: int   # offset within target object (0 for selector fixups); may
                      # wrap (e.g. 0xFFFFFFFA = -6 for biased array bases)
    raw: bytes = field(default=b"", repr=False)

    @property
    def size(self):
        return {SRC_BYTE: 1, SRC_SEL16: 2, SRC_PTR1616: 4, SRC_OFF16: 2,
                SRC_PTR1632: 6, SRC_OFF32: 4, SRC_REL32: 4}[self.src_type]


class LE:
    def __init__(self, data: bytes):
        self.raw = data
        if data[:2] != b"MZ":
            raise ValueError("no MZ stub")
        self.hdr_off = struct.unpack_from("<I", data, 0x3C)[0]
        vals = struct.unpack_from(HDR_FMT, data, self.hdr_off)
        self.h = dict(zip(HDR_NAMES, vals))
        if self.h["sig"] != b"LE":
            raise ValueError("not an LE executable")
        self.stub = data[:self.hdr_off]
        self._parse_objects()
        self._parse_fixups()

    # -- header helpers ---------------------------------------------------
    def _t(self, field):
        return self.hdr_off + self.h[field]

    def _parse_objects(self):
        h = self.h
        ps = h["pagesize"]
        # LE object page table: 4 bytes/entry, page number is 3 bytes stored
        # high byte first, followed by a flags byte.
        self.page_map = []
        for i in range(h["npages"]):
            e = self.raw[self._t("objpagetab") + 4 * i:self._t("objpagetab") + 4 * i + 4]
            num = (e[0] << 16) | (e[1] << 8) | e[2]
            self.page_map.append((num, e[3]))
        self.objects = []
        for i in range(h["nobj"]):
            vsize, base, flags, pidx, npg, _ = struct.unpack_from(
                "<6I", self.raw, self._t("objtab") + 24 * i)
            o = Obj(i + 1, vsize, base, flags, pidx, npg)
            buf = bytearray()
            for p in range(pidx, pidx + npg):
                num, pflags = self.page_map[p - 1]
                if pflags != 0:
                    raise NotImplementedError(f"page flags {pflags:#x}")
                off = h["datapages"] + (num - 1) * ps
                size = h["lastpage"] if num == h["npages"] else ps
                buf += self.raw[off:off + size]
                if len(buf) % ps and p != pidx + npg - 1:
                    buf += bytes(ps - len(buf) % ps)
            # Zero-fill the remainder of the object (BSS, stack).
            o.file_size = len(buf)
            buf += bytes(max(0, vsize - len(buf)))
            o.data = bytes(buf[:max(vsize, len(buf))])
            self.objects.append(o)

    def _parse_fixups(self):
        h = self.h
        fpt = [struct.unpack_from("<I", self.raw, self._t("fixpagetab") + 4 * i)[0]
               for i in range(h["npages"] + 1)]
        rec_base = self._t("fixrectab")
        self.fixups = []
        page_to_obj = {}
        for o in self.objects:
            for k in range(o.npages):
                page_to_obj[o.page_index + k] = (o.index, k * h["pagesize"])
        for page in range(1, h["npages"] + 1):
            pos, end = rec_base + fpt[page - 1], rec_base + fpt[page]
            obj, page_off = page_to_obj[page]
            while pos < end:
                start = pos
                src, flg = self.raw[pos], self.raw[pos + 1]
                pos += 2
                if src & 0x20:
                    cnt = self.raw[pos]
                    pos += 1
                    offs = None
                else:
                    offs = [struct.unpack_from("<h", self.raw, pos)[0]]
                    pos += 2
                if flg & 3 != 0:
                    raise NotImplementedError(f"non-internal fixup flags {flg:#x}")
                if flg & 0x40:
                    tobj = struct.unpack_from("<H", self.raw, pos)[0]
                    pos += 2
                else:
                    tobj = self.raw[pos]
                    pos += 1
                stype = src & 0x0F
                if stype == SRC_SEL16:
                    toff = 0
                elif flg & 0x10:
                    toff = struct.unpack_from("<I", self.raw, pos)[0]
                    pos += 4
                else:
                    toff = struct.unpack_from("<H", self.raw, pos)[0]
                    pos += 2
                if flg & 0x04 or flg & 0x80 or flg & 0x20 or src & 0x10:
                    raise NotImplementedError(f"fixup src={src:#x} flags={flg:#x}")
                if offs is None:
                    offs = list(struct.unpack_from(f"<{cnt}h", self.raw, pos))
                    pos += 2 * cnt
                for so in offs:
                    self.fixups.append(Fixup(obj, page_off + so, stype, tobj, toff,
                                             self.raw[start:pos]))
        # A fixup that straddles a page boundary is recorded on both pages.
        seen = {}
        for f in self.fixups:
            seen.setdefault((f.obj, f.src_off), f)
        self.fixups_unique = sorted(seen.values(), key=lambda f: (f.obj, f.src_off))

    # -- address helpers --------------------------------------------------
    def obj(self, n):
        return self.objects[n - 1]

    @property
    def entry(self):
        return self.obj(self.h["eip_obj"]).base + self.h["eip"]

    @property
    def initial_esp(self):
        return self.obj(self.h["esp_obj"]).base + self.h["esp"]

    def obj_at(self, addr):
        for o in self.objects:
            if o.base <= addr < o.end:
                return o
        return None

    def loaded_image(self):
        """Return {obj_index: bytearray} with all fixups applied as if loaded
        at the preferred base addresses (flat model, selectors left as 0)."""
        img = {o.index: bytearray(o.data) for o in self.objects}
        for f in self.fixups_unique:
            buf = img[f.obj]
            tgt = (self.obj(f.target_obj).base + f.target_off) & 0xFFFFFFFF
            if f.src_type == SRC_OFF32:
                struct.pack_into("<I", buf, f.src_off, tgt)
            elif f.src_type == SRC_REL32:
                src = self.obj(f.obj).base + f.src_off + 4
                struct.pack_into("<i", buf, f.src_off, tgt - src)
            elif f.src_type == SRC_PTR1632:
                struct.pack_into("<I", buf, f.src_off, tgt)
            elif f.src_type == SRC_OFF16:
                struct.pack_into("<H", buf, f.src_off, tgt & 0xFFFF)
            elif f.src_type == SRC_SEL16:
                pass
            else:
                raise NotImplementedError(SRC_NAMES.get(f.src_type, f.src_type))
        return img

    def read(self, addr, n, image=None):
        o = self.obj_at(addr)
        if o is None:
            raise KeyError(hex(addr))
        src = image[o.index] if image else o.data
        off = addr - o.base
        return bytes(src[off:off + n])


def load(path=None):
    from . import ORIGINAL_EXE
    with open(path or ORIGINAL_EXE, "rb") as f:
        return LE(f.read())
