# Independent Review Round 2 — Experiment E7 (`rev-e7-02`)

You are the **fresh Independent Reviewer** (`rev-e7-02`) verifying the Round 2 repair of **Experiment E7** (`research/build-codegen/e7`, HEAD `4194a2f14025b865c313a2bb2e45e3e47e3cf89d`).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e7-02` (detached at `4194a2f14025b865c313a2bb2e45e3e47e3cf89d`)
- **Repair commit since Round 1 (`2ce107a`):** `4194a2f14025b865c313a2bb2e45e3e47e3cf89d`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Verification Checklist (concise & strict)
1. Inspect `git diff 2ce107a..4194a2f` and verify both Round 1 findings are cleanly resolved:
   - F1 (Must Fix): Long-checkout path portability in `capability_probe.py` and `calibrate.py` (uses bounded short paths so Watcom 10.0a compiles cleanly even from a >150-char checkout root, plus regression test in `test_e7.py` and updated docs).
   - F2 (Optional): LF line endings in `analyze.py` and `t4_new_matches.csv` (`git diff --check` clean).
2. Run `pytest -q experiments/build_codegen/e7/test_e7.py` in this review worktree!
3. Verify `git diff 7c23d23 -- tools/ src/ analysis/ tests/ Makefile flake.nix AGENTS.md` is empty and `git diff --check 7c23d23..HEAD` has no CRLF issues on `t4_new_matches.csv`.

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any).
3. Concise verification summary.
