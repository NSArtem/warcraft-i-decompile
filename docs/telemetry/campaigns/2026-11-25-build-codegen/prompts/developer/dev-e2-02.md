# Experiment E2 Repair Assignment (`dev-e2-02`, Fresh Replacement Session)

You are a **fresh Developer session** (`dev-e2-02`) assigned to resolve all 3 findings (1 Must Fix, 2 Should Fix) from Independent Review Round 1 (`rev-e2-01`, `VERDICT: REQUEST_CHANGES`) on Experiment E2.
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e2`
- **Branch:** `research/build-codegen/e2` (current HEAD: `b1614b9803c3d794c810ead6a9f2f4d1678f39c9`, baseline `7c23d2371e95d8de93f0ba1652c8d44b858da273`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strictly Permitted Scope
- Edit ONLY under `experiments/build_codegen/e2/` and `docs/research/build-codegen/`.
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.

## All 3 Reviewer Findings to Resolve Completely

1. **[Must Fix] `results.json` does not reproduce across worktrees (`synthetic.py:17`, `run_e2.py:204`, `E2-compilation-context.md:394`)**
   - **Defect:** Across different checkout paths, `consolidation_rows.csv` reproduced byte-for-byte, while `results.json` differed in 74 fields due to (a) absolute checkout paths embedded in Watcom `-d1+` `$$TYPES` metadata, and (b) 4 non-deterministic uninitialized heap/padding bytes that Watcom 10.0a emits inside the `CONST` alignment gap between string literals!
   - **Fix:**
     - Exclude/normalize checkout-path-dependent `$$TYPES`/`$$SYMBOLS` metadata hashes (or compute deterministic digests over runtime non-debug segments only, while explicitly recording debug-metadata segment names/lengths without raw path-embedded hashes).
     - For synthetic `CONST` literal gaps, record exact literal offsets, literal NUL-terminated bytes, gap byte lengths, and whether gap bytes are non-zero / uninitialized compiler padding (without failing cross-run determinism on Watcom's uninitialized padding bytes — record the gap lengths & non-zero observation deterministically and mask/separate raw non-deterministic padding bytes cleanly from the deterministic comparison payload, OR document clearly what is deterministic vs Watcom's uninitialized CONST padding!).
     - Update `E2-compilation-context.md` reproduction section accurately, and verify determinism across two runs (including verifying no checkout-path strings leak into `results.json`).

2. **[Should Fix] Short object names leave a checkout-path dependency (`harness.py:112`)**
   - **Defect:** In a checkout with a 104-character root path, Watcom 10.0a failed with `rc=8` / access violation on the first alignment fixture due to DOS/Win32 Watcom 10.0a command-line/path length limits.
   - **Fix:** Keep compiler-facing source/object/include paths short & bounded (e.g., pass relative paths from `cwd` or use short relative filenames when invoking `wcc386` / `oldcc.compile_c`!). Verify cleanly.

3. **[Should Fix] Alignment assertion can miss a regression to 16-byte spacing (`test_e2.py:46`)**
   - **Defect:** `off % 4 == 0` also passes 16-byte starts (`0, 16, 32, 64`).
   - **Fix:** Assert the exact probe start offsets (`[0, 8, 20, 40]` for 10.0a `-3r`/`-5r -ot`, `[0, 16, 32, 64]` for 10.0a `-4r -ot` and OW2 `-4r`/`-5r -ot`) and explicitly test fresh `-os` (`[0, 5, 16, 33]`) and `-od` byte packing!

## Acceptance Criteria & Commits
1. Fix all 3 findings cleanly in `experiments/build_codegen/e2/`.
2. Re-run `python3 -m experiments.build_codegen.e2.run_e2` and `pytest -q experiments/build_codegen/e2/test_e2.py` (confirming 100% pass and zero checkout-path leakage in `results.json`).
3. Verify `git diff 7c23d23 -- tools/ src/ analysis/ tests/ Makefile flake.nix AGENTS.md` is empty.
4. Commit cleanly on `research/build-codegen/e2` (`exp(e2): resolve rev-e2-01 findings (deterministic results, short compiler paths, exact alignment assertions)`).
5. Reply concisely with commit SHA, test counts, and verification summary.
