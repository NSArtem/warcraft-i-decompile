# Independent Adversarial Review — Experiment E5 (`rev-e5-01`)

You are the **Independent Reviewer** for **Experiment E5** (`rev-e5-01`, Data-Anchor Decoupling Fix B3).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e5-01` (detached at `de82374233463453b9a8ae9ba338d1e3642b8a67`)
- **Baseline:** `1abb053c112332ec901a8961dc918bdcc25d73c4`
- **Commits under review:** `d701bf0b2964e318b143b27fcaf4ac8718467e04`, `481ce6167edbb26ec64c44fffe1771fba3b710f5`, `de82374233463453b9a8ae9ba338d1e3642b8a67`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E5-contract.md`, `docs/research/build-codegen/E5-data-anchors.md`, and `experiments/build_codegen/e5/{omf_b3.py,build_e5.py,run_e5.py,test_e5.py}`.
2. Run `pytest -q experiments/build_codegen/e5/test_e5.py` in this review worktree!
3. Verify **scope**: Confirm `git diff 1abb053 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty, AND confirm zero `wc1_anchor_` leaks in `src/`, `analysis/`, `tests/`.
4. Independently scrutinize key invariants:
   - Does `omf_b3.py` genuinely call E0's full data byte + forward/reverse pointer relocation check BEFORE rewriting any anchor?
   - Does `THREAD` expansion handle cross-record F0-F3 / T0-T3 state cleanly (including definitions on discarded data segments)?
   - Are ALL 4 scenarios (`SaveErrorDialog` decreasing anchor, real 3-segment GAMEDLG `_DATA`+`CONST`+`_BSS`, `THREAD`, and `FLAT`/`DGROUP`/`Target`/`EXTDEF` frames) genuinely linking to Build A `IDENTICAL` (`8,770/8,770` LE fixups) without sneaking in ASM fallbacks?
   - Do negative controls N1–N4 (altered data byte, wrong pointer target, mutable content-merging / interior struct offset, anchor leak) genuinely fail closed?
   - Run 1–2 quick adversarial `python3 -c` probes against `omf_b3.py` (e.g., trying to rewrite an unverified mutable `_DATA` offset or a corrupted pointer) to confirm fail-closed behavior!

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
