# Independent Adversarial Review — Experiment E7 (`rev-e7-01`)

You are the **Independent Reviewer** for **Experiment E7** (`rev-e7-01`, Original Compiler Calibration — Watcom 10.0a).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e7-01` (detached at the committed E7 HEAD)
- **Baseline:** `7c23d2371e95d8de93f0ba1652c8d44b858da273`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E7-contract.md`, `docs/research/build-codegen/E7-compiler-calibration.md`, and the code under `experiments/build_codegen/e7/`.
2. Run `pytest -q experiments/build_codegen/e7/test_e7.py` in this review worktree (checking portability across checkouts too!).
3. Verify **scope**: Confirm `git diff 7c23d23 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
4. Independently scrutinize key methodological & empirical claims (do NOT re-run the entire 21,618-compile 5-minute sweep unless you spot an inconsistency — instead spot-check 5–10 key cells freshly!):
   - Verify capability probe: `-6r` and `-ob` truly rejected by real 10.0a `wcc386.exe`, supported options accurately recorded in `capability_db.json`.
   - Verify 5-state tracking (`matched`, `mismatched`, `compile_error`, `matcher_unsupported`, `untested`) and FULL `S(f)` retention (not stopping at first match!).
   - Spot-check at least 3 newly `MATCH_BUILDABLE` `-5r` T4 functions (e.g., `OptionsDialog 0x1a800`, `SetCursorShape 0x13dd0`, `AiGuardStartArea 0x29f40`) by freshly compiling and verifying E0 `FunctionMatch` + `RegionMatch` + `check_t3_buildable`!
   - Spot-check the `-4r -> -5r` paired existing-T3 control (`417/417` identical, 0 lost) and `InitNewCampaign 0x1e100` OW2 handling.
   - Verify `cu_hypotheses.json` does NOT infer CU boundaries solely from empty `S(f)` intersections (RFC §12.2!), and that `proposed_presets.json` accurately separates capability DB, CU hypotheses, and Tier-1/Tier-2 presets.
   - Check internal consistency across `capability_db.json`, `calibration_matrix.json`, `t4_new_matches.csv`, `cu_hypotheses.json`, `proposed_presets.json`, and `E7-compiler-calibration.md`.

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
