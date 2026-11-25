# Developer Repair Assignment — Experiment E8 (`dev-e8-03`)

You are the fresh **Developer** (`dev-e8-03`) for **Experiment E8** (Original CU Boundary Evidence Validation), resolving a **HIGH methodological ground-truth defect** uncovered by independent adversarial review (`rev-e8-01`) in Corpus B1 (`real_corpus.py`).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e8`
- **Branch:** `research/build-codegen/e8` (HEAD: `766099e96d9eea57480a0afaf244287ad9433486`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly.

## Critical Ground-Truth Defect Uncovered by Independent Review (`rev-e8-01`)
Independent reviewer `rev-e8-01` audited `experiments/build_codegen/e8/real_corpus.py` (`libsig_corpus`) and proved that extrapolating single-unit `clib_sig` matches to full `[base, base + seglen)` extents WITHOUT verifying the entire code segment against `war.exe` contaminated Corpus B1 ground truth:
1. **Phantom overlapping module `cstrtx3r:cstrtx32`:** Only ONE tiny unit (`__exit_` at `0x34838`, which actually lies *inside* `clib3r:cstrt386`'s `__do_exit_with_msg__` at `0x34815..0x34850`!) matched `cstrtx32`, extrapolating a bogus extent `[0x3464b, ...)` overlapping `cstrt386`. Because `libsig_corpus` resolved overlaps via set intersection (`ka & kb`), pair `(0x34850, 0x34860)` — which is actually the real CU boundary after `cstrt386` ends at `0x3485b` (with 5 zero bytes before `0x34860`!) — was **mislabeled as `same_cu`**! That phantom overlap created bogus FPs for BOTH `zero16` and `style_transition` on Corpus B1!
2. **Unverified single-unit extrapolation (74 of 114 extents):** Any library object admitted to Corpus B1 MUST have its **entire code segment verified byte-for-byte** (masking relocation/fixup bytes from the OMF object!) against `war.exe` at `[base, base + seglen)` (and check that `war.exe` fixups match or are consistent), rather than blindly trusting a single-function signature hit!
3. **Overlap policy (fail closed):** Never label an adjacent pair using set intersection across overlapping extents. Either resolve to a single uniquely full-segment-verified library object, or exclude contested/overlapping regions from Corpus B1 cleanly (and report the exact exclusion count).
4. **Stub-table dominance check (`intxa386`):** `rev-e8-01` noted `('clib3r', 'intxa386', 1)` at `0x3b4b0..0x3b88e` contained 260 function starts (~58% of all 449 pairs in Corpus B1!). Inspect `intxa386` directly:
   - First check whether `intxa386`'s full segment actually matches `war.exe` (it may be a real 256-entry interrupt/stub table or a false match!).
   - If it IS genuinely present in `war.exe` with 250+ tiny interior labels, report BOTH the full verified `libsig` metrics AND a `libsig_without_intxa386` (or per-module-stratified) sensitivity check in `metrics.json` & `E8-cu-boundaries.md` so one assembly stub table does not silently swamp all compiler-generated C runtime pairs!

## Required Actions
1. Fix `experiments/build_codegen/e8/real_corpus.py` (`libsig_corpus`):
   - Enforce **full-segment masked byte verification** (every non-fixup byte in the library `.obj`'s `_TEXT`/CODE segment must match `war.exe` at `[base, base + seglen)`) before admitting any `.obj` extent to Corpus B1.
   - Reject overlapping extents (guarantee ZERO overlapping extents in admitted Corpus B1 ground truth; record rejected partial/overlapping candidates transparently in corpus metadata).
   - Verify what happens to `cstrtx32` (must be rejected!), `(0x34850, 0x34860)` (must NOT be mislabeled `same_cu`!), and `intxa386` (verify exact bytes + add sensitivity summary if legitimate).
2. Re-run `python3 -m experiments.build_codegen.e8.run_e8` to regenerate `docs/research/build-codegen/results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}` cleanly and deterministically (LF line endings, `sort_keys=True`, zero absolute paths, zero stray files in repo root).
3. Add regression tests in `experiments/build_codegen/e8/test_e8.py` proving:
   - Every admitted Corpus B1 extent passes full-segment masked byte verification against `war.exe`.
   - Zero admitted Corpus B1 extents overlap.
   - `cstrtx32` is NOT admitted and `(0x34850, 0x34860)` is NOT labeled `same_cu`.
   - `pytest -q experiments/build_codegen/e8/test_e8.py` passes 100%!
4. Update `docs/research/build-codegen/E8-cu-boundaries.md` so EVERY Corpus B1 count, confusion matrix, FP/FN example, epistemic classification, and summary matches the corrected verified `results/e8/` artifacts!
5. Verify zero production diffs (`git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty) and clean `git status`.
6. Commit 1 clean atomic repair commit on `research/build-codegen/e8`:
   - `exp(e8): enforce full-segment byte verification and non-overlap in Corpus B1 libsig ground truth`
