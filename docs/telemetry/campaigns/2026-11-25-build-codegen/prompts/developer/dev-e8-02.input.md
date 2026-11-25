# Developer Handoff Assignment — Experiment E8 (`dev-e8-02`)

You are the fresh successor **Developer** (`dev-e8-02`) for **Experiment E8** (Original CU Boundary Evidence Validation). Your predecessor (`dev-e8-01`) timed out at 1800s **after** completing all implementation files, all 4 machine-readable result artifacts, and 24/24 passing tests — right before writing `docs/research/build-codegen/E8-cu-boundaries.md` and making the commits.

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e8`
- **Branch:** `research/build-codegen/e8`
- **Baseline commit:** `c946f3854c9fa424f4b47e5305655f8d4a9b6d22`
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly.

## Already Completed Checkpoint in Worktree
- `experiments/build_codegen/e8/{__init__.py,synthetic_corpus.py,real_corpus.py,evaluate_signals.py,run_e8.py,test_e8.py}`
- `docs/research/build-codegen/results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}`
- Note: a stray `p10.map` was left in the worktree root (deleted by Manager); double-check that `run_e8.py` / `synthetic_corpus.py` puts ALL temporary/linker `.map` files under `build/e8/` or a temp dir, NEVER in the repo root!

## Your Bounded Tasks
1. Read `docs/research/build-codegen/contracts/E8-contract.md` and inspect the existing `experiments/build_codegen/e8/*.py` and `docs/research/build-codegen/results/e8/*`.
2. Run `python3 -m experiments.build_codegen.e8.run_e8` and `pytest -q experiments/build_codegen/e8/test_e8.py`. Confirm:
   - 100% tests pass.
   - `run_e8.py` leaves ZERO untracked files in the repo root (e.g., no `p10.map`!). If anything writes to cwd, fix it to write under `build/e8/`.
   - All JSON/CSV outputs are deterministic (LF line endings, `sort_keys=True`, no absolute checkout paths).
   - Strict R4 separation (Corpus A synthetic ground truth, Corpus B real independent `clib3r.lib` `libsig` + `setup.exe` if present, and exploratory game observations kept strictly separate from ground-truth precision/recall).
3. Write `docs/research/build-codegen/E8-cu-boundaries.md` thoroughly grounded in the exact numbers in `results/e8/{synthetic_manifest.json,metrics.json,signal_metrics.csv,game_exploratory.json}`:
   - Corpus A & Corpus B construction, sample sizes, and R4 independence justification (including whether `setup.exe` exists).
   - Full confusion matrices (`TP`, `FP`, `TN`, `FN`, `precision`, `recall`, `F1`, `sample_size`) for EVERY split and merge signal on BOTH Corpus A and Corpus B.
   - Concrete observed FP and FN examples for signals that exhibit them.
   - Explicit RFC §9.2 epistemic classification (`Proven constraint` with stated assumptions, `Strong evidence`, `Weak/Ambiguous heuristic`, `Unreliable/Noisy`) for every signal.
   - Separate clearly-labeled *Exploratory / Non-Ground-Truth* observations on `war.exe`'s game range (`0x104b0..0x3024e`), including signal agreements/disagreements and candidate `none16` splits inside large chunks (`mod_13f60`, `mod_16390`, `mod_1f050`, `STATUS.C`, etc.), never presenting inferred module boundaries or filenames as established facts.
   - Exact reproduction commands.
4. Verify zero production diffs (`git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty) and clean `git status` (only expected untracked `original`).
5. Make the 3 clean atomic commits on `research/build-codegen/e8`:
   - `exp(e8): synthetic Watcom 10.0a + wlink ground-truth corpus and real libsig extractor` (staging `experiments/build_codegen/e8/{__init__.py,synthetic_corpus.py,real_corpus.py}`)
   - `exp(e8): CU boundary signal evaluator, metrics, and pytest suite` (staging `experiments/build_codegen/e8/{evaluate_signals.py,run_e8.py,test_e8.py}` and `docs/research/build-codegen/results/e8/`)
   - `docs(e8): E8 CU boundary evidence validation report` (staging `docs/research/build-codegen/E8-cu-boundaries.md`)
