"""Hand-authored OMF and original layouts with independent data boundaries."""
import struct

from wc1 import le, omf

from ...e0.controls import synthetic
from ..partial_matcher import DataBoundary


def _mov(reg, value):
    return bytes([reg]) + struct.pack("<I", value)


def string_pool(case="shifted_const"):
    base = 0x50000
    # Equal contents in the alias controls make byte comparison insufficient.
    last = b"one\0" if case in ("aliased_const", "aliased_original") else b"two\0"
    compiled = b"longer\0one\0" + last
    original = b"x\0one\0" + last
    z = 2 if case == "aliased_original" else 6
    raw = _mov(0xb8, base) + b"\x48\xc3"
    raw += _mov(0xb8, base+2) + _mov(0xba, base+z) + b"\xc3"
    code = _mov(0xb8, 0) + b"\x40\xc3"
    code += _mov(0xb8, 7) + _mov(0xba, 7 if case == "aliased_const" else 11) + b"\xc3"
    patches = (1, 8, 13)
    targets = (base, base+2, base+z)
    p, m, db = synthetic(code, [omf.Fixup(i, 9, False, "seg", 2, 0) for i in patches],
                         publics={"Sibling_": (1, 0), "Probe_": (1, 7)},
                         original=raw, original_fixes=zip(patches, targets))
    mutable = case in ("mutable_shift", "proven_mutable_shift")
    if case == "corrupted_const":
        compiled = compiled[:-2] + b"X\0"
    proof_kind = "mutable" if mutable else "const_string"
    bounds = tuple(DataBoundary(2, off, base+orig, size, proof_kind,
                                "Independent object and original fixture declarations", symbol)
                   for off, orig, size, symbol in [(7, 2, 4, "One"), (11, 6, 4, "Two")])
    # The changed prefix has different compiled and original lengths. Its slot
    # is intentionally uncertified; the downstream literal boundaries are exact.
    if mutable:
        if case == "proven_mutable_shift":
            for b in bounds:
                m.statics[b.symbol] = (2, b.obj_start)
                db[b.symbol] = dict(addr=b.orig_start, link_name=b.symbol)
        else:
            bounds = ()
    ds = le.Obj(2, len(original), base, le.OBJ_READ | le.OBJ_WRITE, 1, 1)
    m.segments.append(omf.Segment("_DATA" if mutable else "CONST", "DATA", 1,
                                  len(compiled), bytearray(compiled)))
    p.image[2] = bytearray(original)
    p.le.obj_at = lambda a: next((o for o in (p.code, ds) if o.base <= a < o.end), None)
    for i, t in zip(patches, targets):
        p.fix_at[0x10000+i] = (le.Fixup(1, i, 7, 2, t-base), t)
    return p, m, db, bounds


def branch(case):
    if case == "outgoing_rel8":
        return synthetic(b"\xeb\x00\x40\xc3",
                         publics={"Probe_": (1, 0), "Sibling_": (1, 2)},
                         original=b"\xeb\x00\x48\xc3")
    # Object call lands at offset 6. The independently defined original sibling
    # sits at offset 8 or 6. The wrong-target case instead calls offset 8 while
    # the original DB still identifies Sibling at offset 6.
    code = b"\xe8\x01\x00\x00\x00\xc3\x40\xc3\xc3"
    original = b"\xe8\x03\x00\x00\x00\xc3\x48\xc3\xc3"
    p, m, db = synthetic(code, original=original,
                         publics={"Probe_": (1, 0), "Sibling_": (1, 6), "Other_": (1, 8)})
    if case == "direct_rel32":
        db["Sibling_"]["addr"] = 0x10008
        db["Other_"]["addr"] = 0x10006
    elif case == "unresolved_sibling":
        del db["Sibling_"]
    elif case != "wrong_sibling":
        raise ValueError(case)
    return p, m, db
