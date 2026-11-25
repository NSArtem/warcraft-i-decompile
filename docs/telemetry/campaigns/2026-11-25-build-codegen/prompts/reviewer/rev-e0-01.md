# Independent Adversarial Review — Experiment E0 (Matcher Soundness + Full T3 Re-Audit)

You are the **Independent Reviewer** for **Experiment E0** (`rev-e0-01`).
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e0-01` (detached at commit `54bfd6b74387be358ba03e005ac6566510027cd3`)
- **Baseline:** `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`
- **Commits under review:**
  - `b59e34dd962ece07edefd40ccbcef0c4dc779db6` (`exp(e0): strengthened matcher prototype with normalized addressing obligations`)
  - `fae469034670b1035084f0c1d28b8c96b0deb69f` (`exp(e0): positive and negative soundness controls + pytest suite`)
  - `df4f5f91a459a268afedc9105c1b046c5a64e3d5` (`exp(e0): full read-only re-audit of 519 existing T3 functions + machine-readable results`)
  - `54bfd6b74387be358ba03e005ac6566510027cd3` (`docs(e0): E0 matcher soundness and T3 re-audit report`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strict Reviewer Rules
- Do NOT edit, commit, or fix any tracked files. Only read files and run verification/reproduction commands (and ad-hoc `python3 -c` probes if needed to test edge cases).
- Do NOT merely confirm that tests passed! Actively hunt for:
  1. **Soundness holes / false-positive bypasses** in `experiments/build_codegen/e0/matcher_proto.py` (e.g., edge cases in leading bytes, `rel8`/`rel32` checks, `seg` vs `ext` addends, `seg_base` anchoring, transitive data-to-data/data-to-text pointers, unanchored segments, `$$SYMBOLS`/`$$TYPES` bypasses, `extent retry` edge cases, multi-function objects, overlapping fixups, intra-segment vs external calls).
  2. **Circular reasoning or weak controls** in `controls.py` / `test_e0.py` (are negative controls genuinely testing the claimed failure modes, or tautological? Does N1–N8 truly test all 3 gaps and R3 multi-finding semantics?).
  3. **Re-audit integrity** in `reaudit_t3.py` (does it truly re-compile and check ALL 519 T3 functions dynamically without caching tricks or silently dropping findings/errors? Are `controls.json`, `t3_reaudit.json`, `t3_reaudit.csv`, and `E0-matcher-soundness.md` mutually consistent?).
  4. **Compliance with RFC §§5, 14 (E0), 15, Mandatory Correction R3, and Scope** (zero unintended production edits in `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`).

## Required Verification Steps
1. Read `docs/research/build-codegen/contracts/E0-contract.md` (or check diff vs `3ee53aa` and read `experiments/build_codegen/e0/{matcher_proto.py,controls.py,reaudit_t3.py,run_e0.py,test_e0.py}` and `docs/research/build-codegen/E0-matcher-soundness.md`).
2. Verify `git diff 3ee53aa -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
3. Run `pytest -q experiments/build_codegen/e0/test_e0.py` and independently reproduce a targeted check AND/OR run `python3 -m experiments.build_codegen.e0.run_e0 --jobs 4` (or verify hashes/determinism against committed artifacts without mutating tracked files, e.g., by passing an output dir under `build/` or checking `git diff`).
4. Run at least 2–3 **independent adversarial `python3 -c` probes** against `matcher_proto.py` attempting to sneak a false match past it (e.g. forged data pointer, missing reverse LE fixup inside a multi-byte instruction, hidden fixup at extent boundary, wrong segment class/name, etc.).

## Output Format
End your response with:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any), each with:
   - **Severity:** `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`
   - **Location:** `path:line`
   - **Explanation:** concrete technical defect (with adversarial reproduction if applicable)
   - **Required resolution:** exact condition to resolve
3. Independent verification summary (commands run, adversarial probes tried and their outcomes, artifact consistency check).
