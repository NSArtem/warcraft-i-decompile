# Experiment E8 Contract & Developer Assignment — Original CU Boundary Evidence Validation

## 1. Mission & Research Question

You are the Developer for **Experiment E8** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E8`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e8`
- **Branch:** `research/build-codegen/e8`
- **Baseline commit:** `c946f3854c9fa424f4b47e5305655f8d4a9b6d22` (includes E0 and E7's calibration `S(f)` dataset!)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
What are the empirical precision, recall, false-positive rates, false-negative rates, and reliability classifications (`Proven constraint` vs `Strong evidence` vs `Weak/Ambiguous heuristic`) of each proposed CU boundary signal (`zero16`, `zero4`, `zero2`, hidden `none16` boundaries, codegen style transitions, function start alignment, shared epilogues, `CONST` string-pool windows/sharing, private `_DATA`/`_BSS` staircases, compiler flag compatibility `S(f)` from E7, and cross-function call/reference locality) when evaluated against **independent ground truth** (Mandatory Correction R4)?

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§9.1–9.3, §14 E8)
- `docs/subsystems/modules.md`, `tools/wc1/modules_scan.py`, `tools/wc1/codegen_survey.py`, `tools/wc1/clib_sig.py`, `tools/wc1/modules_setup.py`, `analysis/modules.toml`
- `docs/research/build-codegen/results/e7/calibration_matrix.json` & `cu_hypotheses.json` (for `S(f)` signal evaluation!)

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e8/` (synthetic ground-truth corpus builder using Watcom 10.0a + wlink, real independent ground-truth extractor, signal evaluator, runner, pytest suite)
- `docs/research/build-codegen/E8-cu-boundaries.md`
- `docs/research/build-codegen/results/e8/` (machine-readable JSON/CSV confusion matrices and corpus manifests)

**STRICTLY PROHIBITED:**
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- **Mandatory Correction R4:** NEVER use boundaries inferred by heuristic X as ground truth for evaluating heuristic X! Strictly separate (1) synthetic Watcom 10.0a + `wlink` ground truth, (2) independently verified real ground truth (Watcom 10.0a `libsig` object modules and `setup.exe` sharing boundaries established independently of `zero16`/data-staircase signals), and (3) unverified real game candidates (reported separately as exploratory observations, NEVER mixed into ground-truth precision/recall!).
- Do NOT present inferred historical source filenames or module boundaries as established facts.

## 4. Technical Requirements

### 4.1 Independent Ground-Truth Corpus A — Synthetic Watcom 10.0a + `wlink` Linked Executables (`synthetic_corpus.py`)
Build a realistic multi-CU synthetic corpus compiled with **real Watcom C/C++ 10.0a** (`wcc386.exe` via `wc1.oldcc`) and linked with **`wlink system dos4g`** into real DOS/4GW LE executables under `build/e8/` (preserving exact object composition, link order, compiler flags per CU, and linker `.map` ground-truth symbol/segment addresses!):
- Include **at least 15–20 distinct CUs** (~60–80 functions total) spanning all realistic edge cases:
  1. Standard PARA-aligned CUs leaving 1..15 zero bytes (`zero16` positive ground truth).
  2. **Hidden `none16` boundaries:** CUs engineered so their `_TEXT` length is an exact multiple of 16 bytes -> 0 zero bytes before the next CU! (Measures exact recall gap of `zero16`!)
  3. **In-CU 16-byte-aligned interior functions (`none16` non-boundary):** Functions inside the SAME CU that happen to land at `addr % 16 == 0`!
  4. **Compiler style transitions:** Adjacent CUs compiled with OPT (`-s -ot -ol -4r -zp2`), DBG (`-d1+`), OD (`-od`), `-5r`, `-os`, and `-oa` (including an OPT CU adjacent to an OPT CU with DIFFERENT `-4r` vs `-5r` flags!).
  5. **Shared epilogues:** Two functions inside the same CU that trigger Watcom 10.0a cross-function shared epilogues (merge signal!).
  6. **String pooling & `CONST`/`_DATA`/`_BSS`:** CUs with private strings (`CONST`), shared identical string literals within a CU vs across CUs, global cross-CU `_DATA`/`_BSS` pollution (deliberately testing false positives of `_DATA`/`_BSS` staircase heuristics!), and multi-function CUs with cross-CU call traffic.
  7. **Hand-written NASM (`align=2`/`align=4`) object modules** linked alongside Watcom 10.0a C modules to test `zero2`/`zero4` boundaries!

### 4.2 Independent Ground-Truth Corpus B — Real `war.exe` Independently Established Boundaries (`real_corpus.py`)
Extract ONLY boundaries in `war.exe` whose ground truth is established **independently** of the evaluated padding/data-staircase/flag heuristics:
- **Watcom 10.0a `libsig`-matched runtime modules** (using `original/watcom/10.0a/lib386/dos/clib3r.lib` object module boundaries via `wc1.omf.parse_library` + `analysis/symbols/clib.toml` `libsig:` entries — knowing which consecutive functions belong to the same `.obj` vs different `.obj` in `clib3r.lib`!).
- **Independently established `setup.exe` shared-vs-unshared transitions** (where `original/install/setup.exe` is present; check if `setup.exe` exists under `original/` — if present, use it; if absent, document cleanly and rely on `clib3r.lib` + synthetic corpus!).
- **Separately** (clearly labeled as *inferred/exploratory real game analysis, NOT ground truth!*): apply the evaluated signals + E7's `S(f)` clusters to `war.exe`'s game range (`0x104b0..0x3024e`), highlighting where signals agree, disagree, or flag candidate `none16` splits inside large chunks (`mod_13f60`, `mod_16390`, `mod_1f050`, `STATUS.C`, etc.)!

### 4.3 Signal Evaluation & Metrics (`evaluate_signals.py`)
Evaluate every signal across Corpus A (synthetic) and Corpus B (real independent ground truth):
- Split signals: `zero16`, `zero4`, `zero2`, `none16` (baseline), `style_transition` (OPT/DBG/OD/LEAVE), `const_window_break`, `data_bss_staircase_break`, `flag_set_S_disjoint` (from E7 / synthetic known flags), `call_locality_drop`.
- Merge signals (same-CU evidence): `non_16_aligned_start` (`addr % 16 != 0` for C code), `shared_epilogue`, `shared_const_string_literal`, `exclusive_static_data_sharing`.
- Report for EACH signal on EACH ground-truth corpus:
  - `TP`, `FP`, `TN`, `FN`, `precision`, `recall`, `F1`, `sample_size`
  - Concrete examples of observed false positives and false negatives
  - Explicit epistemic classification per RFC §9.2 (`Proven constraint` with stated assumptions, `Strong evidence`, `Weak/Ambiguous heuristic`, `Unreliable/Noisy`)!

## 5. Deliverables, Acceptance Criteria & Atomic Commits
- Deliverables: `experiments/build_codegen/e8/{synthetic_corpus.py,real_corpus.py,evaluate_signals.py,run_e8.py,test_e8.py}`, `docs/research/build-codegen/results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}`, `docs/research/build-codegen/E8-cu-boundaries.md`.
- `pytest -q experiments/build_codegen/e8/test_e8.py` passes 100%; `python3 -m experiments.build_codegen.e8.run_e8` reproduces all results deterministically; zero production diffs.
- 2–3 clean atomic commits:
  1. `exp(e8): synthetic Watcom 10.0a + wlink ground-truth corpus and real libsig extractor`
  2. `exp(e8): CU boundary signal evaluator, metrics, and pytest suite`
  3. `docs(e8): E8 CU boundary evidence validation report`
