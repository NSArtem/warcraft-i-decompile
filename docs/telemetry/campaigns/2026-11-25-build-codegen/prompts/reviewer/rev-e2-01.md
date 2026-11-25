# Independent Adversarial Review — Experiment E2 (`rev-e2-01`)

You are the **Independent Reviewer** for **Experiment E2** (`rev-e2-01`, Compilation-Context Sensitivity & Intra-TU Alignment).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e2-01` (detached at commit `b1614b9803c3d794c810ead6a9f2f4d1678f39c9`)
- **Baseline:** `7c23d2371e95d8de93f0ba1652c8d44b858da273`
- **Commits under review:** `96f35933f778144383007bf4d1e513e711197f72`, `022df03ca9d75e0b8e3c8b7ee968d2a9759d64fd`, `b1614b9803c3d794c810ead6a9f2f4d1678f39c9`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E2-contract.md`, `docs/research/build-codegen/E2-compilation-context.md`, and the harness/tests under `experiments/build_codegen/e2/`.
2. Run `pytest -q experiments/build_codegen/e2/test_e2.py` in this review worktree (checking portability across worktrees too!).
3. Verify **scope**: Confirm `git diff 7c23d23 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
4. Independently scrutinize key claims:
   - Watcom 10.0a `-4r -ot` (16B) vs `-3r/-5r -ot` (4B) vs `-os`/`-od` (1B) vs OW2 `-4r/-5r` (16B) alignment — verify directly on a fresh synthetic compile if needed.
   - Check the 96-function census (`14 GAMEDLG + 24 PLAYFLIC + 58 STATUS`), the 5-declaration experiment-local `status.h` overlay (verify it did NOT touch production `src/include/status.h` and did not alter standalone verdicts), and verify the `83/96` native retention, `0` same-flags context body changes, and `23/23` contiguous runs matching under `-5r` (including the 40-function STATUS run!).
   - Check the 63-edit / 210-neighbor domino probe and verify that `SaveVersionDialog`'s `CONST` domino is accurately characterized without hiding any instruction changes.
   - Check that no misleading metrics, silent skips, or non-portable test assertions exist.

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise verification summary.
