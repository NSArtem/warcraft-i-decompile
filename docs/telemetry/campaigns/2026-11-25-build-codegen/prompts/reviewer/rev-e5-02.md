# Independent Adversarial Review — Experiment E5 Round 2 (`rev-e5-02`)

You are the fresh **Independent Reviewer** (`rev-e5-02`) for **Experiment E5** (Data-Anchor Decoupling Fix B3), performing Round 2 verification after `dev-e5-02` fixed the Watcom 10.0a long-path fixture compile crash uncovered during Round 1 (`rev-e5-01`).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e5-02` (detached at `54d610ac797198ecc6f6826e361954547242ecb5`)
- **Baseline:** `1abb053c112332ec901a8961dc918bdcc25d73c4`
- **Commits under review:**
  - `d701bf0b2964e318b143b27fcaf4ac8718467e04`
  - `481ce6167edbb26ec64c44fffe1771fba3b710f5`
  - `de82374233463453b9a8ae9ba338d1e3642b8a67`
  - `54d610ac797198ecc6f6826e361954547242ecb5` (`exp(e5): resolve rev-e5-01 Watcom 10.0a long-path fixture compile crash`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop` and do NOT run `make verify` (stay strictly within E5!). Run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E5-contract.md`, `docs/research/build-codegen/E5-data-anchors.md`, and inspect `git show 54d610ac797198ecc6f6826e361954547242ecb5`, plus `experiments/build_codegen/e5/{omf_b3.py,build_e5.py,wcc10a.py,run_e5.py,controls.py,test_e5.py}`.
2. Run `pytest -q experiments/build_codegen/e5/test_e5.py` directly in this review worktree (should complete in ~30–60 s and exercise all 9 Build A links, negative controls, and the new long-path regression test!).
3. Run `python3 -m experiments.build_codegen.e5.run_e5` ONCE and check `git diff -- docs/research/build-codegen/results/e5/results.json` to confirm byte-identical cross-worktree reproducibility and zero leaked temp/worktree paths!
4. Verify **scope**: Confirm `git diff 1abb053 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty, and confirm zero `wc1_anchor_` leaks in `src/`, `analysis/`, `tests/`.
5. Independently scrutinize key invariants:
   - Does `wcc10a.py` / `build_e5.py` compile cleanly via short paths without modifying any compiled object semantics, and clean up temporary symlinks/mirrors properly?
   - Does `omf_b3.py` genuinely invoke E0's full data byte + forward/reverse pointer relocation check BEFORE rewriting any anchor?
   - Does `THREAD` expansion handle cross-record F0–F3 / T0–T3 state cleanly (including definitions on discarded data segments)?
   - Are ALL 4 scenarios (`SaveErrorDialog` decreasing anchor, real 3-segment GAMEDLG `_DATA`+`CONST`+`_BSS`, `THREAD`, and `FLAT`/`DGROUP`/`Target`/`EXTDEF` frames) genuinely linking to Build A `IDENTICAL` (`8,770/8,770` LE fixups) without sneaking in ASM fallbacks?
   - Run 2 quick adversarial `python3 -c` probes against `omf_b3.py` (e.g., trying to rewrite an unverified mutable `_DATA` offset or corrupted pointer addend) to confirm fail-closed behavior!

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
