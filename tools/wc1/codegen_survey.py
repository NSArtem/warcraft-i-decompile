"""Survey the compiler code-generation style of every function in war.exe.

usage: python3 -m wc1.codegen_survey [--functions]

Writes build/codegen/survey.txt (and build/codegen/functions.tsv with --functions):
per function the prologue/epilogue/jump-encoding features, then a table by
module (analysis/modules.toml) and by style class.  Pure observation of the
original bytes; no claims about flags (see docs/subsystems/codegen.md).

Features
  pushes   leading `push reg` run (register save set, in order)
  frame    `push ebp; mov ebp,esp` (after the saves, or as the first insns)
  sub      `sub esp,N` right after the frame, with encoding imm8/imm32
  epi      how the frame is released: `mov esp,ebp` / `leave` / `none`
  stk      stack-overflow check (`cmp esp,[mem]` among the first insns)
  jshort/jnear/jnear_s  rel8 jumps, rel32 jumps, rel32 jumps whose target is
           within rel8 range (a compiler that always uses near jumps)
  align    function start modulo 16 (0 = 16-aligned)
  pad      filler bytes between the last instruction and the next function
"""
import argparse
import collections
import os
import tomllib

from . import analysis, path

REG32 = {"eax", "ecx", "edx", "ebx", "esi", "edi", "ebp"}


def feat(p, f):
    s, end, limit = f["start"], f["end"], f["limit"]
    insns = []
    a = s
    while a < end:
        i = p.insns.get(a)
        if i is None:
            break
        insns.append(i)
        a += i.size
    # leading pushes
    k = 0
    pushes = []
    while k < len(insns) and insns[k].mnemonic == "push" and insns[k].op_str in REG32:
        pushes.append(insns[k].op_str)
        k += 1
    frame = False
    if k + 1 < len(insns) and insns[k].mnemonic == "push" and insns[k].op_str == "ebp" \
            and insns[k + 1].mnemonic == "mov" and insns[k + 1].op_str == "ebp, esp":
        frame = True
        k += 2
    elif pushes and pushes[-1] == "ebp" and k < len(insns) and \
            insns[k].mnemonic == "mov" and insns[k].op_str == "ebp, esp":
        frame = True
        k += 1
    sub = None
    if frame and k < len(insns) and insns[k].mnemonic == "sub" and insns[k].op_str.startswith("esp, "):
        i = insns[k]
        sub = (int(i.op_str.split(", ")[1], 0), "imm8" if i.size == 3 else "imm32")
    stk = any(i.mnemonic == "cmp" and i.op_str.startswith("esp, ") for i in insns[:6])
    mnem = [i.mnemonic for i in insns]
    epi = "none"
    if "leave" in mnem:
        epi = "leave"
    elif any(i.mnemonic == "mov" and i.op_str == "esp, ebp" for i in insns):
        epi = "mov esp,ebp"
    elif frame:
        epi = "pop-only"
    js = jn = jns = 0
    for i in insns:
        if i.mnemonic == "jmp" or (i.mnemonic.startswith("j") and i.mnemonic not in ("jmp",)):
            if not i.operands or i.operands[0].type != 2:      # X86_OP_IMM
                continue
            b = i.bytes
            if len(b) == 2:
                js += 1
            elif len(b) in (5, 6) and (b[0] in (0xE9, 0x0F)):
                jn += 1
                d = (i.operands[0].imm & 0xFFFFFFFF) - (i.address + i.size)
                d = d - (1 << 32) if d & 0x80000000 else d
                if -128 <= d <= 127:
                    jns += 1
    pad = p.cbytes[end - p.code.base:limit - p.code.base]
    padk = "none" if not pad else ("zero" if set(pad) == {0} else
                                   "nop" if set(pad) <= {0x90} else "mixed")
    if frame and sub is not None:
        cls = "frame+sub"
    elif frame:
        cls = "frame"
    elif pushes:
        cls = "saves-only"
    else:
        cls = "bare"
    # style: OD = unoptimised (-od) code: all-registers-saved frame with `sub esp,imm32`;
    # DBG = optimised body inside a standard ebp frame (what OW2 -d1+ emits);
    # (a frame with sub esp,N >= 128 needs imm32 anyway and counts as DBG: ambiguous);
    # LEAVE = frame released with `leave` (third-party library, e.g. Miles AIL);
    # OPT = no frame pointer (optimised, esp-relative or register only)
    if epi == "leave":
        style = "LEAVE"
    elif frame and sub is not None and sub[1] == "imm32" and sub[0] < 128:
        style = "OD"          # imm32 although the size fits imm8: the -od code generator
    elif frame:
        style = "DBG"
    else:
        style = "OPT"
    return dict(addr=s, size=end - s, style=style, ninsn=len(insns), pushes=pushes, frame=frame, sub=sub,
                epi=epi, stk=stk, js=js, jn=jn, jns=jns, align=s % 16, pad=padk, padlen=len(pad),
                cls=cls, leaf=not any(m == "call" for m in mnem))


def modules():
    d = tomllib.load(open(path("analysis", "modules.toml"), "rb"))["module"]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--functions", action="store_true")
    a = ap.parse_args()
    p = analysis.run()
    mods = modules()
    starts = [m["start"] for m in mods]
    import bisect
    rows = []
    for f in p.functions:
        try:
            r = feat(p, f)
        except Exception:
            continue
        k = bisect.bisect_right(starts, f["start"]) - 1
        r["mod"] = mods[k]["name"] if k >= 0 else "?"
        r["kind"] = mods[k]["kind"] if k >= 0 else "?"
        rows.append(r)
    os.makedirs(path("build", "codegen"), exist_ok=True)
    out = []
    w = out.append
    w(f"# codegen survey of war.exe: {len(rows)} functions")
    w("")
    w("## by module kind and style class")
    t = collections.defaultdict(collections.Counter)
    for r in rows:
        t[r["kind"]][r["cls"]] += 1
    classes = ["bare", "saves-only", "frame", "frame+sub"]
    w("%-12s %6s " % ("kind", "n") + " ".join("%10s" % c for c in classes))
    for k in sorted(t):
        w("%-12s %6d " % (k, sum(t[k].values())) + " ".join("%10d" % t[k][c] for c in classes))
    w("")
    w("## frame details by module kind")
    w("%-12s %5s %9s %9s %8s %9s %9s %9s %6s" % ("kind", "n", "sub0/imm32", "sub/imm8", "mov-esp", "leave",
                                              "stkchk", "jnear_s", "jshort"))
    for k in sorted(t):
        rs = [r for r in rows if r["kind"] == k]
        w("%-12s %5d %9d %9d %8d %9d %9d %9d %6d" % (
            k, len(rs),
            sum(1 for r in rs if r["sub"] and r["sub"][1] == "imm32"),
            sum(1 for r in rs if r["sub"] and r["sub"][1] == "imm8"),
            sum(1 for r in rs if r["epi"] == "mov esp,ebp"),
            sum(1 for r in rs if r["epi"] == "leave"),
            sum(1 for r in rs if r["stk"]),
            sum(r["jns"] for r in rs), sum(r["js"] for r in rs)))
    w("")
    w("## save-set signatures (leading pushes) by kind, top 6 each")
    for k in sorted(t):
        c = collections.Counter(",".join(r["pushes"]) or "-" for r in rows if r["kind"] == k)
        w(f"{k}: " + "; ".join(f"[{s}] x{n}" for s, n in c.most_common(6)))
    w("")
    w("## style per module kind (OD = -od frame with sub esp,imm32; DBG = optimised body in an ebp frame;")
    w("##   LEAVE = frame released by `leave`; OPT = no frame pointer)")
    styles = ["OPT", "DBG", "OD", "LEAVE"]
    w("%-12s %6s " % ("kind", "n") + " ".join("%7s" % c for c in styles))
    for k in sorted(t):
        c = collections.Counter(r["style"] for r in rows if r["kind"] == k)
        w("%-12s %6d " % (k, sum(c.values())) + " ".join("%7d" % c[x] for x in styles))
    w("")
    w("## style per module (range); `mixed` = more than one of OD/DBG/LEAVE/OPT among functions of")
    w("##   more than a tiny bare leaf (a module is one object file, so mixed styles mean a wrong boundary,")
    w("##   hand-written asm, or two objects)")
    w("%-9s %-9s %-16s %4s %5s %5s %5s %5s  %-6s %4s %5s %5s %s" % (
        "start", "kind", "module", "n", "OPT", "DBG", "OD", "LEAVE", "style", "js", "jn", "jn_s", "padding"))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["mod"]].append(r)
    for m in mods:
        rs = by.get(m["name"], [])
        if not rs:
            continue
        cc = collections.Counter(r["style"] for r in rs)
        big = collections.Counter(r["style"] for r in rs
                                  if not (r["style"] == "OPT" and r["size"] <= 12))
        sty = "+".join(x for x in styles if big[x]) or "OPT"
        if "+" in sty:
            sty = "mixed:" + sty
        pads = collections.Counter(r["pad"] for r in rs)
        w("%-9x %-9s %-16s %4d %5d %5d %5d %5d  %-6s %4d %5d %5d %s" % (
            m["start"], m["kind"], m["name"][:16], len(rs), cc["OPT"], cc["DBG"], cc["OD"], cc["LEAVE"], sty,
            sum(r["js"] for r in rs), sum(r["jn"] for r in rs), sum(r["jns"] for r in rs),
            dict(pads)))
    w("")
    w("## style runs (consecutive functions of the same style; tiny bare leaves are neutral)")
    runs, cur = [], None
    for r in sorted(rows, key=lambda r: r["addr"]):
        st = r["style"]
        if st == "OPT" and r["cls"] == "bare" and r["size"] <= 12:
            st = None
        if st is None:
            if cur:
                cur[1] = r["addr"] + r["size"]
                cur[3] += 1
            continue
        if cur and cur[2] == st:
            cur[1] = r["addr"] + r["size"]
            cur[3] += 1
        else:
            if cur:
                runs.append(cur)
            cur = [r["addr"], r["addr"] + r["size"], st, 1]
    if cur:
        runs.append(cur)
    for lo, hi, st, n in runs:
        w(f"{lo:#8x}-{hi:#8x}  {st:6} {n:4} functions")
    open(path("build", "codegen", "survey.txt"), "w").write("\n".join(out) + "\n")
    if a.functions:
        with open(path("build", "codegen", "functions.tsv"), "w") as fh:
            fh.write("addr\tmodule\tkind\tcls\tsize\tpushes\tsub\tepi\tstk\tjs\tjn\tjns\talign\tpad\tleaf\n")
            for r in rows:
                fh.write("\t".join(str(x) for x in (
                    hex(r["addr"]), r["mod"], r["kind"], r["cls"], r["size"], ",".join(r["pushes"]),
                    r["sub"], r["epi"], int(r["stk"]), r["js"], r["jn"], r["jns"], r["align"], r["pad"],
                    int(r["leaf"])))+"\n")
    print("\n".join(out[:40]))
    print("... full report in build/codegen/survey.txt")


if __name__ == "__main__":
    main()
