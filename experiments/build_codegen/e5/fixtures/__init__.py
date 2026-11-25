"""Controlled THREAD fixture injection; executable bytes are never substituted."""
from wc1 import omf
from wc1.omfpatch import _pack
from ..omf_b3 import Threads, records, index


def threadify(raw):
    """Add real THREAD records, with first definitions on discarded CONST data.

    Target T3 and frame F3 are deliberately consumed across FIXUPP32 records.
    The inserted LEDATA repeats verified bytes already present in the object.
    """
    mod, _ = omf.parse_module(raw)
    ci, const = mod.seg('CONST')
    flat = next(i for i, n in mod.groups.items() if n == 'FLAT')
    if ci is None or not const.length:
        raise ValueError('fixture needs CONST')
    definitions = bytes([0x40 | (1 << 2) | 3]) + index(flat) + bytes([3]) + index(ci)
    reader = Threads()
    out, added, segment = [], False, None
    for t, b in records(raw):
        if not added and t == 0xa1:
            out += [_pack(0xa1, index(ci)+bytes(4)+bytes(const.data)), _pack(0x9d, definitions)]
            added = True
        if t == 0xa1:
            segment, _ = omf._idx(b, 0)
        if t == 0x9d:
            body = bytearray()
            for f in reader.parse(b):
                if segment == mod.seg('_TEXT')[0] and f.tm == 0 and f.ti == ci:
                    # F3, T3, P; displacement remains explicit when present.
                    enc = f.encode()
                    body += enc[:2] + bytes([0x80 | 0x30 | 8 | 3 | (4 if f.disp is None else 0)])
                    if f.disp is not None:
                        body += f.disp.to_bytes(4,'little')
                else:
                    body += f.encode()
            b = body
        out.append(_pack(t,b))
    return b''.join(out)
