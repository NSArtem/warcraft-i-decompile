"""Scratch aid for mod_1b800: compile a C file (its own header flags/compiler),
disassemble the compiled code next to the original function and print a unified
diff of the instruction text (addresses removed, jump targets as offsets).

usage: python3 -m wc1.mod_1b800_dis <file.c> <orig_addr> [n_bytes]
"""
import difflib
import os
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

from . import analysis, match, path


def _lines(md, data, base):
    out = []
    for i in md.disasm(bytes(data), base):
        out.append(f"{i.address - base:04x} {i.mnemonic} {i.op_str}")
    return out


def main(argv):
    src, orig = argv[1], int(argv[2], 16)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    os.makedirs(path("build", "mod_1b800"), exist_ok=True)
    out = path("build", "mod_1b800", os.path.splitext(os.path.basename(src))[0] + ".obj")
    mod = match.compile_c(src, None, out, cc=match.file_cc(src))
    code = [s.data for s in mod.segments if s.cls == "CODE"]
    ours = _lines(md, code[0], 0)
    p = analysis.run()
    n = int(argv[3], 16) if len(argv) > 3 else 0x300
    buf = p.code.data[orig - p.code.base: orig - p.code.base + n]
    theirs = _lines(md, buf, 0)
    # cut the original at the first ret that is followed by filler: keep whole, diff trims
    strip = lambda ls: [l.split(" ", 1)[1] for l in ls]
    print(f"ours {len(ours)} insns, original window {len(theirs)}")
    for l in difflib.unified_diff(strip(theirs), strip(ours), "orig", "ours", lineterm="", n=2):
        print(l)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
