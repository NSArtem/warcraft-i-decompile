# Independent Adversarial Review — Experiment E1 (`rev-e1-01`)

You are the **Independent Reviewer** for **Experiment E1** (`rev-e1-01`, Shared Epilogue Reproduction).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e1-01` (detached at commit `4b5dd79388fa4cc16e1166be936c7b3d736bfab1`)
- **Baseline:** `7c23d2371e95d8de93f0ba1652c8d44b858da273`
- **Commits under review:**
  - `0428f1275ed8a6a745d6bb5b3ea1e95fea601cc3` (`exp(e1): shared epilogue reproduction harness, fixtures, and pytest suite`)
  - `4b5dd79388fa4cc16e1166be936c7b3d736bfab1` (`exp(e1): preserved empirical results, disassembly evidence, and E1 report`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E1-contract.md`, `docs/research/build-codegen/E1-shared-epilogues.md`, and all code/fixtures under `experiments/build_codegen/e1/`.
2. Check **no cheating / no ASM**: Verify `experiments/build_codegen/e1/fixtures/` contains strictly pure C with ZERO `__asm` or `#pragma aux` assembly insertions.
3. Verify **R1 separation**: Confirm `shared_epilogue_reproduced`, `exact_branch_encoding`, `FunctionMatch` (via E0 `matcher_proto.py`), `RegionMatch` (via E0 `matcher_proto.py`), and `build_a_integrated_identical` are cleanly separated and never conflated.
4. Verify **R6 evidence**: Confirm `74 f5` vs `74 f3` and Group B `74 93`/`75 89` across `IntroOpSyncSound` are genuinely reproduced from fresh Watcom 10.0a compiles and preserved accurately in `results.json` and `disasm_evidence.txt`.
5. Verify **Build A IDENTICAL claims independently**: Run `python3 -m experiments.build_codegen.e1.run_e1` (or `pytest -q experiments/build_codegen/e1/test_e1.py`) AND independently check `python3 -m wc1.compare original/install/war.exe build/e1/war_group_a.exe` and `build/e1/war_group_b.exe` (and check that `war_group_a.exe` / `war_group_b.exe` truly linked the compiled C objects rather than falling back to ASM!).
6. Verify **scope**: Confirm `git diff 7c23d23 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.

## Output Format
End with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.
