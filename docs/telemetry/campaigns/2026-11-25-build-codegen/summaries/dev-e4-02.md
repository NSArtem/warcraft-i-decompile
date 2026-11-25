I'll start by reviewing the contract and the checkpoint work left by my predecessor.
Now I'll write the test suite.
Now the report document.
E4 is complete on `research/build-codegen/e4`. Summary of what I verified and delivered as `dev-e4-02`:

## Verification of the checkpoint
- `python3 -m experiments.build_codegen.e4.run_e4` completes in **~20 s** after `dev-e4-01`'s `_check_original_bytes` edit.
- `results.json` reproduced byte-for-byte across separate runs (SHA-256 `892d3bee…e3eb043`), contains **zero** absolute checkout/temp/mirror paths or timestamps, and the runner adds **no file to the repo root**.
- All Watcom 10.0a compiles (both real cases, the controlled TU, every baseline object) go through E5's short mirror (`build_e5.compile_10a` → `/tmp/wc1e5-<hash>/repo`, `COMPILER_PATH_LIMIT=112`), and the suite now asserts that bound, so deeper review worktrees are safe.

## New tests (`test_e4.py`, 17 passing, ~30 s)
- Positive 1 `ScoreTickIncome` (0x24e90): E3 `VerifiedRegion`, byte-invariance over 53 non-relocated bytes, 6 data transforms, Build A `IDENTICAL`, 0 diffs, 8770/8770 LE fixups.
- Positive 2 `FarmPanelChanged` (0x28254): sibling mismatch, intra-TU call kept as `EXTDEF`+self-rel `FIXUPP32`, 5 data refs, Build A `IDENTICAL`.
- Positive 3/3b: controlled `A→C` across mismatching `B` (compiled fixup form and NASM bare `rel32` form) + E5 Fix B3 `wc1_anchor_20000` CONST literal → oracle `IDENTICAL`; also proves OMF16→32 widening and THREAD expansion/round-trip.
- Positive 4: >1024 B `LEDATA32` split at 1022 before the straddling 4-byte field, chunks verified in the emitted records.
- All 8 negative controls (N1 on/off incl. real `DialogHighlightOff` 0x16d48, N2–N6 plus mis-anchored N4b) with exact reason codes; byte-invariant self-check with a deliberately mutated non-address immediate; chunk-planner, checksum/MODEND and loadable-digest unit checks; results determinism/path-free check.
- Added `conftest.py` (same namespace-path bootstrap as E1/E5) so `pytest -q experiments/build_codegen/e4/test_e4.py` works with the console CLI.

## Report
`docs/research/build-codegen/E4-omf-extraction.md` covers the RFC §6.1–6.4 invariant, E3 precondition, E5 Fix B3 integration, 1024-byte chunking, THREAD expansion, byte invariance, all digests/transform provenance, all controls, the honest `DialogHighlightOff` N1b explanation, scope/trust boundary, and reproduction commands.

## Commits (atomic, on `research/build-codegen/e4`)
1. `02e43f6 exp(e4): conservative OMF32 selective slice extractor enforcing relocation equivalence`
2. `a82e572 exp(e4): Build A IDENTICAL extraction tests and 6 fail-closed negative controls`
3. `1a32b17 docs(e4): E4 selective OMF extraction results and feasibility report`

Production diff (`tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` vs `654711eb`) is empty; working tree is clean apart from the pre-existing untracked `original` symlink.