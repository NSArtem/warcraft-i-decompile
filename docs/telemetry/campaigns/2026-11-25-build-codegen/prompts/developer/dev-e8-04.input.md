# Developer Repair Assignment — Experiment E8 (`dev-e8-04`)

You are the fresh **Developer** (`dev-e8-04`) for **Experiment E8** (Original CU Boundary Evidence Validation), resolving the exact findings from Round 2 Independent Review (`rev-e8-02`, `REQUEST_CHANGES`). Note that `rev-e8-02` independently verified that all scientific conclusions and the Round 1 Corpus B1 repair are sound; only these focused reproducibility & test-hygiene findings remain!

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e8`
- **Branch:** `research/build-codegen/e8` (HEAD: `dc1d028009cbfae21ff84146debce59d48d18d1c`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, and short per-session `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly.

## Findings to Resolve
1. **F1 — HIGH (Must Fix): Cross-worktree determinism of `synthetic_manifest.json` (`image.data_sha256`):**
   - Root cause (independently reproduced by `rev-e8-02`): Watcom 10.0a `wcc386` emits uninitialized heap padding bytes in `CONST` between string literals (e.g., 3 padding bytes between `"e8 g17 b\0"` and `"e8 g17 t"` in `g17_uses.obj`), which vary across different build directories/runs (`79 00 73` vs `72 00 72` vs `65 00 6e`). Hashing raw `prog.image[DATA_OBJ]` into `image.data_sha256` causes `synthetic_manifest.json` to drift across fresh checkouts and fail `test_run_e8_regenerates_the_committed_artifacts_byte_identically`!
   - Fix in `experiments/build_codegen/e8/synthetic_corpus.py`: replace raw `data_sha256` with a **padding-normalized / semantic data digest** (e.g., `semantic_data_sha256` hashing the declared initialized bytes of each symbol / NUL-terminated string literal + `_DATA` initializers from `prog.image[DATA_OBJ]`, zeroing or excluding compiler-inserted uninitialized `CONST` alignment-padding gaps between literals, OR explicitly documenting why raw `DATA_OBJ` contains Watcom 10.0a uninitialized `CONST` pad bytes!).
   - Verify determinism by running `synthetic_corpus.build(force=True)` from TWO different temporary build directories (or verifying `run_e8 --refresh` produces byte-identical `synthetic_manifest.json` across fresh rebuilds!).
2. **F2 — LOW (Fix): Plain `pytest` collection bootstrap:**
   - Add `experiments/build_codegen/e8/conftest.py` (exact same 5-line repo-root `sys.path` bootstrap used in `experiments/build_codegen/e4/conftest.py` / `e5/conftest.py`) so `pytest -q experiments/build_codegen/e8/test_e8.py` works directly (not only `python3 -m pytest`).
3. **F3 — LOW (Fix): Zero silent skips on fresh checkout:**
   - In `experiments/build_codegen/e8/test_e8.py`, instead of skipping the 7 Corpus B1 tests and the regeneration test when `build/e8/libsig10a.json` or `build/e8/corpus.json` is missing on a fresh checkout, add a session/module-scoped pytest fixture that builds/populates the cache automatically whenever the real inputs (`war.exe` and `original/watcom/10.0a/lib386/dos/clib3r.lib`) exist! Test on a freshly cleared `build/e8/` that `pytest -q experiments/build_codegen/e8/test_e8.py` runs **all tests with 0 skipped**!
4. **F4 — NIT (Fix):**
   - In `docs/research/build-codegen/E8-cu-boundaries.md`, clarify "112 extents / 111 objects" (`clib3r:cstrt386` contributes both `_TEXT` and `BEGTEXT`) and "non-self-relative library relocations" (matching the actual `verify_segment()` code).

## Acceptance Criteria & Commit
1. Clear `build/e8/`, run `pytest -q experiments/build_codegen/e8/test_e8.py` directly (plain `pytest`, NOT just `python3 -m pytest`), and confirm **all tests pass with 0 skipped and 0 failed**!
2. Run `python3 -m experiments.build_codegen.e8.run_e8 --refresh` twice (and test compiling `g17_uses.c` / rebuilding in a second scratch dir) and confirm `git diff -- docs/research/build-codegen/results/e8/` is **empty** (byte-identical across rebuilds!).
3. Verify zero production diffs (`git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty) and clean `git status`.
4. Commit 1 clean atomic commit on `research/build-codegen/e8`:
   - `exp(e8): resolve rev-e8-02 findings (normalize CONST pad digest, conftest, zero-skip fresh tests)`
