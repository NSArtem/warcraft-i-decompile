"""Patch segment attributes of an OMF object (used by wc1.build).

The in-place build links each compiled C object at the original address of
its functions, between asm pieces.  wcc386 gives `_TEXT` PARA and the data
segments DWORD alignment; the original object may sit at any address (a run of
functions inside a module), so the build sets every segment of the object to
BYTE alignment (the asm pieces carry the exact padding bytes), and renames a
data segment when the original placed that data in a differently named
segment (see docs/subsystems/build.md).
"""
import struct

from .omf import _idx, _name

ALIGN = {"abs": 0, "byte": 1, "word": 2, "para": 3, "page": 4, "dword": 5}


def _records(buf):
    p = 0
    while p < len(buf):
        t = buf[p]
        n = struct.unpack_from("<H", buf, p + 1)[0]
        yield t, bytearray(buf[p + 3:p + 3 + n - 1])
        p += 3 + n


def _pack(t, body):
    rec = bytearray([t]) + struct.pack("<H", len(body) + 1) + body
    rec.append((-sum(rec)) & 0xFF)
    return bytes(rec)


def _has_thread(body, is32):
    """True if a FIXUPP body contains a THREAD subrecord."""
    q = 0
    while q < len(body):
        b = body[q]
        if not b & 0x80:                     # THREAD
            return True
        q += 2                               # locat
        fd = body[q]
        q += 1
        if not fd & 0x80 and (fd >> 4) & 7 < 3:      # explicit frame with datum
            _, q = _idx(body, q)
        if not fd & 0x08:                            # explicit target
            _, q = _idx(body, q)
        if not fd & 0x04:                            # displacement present
            q += 4 if is32 else 2
    return False


def patch(src, dst, align="byte", rename=None, empty=()):
    """Copy object `src` to `dst`, setting every segment's alignment to `align`,
    renaming segments {old_name: new_name} and making the segments named in
    `empty` zero-length (their LEDATA/LIDATA and the FIXUPPs that follow are
    dropped: relocations against them then resolve to whatever the link puts
    at that position).  A renamed segment's LNAMES entry must not be shared
    with another use (true for Watcom's CONST/_DATA)."""
    rename = rename or {}
    recs = list(_records(open(src, "rb").read()))
    lnames = [None]                     # index -> (record no, name)
    for k, (t, body) in enumerate(recs):
        if t == 0x96:
            q = 0
            while q < len(body):
                n, q = _name(body, q)
                lnames.append((k, n))
    seg_names = []
    for k, (t, body) in enumerate(recs):
        if t & ~1 != 0x98:
            continue
        a = body[0] >> 5
        if a == 0:
            raise ValueError(f"{src}: absolute segment not supported")
        body[0] = (body[0] & 0x1F) | (ALIGN[align] << 5)
        q = 1 + (4 if t & 1 else 2)
        ni, _ = _idx(body, q)
        seg_names.append(ni)
        if lnames[ni][1] in empty:
            body[1:q] = bytes(q - 1)
    for old, new in rename.items():
        idx = [i for i in seg_names if lnames[i][1] == old]
        if len(idx) != 1:
            raise ValueError(f"{src}: segment {old!r} defined {len(idx)} times")
        uses = sum(1 for _, n in lnames[1:] if n == old)
        if uses != 1:
            raise ValueError(f"{src}: name {old!r} is used {uses} times in LNAMES")
        k, _ = lnames[idx[0]]
        t, body = recs[k]
        out, q = bytearray(), 0
        while q < len(body):
            n, q2 = _name(body, q)
            out += bytes([len(new)]) + new.encode() if n == old else body[q:q2]
            q = q2
        recs[k] = (t, out)
    drop_segs = {k for k, ni in enumerate(seg_names, 1) if lnames[ni][1] in empty}
    if len(drop_segs) != len(set(empty)):
        raise ValueError(f"{src}: cannot find every segment of {sorted(empty)}")
    kept, dropping = [], False
    for t, body in recs:
        if t & ~1 in (0xA0, 0xA2):
            si, _ = _idx(body, 0)
            dropping = si in drop_segs
            if dropping:
                continue
        elif t & ~1 == 0x9C and dropping:
            if _has_thread(body, t & 1):
                raise ValueError(f"{src}: THREAD subrecord in a dropped FIXUPP")
            continue
        elif t & ~1 != 0x9C:
            dropping = False
        kept.append((t, body))
    recs = kept
    with open(dst, "wb") as f:
        for t, body in recs:
            f.write(_pack(t, body))
