# Experiment E2 Contract & Developer Assignment — Compilation-Context Sensitivity & Intra-TU Alignment

## 1. Mission & Research Question

You are the Developer for **Experiment E2** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E2`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e2`
- **Branch:** `research/build-codegen/e2`
- **Baseline commit:** `<E0_MERGED_COMMIT>` (includes E0's strengthened `experiments/build_codegen/e0/matcher_proto.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
(a) What inter-function alignment (4-byte vs 16-byte), padding patterns, loop alignment, string pooling, and register-allocation behavior does Watcom C/C++ 10.0a actually emit inside multi-function objects across compiler flags (and how does this compare with Open Watcom 2 and `AGENTS.md`'s 16-byte alignment note)?
(b) Across a substantial sample of real existing T3 functions (`GAMEDLG.C`, `STATUS.C`, `PLAYFLIC.C`), how often do functions retain exact matching, lose matching, or gain matching when consolidated into multi-function TUs — and how sensitive are they to neighboring function edits?

**Hypothesis:**
Watcom 10.0a uses 4-byte inter-function alignment (unlike OW2's 16-byte alignment or under specific flags), and a high proportion of existing standalone T3 functions retain exact `FunctionMatch` under TU consolidation, with observable, categorizable causes for any regressions or gains.

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.5, §14 E2)
- `experiments/build_codegen/e0/matcher_proto.py` (use E0's strengthened matcher for ALL matching evaluations!)
- `src/gamedlg/*.c` (14 T3 functions), `src/status/*.c` (58 T3 functions), `src/playflic/*.c` (24 T3 functions)

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e2/` (experimental scripts, synthetic & consolidated temporary C fixtures, pytest suite)
- `docs/research/build-codegen/E2-compilation-context.md`
- `docs/research/build-codegen/results/e2/` (machine-readable JSON/CSV results)

**STRICTLY PROHIBITED:**
- Do NOT modify any production file under `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT run `make verify` directly.

## 4. Technical Requirements

### 4.1 Part A — Synthetic Alignment & Context Sensitivity Matrix
Build deterministic synthetic C fixtures in `experiments/build_codegen/e2/fixtures/` testing:
1. **Inter-function alignment & padding:** Multiple functions of varied body lengths (e.g., ~5, 11, 17, 23 bytes) compiled under Watcom 10.0a across `-3r`, `-4r`, `-5r`, `-ot`, `-os`, `-od`, `-d1+`, `-ol`, `-oa`, `-or` AND Open Watcom 2 (`-4r -ot -ol`, `-5r -ot -ol`)! Measure exact function start offsets (mod 4 / mod 16), exact filler byte sequences (`nop`, `mov eax,eax`, `lea eax,[eax+0]`, `0x00`), and `_TEXT` segment alignment attribute (`SEGDEF`).
2. **Internal loop alignment:** Loops (`for`/`while`) inside functions at varied starting offsets mod 16 under `-3r`/`-4r`/`-5r`/`-ot`/`-os`/`-ol` to check whether shifting a function's `_TEXT` start offset changes loop alignment bytes!
3. **String pooling & shared static data:** Identical string literals across two functions in the same TU (does Watcom 10.0a merge them in `CONST`, and what alignment/padding does `CONST` use under `-ot` vs `-os`?), plus `static` variables and `static` vs `extern` intra-TU calls (does Watcom 10.0a alter register allocation, inlining, or calling convention across `static` vs non-static callees?).

### 4.2 Part B — Large Real-World T3 Consolidation Study
Do NOT use a tiny sample! Programmatically consolidate ALL eligible standalone T3 functions from three representative real areas (total **~80–96 T3 functions**; record exact selection criteria and any excluded files with reasons!):
1. **`GAMEDLG.C`** (all 14 T3 functions, sorted in original address order; note flag homogeneity and `CONST`/`_DATA` interactions!)
2. **`PLAYFLIC.C`** (all 24 T3 functions, sorted in original address order)
3. **`STATUS.C`** (all 58 T3 functions, or contiguous T3 runs / full area consolidation, sorted in original address order; group by flag compatibility if flags differ across the area, AND also test one forced single-flag consolidation to measure flag-heterogeneity impact!)

For EVERY consolidated group:
- Compile each function standalone (baseline control: verify 100% E0 `FunctionMatch` under declared flags).
- Compile the consolidated multi-function TU under Watcom 10.0a (testing primary area flags + `-4r`/`-5r`/`-ot`/`-os`/`-oa`/`-ol` variants).
- Evaluate EVERY function using E0's strengthened `matcher_proto.py` (NOTE: evaluate BOTH per-function `FunctionMatch` on `[fn_off, next_fn_off)` AND check contiguous original-adjacent runs for `RegionMatch` and inter-function relative offsets!).
- Record exact metrics:
  - `n_tested`, `n_retained_match`, `n_lost_match`, `n_gained_match` (if including non-T3 neighbors or flag variants),
  - Exact root cause for EVERY function that changed or lost matching (e.g., inter-function filler/offset shift, `CONST` data-segment base collision across non-contiguous T3s, shared epilogue emitted, register allocation change, `static` symbol collision, flag mismatch across functions in group),
  - Distinguish **genuine codegen change** (compiled instruction bytes of function body changed!) from **expected non-contiguous data-anchor shift** (e.g., consolidating non-adjacent T3s whose `CONST` strings aren't adjacent in `war.exe`!) — report BOTH clearly so metrics are never misleading!

### 4.3 Part C — Neighbor-Perturbation Sensitivity ("Domino Effect" Probe)
Take at least 2 consolidated matching TUs (e.g. a contiguous `PLAYFLIC.C` T3 run and a contiguous `STATUS.C` T3 run) and systematically perturb one neighboring function (change body length by +1/+2/+3/+7 bytes, add a string literal, add register pressure, add an epilogue pattern) and measure whether and how neighboring functions' machine bytes or matching verdicts change!

## 5. Deliverables, Acceptance Criteria & Atomic Commits

Deliverables:
- `experiments/build_codegen/e2/` (synthetic fixtures, consolidation generator, `run_e2.py`, `test_e2.py`)
- `docs/research/build-codegen/results/e2/results.json` & `consolidation_rows.csv`
- `docs/research/build-codegen/E2-compilation-context.md` (with sample size, selection method, uncertainty / Wilson 95% CI where appropriate, OW2 vs 10.0a alignment proof, and exact categorization of all observed changes)

Acceptance criteria:
1. `pytest -q experiments/build_codegen/e2/test_e2.py` passes 100%.
2. `python3 -m experiments.build_codegen.e2.run_e2` reproduces `results.json` and `consolidation_rows.csv`.
3. Zero production modifications (`git diff <BASE> -- tools/ src/ analysis/ tests/ Makefile` is empty).
4. 2–3 clean atomic commits on `research/build-codegen/e2`:
   - Commit 1: `exp(e2): synthetic alignment/context probes and real T3 consolidation harness + tests`
   - Commit 2: `exp(e2): empirical results and E2 compilation-context sensitivity report`
5. End with a concise summary: commit SHAs, Watcom 10.0a vs OW2 alignment findings, exact sample size & retention/loss/gain counts (separating genuine codegen changes from data-anchor collisions), domino-effect findings, and reproduction commands.
