"""Minimal Intel OMF-86/386 reader for Watcom objects and libraries.

Enough to recover, per module: segments with their data, public symbols,
external names and fixups (location, kind, target, addend). Used to compare
compiled C against the original binary and to fingerprint library code.
"""
import struct
from dataclasses import dataclass, field

LOC_NAMES = {0: "lobyte", 1: "off16", 2: "base16", 3: "ptr16:16", 4: "hibyte",
             5: "off16", 9: "off32", 11: "ptr16:32", 13: "off32"}


@dataclass
class Segment:
    name: str
    cls: str
    align: int
    length: int
    data: bytearray = field(default_factory=bytearray)
    fixups: list = field(default_factory=list)   # Fixup


@dataclass
class Fixup:
    offset: int        # within segment
    loc: int           # location type (9 = off32)
    self_rel: bool     # True for call/jmp rel32
    target_kind: str   # "seg" | "grp" | "ext"
    target: object     # segment index / group name / extern name
    disp: int          # explicit displacement (0 if carried in data)

    @property
    def size(self):
        return {0: 1, 1: 2, 2: 2, 3: 4, 4: 1, 5: 2, 9: 4, 11: 6, 13: 4}[self.loc]


@dataclass
class Module:
    name: str = ""
    segments: list = field(default_factory=list)      # index 1-based via segments[i-1]
    groups: dict = field(default_factory=dict)        # index -> name
    externs: list = field(default_factory=list)       # 1-based
    publics: dict = field(default_factory=dict)       # name -> (segidx, offset)
    statics: dict = field(default_factory=dict)       # LPUBDEF: name -> (segidx, offset)
    comdefs: dict = field(default_factory=dict)       # name -> size

    def seg(self, name):
        for i, s in enumerate(self.segments, 1):
            if s.name == name:
                return i, s
        return None, None


def _idx(b, p):
    v = b[p]
    if v & 0x80:
        return ((v & 0x7F) << 8) | b[p + 1], p + 2
    return v, p + 1


def _name(b, p):
    n = b[p]
    return b[p + 1:p + 1 + n].decode("latin-1"), p + 1 + n


def parse_module(buf, start=0):
    """Parse one module starting at buf[start]; returns (Module, end_offset)."""
    m = Module()
    lnames = [None]
    p = start
    last_data = None   # (segment, offset) of the preceding LEDATA/LIDATA
    threads = {("T", i): None for i in range(4)}
    threads.update({("F", i): None for i in range(4)})
    while p < len(buf):
        rtype = buf[p]
        rlen = struct.unpack_from("<H", buf, p + 1)[0]
        body = buf[p + 3:p + 3 + rlen - 1]
        p += 3 + rlen
        is32 = rtype & 1
        base = rtype & ~1
        if rtype == 0x80:
            m.name, _ = _name(body, 0)
        elif base == 0x8A:  # MODEND
            return m, p
        elif rtype == 0x96:  # LNAMES
            q = 0
            while q < len(body):
                n, q = _name(body, q)
                lnames.append(n)
        elif base == 0x98:  # SEGDEF
            attr = body[0]
            q = 1
            align = attr >> 5
            if align == 0:
                q += 3
            if is32:
                length = struct.unpack_from("<I", body, q)[0]
                q += 4
            else:
                length = struct.unpack_from("<H", body, q)[0]
                q += 2
            if attr & 2 and not is32:  # big
                length = 0x10000
            ni, q = _idx(body, q)
            ci, q = _idx(body, q)
            m.segments.append(Segment(lnames[ni], lnames[ci], align, length,
                                      bytearray(length)))
        elif rtype == 0x9A:  # GRPDEF
            ni, _ = _idx(body, 0)
            m.groups[len(m.groups) + 1] = lnames[ni]
        elif rtype in (0x8C, 0xB4):  # EXTDEF / LEXTDEF
            q = 0
            while q < len(body):
                n, q = _name(body, q)
                _, q = _idx(body, q)
                m.externs.append(n)
        elif rtype == 0xBC:  # CEXTDEF
            q = 0
            while q < len(body):
                li, q = _idx(body, q)
                _, q = _idx(body, q)
                m.externs.append(lnames[li])
        elif base in (0x90, 0xB6):  # PUBDEF / LPUBDEF
            gi, q = _idx(body, 0)
            si, q = _idx(body, q)
            if si == 0:
                q += 2
            while q < len(body):
                n, q = _name(body, q)
                if is32:
                    off = struct.unpack_from("<I", body, q)[0]
                    q += 4
                else:
                    off = struct.unpack_from("<H", body, q)[0]
                    q += 2
                _, q = _idx(body, q)
                (m.publics if base == 0x90 else m.statics)[n] = (si, off)
        elif rtype == 0xB0:  # COMDEF
            q = 0
            while q < len(body):
                n, q = _name(body, q)
                _, q = _idx(body, q)
                dt = body[q]
                q += 1

                def leaf(q):
                    v = body[q]
                    if v < 0x80:
                        return v, q + 1
                    k = {0x81: 2, 0x84: 3, 0x88: 4}[v]
                    return int.from_bytes(body[q + 1:q + 1 + k], "little"), q + 1 + k
                if dt == 0x61:
                    a, q = leaf(q)
                    b, q = leaf(q)
                    size = a * b
                else:
                    size, q = leaf(q)
                m.comdefs[n] = size
                m.externs.append(n)
        elif base == 0xA0:  # LEDATA
            si, q = _idx(body, 0)
            if is32:
                off = struct.unpack_from("<I", body, q)[0]
                q += 4
            else:
                off = struct.unpack_from("<H", body, q)[0]
                q += 2
            seg = m.segments[si - 1]
            d = body[q:]
            if len(seg.data) < off + len(d):
                seg.data.extend(bytes(off + len(d) - len(seg.data)))
            seg.data[off:off + len(d)] = d
            last_data = (seg, off)
        elif base == 0xA2:  # LIDATA
            si, q = _idx(body, 0)
            if is32:
                off = struct.unpack_from("<I", body, q)[0]
                q += 4
            else:
                off = struct.unpack_from("<H", body, q)[0]
                q += 2
            seg = m.segments[si - 1]

            def expand(q):
                if is32:
                    rep = struct.unpack_from("<I", body, q)[0]
                    q += 4
                else:
                    rep = struct.unpack_from("<H", body, q)[0]
                    q += 2
                blk = struct.unpack_from("<H", body, q)[0]
                q += 2
                if blk == 0:
                    n = body[q]
                    out = bytes(body[q + 1:q + 1 + n])
                    q += 1 + n
                else:
                    out = b""
                    for _ in range(blk):
                        part, q = expand(q)
                        out += part
                return out * rep, q
            out, q = b"", q
            while q < len(body):
                part, q = expand(q)
                out += part
            if len(seg.data) < off + len(out):
                seg.data.extend(bytes(off + len(out) - len(seg.data)))
            seg.data[off:off + len(out)] = out
            last_data = (seg, off)
        elif base == 0x9C:  # FIXUPP
            q = 0
            while q < len(body):
                b0 = body[q]
                if not b0 & 0x80:  # THREAD
                    d = b0 & 0x40
                    method = (b0 >> 2) & 7
                    num = b0 & 3
                    q += 1
                    idx = None
                    if d == 0 or method < 3:
                        idx, q = _idx(body, q)
                    threads[("F" if d else "T", num)] = (method, idx)
                    continue
                locat = (b0 << 8) | body[q + 1]
                q += 2
                self_rel = not (locat & 0x4000)
                loc = (locat >> 10) & 0xF
                doff = locat & 0x3FF
                fd = body[q]
                q += 1
                if fd & 0x80:
                    fmethod, fidx = threads[("F", (fd >> 4) & 3)]
                else:
                    fmethod = (fd >> 4) & 7
                    fidx = None
                    if fmethod < 3:
                        fidx, q = _idx(body, q)
                if fd & 0x08:
                    tmethod, tidx = threads[("T", fd & 3)]
                    tmethod |= fd & 0x04
                else:
                    tmethod = fd & 7
                    tidx, q = _idx(body, q)
                disp = 0
                if not (tmethod & 4):
                    if is32:
                        disp = struct.unpack_from("<I", body, q)[0]
                        q += 4
                    else:
                        disp = struct.unpack_from("<H", body, q)[0]
                        q += 2
                tm = tmethod & 3
                if tm == 0:
                    kind, tgt = "seg", tidx
                elif tm == 1:
                    kind, tgt = "grp", m.groups.get(tidx)
                elif tm == 2:
                    kind, tgt = "ext", m.externs[tidx - 1]
                else:
                    kind, tgt = "frame", tidx
                seg, base_off = last_data
                seg.fixups.append(Fixup(base_off + doff, loc, self_rel, kind, tgt, disp))
        # COMENT, LINNUM, COMDAT etc. are ignored
    return m, p


def parse_object(path):
    with open(path, "rb") as f:
        buf = f.read()
    m, _ = parse_module(buf)
    return m


def parse_library(path):
    """Yield every module of an OMF library (.lib)."""
    with open(path, "rb") as f:
        buf = f.read()
    if buf[0] != 0xF0:
        raise ValueError("not an OMF library")
    page = struct.unpack_from("<H", buf, 1)[0] + 3
    p = page
    while p < len(buf) and buf[p] == 0x80:
        m, end = parse_module(buf, p)
        yield m
        p = (end + page - 1) // page * page
        while p < len(buf) and buf[p] == 0:
            p += page
        if p < len(buf) and buf[p] == 0xF1:
            break
