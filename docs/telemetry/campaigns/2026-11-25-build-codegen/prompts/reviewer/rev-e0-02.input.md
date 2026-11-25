# Independent Review Round 2 — Experiment E0 (`rev-e0-02`)

You are the **fresh Independent Reviewer** (`rev-e0-02`) verifying the Round 2 repair of **Experiment E0** (`research/build-codegen/e0`, HEAD `dfd2a4c345adcd1ba71e1cf341fd9d3ca9a6f69a`).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e0-02` (detached at `dfd2a4c345adcd1ba71e1cf341fd9d3ca9a6f69a`)
- **Repair commits since Round 1 (`54bfd6b`):**
  - `6b44c39f846be77b5e8772eb6bc4f4abc995a124`
  - `dfd2a4c345adcd1ba71e1cf341fd9d3ca9a6f69a`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT modify tracked files.

## Verification Checklist
1. Inspect `git diff 54bfd6b..dfd2a4c` and verify every one of the 6 Round 1 findings is genuinely fixed (not bypassed or papering over a single fixture):
   - F1 (HIGH): Truncated function bodies (instruction boundary & mid-instruction) rejected.
   - F2 (HIGH): Branch targets evaluated strictly against final retained region (both `rel8` and `rel32` into trimmed tail rejected).
   - F3 (HIGH): Local `PUBDEF`/`LPUBDEF` definitions reconciled against anchors & DB; runtime refs into excluded `$$SYMBOLS`/`$$TYPES` rejected.
   - F4 (MEDIUM): Additional `CODE`-class segments handled fail-closed (no bypassed branch obligations).
   - F5 (MEDIUM): Out-of-bounds fixups (starting at/past segment end) validated before extent filtering.
   - F6 (MEDIUM): Non-zero CLI exit when function-only `ERROR` occurs even with 0 region errors.
2. Run `pytest -q experiments/build_codegen/e0/test_e0.py` and verify `git diff 3ee53aa -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
3. Run at least 2 independent adversarial `python3 -c` probes attempting to bypass the new fixes (e.g., reproducing Round 1's exact attacks plus a variant).
4. Verify saved results (`controls.json`, `t3_reaudit.json`, `t3_reaudit.csv`) and `E0-matcher-soundness.md` are internally consistent and accurately reflect the 55 controls and 519 T3 re-audit. (No need to rerun the full 514-file re-audit unless you suspect inconsistency — spot-checking 5–10 real T3 files directly against `matcher_proto` + running `test_e0.py` is fast and sufficient if consistent!)

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise verification summary.
