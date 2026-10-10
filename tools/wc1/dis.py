"""Quick linear disassembly viewer with fixup annotations.

usage: python3 -m wc1.dis <addr-hex> [count] [--bytes]
"""
import sys

import capstone

from . import le as lefmt


def main():
    a = int(sys.argv[1], 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else 40
    e = lefmt.load()
    img = e.loaded_image()
    fix = {}
    for f in e.fixups_unique:
        fix[e.obj(f.obj).base + f.src_off] = (e.obj(f.target_obj).base + f.target_off) & 0xFFFFFFFF
    o = e.obj_at(a)
    buf = bytes(img[o.index])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    off = a - o.base
    cnt = 0
    while cnt < n and off < len(buf):
        ins = next(md.disasm(buf[off:off + 16], o.base + off, 1), None)
        if ins is None:
            print(f"{o.base+off:08x}: {buf[off]:02x}  (bad)")
            off += 1
        else:
            fx = [f"{s:x}->{fix[s]:x}" for s in range(ins.address, ins.address + ins.size) if s in fix]
            print(f"{ins.address:08x}: {ins.bytes.hex():24s} {ins.mnemonic} {ins.op_str}"
                  + (f"   ; fixup {' '.join(fx)}" if fx else ""))
            off += ins.size
        cnt += 1


if __name__ == "__main__":
    main()
