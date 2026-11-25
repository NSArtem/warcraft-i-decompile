# Experiment E6 Repair Assignment (`dev-e6-02`, Fresh Replacement Session)

You are a **fresh Developer session** (`dev-e6-02`) assigned to resolve the 2 HIGH findings from Independent Review Round 1 (`rev-e6-01`, `VERDICT: REQUEST_CHANGES`) on Experiment E6.
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e6`
- **Branch:** `research/build-codegen/e6` (current HEAD: `bb64f22152f4beec21cc5b1811b00ff6fc05e850`, baseline `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strictly Permitted Scope
- Edit ONLY under `experiments/build_codegen/e6/`, `docs/research/build-codegen/E6-multifunction-t4.md`, and `docs/research/build-codegen/results/e6/`.
- Do NOT touch `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT run `make verify` directly; run `pytest -q experiments/build_codegen/e6/test_e6.py` and `python3 -m experiments.build_codegen.e6.run_e6 --check`.

## Both Reviewer Findings to Resolve Completely (2 HIGH)

1. **[HIGH] Callback context restoration hides ABI violations (`experiments/build_codegen/e6/mf_cemu.py:444`)**
   - **Defect:** After executing a yielded callback (e.g., `OptionsRefresh` or `OptionsApplyTimer` in Group/Integrated mode), the driver restores the saved parent CPU context without checking whether the callback preserved callee-saved registers (`ebx`, `ecx`, `edx`, `esi`, `edi`, `ebp` per Watcom register convention — or exact expected preserved set per calling convention, plus `esp` after `ret N`!) and comparing them between original and C! A compiled `OptionsRefresh` with an inline `xor ebx, ebx` passed with `diffs=[]`!
   - **Fix:** Before restoring the saved parent context after each callback execution:
     - Initialize callee-saved registers to known non-zero sentinel values (or snapshot parent registers before invoking the callback),
     - After the callback returns to the sentinel address, verify BOTH:
       (a) `esp` equals `expected_sp_after_ret` (`call_sp + 4 + expected_stack_pop`) — reject any incorrect `ret N` / stack imbalance!
       (b) All preserved callee-saved registers (for watcall: `ebx`, `ecx`, `edx`, `esi`, `edi`, `ebp`, excluding only scratch/return `eax` and any explicitly clobbered register if specified — or even better, compare the full post-callback register delta `(ebx, ecx, edx, esi, edi, ebp, esp)` against the pre-callback values AND against the original side's post-callback preserved registers!) match expectations; fail closed on ANY register clobber or stack cleanup mismatch!
   - **Required negative controls:** Add pytest & runner negative controls for:
     (a) callback clobbering a callee-saved register (e.g., `ebx` clobbered in compiled `Refresh`),
     (b) callback with incorrect `ret N` stack cleanup!

2. **[HIGH] Reachable-range truncation permits substituted-callee entry bypass (`experiments/build_codegen/e6/mf_cemu.py:148, 253-255, 403-406`)**
   - **Defect:** Function ranges were computed only from entry-reachable instructions, leaving executable trailing bytes after an early `ret` unowned. A fixture with `ret; mov word [_line_timer],7; ret` at `IntroLoadCreditLines_` allowed `IntroFrame` to jump to `IntroLoadCreditLines_+1`, bypassing BOTH static and dynamic isolation checks because `+1` fell outside the truncated reachable range!
   - **Fix:** Separate **contiguous symbol ownership span** `[sym_off, next_sym_off)` (or `[sym_off, seg.length)`) from entry reachability!
     - Every byte in `[sym_off, next_sym_off)` of a substituted sibling belongs to that substituted sibling (except pure trailing alignment filler if verified non-targeted — or even stricter: reject ANY jump/transfer targeting ANY non-entry byte in `[sym_off + 1, next_sym_off)` AND reject ANY transfer into unclassified/unowned executable gaps in `_TEXT` both statically and dynamically!).
     - Dynamically, in the `UC_HOOK_CODE` monitor, reject ANY execution at an address inside a substituted sibling's full contiguous span `[sym_base + 1, sym_span_end)` OR in any unowned executable gap of `_TEXT`!
   - **Required negative control:** Add the exact trailing-code bypass variant (`ret; mov word [_line_timer],7; ret` at loader symbol, jumped to at `+1`) alongside N6 and verify it fails closed with `IsolationImpossibleError` (both statically and dynamically)!

## Acceptance Criteria & Commits
1. Fix both HIGH findings cleanly in `experiments/build_codegen/e6/mf_cemu.py`.
2. Add the 3 new negative controls (register clobber, incorrect `ret N`, trailing-code gap bypass) to `scenarios.py`, `test_e6.py`, and `run_e6.py`.
3. Re-run `pytest -q experiments/build_codegen/e6/test_e6.py` and `python3 -m experiments.build_codegen.e6.run_e6` + `--check` (confirming byte-identical JSON).
4. Update `docs/research/build-codegen/E6-multifunction-t4.md` and `docs/research/build-codegen/results/e6/results.json`.
5. Verify `git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile` is empty.
6. Create 1–2 clean atomic commits on `research/build-codegen/e6`:
   - `exp(e6): resolve rev-e6-01 findings (callback ABI validation + contiguous ownership span isolation)`
   - `docs(e6): refresh E6 results and report after review hardening`
7. Reply with commit SHAs, updated test count, and verification summary.
