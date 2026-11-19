"""Byte-level diff with fixups masked, then the instruction context.

usage: python3 -m wc1.mod_2efd0_cmp <file.c> <orig-addr-hex> [n-bytes]

Compiles with the file's own headers (wc1.match.compile_c), masks the bytes
that the OMF marks as relocations (the linker would fill the target address
there) and compares against the original bytes at <orig-addr>.  The first
unmasked difference is reported with the disassembly of both sides up to and
including it, so a T3 near miss can be read instruction by instruction.
"""
import os
import re
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

from . import analysis, match, path

MD = Cs(CS_ARCH_X86, CS_MODE_32)


def compiled(src):
    os.makedirs(path("build", "mod_2efd0", "obj"), exist_ok=True)
    cc = match.file_cc(src)
    out = path("build", "mod_2efd0", "obj",
               os.path.splitext(os.path.basename(src))[0] + ".obj")
    mod = match.compile_c(src, None, out, cc=cc)
    data = bytearray()
    masked = set()
    for s in mod.segments:
        if s.cls != "CODE":
            continue
        base = len(data)
        data += s.data
        for fx in s.fixups:
            for k in range(fx.offset, fx.offset + fx.size):
                masked.add(base + k)
    return bytes(data), masked


def norm(ins):
    t = f"{ins.mnemonic} {ins.op_str}"
    t = re.sub(r"0x[0-9a-f]+", "#", t)
    t = re.sub(r"\b\d+\b", "#", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def insn_diff(mine, orig, addr):
    ms = list(MD.disasm(mine, 0))
    os_ = list(MD.disasm(orig, addr))
    for i in range(max(len(ms), len(os_))):
        a = ms[i] if i < len(ms) else None
        b = os_[i] if i < len(os_) else None
        if a and b and norm(a) == norm(b):
            continue
        print(f"instruction {i} differs:")
        for k in range(max(0, i - 6), min(i + 4, max(len(ms), len(os_)))):
            aa = ms[k] if k < len(ms) else None
            bb = os_[k] if k < len(os_) else None
            ta = f"{aa.address:04x} {aa.mnemonic} {aa.op_str}" if aa else "--"
            tb = f"{bb.address:05x} {bb.mnemonic} {bb.op_str}" if bb else "--"
            mark = "" if (aa and bb and norm(aa) == norm(bb)) else "  <<"
            print(f"  {ta:34}| {tb}{mark}")
        return
    print("instruction streams equal")


def main():
    src = sys.argv[1]
    addr = int(sys.argv[2], 16)
    limit = int(sys.argv[3], 0) if len(sys.argv) > 3 else None
    mine, masked = compiled(src)
    p = analysis.run()
    if limit is None:
        f = next((f for f in p.functions if f["start"] == addr), None)
        limit = (f["limit"] - addr) if f else len(mine)
    limit = min(limit, len(mine))
    orig = p.code.data[addr - p.code.base: addr - p.code.base + limit]
    first = None
    for i in range(limit):
        if i in masked:
            continue
        if mine[i] != orig[i]:
            first = i
            break
    print(f"# {src}: {len(mine)} bytes compiled, compared {limit}"
          f" ({'MATCH' if first is None else f'first diff at +{first:#x}'})")
    if first is None:
        return 0
    # disassemble both sides and print the instructions covering [first-24, first+8]
    lo = max(0, first - 0x20)
    hi = first + 0x10
    ms = [i for i in MD.disasm(mine[lo:hi], lo)]
    os_ = [i for i in MD.disasm(bytes(orig[lo:hi]), addr + lo)]
    print("  compiled                          | original")
    for i in range(max(len(ms), len(os_))):
        a = ms[i] if i < len(ms) else None
        b = os_[i] if i < len(os_) else None
        ta = f"{a.address:04x} {a.mnemonic} {a.op_str}" if a else ""
        tb = f"{b.address:05x} {b.mnemonic} {b.op_str}" if b else ""
        mark = ""
        if a and b and (a.mnemonic != b.mnemonic or a.op_str != b.op_str):
            mark = "  <<"
        print(f"  {ta:33}| {tb}{mark}")
    print("  compiled: " + " ".join(f"{x:02x}" for x in mine[lo:hi]))
    print("  original: " + " ".join(f"{x:02x}" for x in orig[lo:hi]))
    print()
    insn_diff(mine[:limit], bytes(orig), addr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
