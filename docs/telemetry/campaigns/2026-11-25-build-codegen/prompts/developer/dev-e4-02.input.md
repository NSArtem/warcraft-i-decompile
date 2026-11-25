# Developer Handoff Assignment — Experiment E4 (`dev-e4-02`)

You are the fresh successor **Developer** (`dev-e4-02`) for **Experiment E4** (Selective OMF Extraction Feasibility). Your predecessor (`dev-e4-01`) timed out at 1800s **after** completing `experiments/build_codegen/e4/omf_extract.py`, all fixtures, `run_e4.py`, and deterministic `docs/research/build-codegen/results/e4/results.json` (proving BOTH `ScoreTickIncome` and `FarmPanelChanged` link to Build A `IDENTICAL` with 0 byte diffs and 8,770/8,770 LE fixups, plus controlled `A->C` + E5 Fix B3 `CONST` anchor, >1024 B multi-chunk `LEDATA`, and all 6 fail-closed negative controls N1–N6) — right as it was about to write `test_e4.py`, `E4-omf-extraction.md`, and make the atomic commits!

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e4`
- **Branch:** `research/build-codegen/e4` (baseline: `654711eb32f5ef7c84c46e108e5a1435c2011a73`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `wlink`, `nasm`, `git` directly.

## Already Completed Checkpoint in Worktree
- `experiments/build_codegen/e4/{__init__.py,omf_extract.py,run_e4.py}`
- `experiments/build_codegen/e4/fixtures/{__init__.py,builder.py,support.py,controlled_tu.c,direct_call.asm,interior_call.asm,data_provider.asm,runtime.asm}`
- `docs/research/build-codegen/results/e4/results.json`

## Your Bounded Tasks
1. Read `docs/research/build-codegen/contracts/E4-contract.md` and inspect `experiments/build_codegen/e4/omf_extract.py` (especially `_check_original_bytes` which `dev-e4-01` edited right before timeout!), `run_e4.py`, `fixtures/`, and `docs/research/build-codegen/results/e4/results.json`.
2. Re-run `python3 -m experiments.build_codegen.e4.run_e4` and confirm:
   - Completes cleanly (~20s) after `dev-e4-01`'s last edit to `_check_original_bytes`.
   - `results.json` is 100% deterministic across repeated runs, contains zero absolute worktree/temp paths or timestamps, and leaves ZERO stray files in repo root.
   - Double-check all Watcom 10.0a compiles go through short paths (<=112 chars, via E5's `wcc10a.py` or equivalent) so E4 also works cleanly in a longer review worktree path!
3. Write a thorough `experiments/build_codegen/e4/test_e4.py` testing:
   - Positive Case 1: `ScoreTickIncome` (`0x24e90`) extraction from multi-function `score_reference` -> E3 `RegionMatch` + byte-invariant check + Build A `IDENTICAL` (`0` byte diffs, `8,770/8,770` LE fixups).
   - Positive Case 2: `FarmPanelChanged` (`0x28254`) extraction from `panel_state_reference.c` (with mismatching sibling `UnitPanelStateChanged` + externalized call + 5 data relocations) -> Build A `IDENTICAL` (`0` byte diffs, `8,770/8,770` LE fixups).
   - Positive Case 3: Controlled `A -> C` across mismatching `B` (both compiled `EXTDEF`/seg fixup AND direct unfixed `call rel32` -> `EXTDEF + FIXUPP32(self_rel=True)`) + E5 Fix B3 `wc1_anchor_*` verified `CONST` literal -> oracle `IDENTICAL`.
   - Positive Case 4: Multi-chunk >1024 B `LEDATA` with 4-byte fixup straddling byte 1022–1026 -> split cleanly before fixup slot and linked `IDENTICAL`.
   - All 6+ Fail-Closed Negative Controls: N1 (`DialogHighlightOn` AND real `DialogHighlightOff` `0x16d48` outgoing `rel8`), N2 (interior target), N3 (ambiguous/unknown symbol identity), N4 (unproven mutable data layout), N5 (incorrect relocation target), N6 (incomplete closure / shared jump table).
   - Byte-invariant self-check (deliberately mutating a non-relocated byte fails closed) and `results.json` determinism / path-free check.
   - Run `pytest -q experiments/build_codegen/e4/test_e4.py` and confirm **100% pass**!
4. Write `docs/research/build-codegen/E4-omf-extraction.md` grounded strictly in `results.json`:
   - Architecture & invariants (RFC §6.1–6.4 Post-Codegen Symbolic Relocation Equivalence, E3 RegionMatch precondition, E5 Fix B3 `wc1_anchor_*` integration, `LEDATA32` <= 1024 B chunking, `THREAD` expansion, byte-invariant assertion).
   - All 4 positive cases with exact digests, relocation transformation provenance, and Build A / oracle compare results.
   - Honest explanation of why `DialogHighlightOff` (`0x16d48`) is a real fail-closed negative control (N1b, matching E3's refutation) rather than extractable standalone.
   - All 6 negative control classes with exact rejection codes.
   - Scope/trust boundary & exact reproduction commands.
5. Verify zero production diffs (`git diff 654711eb -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty) and clean `git status`.
6. Make 3 clean atomic commits on `research/build-codegen/e4`:
   - `exp(e4): conservative OMF32 selective slice extractor enforcing relocation equivalence` (staging `experiments/build_codegen/e4/{__init__.py,omf_extract.py,fixtures/}`)
   - `exp(e4): Build A IDENTICAL extraction tests and 6 fail-closed negative controls` (staging `experiments/build_codegen/e4/{run_e4.py,test_e4.py}` and `docs/research/build-codegen/results/e4/results.json`)
   - `docs(e4): E4 selective OMF extraction results and feasibility report` (staging `docs/research/build-codegen/E4-omf-extraction.md`)
