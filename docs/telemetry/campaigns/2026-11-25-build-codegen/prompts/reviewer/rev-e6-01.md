# Independent Adversarial Review — Experiment E6 (Multi-Function T4 Verification)

You are the **Independent Reviewer** for **Experiment E6** (`rev-e6-01`).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e6-01` (detached at commit `bb64f22152f4beec21cc5b1811b00ff6fc05e850`)
- **Baseline:** `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`
- **Commits under review:**
  - `c9bc5de5239c634ee19e71f434316afc98b9c8c4`
  - `257f256dd25f44257f7c81d00ba39e9a2449977a`
  - `732a605b808acd0d63fca29731f76caaab9e37ce`
  - `bb64f22152f4beec21cc5b1811b00ff6fc05e850`
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strict Reviewer Rules
- Do NOT edit, commit, or fix any tracked files. Only read files and run verification/reproduction commands (and ad-hoc `python3 -c` probes).
- Do NOT merely confirm tests passed! Actively hunt for:
  1. **R2 Pointer Identity & Anti-Cheat Holes** in `experiments/build_codegen/e6/mf_cemu.py`:
     - Does `Group` / `Integrated` genuinely run the REAL compiled C callbacks (`OptionsRefresh`, `OptionsApplyTimer`) in emulator heap, NEVER redirecting verified C implementations to original machine code?
     - Can a broken pointer, swapped callback, broken aliasing, or non-pointer byte diff sneak past R2 pointer correspondence?
     - Can a stub be installed inside `verification_boundary`, or an undeclared stub outside, or an asymmetric stub, without failing closed?
     - Is the generator-based callback execution (`DialogRun` yielding callback addresses) faithful to real x86 call/return semantics (registers, stack cleanup, side effects)?
  2. **Empirical Claim Verification:**
     - Independently check the parsed OMF of `playflic_pair_tu.c` to verify the refutation of the zero-FIXUPP premise (`IntroFrame -> IntroLoadCreditLines` actually has 1 EXTDEF FIXUPP!).
     - Check whether `no_fixup_call.asm` genuinely has 0 call fixups and executes the `UC_HOOK_CODE` entry hook without machine-code patching.
  3. **Fail-Closed Isolation Checks (N6, N7):**
     - Are the static/dynamic isolation checks genuinely catching interior jumps and inlined callees, or can a sneaky case bypass them?
  4. **Scope & Reproducibility:**
     - Confirm `git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile` is empty.
     - Run `pytest -q experiments/build_codegen/e6/test_e6.py` and `python3 -m experiments.build_codegen.e6.run_e6 --check`.
     - Run at least 2 independent adversarial `python3 -c` probes against `mf_cemu.py`.

## Output Format
End your response with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any), each with Severity (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`), Location (`path:line`), Explanation, and Required resolution.
3. Independent verification summary (commands run, adversarial probes, artifact check).
