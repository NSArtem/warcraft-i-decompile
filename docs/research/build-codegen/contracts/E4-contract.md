# Experiment E4 Contract & Developer Assignment — Selective OMF Extraction Feasibility

## 1. Mission & Research Question

You are the Developer for **Experiment E4** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E4`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e4`
- **Branch:** `research/build-codegen/e4`
- **Baseline commit:** `ed21ca38feadcadf7e5ba62feed65430d957a6af` (includes E0 `matcher_proto.py`, E3 `partial_matcher.py`, and E5 `omf_b3.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
Is it practically feasible to extract a verified code region (`VerifiedRegion`) from a whole-TU compiled multi-function OMF32 object — strictly obeying the RFC's **Post-Codegen Symbolic Relocation Equivalence** invariant — transform its `LEDATA` (<=1024 B), `FIXUPP32`, `THREAD`, `PUBDEF`/`LPUBDEF`, `EXTDEF`, intra-TU `call`/`jmp rel32`, and data dependencies, and link the extracted slice into **Build A `IDENTICAL`** (`0` byte diffs, `0` diffs across all `8770` LE fixups)?

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§6.1–6.4, §7.1, §14 E4)
- `experiments/build_codegen/e0/matcher_proto.py`, `experiments/build_codegen/e3/partial_matcher.py`, `experiments/build_codegen/e5/omf_b3.py`
- `tools/wc1/omf.py`, `tools/wc1/omfpatch.py`, `tools/wc1/build.py`

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e4/` (OMF32 selective extractor prototype, isolated Build A verifier, fixtures, runner, pytest suite)
- `docs/research/build-codegen/E4-omf-extraction.md`
- `docs/research/build-codegen/results/e4/` (machine-readable JSON results + relocation transformation records)

**STRICTLY PROHIBITED:**
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- **NEVER change opcodes, instruction lengths, register operands, non-address immediates, or machine operations!**
- **NEVER convert `rel8` to `rel32`!**
- **NEVER infer an unknown compiled target solely from `war.exe`!**
- Do NOT run `make verify` directly.

## 4. Technical Requirements

### 4.1 Conservative OMF32 Slice Extractor (`experiments/build_codegen/e4/omf_extract.py`)
Build a strict, fail-closed OMF32 extractor taking `(compiled_obj_path, verified_region_spec, symbol_db, orig_program)` -> `(extracted_obj_path, provenance_record)`:
1. Verify the slice passes E0/E3 `RegionMatch` BEFORE extraction.
2. Re-slice `_TEXT` to `[obj_lo, obj_hi)` splitting cleanly into `LEDATA32` chunks of <= 1024 bytes (so 10-bit `FIXUPP32` `doff` never overflows!).
3. Rebase all retained `PUBDEF32`/`LPUBDEF32` symbols inside `[obj_lo, obj_hi)` by `-obj_lo` (drop symbols outside the slice!).
4. Rebase all retained `FIXUPP32` records (expanding any `THREAD` subrecords cleanly!):
   - Intra-slice `seg(_TEXT)` fixups (e.g. jump tables owned exclusively by the slice): rebase inline/disp offset by `-obj_lo`.
   - Intra-TU `call`/`jmp rel32` targeting an independently DB-verified symbol OUTSIDE `[obj_lo, obj_hi)` (whether emitted with an `EXTDEF`/`seg` fixup OR as a direct unfixed `rel32` displacement!): verify the compiled call target matches a known DB symbol AND original at that offset calls `orig_addr(target)`, then emit `EXTDEF` + `FIXUPP32(loc=9, self_rel=True, target=ext_idx)` with inline displacement `0` (recording the exact transformation in `provenance_record`!).
   - Data dependencies: integrate cleanly with E5's `wc1_anchor_*` rewriting (whole-segment or proven RFC §6.3 `CONST` literal only!).
   - Re-chunk `FIXUPP32` records so each `FIXUPP32` immediately follows the exact `LEDATA32` chunk containing its offset (handling cross-1024-byte-boundary fixup slots by splitting `LEDATA32` safely BEFORE any 4-byte fixup field!).
5. **Strict Fail-Closed Negative Rejection Rules (RFC §6.2):**
   - Outgoing `rel8` targeting outside `[obj_lo, obj_hi)` -> FAIL CLOSED (`UnsupportedExtractionError: outgoing_rel8`).
   - Interior branch/call target inside another function outside `[obj_lo, obj_hi)` -> FAIL CLOSED (`interior_target`).
   - Ambiguous or unknown symbol identity (target not independently confirmed in symbol DB) -> FAIL CLOSED (`ambiguous_symbol`).
   - Incorrect/unproven data layout shift (mutable `_DATA` shifted) -> FAIL CLOSED (`data_layout_mismatch`).
   - Incorrect relocation target (compiled target != original target) -> FAIL CLOSED (`relocation_target_mismatch`).
   - Incomplete region dependency closure (e.g., shared jump table outside slice, or unowned `static` helper) -> FAIL CLOSED (`incomplete_closure`).
   - Byte-invariant self-check: assert that every non-relocated byte in the extracted `_TEXT` is 100% byte-identical to `orig_compiled_text[obj_lo:obj_hi]` (proving zero opcode/length/register/immediate modifications!).

### 4.2 Required Positive & Negative Extraction Cases (`experiments/build_codegen/e4/run_e4.py` & `test_e4.py`)
1. **Positive Case 1 — `ScoreTickIncome` (`0x24e90`) extracted from multi-function `score_reference` fixture** (using E3's verified `sum = delta + score` variant, with mismatching `RankName` & `ScoreSetPage` in the same compiled `.obj` and 3-byte canonical alignment tail):
   - Extract `ScoreTickIncome` slice -> verify valid OMF32 -> link into isolated `build/e4/war_score.exe` -> prove **`wc1.compare == IDENTICAL`** (`0` byte diffs, `8,770/8,770` LE fixups)!
2. **Positive Case 2 — `FarmPanelChanged` (`0x28254`) extracted from `src/status/panel_state_reference.c`** (where sibling `UnitPanelStateChanged` `0x281f4` mismatches in 61 bytes and `FarmPanelChanged` calls `UnitPanelStateChanged` + references 5 absolute data relocations):
   - Extract `FarmPanelChanged` slice -> link into isolated `build/e4/war_farm.exe` -> prove **`wc1.compare == IDENTICAL`** (`0` byte diffs, `8,770/8,770` LE fixups)!
   - *(Note from E3 empirical refutation: standalone `DialogHighlightOff` `0x16d48` under `-s -os -ol -4r -zp2` is folded onto offset `0x5f` with `DialogHighlightOn` and branches via `rel8` `74 df`/`74 f5` into `DialogItemHitTest`'s epilogue; it is therefore moved to real negative fail-closed control N1b below rather than a positive case!)*
3. **Positive Case 3 — Intra-TU `call rel32` across mismatching neighbor `B` (`A -> C`) + E5 Fix B3 data-anchor integration:**
   - Controlled multi-function TU `[A, B_mismatch, C]` compiled with real Watcom 10.0a (and/or NASM for direct unfixed `call rel32` if 10.0a emits `EXTDEF` FIXUPP) proving intra-TU `call rel32` targeting external-to-slice symbol `C` is cleanly transformed into `EXTDEF + FIXUPP32(self_rel=True)` with exact provenance, AND a multi-function extraction carrying a verified `CONST` literal dependency anchored via E5's `omf_b3.py` (`wc1_anchor_*`) -> linked cleanly to an identical oracle executable (or Build A `IDENTICAL` for a real game slice with `CONST`)!
4. **Positive Case 4 — Multi-chunk `LEDATA` (>1024 B) boundary test:**
   - Synthetic object >1024 B with a 4-byte fixup spanning across byte 1022–1026 -> verify safe chunk splitting BEFORE the fixup slot and `wlink` linkability!
5. **All 6 Required Negative Controls (Fail Closed):**
   - N1: Outgoing `rel8` — BOTH `DialogHighlightOn` AND real `DialogHighlightOff` (`0x16d48`, confirming E3's refutation fails closed in E4!) jumping into `DialogItemHitTest`'s epilogue -> rejected fail-closed!
   - N2: Interior target inside another function -> rejected fail-closed!
   - N3: Ambiguous/unknown symbol identity (attempt to infer unknown target from `war.exe`) -> rejected fail-closed!
   - N4: Incorrect/unproven mutable data layout -> rejected fail-closed!
   - N5: Incorrect relocation target -> rejected fail-closed!
   - N6: Incomplete region dependency closure (shared jump table or unmapped local static) -> rejected fail-closed!

## 5. Deliverables, Acceptance Criteria & Atomic Commits
- Deliverables: `experiments/build_codegen/e4/{omf_extract.py,fixtures/,run_e4.py,test_e4.py}`, `docs/research/build-codegen/results/e4/results.json` (preserving original compiled obj SHA-256, extracted obj SHA-256, relocation transform log, Build A compare verdict), `docs/research/build-codegen/E4-omf-extraction.md`.
- `pytest -q experiments/build_codegen/e4/test_e4.py` passes 100%; `python3 -m experiments.build_codegen.e4.run_e4` reproduces `results.json`; zero production diffs.
- 2–3 clean atomic commits:
  1. `exp(e4): conservative OMF32 selective slice extractor enforcing relocation equivalence`
  2. `exp(e4): Build A IDENTICAL extraction tests and 6 fail-closed negative controls`
  3. `docs(e4): E4 selective OMF extraction results and feasibility report`
