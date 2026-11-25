# Experiment E7 Repair Assignment (`dev-e7-02`, Fresh Replacement Session)

You are a **fresh Developer session** (`dev-e7-02`) assigned to resolve the 2 minor engineering findings from Independent Review Round 1 (`rev-e7-01`, `VERDICT: REQUEST_CHANGES`) on Experiment E7. All scientific data, 23,504 cells, 19 new matches, 13 Build A IDENTICAL links, and 18 tests were independently verified clean — do NOT re-run the full 21,618-compile sweep unless needed!
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e7`
- **Branch:** `research/build-codegen/e7` (current HEAD: `2ce107add80ccfc8bc8dcd0aab89e0c813bbe266`, baseline `7c23d2371e95d8de93f0ba1652c8d44b858da273`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strictly Permitted Scope
- Edit ONLY under `experiments/build_codegen/e7/` and `docs/research/build-codegen/`.
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.

## Findings to Resolve
1. **[Must Fix] Checkout path portability (`capability_probe.py:75`, `calibrate.py:71`, `E7-compiler-calibration.md:165`)**
   - In a checkout with a 154-character root path, Watcom 10.0a crashed with an access violation because absolute long paths were passed to `wcc386.exe`.
   - Fix both `capability_probe.py` and `calibrate.py` so compiler-facing source/include/output paths stay short & bounded (e.g., use relative paths from `cwd` or a short symlink/temp dir under `/tmp` or relative staging so `Z:\...` paths never exceed Watcom 10.0a's Win32/DOS command-line/path limits!).
   - Verify with a regression test in `test_e7.py` (testing capability probe + a real calibration cell from a long-path symlink or confirming short paths are passed) AND document cleanly in `E7-compiler-calibration.md`.
2. **[Optional] CSV LF line endings (`analyze.py:225`)**
   - Set `lineterminator="\n"` in `csv.writer` / `csv.DictWriter`, regenerate `docs/research/build-codegen/results/e7/t4_new_matches.csv` from `calibration_matrix.json`, and confirm `git diff --check` is clean.

## Acceptance Criteria
1. `pytest -q experiments/build_codegen/e7/test_e7.py` passes 100% (including long-path portability test!).
2. `git diff --check` is clean and `git diff 7c23d23 -- tools/ src/ analysis/ tests/ Makefile flake.nix AGENTS.md` is empty.
3. Commit cleanly on `research/build-codegen/e7`: `exp(e7): resolve rev-e7-01 path portability and CSV LF findings`.
4. Reply concisely with commit SHA and verification summary.
