# Experiment E0 Repair Assignment (`dev-e0-02`, Fresh Replacement Session)

You are a **fresh Developer session** (`dev-e0-02`) assigned to resolve all 6 findings from Independent Review Round 1 (`rev-e0-01`, `VERDICT: REQUEST_CHANGES`) on Experiment E0.
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e0`
- **Branch:** `research/build-codegen/e0` (current HEAD: `54bfd6b74387be358ba03e005ac6566510027cd3`, baseline `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strictly Permitted Scope
- Edit ONLY under `experiments/build_codegen/e0/`, `docs/research/build-codegen/E0-matcher-soundness.md`, and `docs/research/build-codegen/results/e0/`.
- Do NOT touch `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT run `make verify` directly; run `pytest -q experiments/build_codegen/e0/test_e0.py` and `python3 -m experiments.build_codegen.e0.run_e0 --jobs 4`.

## All 6 Reviewer Findings to Resolve Completely (3 HIGH, 3 MEDIUM)

1. **[HIGH] Truncated function bodies pass (`experiments/build_codegen/e0/matcher_proto.py:351`)**
   - **Defect:** Verification uses compiled extent `[off, end)` without requiring it to cover the discovered original function end (`f["end"]`). Deleting the final `c3` (`ret`) from `InitPaths` and decrementing `_TEXT` length returned `FunctionMatch=MATCH, RegionMatch=MATCH`.
   - **Fix:** Require complete original-body coverage (`end - off >= orig_fn["end"] - base`, or exact coverage when discovered function end exists; never accept a truncated body shorter than `orig_fn["end"] - base`) before returning `MATCH` for either `FunctionMatch` or `RegionMatch`! Also reject mid-instruction truncation cleanly.
   - **Required negative controls:** Add controls for (a) truncation at an instruction boundary (e.g. `InitPaths` missing final `ret`), and (b) truncation inside an instruction!

2. **[HIGH] Trimmed bytes still count as internal branch targets (`experiments/build_codegen/e0/matcher_proto.py:275`)**
   - **Defect:** Branch target classification uses the untrimmed segment length after extent retry shortens the verified region. E.g. compiled `e9 00000000 90` vs original `e9 00000000 c3` with `orig_fn_end = +5` matched because the jump targeted offset 5 (excluded from retained region `[0, 5)`), silently discarding reachable differing bytes!
   - **Fix:** Evaluate branch target closure strictly against the **final retained region** `[region_lo, region_hi)`. Reject trimming bytes that are targeted by any branch inside the retained region, and require an explicit OMF relocation for any branch targeting outside the final retained region!
   - **Required negative controls:** Cover BOTH `rel8` and `rel32` jumps targeting trimmed tail bytes!

3. **[HIGH] External resolution ignores definitions in the same module (`experiments/build_codegen/e0/matcher_proto.py:154`)**
   - **Defect:** External fixup targets (`target_kind == "ext"`) resolve directly through `funcs_by_link` without checking `mod.publics` / `mod.statics`. Defining a referenced symbol (`__argv`) inside excluded `$$SYMBOLS`/`DEBSYM` still returned `RegionMatch=MATCH`, and a DATA public whose DB address contradicts its inferred segment base still passed!
   - **Fix:** Check `mod.publics` and `mod.statics` first when resolving `ext` targets (mirroring linker/Watcom `LPUBDEF`/`LEXTDEF` semantics):
     - If a referenced symbol is defined in an excluded metadata segment (`$$SYMBOLS`/`$$TYPES`), REJECT fail-closed (`UNSUPPORTED` / `MISMATCH`, never `MATCH`)!
     - Reconcile local `PUBDEF`/`LPUBDEF` definitions in runtime data/code segments against BOTH inferred segment anchors (`seg_base[si] + sym_off`) AND symbol-DB addresses (if present in DB, `seg_base[si] + sym_off` MUST equal `db_entry["addr"]`!).
     - Follow references through locally defined external symbols consistently for anchor propagation.
   - **Required negative controls:** (a) referenced symbol defined in `$$SYMBOLS`/`DEBSYM` -> fail closed; (b) DATA public whose DB address contradicts its inferred segment base -> fail closed!

4. **[MEDIUM] Additional executable segments bypass branch obligations (`experiments/build_codegen/e0/matcher_proto.py:413`)**
   - **Defect:** Anchored segments other than `_TEXT` are checked with `code=False` regardless of `seg.cls`. An anchored `EXTRA_TEXT` (`cls == "CODE"`) segment with an external `call rel32` lacking an OMF fixup returned `MATCH`.
   - **Fix:** Explicitly return `UNSUPPORTED` for any nonempty additional `CODE`-class segment other than `_TEXT` (or check it with full code branch obligations — returning `UNSUPPORTED` fail-closed is cleanest and safest for v1, or if checked as code ensure missing relocations fail closed).
   - **Required negative control:** Anchored additional `CODE`-class segment with missing external `call rel32` fixup -> fails closed (NEVER `MATCH`)!

5. **[MEDIUM] Completely out-of-bounds fixups disappear before validation (`experiments/build_codegen/e0/matcher_proto.py:190`)**
   - **Defect:** Fixups are filtered by overlap with `[lo, hi)` before bounds and unsupported-construct checks. A 1-byte `ret` segment with `Fixup(offset=1, loc=11, target_kind="grp", target=99)` returned `MATCH` with 0 findings.
   - **Fix:** Validate ALL fixups on every non-metadata segment BEFORE extent filtering: check `loc` validity, `target_kind` validity, and strict bounds (`0 <= fu.offset` and `fu.offset + fu.size <= seg.length`, rejecting fields starting at or past `seg.length` or negative offset with `ERROR` or `UNSUPPORTED`, NEVER silently dropping them!).
   - **Required negative control:** Segment with out-of-bounds fixup starting exactly at `seg.length` (and with unsupported loc/target) -> fails closed!

6. **[MEDIUM] Function-only audit errors permit successful command exit (`experiments/build_codegen/e0/run_e0.py:20`; `reaudit_t3.py:177`)**
   - **Defect:** Exit status checked only region errors, allowing `FunctionMatch=ERROR` (e.g., missing expected T3 public) to exit 0.
   - **Fix:** Return non-zero exit code if ANY `ERROR` occurs at either function OR region verification level (including missing expected publics or audit exceptions).
   - **Required regression test:** Add an entry-point pytest test verifying non-zero exit when a function-level `ERROR` occurs even with 0 region errors!

## Acceptance Criteria & Commits
1. Fix all 6 findings cleanly in `experiments/build_codegen/e0/`.
2. Add all required negative controls & regression tests to `controls.py` and `test_e0.py`.
3. Re-run `python3 -m experiments.build_codegen.e0.run_e0 --jobs 4` (confirming ALL controls pass and re-verifying all 519 T3 functions!) and `pytest -q experiments/build_codegen/e0/test_e0.py`.
4. Update `docs/research/build-codegen/E0-matcher-soundness.md` and `docs/research/build-codegen/results/e0/{controls.json,t3_reaudit.json,t3_reaudit.csv}` to reflect the hardened implementation and expanded controls.
5. Verify `git diff 3ee53aa -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
6. Create 1–2 clean atomic commits on `research/build-codegen/e0`:
   - `exp(e0): resolve rev-e0-01 soundness findings (truncation, trimmed branch targets, local defs, extra CODE, OOB fixups, CLI exit)`
   - `docs(e0): refresh E0 results and report after review hardening`
7. Reply with commit SHAs, updated control count, updated 519-T3 audit counts, and exact reproduction output.
