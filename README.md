# Warcraft: Orcs & Humans — source reconstruction

Evidence-driven decompilation of the DOS release of *Warcraft: Orcs & Humans*
(CD version 1.22h, `WAR.EXE`, Watcom C/C++32 + DOS/4GW).

The repository contains **tools, evidence and reconstructed source only**.
The game itself is never committed; everything is regenerated from your own
copy of the CD dump (`CD_DIC.rar`, Redump/DIC format).

## Quick start

```sh
nix develop                # toolchain: Open Watcom 2, NASM, Python+capstone/unicorn, Ghidra, DOSBox-X
cp /path/to/CD_DIC.rar .
make extract               # CD_DIC.rar -> original/ (every stage hash-verified)
make verify                # symbols + round-trip + C matches + build + tests
make run                   # boot build/war.exe headless, screenshots in build/run/
```

## How it works

1. **Extraction** (`tools/bootstrap.sh`): RAR → data track (MODE1/2352) →
   ISO9660 → `WAR.EXA` (an lh5 archive) → `war.exe`.
2. **Analysis** (`wc1.le`, `wc1.analysis`): LE parsing, then validated
   recursive-descent disassembly seeded by the entry point and every fixup
   target; 97.3% of the code object is decoded instructions/jump tables, the
   remainder verified data-in-code and alignment filler.
3. **Round-trip** (`wc1.emit`, `wc1.roundtrip`): the program is emitted as
   fully symbolic NASM; assembled at the original addresses it is
   byte-identical to the loaded image (99.4% as real instructions).
4. **Rebuild** (`wc1.build`): the same asm, linked with Open Watcom `wlink`
   into a DOS/4GW executable, is load-equivalent to the original (same
   objects, entry, stack, all 8770 fixups) and runs.
5. **Reconstruction**: functions are rewritten in C (`src/`), compiled with
   `wcc386`, and verified with `wc1.match` (identical code and relocation
   targets). Verified functions replace their asm in the build, linked at
   their original addresses, so the hybrid executable stays identical.

See `docs/METHODOLOGY.md` for the evidence/confidence model and verification
tiers, `docs/ANALYST_GUIDE.md` for tools and conventions, and
`docs/REFERENCES.md` for external sources (including the original module
list from the Insider's Guide).

## Status

See `docs/STATUS.md`.
