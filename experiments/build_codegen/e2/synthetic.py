"""Deterministic synthetic fixtures, raw SEGDEF/filler/loop/call evidence."""
from dataclasses import asdict
import struct

import capstone

from .harness import (HERE, SCRATCH, FLAGS, VARIANTS, body_evidence,
                      compile_source, starts)

MATRIX = dict(VARIANTS)
MATRIX.update(od=FLAGS.replace("-ot -ol", "-od"),
              no_ol_alias=FLAGS.replace(" -ol", "") + " -oa",
              cpu3_size=FLAGS.replace("-4r", "-3r").replace("-ot", "-os"),
              cpu5_size=FLAGS.replace("-4r", "-5r").replace("-ot", "-os"))


def snapshot(mod):
    """Exact raw OMF segment bytes and fixups (small synthetic objects only)."""
    return dict(publics=mod.publics, statics=mod.statics, externs=mod.externs,
        segments=[dict(name=s.name, cls=s.cls, segdef_align=s.align,
                       length=s.length, hex=bytes(s.data).hex(),
                       fixups=[asdict(f) for f in s.fixups]) for s in mod.segments])


def layout(mod):
    _, text = mod.seg("_TEXT")
    return dict(text_segdef_align=text.align,
        functions=[dict(name=n, start=o, mod4=o % 4, mod16=o % 16,
                       **{k: v for k, v in body_evidence(mod, n).items()
                          if k not in ("start", "instructions", "neutral_hex", "fixups", "calls")})
                   for o, n in starts(mod)])


def loop_source(prefix, internal_prefix=True):
    # Prefix lengths 0..15 shift the loop's input position independently of
    # the compiler's mandatory inter-function alignment. A preceding exported
    # function also varies the next function's absolute start where allowed.
    emit = "" if prefix == 0 else (
        'void Prefix(void);\n#pragma aux Prefix = ' + ' '.join(['0x90']*prefix) +
        ' modify exact [];\n')
    lead_call = "" if prefix == 0 else "Prefix();"
    call = lead_call if internal_prefix else ""
    return emit + f"""
void Lead(void) {{ {lead_call} }}
unsigned LoopFor(volatile unsigned *p, unsigned n) {{
    unsigned i, s = 0; {call}
    for (i = 0; i < n; ++i) s += p[i];
    return s;
}}
unsigned LoopWhile(volatile unsigned *p, unsigned n) {{
    unsigned s = 0; {call}
    while (n) {{ s += *p++; --n; }}
    return s;
}}
"""


def loops(mod):
    _, text = mod.seg("_TEXT")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    rows = []
    for off, name in starts(mod):
        if not name.startswith("Loop"):
            continue
        body = body_evidence(mod, name)
        insns = list(md.disasm(bytes(text.data[off:off+body["body_size"]]), off))
        back = []
        for i in insns:
            if not (i.mnemonic.startswith("j") or i.mnemonic.startswith("loop")):
                continue
            try:
                target = int(i.op_str, 16)
            except ValueError:
                continue
            if off <= target < i.address:
                before = [j for j in insns if j.address < target]
                # Padding is explicit and independently inspectable, not
                # guessed from zero bytes inside operands.
                padding = []
                for j in reversed(before):
                    if j.mnemonic == "nop" or (j.mnemonic == "mov" and
                            j.op_str in ("eax, eax", "ebx, ebx", "edx, edx")) or (
                            j.mnemonic == "lea" and j.op_str in ("eax, [eax]", "edx, [edx]")):
                        padding.insert(0, bytes(j.bytes).hex())
                    else:
                        break
                back.append(dict(branch_offset=i.address, target_offset=target,
                    target_mod4=target % 4, target_mod16=target % 16,
                    target_relative_to_function=target-off,
                    preceding_filler_hex="".join(padding)))
        rows.append(dict(name=name, start=off, start_mod16=off % 16,
                         back_edges=back, body_hex=body["body_hex"]))
    return rows


def call_source(kind):
    callee = "unsigned Callee(unsigned a, unsigned b, unsigned c) { return (a * 7 + b) ^ c; }\n"
    if kind == "static":
        callee = "static " + callee
    if kind == "extern":
        callee = "extern unsigned Callee(unsigned, unsigned, unsigned);\n"
    return callee + """
unsigned Caller(unsigned a, unsigned b, unsigned c, unsigned d)
{
    unsigned x = a * 3 + d, y = b ^ d, z = c + d;
    return Callee(x, y, z) + a + b + c + d;
}
"""


def run_synthetic():
    rows, loop_rows, call_rows = [], [], []
    configs = [("10.0a", k, v) for k, v in MATRIX.items()]
    configs += [("ow2", k, VARIANTS[k]) for k in ("native", "cpu5")]
    for cc, variant, flags in configs:
        for fixture in ("alignment", "pooling"):
            mod = compile_source(HERE / "fixtures" / (fixture + ".c"), flags,
                                 f"synthetic/{cc}/{variant}_{fixture}", cc)
            row = dict(compiler=cc, variant=variant, flags=flags, fixture=fixture,
                       layout=layout(mod), omf=snapshot(mod))
            if fixture == "pooling":
                ti, text = mod.seg("_TEXT")
                refs = {}
                for off, name in starts(mod):
                    body = body_evidence(mod, name)
                    refs[name] = [dict(segment=mod.segments[f.target-1].name,
                        addend=struct.unpack_from("<I", text.data, f.offset)[0] + f.disp)
                        for f in text.fixups if off <= f.offset < off+body["body_size"]
                        and f.target_kind == "seg"]
                row["data_references"] = refs
                a, b = refs["PoolA_"], refs["PoolB_"]
                row["identical_strings_merged"] = bool(a and a == b)
            rows.append(row)
        # Every prefix length, both loop shapes, all requested 10.0a flags.
        for mode in ("neighbor_only", "internal_prefix"):
            for prefix in range(16):
                src = SCRATCH / "synthetic" / f"loop_{mode}_{prefix}.c"
                src.parent.mkdir(parents=True, exist_ok=True)
                src.write_text(loop_source(prefix, mode == "internal_prefix"))
                mod = compile_source(src, flags, f"synthetic/{cc}/{variant}_{mode}_loop{prefix}", cc)
                loop_rows.append(dict(compiler=cc, variant=variant, flags=flags, mode=mode,
                                      prefix_bytes=prefix, functions=loops(mod)))
        for kind in ("extern", "global", "static"):
            src = SCRATCH / "synthetic" / f"calls_{kind}.c"
            src.write_text(call_source(kind))
            mod = compile_source(src, flags, f"synthetic/{cc}/{variant}_{kind}", cc)
            call_rows.append(dict(compiler=cc, variant=variant, flags=flags, kind=kind,
                                 layout=layout(mod), omf=snapshot(mod),
                                 caller=body_evidence(mod, "Caller_")))
        print(f"synthetic: {cc} {variant}", flush=True)
    return dict(matrix=rows, loops=loop_rows, calls=call_rows,
        segdef_alignment_codes={"1": "byte", "2": "word", "3": "paragraph (16)",
                                "4": "page (256)", "5": "dword (4)"},
        notes=["Aux byte emitters give exact 5/11/17/23 bodies under optimized flags; OD/debug may add frames.",
               "Natural C controls accompany exact-length functions.",
               "Prefixes 0..15 vary loop positions; Lead also varies preceding body length.",
               "Static/global/extern have identical callee semantics and three register parameters."])
