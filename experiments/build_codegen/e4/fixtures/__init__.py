"""E4 fixtures: real compiled slices plus independent OMF32 control objects.

All generated files go under `build/e4/`; source fixtures are repository files.
The real cases compile existing reference C; the controlled cases use the
original Watcom 10.0a or NASM.  Synthetic originals are in-memory images built
here, so no game bytes are persisted.
"""
import struct
from types import SimpleNamespace

import capstone
from wc1 import le, omf
from wc1.omfpatch import _pack
from experiments.build_codegen.e4 import omf_extract as x
from experiments.build_codegen.e0.matcher_proto import OriginalIndex
from experiments.build_codegen.e3.partial_matcher import CandidateRegion, DataBoundary
from . import builder, support

DATA_BASE = 0x50000
CODE_BASE = 0x10000


def synthetic_program(code, publics, *, data=None, ends=None, jump_tables=None,
                      original=None, original_fixes=()):
    """An in-memory original image, its function table and symbol database.

    `code` is the compiled body; the original image defaults to the same bytes.
    `original_fixes` are (field offset in _TEXT, original target address) pairs
    that become loader fixups of the synthetic image.
    """
    image = bytearray(original if original is not None else code)
    objects = {1: le.Obj(1, len(image), CODE_BASE, le.OBJ_READ | le.OBJ_EXEC, 1, 1)}
    base = DATA_BASE
    for k, raw in enumerate((data or {}).values(), 2):
        objects[k] = le.Obj(k, len(raw), base, le.OBJ_READ | le.OBJ_WRITE, 1, 1)
        base += len(raw)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    insns = {i.address: i for i in md.disasm(bytes(image), CODE_BASE)}
    starts = sorted(off for si, off in publics.values() if si == 1)
    ends = list(ends or (starts[1:] + [len(code)]))
    functions = [dict(start=CODE_BASE + off, end=CODE_BASE + end,
                      limit=CODE_BASE + end) for off, end in zip(starts, ends)]

    def obj_at(addr):
        for obj in objects.values():
            if obj.base <= addr < obj.end:
                return obj
        return None

    imgs = {1: bytearray(image)}
    for k, raw in enumerate((data or {}).values(), 2):
        imgs[k] = bytearray(raw)
    p = SimpleNamespace(code=objects[1], cbytes=bytes(image), image=imgs,
                        le=SimpleNamespace(obj_at=obj_at), fix_at={}, insns=insns,
                        functions=functions, jump_tables=jump_tables or {}, owner={})
    for off, target in original_fixes:
        p.fix_at[CODE_BASE + off] = (le.Fixup(1, off, 7, obj_at(target).index,
                                              target - obj_at(target).base), target)
    db = {n: dict(addr=CODE_BASE + off, link_name=n)
          for n, (si, off) in publics.items() if si == 1}
    return p, db


def write(raw, name):
    return support.write_obj(name, raw)


# --------------------------------------------------------------- real cases
def compile_reference(relpath, flags, name):
    from experiments.build_codegen.e5 import build_e5 as b
    obj = support.OBJ / (name + ".obj")
    support.OBJ.mkdir(parents=True, exist_ok=True)
    b.compile_10a(support.ROOT / relpath, obj, flags)
    return obj


# ------------------------------------------------------ positive case 3 / 3b
def _tu_case(name, obj, runtime, starts, ends, names):
    oracle_exe, oracle = support.mini_link([obj, runtime], name + "_oracle")
    code = next(o for o in oracle.objects if o.is_code)
    ranges = [(n, code.base + off, code.base + end)
              for n, off, end in zip(names, starts, ends)]
    prog = support.program_from_le(oracle, support.function_table(oracle, ranges, {}))
    db = {n: dict(addr=a, link_name=n) for n, a, e in ranges}
    return dict(obj=obj, runtime=runtime, oracle_exe=oracle_exe, oracle=oracle,
                prog=prog, db=db, ranges=ranges, code_base=code.base,
                candidate=CandidateRegion(0, starts[1], code.base),
                index=OriginalIndex(prog))


def controlled():
    """Real 10.0a TU [A, B, C]: extract A, rebuild the oracle executable."""
    obj = support.compile_controlled()
    mod = omf.parse_object(obj)
    text = support.text_bytes(obj)
    runtime = support.runtime_object()
    starts = sorted(off for si, off in mod.publics.values() if si == 1)
    ends = support.body_ends(text, starts)
    names = [n for n, (si, off) in sorted(mod.publics.items(), key=lambda kv: kv[1][1])
             if si == 1]
    case = _tu_case("p3", obj, runtime, starts, ends, names)
    case.update(mod=mod, text=text, const_si=mod.seg("CONST")[0])
    return case


def direct_call():
    """NASM TU with a plain (unfixed) intra-TU `call rel32` over a neighbour."""
    obj = support.assemble(support.HERE / "direct_call.asm", "p3b_direct")
    mod = omf.parse_object(obj)
    text = support.text_bytes(obj)
    runtime = support.runtime_object()
    starts = sorted(off for si, off in mod.publics.values() if si == 1)
    ends = support.body_ends(text, starts)
    names = [n for n, (si, off) in sorted(mod.publics.items(), key=lambda kv: kv[1][1])
             if si == 1]
    case = _tu_case("p3b", obj, runtime, starts, ends, names)
    case.update(mod=mod, text=text)
    return case


def interior_call():
    """NASM TU whose only call targets the interior of the neighbour."""
    obj = support.assemble(support.HERE / "interior_call.asm", "n2_interior")
    mod = omf.parse_object(obj)
    text = support.text_bytes(obj)
    starts = sorted(off for si, off in mod.publics.values() if si == 1)
    ends = support.body_ends(text, starts)
    prog, db = synthetic_program(text, mod.publics, ends=ends)
    return dict(obj=obj, mod=mod, prog=prog, db=db,
                candidate=CandidateRegion(0, starts[1], CODE_BASE))


def long_chunk():
    """One 1500-byte LEDATA with an off32 field straddling byte 1022-1026."""
    field = 1022
    code = bytearray(b"\x90" * 1021 + b"\xB8" + b"\x00" * 4 +
                     b"\x90" * (1500 - 1021 - 5 - 1) + b"\xC3")
    assert len(code) == 1500
    struct.pack_into("<I", code, field, 0)      # filled by the linker
    raw = builder.build(
        segments=[dict(name="_TEXT", cls="CODE", data=bytes(code), align=1,
                       fixups=[dict(offset=field, loc=9, self_rel=False, fm=5,
                                    tm=2, ti=1, disp=0)])],
        publics=[("E4_Long", 1, 0)], externs=["_e4_data"], whole_ledata=True)
    source = support.write_obj("p4_source", raw)
    provider = support.assemble(support.HERE / "data_provider.asm", "p4_provider")
    oracle_exe, oracle = support.mini_link([source, provider], "p4_oracle")
    code_obj = next(o for o in oracle.objects if o.is_code)
    prog = support.program_from_le(
        oracle, [dict(start=code_obj.base, end=code_obj.base + 1500,
                      limit=code_obj.base + 1500)])
    data_addr = prog.fix_at[code_obj.base + field][1]
    db = {"E4_Long": dict(addr=code_obj.base, link_name="E4_Long"),
          "_e4_data": dict(addr=data_addr, link_name="_e4_data")}
    return dict(obj=raw, raw=raw, mod=omf.parse_module(raw)[0], prog=prog, db=db,
                provider=provider, oracle_exe=oracle_exe, oracle=oracle,
                source=source, code_base=code_obj.base, data_addr=data_addr,
                field=field, candidate=CandidateRegion(0, 1500, code_obj.base))


# ------------------------------------------------------------ negative cases
def jump_table():
    """Segment relocation to a jump table that lives outside the slice."""
    table = 0x10
    compiled = bytes(b"\xFF\x25" + struct.pack("<I", table) + b"\xC3" +
                     b"\x90" * 10 + struct.pack("<I", CODE_BASE) + b"\xC3")
    original = bytearray(compiled)
    struct.pack_into("<I", original, 2, CODE_BASE + table)
    prog, db = synthetic_program(
        compiled, {"E4_Jumper": (1, 0), "E4_Sibling": (1, table)}, ends=[7, 21],
        original=bytes(original))
    prog.fix_at[CODE_BASE + 2] = (le.Fixup(1, 2, 7, 1, table), CODE_BASE + table)
    raw = builder.build(
        segments=[dict(name="_TEXT", cls="CODE", data=compiled, align=1,
                       fixups=[dict(offset=2, loc=9, self_rel=False, fm=5, tm=0, ti=1,
                                    disp=0)])],
        publics=[("E4_Jumper", 1, 0), ("E4_Sibling", 1, table)])
    return dict(obj=raw, mod=omf.parse_module(raw)[0], prog=prog, db=db,
                candidate=CandidateRegion(0, table, CODE_BASE))


def mutable_data():
    """Slice with a mutable local _DATA object; the plan can be mis-anchored.

    The compiled field carries the object-relative addend (0); the original
    image carries the absolute address, exactly as a real relocation does.
    """
    compiled = b"\xA1" + b"\x00" * 4 + b"\xC3"
    original = b"\xA1" + struct.pack("<I", DATA_BASE) + b"\xC3"
    data = bytes([1, 2, 3, 4, 5, 6, 7, 8])
    prog, db = synthetic_program(compiled, {"E4_Data": (1, 0)}, data={"_DATA": data},
                                 ends=[6], original=original,
                                 original_fixes=[(1, DATA_BASE)])
    db["_e4_mutable"] = dict(addr=DATA_BASE, size=len(data), link_name="_e4_mutable")
    raw = builder.build(
        segments=[dict(name="_TEXT", cls="CODE", data=compiled, align=1,
                       fixups=[dict(offset=1, loc=9, self_rel=False, fm=5, tm=2, ti=1,
                                    disp=0)]),
                  dict(name="_DATA", cls="DATA", data=data, align=1)],
        publics=[("E4_Data", 1, 0), ("_e4_mutable", 2, 0)], externs=["_e4_mutable"])
    boundaries = [DataBoundary(segment=2, obj_start=0, orig_start=DATA_BASE,
                               size=len(data), kind="mutable",
                               evidence="fixture: one 4-byte aligned mutable array declared once",
                               symbol="_e4_mutable")]
    return dict(obj=raw, mod=omf.parse_module(raw)[0], prog=prog, db=db,
                boundaries=boundaries, data_base=DATA_BASE,
                candidate=CandidateRegion(0, 6, CODE_BASE))


def swap_extname(raw, old, new):
    """EXTDEF rename of equal length (an incorrect relocation target).

    The containing record is re-packed so every checksum stays valid.
    """
    if len(old) != len(new):
        raise ValueError("equal-length names required")
    needle = bytes([len(old)]) + old.encode("latin-1") + b"\x00"
    replacement = bytes([len(new)]) + new.encode("latin-1") + b"\x00"
    out, found = [], 0
    for t, body in x.read_records(bytes(raw)):
        if t & ~1 in (0x8C, 0xB4, 0xBC) and needle in bytes(body):
            body = bytearray(bytes(body).replace(needle, replacement))
            found += 1
        out.append(_pack(t, body))
    if found != 1:
        raise ValueError(f"{old!r} declared in {found} EXTDEF records")
    return b"".join(out)
