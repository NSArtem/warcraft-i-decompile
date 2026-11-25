# Developer Assignment — Experiment E8 (`dev-e8-01`)

You are the **Developer** for **Experiment E8** (Original CU Boundary Evidence Validation) of the Build & Codegen Infrastructure research campaign.

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e8`
- **Branch:** `research/build-codegen/e8`
- **Baseline commit:** `c946f3854c9fa424f4b47e5305655f8d4a9b6d22` (includes E0 matcher and E7 calibration `S(f)` dataset!)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wlink`, `nasm`, `git` directly.

## Contract & Mandatory Reading
Read `docs/research/build-codegen/contracts/E8-contract.md` in full, plus:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§9.1–9.3, §14 E8)
- `docs/subsystems/modules.md`, `tools/wc1/modules_scan.py`, `tools/wc1/codegen_survey.py`, `tools/wc1/clib_sig.py`, `tools/wc1/modules_setup.py`, `analysis/modules.toml`
- `docs/research/build-codegen/results/e7/calibration_matrix.json` & `cu_hypotheses.json`

## Critical Engineering Lessons from Earlier Campaign Experiments (MUST FOLLOW)
1. **Watcom 10.0a path-length bug (E2/E5/E7):** Watcom 10.0a `wcc386.exe` crashes with an Access Violation if source or `-i=` paths exceed ~128 characters! Always invoke Watcom 10.0a compiles using short paths (e.g., via a short temporary symlink under `/tmp` or short `cwd`/relative paths <= 100 chars; see `experiments/build_codegen/e7/common.py` for a clean pattern) so your synthetic corpus builder works cleanly from ANY checkout path length (including 160+ char review worktrees!).
2. **Cross-worktree determinism:** NEVER embed absolute checkout paths, temp paths, timestamps, or host-specific fields in `docs/research/build-codegen/results/e8/*.{json,csv}`. Write CSV files with explicit `lineterminator='\n'` (LF, not CRLF) and JSON with `sort_keys=True`. Re-running `python3 -m experiments.build_codegen.e8.run_e8` from a different worktree path must produce byte-identical JSON/CSV artifacts!
3. **Mandatory Correction R4 (No Circular Ground Truth):**
   - Strictly separate:
     - **Corpus A (Synthetic Watcom 10.0a + `wlink` Ground Truth):** 15–20+ CUs (~60–80 functions) compiled with real Watcom 10.0a (and NASM for `zero2`/`zero4`) and linked with real `wlink system dos4g` into real LE executable(s) under `build/e8/`, with exact ground-truth CU ownership from the build recipe & linker `.map` file. Include all 7 required edge cases from the contract (PARA `zero16`, exact-16B-multiple hidden `none16`, in-CU 16B-aligned interior functions, OPT/DBG/OD/`-5r`/`-os`/`-oa` transitions including adjacent `-4r` vs `-5r`, shared epilogues, private vs cross-CU string pooling & deliberate cross-CU `_DATA`/`_BSS` pollution, and NASM `align=2`/`align=4` modules).
     - **Corpus B (Real `war.exe` Independent Ground Truth):** ONLY boundaries established independently of the evaluated signals:
       - Watcom 10.0a `libsig`-matched runtime modules from `original/watcom/10.0a/lib386/dos/clib3r.lib` + `analysis/symbols/clib.toml` (`libsig:` entries) — consecutive functions in the same `.obj` vs different `.obj` in `clib3r.lib`!
       - Check if `original/install/setup.exe` (or any `setup.exe` under `original/`) exists; if present, include independent `setup.exe` shared-vs-unshared boundary transitions; if absent, document cleanly and keep Corpus B purely `libsig`-backed.
     - **Exploratory Game Analysis (SEPARATE, NEVER mixed into precision/recall):** Apply the evaluated signals + E7's `S(f)` clusters to `war.exe`'s game range (`0x104b0..0x3024e`), clearly labeled as *exploratory/inferred (non-ground-truth)*, highlighting signal agreements, disagreements, and candidate hidden `none16` splits inside large chunks (`mod_13f60`, `mod_16390`, `mod_1f050`, `STATUS.C`, etc.).
4. **Scope & Prohibition:** Only write under `experiments/build_codegen/e8/`, `docs/research/build-codegen/results/e8/`, and `docs/research/build-codegen/E8-cu-boundaries.md`. Zero edits to `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, `AGENTS.md`. Do NOT run `make verify`.

## Deliverables & Acceptance Criteria
1. `experiments/build_codegen/e8/{__init__.py,synthetic_corpus.py,real_corpus.py,evaluate_signals.py,run_e8.py,test_e8.py}`
2. `docs/research/build-codegen/results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}`
3. `docs/research/build-codegen/E8-cu-boundaries.md` with confusion matrices (`TP/FP/TN/FN/precision/recall/F1/sample_size`), concrete observed FP/FN examples, and explicit epistemic classifications (`Proven constraint`, `Strong evidence`, `Weak/Ambiguous heuristic`, `Unreliable/Noisy`) for every split and merge signal on both corpora, plus exploratory game observations.
4. `python3 -m experiments.build_codegen.e8.run_e8` reproduces all artifacts deterministically, and `pytest -q experiments/build_codegen/e8/test_e8.py` passes 100% (include a test checking no circular leakage between corpora and checking LF/determinism).
5. 2–3 clean atomic commits on `research/build-codegen/e8`:
   - `exp(e8): synthetic Watcom 10.0a + wlink ground-truth corpus and real libsig extractor`
   - `exp(e8): CU boundary signal evaluator, metrics, and pytest suite`
   - `docs(e8): E8 CU boundary evidence validation report`
