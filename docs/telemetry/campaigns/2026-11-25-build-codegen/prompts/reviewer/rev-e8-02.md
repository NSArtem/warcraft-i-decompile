# Independent Adversarial Review — Experiment E8 Round 2 (`rev-e8-02`)

You are the fresh **Independent Reviewer** (`rev-e8-02`) for **Experiment E8** (Original CU Boundary Evidence Validation), performing Round 2 verification after `dev-e8-03` resolved the HIGH Corpus B1 `libsig` ground-truth defect uncovered during Round 1 (`rev-e8-01`).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e8-02` (detached at `dc1d028009cbfae21ff84146debce59d48d18d1c`)
- **Baseline:** `c946f3854c9fa424f4b47e5305655f8d4a9b6d22`
- **Commits under review:**
  - `0eeacec5b51836ed9d2ef1257e2fdd02320e42a8`
  - `0fd1a31096879a790897b561bd8ea1bb0a7db57b`
  - `766099e96d9eea57480a0afaf244287ad9433486`
  - `dc1d028009cbfae21ff84146debce59d48d18d1c` (`exp(e8): enforce full-segment byte verification and non-overlap in Corpus B1 libsig ground truth`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, and short per-session `TMPDIR` configured; caches pre-warmed). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E8-contract.md`, `docs/research/build-codegen/E8-cu-boundaries.md`, and inspect `git show dc1d028009cbfae21ff84146debce59d48d18d1c`, plus `experiments/build_codegen/e8/{synthetic_corpus.py,real_corpus.py,evaluate_signals.py,run_e8.py,test_e8.py}` and `docs/research/build-codegen/results/e8/*`.
2. Run `pytest -q experiments/build_codegen/e8/test_e8.py` AND `python3 -m experiments.build_codegen.e8.run_e8` ONCE in this review worktree:
   - Confirm 100% tests pass, zero Watcom 10.0a path crashes, zero stray files in repo root, LF line endings, and byte-identical cross-worktree regeneration of all 4 files under `docs/research/build-codegen/results/e8/` (`git diff` empty!).
3. Verify **scope**: Confirm `git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
4. **Verify Resolution of Round 1 (`rev-e8-01`) HIGH Finding:**
   - Does `real_corpus.py` genuinely enforce **full-segment masked byte verification** (every non-fixup byte of the `.obj` code segment matches `war.exe` at `[base, base + seglen)`) before admitting ANY `.obj` extent to Corpus B1?
   - Are there **ZERO overlapping extents** in admitted Corpus B1?
   - Is phantom `cstrtx3r:cstrtx32` rejected and is `(0x34850, 0x34860)` NOT mislabeled `same_cu`?
   - How was `intxa386` verified and stratified (`libsig_without_intxa386` or equivalent), and do the report & JSON/CSV numbers agree 100%?
5. **Adversarial methodological audit (Mandatory Correction R4):**
   - Confirm zero circularity in Corpus A (synthetic Watcom 10.0a + `wlink` + NASM, all 7 edge cases) and Corpus B1/B2 (`clib3r.lib` + `setup.exe`).
   - Confirm Exploratory Game Analysis is strictly excluded from ground-truth precision/recall and avoids presenting inferred module boundaries/filenames as established facts.
   - Spot-check confusion matrix arithmetic (`TP + FP + TN + FN == sample_size`, `precision`, `recall`, `F1`), cited FP/FN addresses, and RFC §9.2 epistemic classifications (`Proven constraint`, `Strong evidence`, `Weak/Ambiguous heuristic`, `Unreliable/Noisy`).

## Output Format
End with an explicit verdict line in your final message:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-25T20:35:55.997971Z` (Unix epoch `1795638955`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-25T21:05:55Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-25T20:56:55Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly required by your assignment. Batch independent shell commands into a single step where safe to reduce turn latency.
