# Experiment E3 Contract & Developer Assignment — Partial Object Matching

## 1. Mission & Research Question

You are the Developer for **Experiment E3** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E3`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e3`
- **Branch:** `research/build-codegen/e3`
- **Baseline commit:** `1abb053c112332ec901a8961dc918bdcc25d73c4` (includes approved E0 `experiments/build_codegen/e0/matcher_proto.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
Can an experimental partial-object matcher built on E0's strengthened normalized addressing obligations contract reliably prove independent `FunctionMatch` and closed `RegionMatch` regions inside a partially mismatching multi-function OMF object — without letting an unrelated mismatching sibling poison a valid region's segment-base inference, AND without falsely accepting a region whose apparent match depends on ignoring an unresolved/mismatching neighbor or invalid data layout?

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§5.1–5.3, §6.2–6.3, §7.1, §14 E3)
- `experiments/build_codegen/e0/matcher_proto.py`
- Real multi-function reference files:
  - `src/save_score/score_reference.c` (`ScoreTickIncome` `0x24e90` + mismatching `RankName` `0x255b8` / `ScoreSetPage` `0x257f8`; note: `ScoreTickIncome` matches under 10.0a with `sum = delta + score` or let's test BOTH as-is and with a temporary fixture in `experiments/build_codegen/e3/fixtures/` where `ScoreTickIncome` matches while siblings mismatch!)
  - `src/mod_16390/dialog_hit_test_reference.c` (`DialogHighlightOff` `0x16d48` matches under `-s -os -ol -4r -zp2`, while `DialogItemHitTest` & `DialogHighlightOn` mismatch!)
  - `src/status/panel_state_reference.c` (`FarmPanelChanged` `0x28254` matches under `-s -ot -oa -ol -4r -zp2`, while `UnitPanelStateChanged` mismatches!)

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e3/` (experimental partial matcher, fixtures, runner, pytest suite)
- `docs/research/build-codegen/E3-partial-matching.md`
- `docs/research/build-codegen/results/e3/` (machine-readable JSON results)

**STRICTLY PROHIBITED:**
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT run `make verify` directly.
- Never silently accept an unresolved neighbor dependency or unverified data shift.

## 4. Technical Requirements

### 4.1 Partial-Object Matcher Prototype (`experiments/build_codegen/e3/partial_matcher.py`)
Extend/compose E0's `matcher_proto.py` to evaluate multi-function OMF objects at **per-candidate-region granularity** (`CandidateRegion -> VerifiedRegion | Conditional | Mismatch | Unsupported`):
1. **Localized (Region-Scoped) Segment-Base Inference vs Object-Wide Inference:**
   - Infer `_TEXT` base and referenced data-segment (`CONST`/`_DATA`/`_BSS`) bases **strictly from the candidate region's own relocations** (NOT polluted by mismatching siblings outside the region!).
   - Compare object-wide `seg_base` (which fails when a mismatching sibling shifts `CONST` or has a bad data ref) vs region-local `seg_base` + **RFC §6.3 per-symbol/string-literal rules**:
     - `data_scope = "whole_segment"`: region uses the entire data segment at consistent base `sb`, all bytes & pointer fixups verified.
     - `data_scope = "per_symbol_const"`: strictly ONLY for immutable `CONST` string literals satisfying ALL 4 RFC §6.3 conditions (read-only `CONST`, byte-for-byte + NUL match, original instruction references that exact address, no pointer-identity/aliasing violation!).
     - Mutable `_DATA`/`_BSS` shifted by a mismatching sibling: **FAIL CLOSED** unless an independent, proven symbol boundary exists (`data_scope = "per_symbol_mutable"` with explicit boundary proof; NEVER accept an unverified interior offset shift!).
2. **Closed-Region Dependency Classification:**
   For every candidate region `[obj_lo, obj_hi)` inside a multi-function `_TEXT`:
   - Check internal branches (`rel8`/`rel32`): any outgoing `rel8` targeting outside `[obj_lo, obj_hi)` -> **NOT independently matchable** (`CONDITIONAL` / `MISMATCH` with `outgoing_rel8_dependency`; requires expanding region to include target).
   - Check outgoing `call`/`jmp rel32` to a sibling function outside `[obj_lo, obj_hi)`: classify as `PROVEN_FUNCTION_MATCH` + `REGION_MATCH_WITH_REL32_REWRITE_NEEDED` ONLY when the sibling has an independent DB entry AND the original calls `orig_addr(sibling)` (explicitly distinguishing `proven_standalone_region` vs `requires_rel32_extraction` vs `blocked_by_sibling_dependency`).
   - Check incoming internal references from mismatching siblings (recorded as diagnostic metadata, NOT breaking `FunctionMatch`, per RFC §7.1).
   - Enforce ALL E0 soundness invariants (no truncated bodies, no out-of-bounds fixups, no unverified leading bytes, no ignored local definitions/metadata).

### 4.2 Required Real & Synthetic Cases (`experiments/build_codegen/e3/run_e3.py` & `test_e3.py`)
1. **Real Case 1 (`DialogHighlightOff` `0x16d48` in `src/mod_16390/dialog_hit_test_reference.c` under `-s -os -ol -4r -zp2`):**
   Prove `DialogHighlightOff` achieves independent `RegionMatch` while `DialogItemHitTest` and `DialogHighlightOn` are `MISMATCH`, with zero outgoing sibling dependencies!
2. **Real Case 2 (`FarmPanelChanged` `0x28254` in `src/status/panel_state_reference.c` under `-s -ot -oa -ol -4r -zp2`):**
   Prove `FarmPanelChanged` achieves `FunctionMatch` + `RegionMatch` (explicitly noting its intra-TU tail/call to mismatching sibling `UnitPanelStateChanged` `0x281f4` — check whether Watcom 10.0a emits an `EXTDEF` FIXUPP or direct `rel32`, and classify its extraction/dependency requirement honestly!).
3. **Real Case 3 (`ScoreTickIncome` `0x24e90` in experimental multi-function fixture copied from `src/save_score/score_reference.c` with `sum = delta + score` under `-s -ot -ol -4r -zp2`):**
   Prove `ScoreTickIncome` achieves independent `RegionMatch` while `RankName` (`0x255b8`) and `ScoreSetPage` (`0x257f8`) remain `MISMATCH` in the same compiled `.obj`! (Also run on unmodified `src/save_score/score_reference.c` as baseline control showing 1-reg mismatch!)
4. **Shifted `CONST` String-Pool Case (Positive & Negative Controls):**
   - Positive: Multi-function fixture where mismatching Sibling A prepends a different-length string literal in `CONST`, shifting Matching Function B's string literal offset in `CONST` -> object-wide `seg_base` fails, while region-local `per_symbol_const` (all 4 RFC §6.3 checks) cleanly proves B's match!
   - Negative (N1 — Mutable `_DATA` shift): Same shift applied to mutable `_DATA` without independent boundary proof -> MUST fail closed!
   - Negative (N2 — Outgoing `rel8` into mismatching sibling): Matching body with `rel8` targeting a mismatching sibling -> MUST fail closed (`cannot isolate region`)!
   - Negative (N3 — Unresolved/wrong sibling call target): Region calling a sibling whose original call targets a DIFFERENT address -> MUST fail closed!
   - Negative (N4 — Corrupted `CONST` literal bytes or broken aliasing): Two distinct `CONST` references aliased wrongly or 1 byte altered -> MUST fail closed!

## 5. Deliverables, Acceptance Criteria & Atomic Commits
- Deliverables: `experiments/build_codegen/e3/{partial_matcher.py,fixtures/,run_e3.py,test_e3.py}`, `docs/research/build-codegen/results/e3/results.json`, `docs/research/build-codegen/E3-partial-matching.md`.
- `pytest -q experiments/build_codegen/e3/test_e3.py` passes 100%; `python3 -m experiments.build_codegen.e3.run_e3` reproduces `results.json` deterministically; zero production diffs.
- 2 clean atomic commits:
  1. `exp(e3): partial-object matcher prototype, fixtures, and positive/negative tests`
  2. `exp(e3): empirical results and E3 partial object matching report`
