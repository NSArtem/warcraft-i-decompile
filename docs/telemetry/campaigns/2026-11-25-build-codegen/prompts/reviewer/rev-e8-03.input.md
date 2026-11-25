# Independent Adversarial Review — Experiment E8 Round 3 (`rev-e8-03`)

You are the fresh **Independent Reviewer** (`rev-e8-03`) for **Experiment E8** (Original CU Boundary Evidence Validation), performing final Round 3 verification after `dev-e8-04` resolved all findings F1–F4 from Round 2 (`rev-e8-02`, `REQUEST_CHANGES`).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e8-03` (detached at `06235f6d155fdffb4650138aa823eae6decd53c0`)
- **Baseline:** `c946f3854c9fa424f4b47e5305655f8d4a9b6d22`
- **Commits under review:**
  - `0eeacec5b51836ed9d2ef1257e2fdd02320e42a8`
  - `0fd1a31096879a790897b561bd8ea1bb0a7db57b`
  - `766099e96d9eea57480a0afaf244287ad9433486`
  - `dc1d028009cbfae21ff84146debce59d48d18d1c`
  - `06235f6d155fdffb4650138aa823eae6decd53c0` (`exp(e8): resolve rev-e8-02 findings (normalize CONST pad digest, conftest, zero-skip fresh tests)`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, and short per-session `TMPDIR` configured; caches pre-warmed). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Inspect `git show 06235f6d155fdffb4650138aa823eae6decd53c0` and verify scope (`git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` must be empty).
2. **Fresh-checkout zero-skip test check (F2 & F3):**
   - In this pristine review worktree (where `build/e8/` does NOT exist yet!), run plain **`pytest -q experiments/build_codegen/e8/test_e8.py`** (NOT `python3 -m pytest` — specifically verifying `conftest.py` fixes plain `pytest`!).
   - Confirm **100% pass with 0 failed and 0 skipped**!
3. **Cross-worktree determinism check (F1):**
   - Run `python3 -m experiments.build_codegen.e8.run_e8 --refresh` in this fresh review worktree and confirm `git diff -- docs/research/build-codegen/results/e8/` is **completely empty** (all 4 files byte-identical, LF-only, zero paths/timestamps, zero stray files in repo root)!
   - Inspect how `synthetic_corpus.py` computes the normalized/semantic data digest: confirm it genuinely hashes all declared initialized data bytes/strings while excluding only compiler-inserted uninitialized `CONST` alignment padding (not silently dropping real data bytes!).
4. **Verify F4 & overall consistency:**
   - Confirm `E8-cu-boundaries.md` clarifies "112 extents / 111 objects" and "non-self-relative library relocations", and stays 100% consistent with `results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}` and R4 independence.

## Output Format
End with an explicit verdict line in your final message:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
