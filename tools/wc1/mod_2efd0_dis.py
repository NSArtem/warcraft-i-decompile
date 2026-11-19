"""Disassemble the code of a compiled C file next to the original bytes.

For iterating on a T3 attempt: `wc1.match` reports *where* bytes differ, this
shows *what* both sides are.  It compiles the file with its own
codegen-flags/-compiler headers (wc1.match.compile_c), reads the code
segments out of the OMF object and disassembles them; with `--orig <addr>` it
also disassembles the original function at that address from war.exe, so the
two can be compared instruction by instruction.

usage: python3 -m wc1.mod_2efd0_dis <file.c> [--orig 0x2f3dc] [--args "--os"]
"""
import argparse
import os
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

from . import analysis, match, omf, path

FLAGS = CS_ARCH_X86 | CS_MODE_32


def _md():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    return md


def compiled_code(src, extra_args=None):
    """Compile `src` and return [(segment_name, bytes)] for its code segments."""
    os.makedirs(path("build", "mod_2efd0", "obj"), exist_ok=True)
    cc = match.file_cc(src)
    out = path("build", "mod_2efd0", "obj",
               os.path.splitext(os.path.basename(src))[0] + ".obj")
    mod = match.compile_c(src, None, out, cc=cc)
    return [(s.name, s.data) for s in mod.segments if s.cls == "CODE"], mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--orig", type=lambda s: int(s, 16), default=None)
    ap.add_argument("--n", type=int, default=0, help="original byte count")
    a = ap.parse_args()
    md = _md()
    code, mod = compiled_code(a.src)
    print(f"# {a.src} ({match.file_cc(a.src)})")
    for name, data in code:
        print(f"## segment {name} ({len(data)} bytes)")
        for i in md.disasm(bytes(data), 0):
            print(f"  {i.address:04x}  {i.mnemonic:8} {i.op_str}")
    if a.orig is not None:
        p = analysis.run()
        n = a.n or 0x200
        buf = p.code.data[a.orig - p.code.base: a.orig - p.code.base + n]
        print(f"## original {a.orig:#x}")
        for i in md.disasm(bytes(buf), a.orig):
            print(f"  {i.address:05x}  {i.mnemonic:8} {i.op_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
