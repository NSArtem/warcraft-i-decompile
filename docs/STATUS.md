# Status

Last updated: 2026-10-10 (see CLAUDE.md for the hand-off and next steps).

## Pipeline (all mechanically verified, `make verify`)

| Stage | State |
|---|---|
| Reproducible environment | `flake.nix`: Open Watcom 2, NASM, Python (capstone, unicorn), Ghidra 12.1, DOSBox-X, Xvfb |
| Extraction | `tools/bootstrap.sh`: CD_DIC.rar → war.exe, every stage hash-checked against `analysis/provenance/` |
| LE parsing | 2 objects, entry 0x34584, 8770 off32 fixups |
| Code discovery | 1704 functions (incl. unreferenced ones found by gap scan and tail-jump-only entries), 17 switch tables; 97.3% of the code object decoded, rest verified data-in-code/filler |
| T1 round-trip | generated NASM reassembles byte-identically; 385 of 64305 instructions kept as raw bytes (encodings NASM can't express) |
| T2 relink | wlink output load-equivalent to the original (objects, entry, stack, fixups, image) and runs in DOSBox-X |
| T3 matching | `wc1.match` verifies C functions (code + relocation targets + module data) |
| T5 runtime | headless DOSBox-X runs with screenshots (`wc1.run`); hybrid build with C boots |

## Reconstruction

| Metric | Count |
|---|---|
| Functions reconstructed in C and matched (T3) | 1 (`InitPaths`) |
| Symbol DB entries | see `python3 -m wc1.symbols` |

## Paused (agents stopped; relaunch per CLAUDE.md)

runtime (clib), audio (AIL + game sound), modules (translation-unit layout),
ghidra (decompiler hints), resources (.WAR format, decompression), graphics
(video, blitters, FLIC, fonts, input).
