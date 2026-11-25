"""Minimal deterministic OMF32 object writer for E4 synthetic controls.

Only the record subset the extractor supports is emitted, in the legal order
(LNAMES, SEGDEF, GRPDEF, EXTDEF, LEDATA+FIXUPP, PUBDEF/LPUBDEF, MODEND).
Frames are written as `Target` (method 5) so no group is required; a fixup can
also name a group explicitly.  Nothing here is derived from the game image.
"""
import struct

from wc1 import omf
from wc1.omfpatch import _pack
from experiments.build_codegen.e4.omf_extract import RawFix, _idx_bytes


def _lnames(names):
    out = bytearray([0])                     # index 1: empty name (Watcom style)
    index = {"": 1}
    for name in names:
        if name in index:
            continue
        index[name] = len(index) + 1
        out += bytes([len(name)]) + name.encode("latin-1")
    return bytes(out), index


def build(*, segments, publics=(), statics=(), externs=(), groups=(),
          module="e4.obj", whole_ledata=False):
    """Serialize one module.

    segments: [{name, cls, data, fixups, align=1, length=None}]
    publics/statics: [(name, segment_index, offset)]
    externs: [name]
    groups: [(name, [segment indices])]
    fixups: [{offset, tm, ti, self_rel=True, loc=9, fm=5, fi=None, disp=None}]
    """
    seg_names = [s["name"] for s in segments]
    class_names = [s.get("cls", "DATA") for s in segments]
    group_entries, group_names = [], []
    for name, members in groups:
        group_names.append(name)
        group_entries.append((name, members))
    body_names, index = _lnames(seg_names + list(dict.fromkeys(class_names)) + group_names)

    records = [(0x80, bytearray(bytes([len(module)]) + module.encode("latin-1"))),
               (0x96, bytearray(body_names))]
    for s in segments:
        attr = ((s.get("align", 1) & 7) << 5) | (2 << 2) | 1
        length = s.get("length", len(s["data"]))
        records.append((0x99, bytearray(bytes([attr]) + struct.pack("<I", length) +
                                        _idx_bytes(index[s["name"]]) +
                                        _idx_bytes(index[s.get("cls", "DATA")]) + b"\x01")))
    for name, members in group_entries:
        records.append((0x9A, bytearray(_idx_bytes(index[name]) +
                                        (b"\xff" + bytes(members) if members else b""))))
    if externs:
        body = b"".join(bytes([len(n)]) + n.encode("latin-1") + b"\x00" for n in externs)
        records.append((0x8C, bytearray(body)))
    ext_index = {n: i + 1 for i, n in enumerate(externs)}

    for si, s in enumerate(segments, 1):
        data = bytes(s["data"])
        fixups = sorted(s.get("fixups", []), key=lambda f: f["offset"])
        spans = [(f["offset"], f["offset"] + 4) for f in fixups]
        cuts, start = [], 0
        while start < len(data):
            end = len(data) if whole_ledata else min(start + 1024, len(data))
            if end < len(data):
                for a, b in spans:
                    if a < end < b:
                        end = a
                        break
            cuts.append((start, end))
            start = end
        for start, end in cuts:
            records.append((0xA1, bytearray(_idx_bytes(si) + struct.pack("<I", start) +
                                            data[start:end])))
            encoded = []
            for f in fixups:
                if start <= f["offset"] < end:
                    encoded.append(RawFix(f["offset"] - start, f.get("loc", 9),
                                          f.get("self_rel", True), f.get("fm", 5),
                                          f.get("fi"), f["tm"], f["ti"],
                                          f.get("disp")).encode())
            if encoded:
                records.append((0x9D, bytearray(b"".join(encoded))))

    for rt, table in ((0x91, publics), (0xB7, statics)):
        by_seg = {}
        for name, si, off in table:
            by_seg.setdefault(si, []).append((name, off, 0))
        for si, entries in sorted(by_seg.items()):
            body = _idx_bytes(1) + _idx_bytes(si)     # group 1, segment si
            for name, off, typ in entries:
                body += (bytes([len(name)]) + name.encode("latin-1") +
                         struct.pack("<I", off) + _idx_bytes(typ, True))
            records.append((rt, bytearray(body)))

    records.append((0x8A, bytearray(b"\x00")))
    return b"".join(_pack(t, body) for t, body in records)


def resolve_fixup(fix, segments, externs):
    """(tm, ti) for a symbolic fixup target: ('seg', n) or ('ext', name)."""
    kind, target = fix
    if kind == "seg":
        return 0, target
    return 2, externs.index(target) + 1
