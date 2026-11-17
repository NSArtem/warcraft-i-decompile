"""Analysis dump for the CMD.C area (and read-only looks at neighbours).

usage: python3 -m wc1.cmd_123f0_dump SPEC [SPEC ...]
  LO-HI                dump every function in the range (default 0x123f0-0x12b80)
  CTX:ADDR[:BACK:FWD]  raw-ish disassembly around an address (caller context)
  DATA:ADDR[:LEN]      hex dump of data bytes + strings + cheat-decoded strings
  XREF:ADDR[:N]        every reference into [ADDR, ADDR+N)

XOR-decoding follows fn_12800: byte i of the reference string is compared
against the input XOR (1 << (i % 8)) (rotl of 0x01010101 by one bit per byte).
Everything is read-only; the result is written to build/cmd_123f0/dump.txt.
"""
import argparse
import bisect
import os

from capstone import x86

from wc1 import analysis, emit, path, symbols

LO_DEFAULT = 0x123F0
HI_DEFAULT = 0x12B80


def load_data(p, addr, n):
    d = p.data
    if d.base <= addr and addr + n <= d.base + d.vsize:
        return bytes(p.image[d.index])[addr - d.base:addr - d.base + n]
    return None


def cstr(p, addr, maxlen=64):
    raw = load_data(p, addr, maxlen)
    if raw is None:
        return None
    z = raw.find(0)
    return raw[:z if z >= 0 else maxlen]


def cheat_decode(data):
    return bytes(b ^ (1 << (i % 8)) for i, b in enumerate(data))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="*")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    p = analysis.run()
    funcs, datas, _ = symbols.load(strict=False)
    names = {e["addr"]: e["link_name"] for t in (datas, funcs) for e in t.values()}
    starts = [f["start"] for f in p.functions]
    e = emit.Emitter(p, names=names)

    lines = []
    W = lines.append

    def where(x):
        if not p.in_code(x):
            return f"data {x:#x}"
        k = bisect.bisect_right(starts, x) - 1
        s = starts[k] if k >= 0 else None
        n = names.get(s, f"fn_{s:05x}") if s is not None else "?"
        return f"{n}+{x - s:#x}" if s is not None else f"{x:#x}"

    def refs_to(lo, hi, skip=None):
        for ia, i in sorted(p.insns.items()):
            if skip is not None and skip[0] <= ia < skip[1]:
                continue
            if i.mnemonic in analysis.COND_JUMPS | {"jmp", "call"} and i.operands and \
                    i.operands[0].type == x86.X86_OP_IMM:
                t = i.operands[0].imm & 0xFFFFFFFF
                if lo <= t < hi:
                    W(f"  {i.mnemonic:5} {t:#x} <- {ia:05x} ({where(ia)})")
        for s, (fx, t) in sorted(p.fix_at.items()):
            if skip is not None and skip[0] <= s < skip[1]:
                continue
            if lo <= t < hi:
                ins = p.insns.get(p.owner.get(s)) if s in p.owner else None
                txt = f"{ins.mnemonic} {ins.op_str}" if ins else "pointer data"
                W(f"  ptr   {t:#x} <- {s:05x} ({where(s)})  {txt}"
                  + (f" [+{t - lo}]" if t != lo else ""))

    def disasm(lo, hi):
        x = lo
        while x < hi:
            if x in e.labels:
                W(f"{e.labels[x]}:")
            if x in p.insns:
                i = p.insns[x]
                W(f"  {x:05x}  {e.insn_text(i) or i.mnemonic + ' ' + i.op_str}")
                x += i.size
            else:
                if x in p.fix_at:
                    W(f"  {x:05x}  dd {e.sym(p.fix_at[x][1])}")
                    x += 4
                else:
                    y = x
                    while y < hi and y not in p.insns and y not in p.fix_at:
                        y += 1
                    W(f"  {x:05x}  db {p.cbytes[x - p.code.base:y - p.code.base].hex()}")
                    x = y

    specs = a.specs or [f"{LO_DEFAULT:#x}-{HI_DEFAULT:#x}"]
    for spec in specs:
        if spec.startswith("CTX:"):
            parts = spec[4:].split(":")
            at = int(parts[0], 16)
            back = int(parts[1], 16) if len(parts) > 1 else 0x40
            fwd = int(parts[2], 16) if len(parts) > 2 else 0x40
            f = next((f for f in p.functions if f["start"] <= at < f["limit"]), None)
            owner = (f"{names.get(f['start'], hex(f['start']))} {f['start']:#x}..{f['limit']:#x}"
                     if f else "no function")
            W(f"\n=== context {at - back:#x}..{at + fwd:#x} (in {owner}) ===")
            disasm(at - back, at + fwd)
            continue
        if spec.startswith("DATA:"):
            parts = spec[5:].split(":")
            at = int(parts[0], 16)
            n = int(parts[1], 16) if len(parts) > 1 else 0x100
            raw = load_data(p, at, n)
            W(f"\n=== data {at:#x} +{n:#x} ===")
            if raw is None:
                W("  (not in the data object)")
                continue
            for off in range(0, n, 16):
                chunk = raw[off:off + 16]
                txt = "".join(chr(c) if 0x20 <= c < 0x7F else "." for c in chunk)
                W(f"  {at + off:05x}  {chunk.hex(' '):48} {txt}")
            W("  strings:")
            i = 0
            while i < n:
                z = raw.find(0, i)
                if z < 0:
                    z = n
                s = raw[i:z]
                if len(s) >= 2:
                    dec = cheat_decode(s)
                    plain = all(0x20 <= c < 0x7F for c in s)
                    ok = all(0x20 <= c < 0x7F for c in dec)
                    W(f"    {at + i:05x} raw={s!r}{' (plain)' if plain else ''}"
                      f" xor-decoded={dec!r}{'' if ok else ' (not printable)'}")
                i = z + 1
            for addr, txt, kind in strings_obf(p, at, n):
                W(f"    OBF {addr:05x} [{kind}] = {txt!r}")
            continue
        if spec.startswith("XREF:"):
            parts = spec[5:].split(":")
            t0 = int(parts[0], 16)
            t1 = t0 + (int(parts[1], 16) if len(parts) > 1 else 1)
            W(f"\n=== xrefs to {t0:#x}..{t1:#x} ===")
            refs_to(t0, t1)
            continue
        lo, hi = (spec.split("-") + [None])[:2]
        lo = int(lo, 16)
        hi = int(hi, 16) if hi else lo + 1
        W(f"\n=== range {lo:#x}..{hi:#x} ===")
        for f in p.functions:
            if not (lo <= f["start"] < hi):
                continue
            W(f"\n; {f['start']:#x}..{f['limit']:#x} ({f['limit'] - f['start']} bytes, "
              f"{f['ninsns']} insns) cross={[hex(c) for c in f['cross']]}")
            disasm(f["start"], f["limit"])
            callees = sorted({i.operands[0].imm & 0xFFFFFFFF for ia, i in p.insns.items()
                              if f["start"] <= ia < f["limit"] and i.mnemonic == "call"
                              and i.operands and i.operands[0].type == x86.X86_OP_IMM})
            W(";   calls: " + ", ".join(f"{names.get(c, hex(c))} [{where(c)}]" for c in callees))
            refs = sorted({t for s, (fx, t) in p.fix_at.items() if f["start"] <= s < f["limit"]})
            for r in refs:
                d = load_data(p, r, 40)
                s = cstr(p, r)
                info = []
                if s and len(s) >= 2 and all(0x20 <= c < 0x7F for c in s):
                    info.append(f"string {s!r}")
                    info.append(f"cheat-decoded {cheat_decode(s)!r}")
                elif d:
                    info.append("bytes " + d[:16].hex(' '))
                    info.append("dwords " + ", ".join(
                        hex(int.from_bytes(d[i:i + 4], "little")) for i in range(0, 32, 4)))
                W(f";   ref {r:#x} ({names.get(r, 'unnamed')}): " + " | ".join(info))
        if hi - lo > 1:
            W(f"; --- references into {lo:#x}..{hi:#x} ---")
            refs_to(lo, hi, skip=(lo, hi))

    out = a.out or path("build", "cmd_123f0", "dump.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
