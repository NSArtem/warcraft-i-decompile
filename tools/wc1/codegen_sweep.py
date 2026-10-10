"""Compile a C file under several wcc386 flag sets and compare each function
with the original bytes (no symbol database needed).

usage: python3 -m wc1.codegen_sweep file.c [--flags "F1" --flags "F2" ...] [--diff]
                                     [--summary] [-v]

Every function in the file must be preceded by an annotation comment
`/* @0xADDR ... */` (the comment may continue) giving its address in war.exe; annotations are paired with
the compiled functions in source order (so one source function may be tried
in several spellings, each with the same annotation).

Per function and flag set the result is
  MATCH    code bytes identical (relocation fields masked, trailing 4-byte
           alignment filler ignored) AND every relocation is consistent with
           the original: an external symbol name always resolves to one
           original address (minus addend) and no two names share one; the
           module-local segments (CONST/_DATA) use one base.  This is the
           weaker, symbol-database-free form of the wc1.match check;
           unnamed functions can only be certified this way.
  RELOC    bytes identical but a relocation target is inconsistent
  len g/w, N diff   otherwise (compiled length / original length, differing bytes)
With --diff, a side-by-side instruction diff for the first flag set.
Scratch objects go to build/codegen/.
"""
import argparse
import os
import re
import struct
import subprocess

import capstone

from . import analysis, omf, path
from .match import orig_target

_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def is_filler(b):
    """True if b consists only of no-op alignment filler (nop, mov r,r, lea r,[r+0], zero padding)."""
    if set(b) == {0}:
        return True
    k = 0
    while k < len(b):
        i = next(_MD.disasm(b[k:k + 8], 0, 1), None)
        if i is None:
            return False
        ops = [x.strip() for x in i.op_str.split(",")]
        if i.mnemonic == "nop":
            pass
        elif i.mnemonic == "mov" and len(ops) == 2 and ops[0] == ops[1]:
            pass
        elif i.mnemonic == "lea" and len(ops) == 2 and re.fullmatch(
                r"\[%s(\s*\+\s*0(x0)?)?\]" % re.escape(ops[0]), ops[1]):
            pass
        else:
            return False
        k += i.size
    return True


def compile_c(src, flags, out):
    env = dict(os.environ)
    env.setdefault("INCLUDE", os.path.join(env.get("WATCOM", ""), "h"))
    cmd = ["wcc386", "-q", "-zl", "-bt=dos"] + flags.split() + [f"-i={path('src', 'include')}",
                                                                  f"-fo={out}", src]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return None, r.stdout + r.stderr
    return omf.parse_object(out), ""


def functions_of(mod):
    ti, text = mod.seg("_TEXT")
    if text is None:
        return None, []
    by_off = {}
    for n, (si, off) in list(mod.publics.items()) + list(mod.statics.items()):
        if si == ti:
            by_off.setdefault(off, []).append(n)
    # OW2 folds functions with identical bodies onto one address: report them as "a=b"
    starts = sorted((off, "=".join(sorted(ns))) for off, ns in by_off.items())
    res = []
    for k, (off, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text.data)
        fx = [(fu.offset - off, fu) for fu in text.fixups if off <= fu.offset < end]
        mask = set()
        for o, fu in fx:
            mask.update(range(o, o + fu.size))
        res.append((name, bytes(text.data[off:end]), mask, fx))
    return text, res


def disasm(b, base):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    return [(i.address - base, i.bytes.hex(), f"{i.mnemonic} {i.op_str}") for i in md.disasm(b, base)]


def compare(got, want, mask):
    """MATCH or a short mismatch description (bytes only)."""
    if len(got) > len(want) and is_filler(got[len(want):]):
        got = got[:len(want)]
    if len(got) == len(want) and all(g == w or j in mask for j, (g, w) in enumerate(zip(got, want))):
        return "MATCH"
    nd = sum(1 for j in range(min(len(got), len(want))) if got[j] != want[j] and j not in mask)
    return f"len {len(got)}/{len(want)}, {nd} diff"


def sidebyside(got, want):
    a, b = disasm(got, 0), disasm(want, 0)
    out = []
    for k in range(max(len(a), len(b))):
        l = f"{a[k][1]:<16} {a[k][2]:<28}" if k < len(a) else " " * 45
        r = f"{b[k][1]:<16} {b[k][2]}" if k < len(b) else ""
        out.append(("  " if (k < len(a) and k < len(b) and a[k][1] == b[k][1]) else "!!") + l + " | " + r)
    return "\n".join(out)


_P = []


def program():
    if not _P:
        _P.append(analysis.run())
    return _P[0]


def reloc_check(p, rows):
    """Cross-check relocations of the byte-identical functions.

    Returns ({index: message} for bad ones, {segment index: original base})."""
    ext, seg, rev, bad = {}, {}, {}, {}
    for k, (name, a, st, got, want, fx) in enumerate(rows):
        if st != "MATCH":
            continue
        for o, fu in fx:
            ot = orig_target(p, a + o, fu)
            if ot is None:
                bad[k] = f"{name}+{o:#x}: original has no fixup here"
                break
            val = ot - (struct.unpack_from("<i", got, o)[0] + fu.disp)
            if fu.target_kind == "ext":
                tab = ext
            elif fu.target_kind == "seg":
                tab = seg
            else:
                bad[k] = f"{name}+{o:#x}: unsupported fixup target {fu.target_kind}"
                break
            if tab.setdefault(fu.target, val) != val:
                bad[k] = f"{name}+{o:#x}: {fu.target} resolves to {tab[fu.target]:#x} and {val:#x}"
                break
            if tab is ext and rev.setdefault(val, fu.target) != fu.target:
                bad[k] = f"{name}+{o:#x}: {fu.target} and {rev[val]} share {val:#x}"
                break
    return bad, seg


def data_check(p, mod, seg):
    """Module-local data (CONST, _DATA) must equal the original bytes at the derived base."""
    bad = {}
    for si, sb in seg.items():
        sg = mod.segments[si - 1]
        if sg.name == "_TEXT":
            continue
        o = p.le.obj_at(sb)
        if o is None:
            bad[si] = f"{sg.name} base {sb:#x} outside the image"
            continue
        img = p.image[o.index]
        want = bytes(img[sb - o.base:sb - o.base + len(sg.data)])
        mask = set()
        for fu in sg.fixups:
            mask.update(range(fu.offset, fu.offset + fu.size))
        diff = [j for j in range(len(sg.data)) if j not in mask and sg.data[j] != want[j]]
        if diff:
            bad[si] = f"{sg.name} @ {sb:#x}: first data difference at +{diff[0]:#x}"
    return bad


def sweep(src, flagsets, show_diff=False, quiet=False):
    p = program()
    text = open(src).read()
    # annotation -> the function defined right after it: {C name: address}
    ann = {}
    for m in re.finditer(r"/\*\s*@(0x[0-9a-fA-F]+)\b.*?\*/\s*[\w\s\*]*?\b(\w+)\s*\(", text, re.S):
        ann[m.group(2)] = int(m.group(1), 16)
    os.makedirs(path("build", "codegen"), exist_ok=True)
    table = []
    for fi, fl in enumerate(flagsets):
        out = path("build", "codegen", f"sweep_{os.path.basename(src)}_{fi}.obj")
        mod, err = compile_c(src, fl, out)
        if mod is None:
            table.append((fl, None, err))
            continue
        _, fs = functions_of(mod)
        rows = []
        for (name, got, mask, fx) in fs:
            cands = [n for n in name.split("=")]
            hit = [c for c in ann if any(x in (c, c + "_", "_" + c) for x in cands)]
            if not hit:
                continue
            a = ann[hit[0]]
            if len({ann[h] for h in hit}) > 1:
                name += " (folded: " + ",".join(hit) + " have different annotations)"
            elif len(hit) > 1:
                name = "=".join(hit)
            else:
                name = hit[0] if len(cands) == 1 else "=".join(hit)
            off = a - p.code.base
            want = p.cbytes[off:off + len(got)]
            st = compare(got, want, mask)
            if not got:
                st = "EMPTY"
            if st not in ("MATCH",):
                # the original may be shorter/longer: use the function end found by discovery
                f = next((f for f in p.functions if f["start"] == a), None)
                if f is not None:
                    want = p.cbytes[off:f["end"] - p.code.base]
                    st = compare(got, want, mask)
            rows.append((name, a, st, got, want, fx))
        bad, segs = reloc_check(p, rows)
        for k, msg in bad.items():
            n, a, st, g, w, fx = rows[k]
            rows[k] = (n, a, "RELOC " + msg, g, w, fx)
        dbad = data_check(p, mod, segs)
        for k, (n, a, st, g, w, fx) in enumerate(rows):
            if st == "MATCH":
                hit = [dbad[fu.target] for o, fu in fx if fu.target_kind == "seg" and fu.target in dbad]
                if hit:
                    rows[k] = (n, a, "DATA " + hit[0], g, w, fx)
        table.append((fl, [r[:5] for r in rows], ""))
    if not quiet:
        for fl, rows, err in table:
            print(f"## {fl}")
            if rows is None:
                print("   COMPILE ERROR", err.strip().splitlines()[:3])
                continue
            for name, a, st, got, want in rows:
                print(f"   {name:<22} {a:#x}  {st}")
        if show_diff:
            fl, rows, _ = table[0]
            for name, a, st, got, want in rows or []:
                if st != "MATCH":
                    print(f"\n--- {name} {a:#x} flags [{fl}]   (left: compiled, right: original)")
                    print(sidebyside(got, want))
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--flags", action="append", default=[])
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--summary", action="store_true", help="one line per flag set: matches/total")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    t = sweep(a.src, a.flags or ["-s -ot"], a.diff, quiet=a.summary)
    if a.summary:
        for fl, rows, err in t:
            if rows is None:
                print(f"{fl:<40} COMPILE ERROR")
                continue
            ok = [n for n, _, st, _, _ in rows if st == "MATCH"]
            if a.verbose:
                print(f"{fl:<28} {len(ok)}/{len(rows)}  " + " ".join(
                    f"{n.rstrip('_')}={st if st == 'MATCH' else st.replace('len ', '').replace(' diff', 'd')}"
                    for n, _, st, _, _ in rows))
            else:
                print(f"{fl:<40} {len(ok)}/{len(rows)}  {' '.join(n.rstrip('_') for n in ok)}")


if __name__ == "__main__":
    main()
