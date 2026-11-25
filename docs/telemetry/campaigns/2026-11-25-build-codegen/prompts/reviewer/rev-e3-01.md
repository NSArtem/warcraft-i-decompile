# Independent Adversarial Review — Experiment E3 (`rev-e3-01`)

You are the **Independent Reviewer** for **Experiment E3** (`rev-e3-01`, Partial Object Matching).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e3-01` (detached at `eaaf87affd2db0e9e31bb88ec08ffcf347558ec9`)
- **Baseline:** `1abb053c112332ec901a8961dc918bdcc25d73c4`
- **Commits under review:** `ee17095f2aaf3fdc02698e7fa6538b018ef8963c`, `eaaf87affd2db0e9e31bb88ec08ffcf347558ec9`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E3-contract.md`, `docs/research/build-codegen/E3-partial-matching.md`, and `experiments/build_codegen/e3/{partial_matcher.py,run_e3.py,test_e3.py,fixtures/synthetic.py}`.
2. Run `PYTHONDONTWRITEBYTECODE=1 pytest -q experiments/build_codegen/e3/test_e3.py` AND `PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.build_codegen.e3.run_e3` (checking cross-worktree reproducibility against committed `results.json` — verify `git diff` stays empty or note any path-dependent drift!).
3. Verify **scope**: Confirm `git diff 1abb053 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
4. Independently verify key claims:
   - Confirm `DialogHighlightOff` refutation (`0x16d50` `je 0x16d31` outgoing `rel8` + Watcom `-os` symbol folding at `0x5f`).
   - Confirm `FarmPanelChanged` (`0x28254`) and `ScoreTickIncome` (`0x24e90` with `sum = delta + score`) truly pass region-scoped matching while mismatching siblings remain `MISMATCH`.
   - Scrutinize `partial_matcher.py` for soundness bypasses (e.g., mutable `_DATA` shift without boundary proof, wrong sibling call target, outgoing `rel8`, broken `CONST` aliasing, out-of-bounds fixups, truncated bodies) with 1–2 quick adversarial `python3 -c` probes.

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
