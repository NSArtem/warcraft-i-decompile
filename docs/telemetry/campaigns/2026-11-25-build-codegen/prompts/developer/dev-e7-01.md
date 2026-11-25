# Experiment E7 Contract & Developer Assignment — Original Compiler Calibration (Watcom 10.0a)

## 1. Mission & Research Question

You are the Developer for **Experiment E7** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E7`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e7`
- **Branch:** `research/build-codegen/e7`
- **Baseline commit:** `7c23d2371e95d8de93f0ba1652c8d44b858da273` (includes approved E0 `experiments/build_codegen/e0/matcher_proto.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
1. Which compiler options are genuinely supported by Watcom C/C++ 10.0a (`wcc386.exe`), and how do they affect codegen on real Warcraft I functions?
2. Across ALL `519` existing T3 functions AND ALL dependency-clean T4 functions, what is the full compatible flag set `S(f)` for each function under Watcom 10.0a, how many new function-level / whole-object / E0-`RegionMatch` / genuinely buildable T3 matches and score improvements emerge, and which existing T3s regress under alternative flags?
3. Do compatible flag sets `S(f)` cluster consistently across `analysis/modules.toml` / candidate CU boundaries, and what compact Tier-1 / Tier-2 production search presets are empirically justified?

**Hypothesis:**
Empirical calibration of Watcom 10.0a (including `-5r`, `-3r`, `-or`, `-oi`, `-om`, `-zp1`, `-d1+`, `-os`, etc.) reveals a compact, evidence-backed preset hierarchy yielding deterministic zero-LLM buildable T3 promotions and strict mismatch score improvements beyond the legacy 8-preset OW2-derived list, while clarifying which flags cause regressions on existing T3s.

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.7, §12.1–12.3, §14 E7)
- `docs/research/m2-completion/blocker-analysis.md` (§1 #6, §8.1)
- `experiments/build_codegen/e0/matcher_proto.py` (use E0's strengthened matcher for ALL `FunctionMatch` and `RegionMatch` verdicts!)
- `tools/wc1/permuter.py`, `tools/wc1/t3_audit.py`, `tools/wc1/build.py`, `tools/wc1/oldcc.py`, `analysis/modules.toml`

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e7/` (deterministic sweep scripts, capability probe, analysis scripts, pytest suite)
- `docs/research/build-codegen/E7-compiler-calibration.md`
- `docs/research/build-codegen/results/e7/` (machine-readable JSON/CSV calibration databases)

**STRICTLY PROHIBITED:**
- Do NOT modify any production file under `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT call any LLM during calibration; this experiment is 100% deterministic.
- Do NOT infer a new CU boundary solely from an empty intersection of `S(f)` (RFC §12.2!).
- Do NOT run `make verify` directly.

## 4. Technical Requirements

### 4.1 Layer 1 — Watcom 10.0a Compiler Capability Database (`capability_probe.py`)
1. Deterministically capture `wcc386.exe` (10.0a) usage output and probe EVERY candidate option on a controlled synthetic C probe suite (covering loops, byte/short compares, struct packing, bitfields, switch tables, multiplications, `strcpy`/`memset` intrinsics, tail calls, stack frames, float/int ops):
   - Architecture/calling conv: `-3r`, `-4r`, `-5r` (plus verify `-6r` is rejected!)
   - Optimization letters: `-ot`, `-os`, `-od`, `-ol`, `-ol+`, `-oa`, `-or`, `-oi`, `-om`, `-oc`, `-oe`, `-ou`, `-ox`, `-oz`, `-of`, `-of+` (plus verify `-ob` is rejected!)
   - Packing/debug/other: `-zp1`, `-zp2`, `-zp4`, `-d1`, `-d1+`, `-d2`, `-j`, `-ri`, `-zc`
2. Record for every flag: `supported` (bool), `observed_codegen_effect` (bool + concrete diff description on synthetic probe), `warnings_or_errors`.
3. Output `docs/research/build-codegen/results/e7/capability_db.json`.

### 4.2 Layer 2 — Full Deterministic Calibration Sweep (`calibrate.py`)
Dynamically discover:
- **Cohort A (All existing T3):** All in-scope `c == "T3"` functions (`519` functions across `514` C files).
- **Cohort B (Dependency-clean T4):** All in-scope `c == "T4"` functions (`385` total) — identify which T4 units are dependency-clean (0 unresolved external relocations on baseline compile) vs have unresolved relocations (record BOTH counts explicitly; sweep ALL dep-clean T4 units!).

**Configuration grid (all verified supported under Layer 1):**
Design a disciplined, fast, orthogonal Watcom 10.0a configuration grid (~16–20 core configs covering the high-signal axes, using `jobs=6` parallel workers inside the isolated Wine prefix so total sweep finishes in ~3–5 minutes!):
- Core OPT axis (`-4r` vs `-5r` vs `-3r`):
  1. `-s -ot -ol -4r -zp2` (current default)
  2. `-s -ot -oa -ol -4r -zp2`
  3. `-s -ot -4r -zp2`
  4. `-s -ot -oa -4r -zp2`
  5. `-s -os -ol -4r -zp2`
  6. `-s -ot -ol -5r -zp2`
  7. `-s -ot -oa -ol -5r -zp2`
  8. `-s -ot -5r -zp2`
  9. `-s -os -ol -5r -zp2`
  10. `-s -ot -ol -3r -zp2`
- Secondary optimization & packing/debug axes:
  11. `-s -ot -ol -or -4r -zp2`
  12. `-s -ot -ol -oi -4r -zp2`
  13. `-s -ot -ol -om -4r -zp2`
  14. `-s -ot -ol -oc -4r -zp2`
  15. `-s -ot -ol+ -4r -zp2`
  16. `-s -ot -ol -4r -zp1`
  17. `-s -ot -ol -5r -zp1`
  18. `-s -ot -ol -4r -d1+ -zp2`
  19. `-s -ot -ol -5r -d1+ -zp2`
  20. `-s -od -4r -zp2`
  21. `-s -od -4r -d1+ -zp2`
  (Also test `-s -ot -oa -ol -5r -zp2` and `-s -os -4r -zp2` if fast; record EVERY tested config and explicitly list untested combinations as `untested` per RFC §12.2!)

**CRITICAL requirements for every `(function, config)` cell:**
1. Record the **FULL compatible set `S(f)`** — NEVER stop at the first matching config!
2. Record one of the **5 RFC §12.2 states**: `matched`, `mismatched`, `compile_error`, `matcher_unsupported`, `untested`.
3. Evaluate with **E0's strengthened `matcher_proto.py`** (both `FunctionMatch` and `RegionMatch`) AND `wc1.match.diff_function` score!
4. For EVERY newly matching T4 function (not currently T3), ALSO check:
   - `whole_object_match` (all functions & data in its `.c` file match under that config),
   - `e0_region_match`,
   - `check_t3_buildable` (`wc1.build.check_t3_buildable` — note: pass the compiled `.obj`!),
   - And for representative newly `MATCH_BUILDABLE` T4 functions (e.g., at least 3 new `-5r` buildable matches), run an isolated Build A link check (`build/e7/`) confirming `wc1.compare == IDENTICAL`!
5. Compute **T3 regression / compatibility matrix** across all 519 existing T3s:
   - `only_4r`, `only_5r`, `both_4r_5r`, `only_3r`, `neither_4r_nor_5r` (e.g. `-d1+`, `-od`, `-os`, `-oa`, `ow2`),
   - Exact regression counts when switching default `-4r` -> `-5r` or toggling `-ol`, `-oa`, `-or`, `-oi`, `-zp1`.
6. Compute **CU-level flag consistency (`cu_hypotheses.json`)**:
   - Group audited functions by `analysis/modules.toml` module ranges, compute per-module intersection $\bigcap_{f \in M} S(f)$, identify modules with non-empty consistent flag sets vs empty intersections, and diagnose the competing causes of any empty intersection (RFC §12.2: NEVER conclude a new CU boundary from empty intersection alone!).
7. Compute **Layer 3 — Proposed Production Search Presets (`proposed_presets.json`)**:
   - Greedy set-cover / marginal-yield ranking over the empirically tested configs, producing concrete Tier 1 (fast default) and Tier 2 (extended) presets with exact marginal T3 gain, buildable T3 gain, and score-improvement counts (preserving full R6 evidence for `-5r`!).

## 5. Deliverables, Acceptance Criteria & Atomic Commits

Deliverables:
- `experiments/build_codegen/e7/` (`capability_probe.py`, `calibrate.py`, `run_e7.py`, `test_e7.py`)
- `docs/research/build-codegen/results/e7/{capability_db.json,calibration_matrix.json,t4_new_matches.csv,cu_hypotheses.json,proposed_presets.json}`
- `docs/research/build-codegen/E7-compiler-calibration.md`

Acceptance criteria:
1. `pytest -q experiments/build_codegen/e7/test_e7.py` passes 100% (validates schema, 5-state tracking, no silent truncation of `S(f)`, capability probe determinism, and consistency of committed JSON/CSV results).
2. `python3 -m experiments.build_codegen.e7.run_e7` cleanly reproduces all results.
3. Zero production modifications (`git diff <BASE> -- tools/ src/ analysis/ tests/ Makefile` is empty).
4. 2–3 clean atomic commits on `research/build-codegen/e7`:
   - Commit 1: `exp(e7): Watcom 10.0a capability probe and deterministic calibration harness + tests`
   - Commit 2: `exp(e7): full T3/T4 calibration datasets, CU hypotheses, and preset recommendations`
   - Commit 3: `docs(e7): E7 original compiler calibration report`
5. End with a concise summary: commit SHAs, exact counts (T3 cohort, dep-clean T4 cohort, new function matches, whole-object matches, E0 region matches, buildable T3s, score improvements, `-4r` vs `-5r` T3 compatibility matrix, proposed Tier-1/Tier-2 presets), and reproduction commands.
