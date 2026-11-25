# Developer Assignment — Experiment E4 (`dev-e4-01`)

You are the **Developer** for **Experiment E4** (Selective OMF Extraction Feasibility) of the Build & Codegen Infrastructure research campaign.

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e4`
- **Branch:** `research/build-codegen/e4`
- **Baseline commit:** `ed21ca38feadcadf7e5ba62feed65430d957a6af` (includes E0 `matcher_proto.py`, E3 `partial_matcher.py`, and E5 `omf_b3.py` + `build_e5.py` + `wcc10a.py`!)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `wlink`, `nasm`, `git` directly.

## Contract & Mandatory Reading
Read `docs/research/build-codegen/contracts/E4-contract.md` in full, plus:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§6.1–6.4, §7.1, §14 E4)
- `experiments/build_codegen/e0/matcher_proto.py`
- `experiments/build_codegen/e3/partial_matcher.py` (and `docs/research/build-codegen/E3-partial-matching.md`)
- `experiments/build_codegen/e5/omf_b3.py`, `experiments/build_codegen/e5/build_e5.py`, `experiments/build_codegen/e5/wcc10a.py`
- `tools/wc1/omf.py`, `tools/wc1/omfpatch.py`, `tools/wc1/build.py`

## Critical Engineering Lessons from Earlier Campaign Experiments (MUST FOLLOW)
1. **Reuse E5's short-path Watcom 10.0a compiler helper (`wcc10a.py` / `build_e5.py`)!** Watcom 10.0a `wcc386.exe` crashes with an Access Violation if source or `-i=` paths exceed ~128 chars. Always compile via short paths (<= 112 chars) so E4 works cleanly from ANY checkout path length (including 160+ char review worktrees)!
2. **Cross-worktree determinism:** NEVER embed absolute checkout paths, temp paths, timestamps, or host-specific fields in `docs/research/build-codegen/results/e4/results.json`. Also remember Watcom 10.0a `THEADR`/`COMENT`/`$$TYPES` records carry compiler-facing paths — for deterministic hashes across checkouts, either hash loadable OMF records / canonical normalized JSON OR use E5's deterministic short-mirror convention and explicitly document what each SHA-256 covers!
3. **E3 empirical finding on `DialogHighlightOff` (`0x16d48`):** E3 proved that under `-s -os -ol -4r -zp2`, Watcom folds `DialogHighlightOn_` and `DialogHighlightOff_` onto offset `0x5f` and its `je 0x16d31` branches outside the slice into `DialogItemHitTest`'s epilogue. Therefore:
   - Prove full **Build A `IDENTICAL` (`0` byte diffs, `8,770/8,770` LE fixups)** extraction on BOTH **`ScoreTickIncome` (`0x24e90`)** (from E3's `score_reference` fixture with `sum = delta + score` and mismatching siblings `RankName`/`ScoreSetPage`) AND **`FarmPanelChanged` (`0x28254`)** (from `src/status/panel_state_reference.c` with mismatching sibling `UnitPanelStateChanged` `0x281f4`, 5 absolute data relocations, and externalized call to `UnitPanelStateChanged`)!
   - Also prove **Positive Case 3** (controlled `A -> C` across mismatching `B` intra-TU `call rel32` -> `EXTDEF + FIXUPP32(self_rel=True)` conversion — test BOTH a compiled `EXTDEF`/seg-fixup call AND a direct unfixed `call rel32` fixture! — plus E5 Fix B3 `wc1_anchor_*` data-anchor integration on a slice with a verified `CONST` literal) AND **Positive Case 4** (multi-chunk >1024 B `LEDATA` with a 4-byte fixup straddling byte 1022–1026 safely split and linked by `wlink`)!
   - Test BOTH `DialogHighlightOn` AND real `DialogHighlightOff` as **N1 outgoing `rel8` fail-closed negative controls**, alongside N2 (interior target), N3 (ambiguous/unknown symbol), N4 (unproven mutable data layout), N5 (incorrect relocation target), and N6 (incomplete dependency closure / shared jump table)!
4. **Hard invariants (RFC §6.2):**
   - Verify the slice passes E3 `RegionMatch` BEFORE extraction!
   - Assert byte-for-byte identity of EVERY non-relocated byte in the extracted `_TEXT` vs `orig_compiled_text[obj_lo:obj_hi]` (zero opcode/length/register/non-address-immediate mutations!).
   - NEVER convert `rel8` to `rel32`. NEVER infer unknown compiled targets solely from `war.exe`.
   - Zero edits to `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, `AGENTS.md`. Keep all build/temp outputs under `build/e4/`.

## Deliverables & Acceptance Criteria
1. `experiments/build_codegen/e4/{__init__.py,omf_extract.py,fixtures/,run_e4.py,test_e4.py}`
2. `docs/research/build-codegen/results/e4/results.json` (preserving compiled/extracted object digests, relocation transform provenance records, Build A compare verdicts for `ScoreTickIncome` and `FarmPanelChanged`, controlled `A -> C` + `CONST` + >1024 B chunking results, and N1–N6 fail-closed records)
3. `docs/research/build-codegen/E4-omf-extraction.md`
4. `python3 -m experiments.build_codegen.e4.run_e4` reproduces `results.json` deterministically, `pytest -q experiments/build_codegen/e4/test_e4.py` passes 100%, zero production diffs.
5. 2–3 clean atomic commits on `research/build-codegen/e4`:
   - `exp(e4): conservative OMF32 selective slice extractor enforcing relocation equivalence`
   - `exp(e4): Build A IDENTICAL extraction tests and 6 fail-closed negative controls`
   - `docs(e4): E4 selective OMF extraction results and feasibility report`
