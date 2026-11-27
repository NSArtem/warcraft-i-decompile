# Build & Codegen Infrastructure — Architecture Consilium
## Round 0 — Independent Analysis and Opening Position

- **Author:** Architect C — Gemini (`Gemini 4 Neon (High)`, harness `agy 1.5.17`)
- **Consilium Baseline:** `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`
- **RFC Under Reconsideration:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13` (blob `e81b117a1ece4f90e8b5cf17c0085b9cfb441b19`, identical at `e6150b8`)
- **Production Reference Inspected:** `main@a21772b8140b4b07012cde8da7da18ad3f6d56b6` (post E7 presets `3123a47` and M2 mechanical cleanup `dae45bd`)
- **Evidence Manifest:** `EV-1` (`2026-11-27T03:40:00Z`)
- **Durable Copy:** [CONSILIUM-R00-POSITION.md](file:///mnt/data/projects/warcraft-1-decompile-wt/cons-c/CONSILIUM-R00-POSITION.md)

---

## 1. Position Summary

**Verdict on RFC (`6f319ac`) and E0–E8 (`e6150b8`):** Retain the RFC's core architectural skeleton with targeted revisions—do not discard it, and do not adopt it verbatim. Its foundational separations (`FunctionMatch` vs `RegionMatch`, `CandidateRegion -> VerifiedRegion -> PlacementPlan`, `semantic_owner` vs `physical_provider`, explicit multi-function T4 trust boundaries, and provenance-tracked compilation) held up rigorously. However, E0–E8, production merges on `main@a21772b`, and seven independent probes **refute key RFC factual premises, expose three material gaps missed by E0–E8, and require reordering the production roadmap** around genuine M2 completion rather than T3 count optimization.

### Established by E0–E8 and Production Merges
- **Verification & codegen (`E0`, `E1`, `E2`, `E7`):** E0 catches 39/39 negative controls while passing 519/519 baseline T3s—and **Probe 4** extends this to **539/539 (`100%`)** production T3s on `main@a21772b`. E1/E2 proved Watcom 10.0a `-5r` (4-byte intra-CU alignment, `PARA` 16B `SEGDEF`) reproduces shared `rel8` epilogues (Group A `-oa -5r`, Group B `-5r`, Build A `IDENTICAL`), with **0/96** same-flags context codegen drift and **23/23** contiguous runs passing `RegionMatch`. E7 (`21,618` compiles, 0/417 `-4r -> -5r` regressions) already shipped 14 presets + 13 T3s into `main@a21772b` (`3123a47`), alongside M2 mechanical cleanup (`dae45bd`), bringing production to **912/1010 DONE (`90.3%`)**.
- **Behavioral T4 & CU recovery (`E6`, `E8`):** E6 proved fail-closed multi-function T4 (`VerificationBoundary`, `DependencySubstitutionPolicy`, ABI-checked generator callbacks, R2 logical pointers). E8 refuted RFC §9.3's `_DATA`/`_BSS` staircases (`0.250`/`0.281` precision) and `call_locality_drop` (`0.323`/`0.179`), establishing a premise-carrying constraint graph.

### Three Material Gaps Uncovered by This Review
1. **Watcom 10.0a uninitialized `CONST` alignment padding breaks E0 and E5 on real multi-string `-ot` CUs (Probes 3 & 7):** **157/293** fixup-bounded `war.exe` `CONST` strings contain non-zero 1994 heap residue in 1..3-byte alignment gaps (`SaveSlotPath` `0x56b1c`: `".net\0"` + `8d 75 e0`), and live Watcom 10.0a `-ot -5r` emits **non-deterministic** heap bytes (`73 00 2f` vs `76 00 61`) across consecutive runs. E0/E2/E5 missed this only because 11/11 E0 local-data T3s have 1 string each and E2's `GAMEDLG` strings are exact multiples of 4 bytes (`40B`, `36B`). Both E0 and E5 require **Invariant V4** (explicit 5-condition unreachable 1..3B `CONST` gap exemption, forcing Build A `physical_provider = ASM`).
2. **Incomplete B2 model causes `IntroOpSyncSound` (`0x23170`) false positive and misses entry-targeting `rel8` (Probe 1):** `wc1.emit.replaced_interior_refs` and RFC §7.2 model only cut-interior targets, missing both **cut-spanning `rel8`** (11 binary-wide; `IntroOpWaitSound` crossing `IntroOpSyncSound` `0x23170`) and **cut-entry `rel8`** (14 binary-wide; `EndCheckSurvive` targeting `MissionDefeat` entry `0x2f73c`). Unified Fix B2 must handle all cross-piece `rel8` under `in_place` mode (never `--legacy`) and unify `check_t3_buildable` with `BuildAPlacementPlan`.
3. **E4 selective OMF extraction prototype has 4 uncaught bugs (Probe 5):** `e4/omf_extract.py@e6150b8` crashes on cross-record `THREAD` (`:258, :823`, reproduced live), corrupts non-`_TEXT` `PUBDEF`/`LPUBDEF` when `lo > 0` (`:798-807`), linearly disassembles jump tables (`:378`), and lacks 64-fixup chunking (`:766`), plus `rev-e4-01` F1–F4.

### Strategic Sequencing Verdict
Of the **98** remaining not-DONE functions on `main@a21772b`, **68** are blocked by atomic cross-module symbol migration + Wave 3R (`61` `fn_*` + `7` `low`-conf), **10** are Wave-3 ready (`BULLET.C`), **7** are B1/B2-blocked, **5** are real ref-C bugs, and **8** require user governance. **B3 (E5), E4 extraction, E6 multi-function T4, and E8 CU recovery unlock 0/98 M2 functions.** Land **Stage 0** (hardened E0 + V4, `oldcc` short-path guard D9, `t3_audit` R3 fixes, `check_t3_buildable` cross-piece `rel8` guard) and **Stage 1** (`VerifiedRegion`/`BuildAPlacementPlan` + B1 + Unified B2 -> `+7` DONE), then drive **Stage 2** (atomic symbol migration + Wave 3R + ref-C fixes -> M2 completion), deferring **Stage 3** (unified OMF32 codec, B3+V4, E6 multi-function T4, E8 advisor, conditional E3/E4) to post-M2.

---

## 2. Experiment-by-Experiment Interpretation (E0–E8)

Throughout this section, claims are explicitly stratified into **Experimental Facts (`[FACT]`)**, **Architectural Interpretations (`[INTERP]`)**, **Engineering Decisions (`[DECISION]`)**, **Untested Assumptions (`[ASSUMP]`)**, and **Open Questions (`[OPEN]`)**.

---

### 2.1 E0 — Matcher Soundness Regression Suite

- **Artifacts:** Merge commit `7c23d23` (`research/build-codegen-experiments@e6150b8`); report `docs/research/build-codegen/E0-matcher-soundness.md@e6150b8`; contract `docs/research/build-codegen/contracts/E0-contract.md@e6150b8`; prototype `experiments/build_codegen/e0/matcher_proto.py@e6150b8`; tests `experiments/build_codegen/e0/test_e0_matcher.py@e6150b8` (77 pytest tests); results `docs/research/build-codegen/results/e0/{controls.json,t3_reaudit.json,summary.json}@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e0-01.md@e6150b8`.
- **Hypothesis:** Replacing production `wc1.match.match_obj` (`tools/wc1/match.py@a21772b`) with a bidirectional Normalized Addressing Obligation verifier separating `FunctionMatch` (local match) from `RegionMatch` (closed whole-object/region match with leading/trailing/data-segment verification) will catch all silent soundness holes (one-directional fixup checks, unverified trailing/leading bytes, unverified local data segments, unchecked rel8/rel32 target closure, silent truncation) with 0 regressions across all existing T3 functions.
- **Method actually executed:** Implemented standalone `matcher_proto.py` (`561` lines) with `extract_obj_obligations`, `extract_orig_obligations`, `verify_obligations` (bidirectional multiset/offset equality), `match_function`, and `match_region`; ran 55 crafted OMF/assembly controls (synthetic NASM + real Watcom 10.0a/OW2 compiles) and re-audited all 519 baseline T3 functions (`e14d5c0`). Independently extended in **Probe 4** to all 20 newly promoted T3 functions on `main@a21772b` (539 total).
- **Positive controls:** 16 positive controls (`controls.json@e6150b8`), covering exact code match, self-relative `CALL`/`JMP`, flat/DGROUP data relocations, valid `NOP`/alignment trailing filler, valid leading jump table bytes (synthetic), valid single-string local `CONST`/`_DATA` segments, multi-function closed regions, and non-zero extent offset matches. All 16 returned `MATCH`.
- **Negative controls:** 39 negative controls: 25 `MISMATCH` (wrong target symbol, missing/extra OMF fixup, wrong fixup width/kind, swapped relocation targets, modified local `CONST`/`_DATA` byte, non-filler trailing instruction, unexpected leading byte, truncated code, wrong addend) and 14 `UNSUPPORTED` (external `rel8` escaping region, unhandled OMF fixup method/location, unverified trailing branch target inside trimmed filler `trimmed_branch_target`, ambiguous data anchor). All 39 failed closed (`55/55` controls passed, `77/77` pytest tests green).
- **Demonstrated facts (`[FACT]`):**
  1. All **519/519** baseline T3s (`t3_reaudit.json@e6150b8`) and all **20/20** newly added T3s on `main@a21772b` (**Probe 4**, total **539/539**) pass both `FunctionMatch=MATCH` and `RegionMatch=MATCH`.
  2. Of the 519 baseline T3s, **0** have leading bytes (`lead > 0`), **0** have fixups inside local data segments, and **only 11** have any local data segment at all—and **all 11/11 contain exactly one string literal** in `CONST` (**Probe 7b**: `0x1a8e4`, `0x1a914`, `0x1a95c`, `0x1ab28`, `0x21554`, `0x21844`, `0x21c68`, `0x312f0`, `0x31360`, `0x31a80`, `0x32540`). None of the 20 new `main@a21772b` T3s have local data segments or leading bytes (**Probe 4**).
  3. Production `wc1.match.match_obj` (`tools/wc1/match.py:322-370@a21772b`) still checks fixups one-directionally (`orig_fixups` missing-fixup gaps, trailing bytes silently ignored beyond `orig_len`, local `CONST`/`_DATA` unverified in `match_obj`).
- **Assumptions (`[ASSUMP]`):**
  1. `matcher_proto.py:333` assumes every unrelocated byte of a local `CONST` segment emitted by Watcom 10.0a is deterministic and byte-identical to `war.exe`. **Refuted by Probes 3 & 7** on multi-string `-ot` `CONST` segments!
  2. `matcher_proto.py:358-359` assumes `FunctionMatch` can validate internal `rel8`/`rel32` branch closure against the whole object's linear `[region_base, region_end)` anchored at the *first* public (`self.bases.get(self.ti, base - lo)`). **Refuted by E2 Cause B** (`E2-context-alignment.md@e6150b8`): in a non-contiguous multi-function TU, a later function's ordinary intra-function `rel8` lands outside `[region_base, region_end)` and triggers a false `UNSUPPORTED: external_rel8`.
  3. Assumes `original/war.exe` disassembly decoded by `wc1.insns` faithfully captures every jump-table and code boundary (data-in-code like `0x110a0`/`0x11530` remain outside verified T3 scope).
- **Limitations:**
  - `matcher_proto.py` is standalone prototype code in `experiments/`, not wired into `tools/wc1/match.py`.
  - No real `war.exe` T3 exercised leading jump-table bytes (`0/539`) or multi-string `CONST` (`0/539`) or data-segment fixups (`0/539`); those code paths were only exercised synthetically.
  - Does not verify Build A placement invariants (e.g., cross-piece `rel8` from untouched ASM neighbors); that belongs to `PlacementPlan`.
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §§5.1–5.3 & §15 STAND WITH TWO MANDATORY FIXES:** (1) `FunctionMatch` must evaluate branch closure strictly against the function's own interval `[base, base + (end - off))`, never the first public's linear region; (2) local `CONST` verification must explicitly recognize unreachable 1..3-byte 4-byte-alignment padding strictly between verified NUL-terminated string literals (never masking `_DATA`, interior bytes, or `>=4B` gaps).
- **Further experiment required? (`[OPEN]`):** Yes — **EXP-1 (Probe on `CONST` alignment-gap verifier)** against `SaveSlotPath` (`0x14740`) and `GAMEDLG` multi-string `-ot` TUs to confirm zero false positives and zero false negatives before merging E0 into `tools/wc1/match.py`.

---

### 2.2 E1 — Shared Epilogue Reproduction

- **Artifacts:** Merge commit `b2965ba` (`@e6150b8`); report `docs/research/build-codegen/E1-shared-epilogue.md@e6150b8`; contract `contracts/E1-contract.md@e6150b8`; script/tests `experiments/build_codegen/e1/{run_e1.py,test_e1.py}@e6150b8` (18 tests); results `results/e1/{summary.json,variants.json,build_a.json}@e6150b8`.
- **Hypothesis:** Watcom 10.0a naturally emits cross-function short `rel8` shared epilogues when sibling functions from the same original CU are compiled together in one TU under the right compiler flags—specifically testing Group A (`DialogItemHitTest` `0x16cc8`, `DialogHighlightOn` `0x16d34`, `DialogHighlightOff` `0x16d48`) and Group B (`IntroOpPlaySound` `0x2315c`, `IntroOpSyncSound` `0x23170`, `IntroOpWaitSound` `0x231cc`).
- **Method actually executed:** Swept 97 multi-function TU variants (`196` function observations) across compiler flags (`-4r`/`-5r`, `-ot`/`-os`/`-oa`, etc.) and source spellings; verified candidate objects with E0 `RegionMatch` and full Build A link to `war.exe` (`IDENTICAL`). Also tested standalone `IntroOpSyncSound` (`0x23170`) replacement in Build A.
- **Positive controls:**
  - **Group A (`-oa -5r`, revised pure C TU):** Exact byte-for-byte reproduction of both cross-function `rel8` shared epilogues (`0x16d3c: 74 f3`, `0x16d50: 74 df`), E0 `RegionMatch=MATCH`, full Build A `IDENTICAL` (`build_a.json@e6150b8`).
  - **Group B (`-5r`, unmodified canonical C TU):** Exact reproduction of `0x2315c`, `0x23170` (`IntroOpSyncSound` in the middle, offsets `0 / 0x14 / 0x70`), and `0x231cc` including `0x231d7: 74 93` and `0x231e1: 75 89` jumping across `IntroOpSyncSound` into `IntroOpPlaySound`; E0 `RegionMatch=MATCH`; full Build A `IDENTICAL`.
- **Negative controls:**
  - **R6 negative control (alignment delta):** `-4r` / wrong alignment yields `74 f5` instead of `74 f3` (`+2B` filler shift) -> rejected as `MISMATCH`.
  - **Standalone `IntroOpSyncSound` (`0x23170`) Build A control (4 variants):** Replacing only `0x23170` fails NASM assembly (`OBJ format can only handle 16- or 32-byte relocations`) because ASM `IntroOpWaitSound` branches across the `0x23170` cut to ASM `IntroOpPlaySound`.
- **Demonstrated facts (`[FACT]`):**
  1. Watcom 10.0a cross-function `rel8` tail-sharing IS natively reproducible in pure C when sibling functions are co-compiled in a single TU under `-5r` (or `-oa -5r`).
  2. Co-compiling a shared-epilogue cluster into one `VerifiedRegion` eliminates the cross-piece `rel8` boundary entirely for Build A, achieving `IDENTICAL` links with zero NASM workarounds.
  3. E1 already demonstrated—before M2 cleanup hit it in production!—that standalone replacement of `IntroOpSyncSound` (`0x23170`) breaks NASM assembly due to spanning `rel8` from `IntroOpWaitSound`.
- **Assumptions (`[ASSUMP]`):**
  1. Group A required revised C spelling + `-oa -5r` (not unmodified existing T4 sources), and Group B's `IntroOpWaitSound` (`0x231cc`) is still one of the 5 `PLAYFLIC` xfail T4 functions on `main@a21772b` (`test_playflic_t4.py`), meaning Group B's exact E1 C source must be verified for T4 behavioural parity when promoted in production (note: E1 matched `war.exe` bytes identically, which subsumes behavioural parity for `0x231cc`!).
  2. Assumes other shared-epilogue clusters (`0x1e380`/`0x1e3b4`, `0x1af90`/`0x1b00c`, `0x2c1e8`/`0x2c208`, `0x2e96c`/`0x2e9c4`, `0x2efd0`/`0x2f0a8`, `0x2f694`/`0x2f73c`, `0x28074`/`0x28093`) behave analogously—untested for those 7 clusters.
- **Limitations:** Only 2 of 9 game-range shared-epilogue clusters tested (though they include both adjacent and spanning `rel8` cases). Does not solve the *incremental* state where only one member of a cluster has C reconstructed (that requires unified Fix B2).
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §7.2 & §14(E1) STAND AND ARE STRENGTHENED:** Co-compiled multi-function `VerifiedRegion` is the preferred long-term, zero-hack solution for shared-epilogue clusters (and Group B's E1 C also resolves one of the 4 `PLAYFLIC` xfail functions!). However, unified Fix B2 remains necessary for incremental M2 progress when a sibling function is not yet reconstructed (e.g., `fn_2e9c4` or `ViewportLayerCallback` or standalone `MissionDefeat`).
- **Further experiment required? (`[OPEN]`):** No blocking experiment for architecture; production promotion of Group A/B only needs normal `make verify` + Build A check.

---

### 2.3 E2 — Compilation-Context Sensitivity & Intra-TU Alignment

- **Artifacts:** Merge commit `c30f3f5` (`@e6150b8`); report `docs/research/build-codegen/E2-context-alignment.md@e6150b8`; contract `contracts/E2-contract.md@e6150b8`; code/tests `experiments/build_codegen/e2/{run_e2.py,test_e2.py}@e6150b8` (27 tests); results `results/e2/{alignment_matrix.json,loop_sensitivity.json,census_96.json,domino_probe.json,summary.json}@e6150b8`.
- **Hypothesis:** Test RFC §2.2.5's premise ("Watcom 10.0a always aligns functions to 4 bytes, whereas OW2 aligns to 16 bytes") and measure whether consolidating multiple functions into one TU introduces codegen drift (context sensitivity, loop alignment, call/tail-call changes, `CONST`/`_DATA` dominoes).
- **Method actually executed:**
  - 28-cell compiler alignment matrix (`10.0a` vs `OW2` × `-3r`/`-4r`/`-5r` × `-ot`/`-os`/`-od`).
  - 448 loop-alignment TUs testing branch/loop target alignment sensitivity.
  - 42 intra-TU call controls.
  - 96-T3 multi-function consolidation census across real game areas (`2,097` function observations), including 23 contiguous runs (up to 40-function `STATUS.C`) and forced whole-area TUs.
  - 63-edit / 210-neighbor domino probe mutating one function and measuring neighbor byte stability.
- **Positive controls:**
  - **23/23 contiguous multi-function runs** (including 40-function `STATUS.C`, `GAMEDLG` runs) pass E0 `RegionMatch=MATCH` under `-5r` with exact original inter-function alignment!
  - **0/96 same-flags context instruction changes** across 2,097 observations.
- **Negative controls:**
  - Controlled `-os` context test detects **23** genuine body changes—100% attributable to cross-function tail-sharing/epilogue folding (expected `-os` optimization, not spooky context drift).
  - Domino probe detects **1** real cross-function `CONST` addend shift (`SaveVersionDialog` when `VersionMismatchDialog`'s literal length changes), proving data-layout coupling inside shared `CONST`.
  - Forced non-contiguous consolidation exposes 13/96 `FunctionMatch` losses, cleanly classified into Causes B (9 E0 bug), C (flag mismatch), D (static/extern visibility), F (intervening data/padding)—**0** codegen drift.
- **Demonstrated facts (`[FACT]`):**
  1. **RFC §2.2.5's alignment premise is REFUTED:** Watcom 10.0a intra-TU function alignment is **flag-dependent**:
     - `-4r -ot`: **16-byte** aligned (matches `i486` cache-line preference!).
     - `-3r -ot` and `-5r -ot`: **4-byte** aligned (matching `war.exe`!).
     - `-os` and `-od`: **1-byte** aligned (packed).
     - Meanwhile, Watcom 10.0a's OMF `_TEXT` `SEGDEF` itself carries **PARA (16-byte)** segment alignment even under `-5r` (so separate `.obj` files are 16-byte aligned by `wlink`, whereas functions inside a single `-5r` `.obj` are 4-byte aligned!).
     - OW2 aligns to **16-byte** under both `-4r` and `-5r`.
  2. **Same-flags intra-TU codegen is context-independent (`0/96` drift)** under `-ot`, confirming that multi-function CUs are safe from mysterious compiler crosstalk when flags match.
  3. **E0 `FunctionMatch` has a confirmed bug (`Cause B`, 9/13 losses):** evaluating intra-function branch bounds against the first public's linear region breaks non-contiguous `FunctionMatch`.
  4. **Hidden coincidence uncovered by Probe 7d:** E2's `GAMEDLG` `gamedlg_run_1_aligned_0` (`VersionMismatchDialog` + `SaveVersionDialog`) passed E0 `RegionMatch` with 0 `CONST` diffs *only* because `len("Warcraft version numbers are different.\0") == 40` (`40 % 4 == 0`) and `len("Saved game uses old version number!\0") == 36` (`36 % 4 == 0`), leaving zero alignment gap bytes!
- **Assumptions (`[ASSUMP]`):** Assumes `0/96` context drift generalizes to functions with `-o` global optimizations (e.g. `-ox`, `-oi` inlining) only when functions are non-`static` or do not trigger interprocedural inlining/register-use propagation; Watcom 10.0a `-ot` does not inline across non-inline functions, but `static` functions under `-oi`/`-ox` could behave differently.
- **Limitations:** 96-T3 census tested `-5r`/`-4r`/`-os` on existing T3s, not `static` helper inlining under `-oi`. Did not exercise a multi-string `CONST` run with `len % 4 != 0`.
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §2.2.5 MUST BE REPLACED** with the verified alignment table (`-4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`, `OW2 = 16B`).
  - **RFC §4 / §7 / §18 STAND AND ARE STRENGTHENED:** Because `-5r` produces exact 4-byte intra-CU alignment with `0/96` codegen drift and 23/23 contiguous runs passing `RegionMatch`, **whole-TU integration (`RegionMatch`) is dramatically simpler and more reliable than expected**, sharply reducing the need for E4 selective extraction!
- **Further experiment required? (`[OPEN]`):** Verify `CONST` alignment-gap handling on a multi-string `-ot` contiguous run with `len % 4 != 0` (**EXP-1**), and document whether `-oi`/`-ox` inlining of `static` functions changes context sensitivity when encountered.

---

### 2.4 E3 — Partial Object Matching

- **Artifacts:** Merge commit `13963fb` (`@e6150b8`); report `docs/research/build-codegen/E3-partial-matching.md@e6150b8`; contract `contracts/E3-contract.md@e6150b8`; prototype `experiments/build_codegen/e3/partial_matcher.py@e6150b8` (`761` lines); tests `experiments/build_codegen/e3/test_e3_partial.py@e6150b8` (24 tests); results `results/e3/summary.json@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e3-01.md@e6150b8`.
- **Hypothesis:** A fail-closed partial matcher can verify a matched single-function (or contiguous sub-region) slice inside a multi-function `.obj` containing mismatching sibling functions—without weakening E0's soundness invariants—and recover real `MATCH_UNBUILDABLE` targets (`FarmPanelChanged 0x28254`, `ScoreTickIncome 0x24e90`, `DialogHighlightOff 0x16d48`).
- **Method actually executed:** Built `partial_matcher.py` implementing `PartialMatchResult` (`FunctionMatch` vs `RegionMatch` vs `PartialRegionMatch`), slice-local branch closure, cross-slice branch rejection, trailing-filler verification, and per-symbol data checks; ran 24 tests including 3 real targets and synthetic shifted `CONST`/negative controls.
- **Positive controls:**
  - **`FarmPanelChanged` (`0x28254`):** Partial slice matched inside multi-function TU (sibling `UnitPanelStateChanged` mismatched); Watcom 10.0a emitted a self-relative `EXTDEF` `FIXUPP` to `UnitPanelStateChanged_` (no bare `rel32` needed).
  - **`ScoreTickIncome` (`0x24e90`):** Partial slice matched (`sum = delta + score` spelling, 3B trailing alignment filler verified and trimmed cleanly).
  - Synthetic shifted `CONST` slice matched via per-symbol data check.
- **Negative controls:**
  - **`DialogHighlightOff` (`0x16d48`):** Refuted as a standalone partial-slice target—under `-os` it folds with `DialogHighlightOn` at `0x5f` and has an outgoing `rel8` into `DialogItemHitTest` (`0x16d31`). Partial matcher rightly rejected it (`UNSUPPORTED: external_rel8`).
  - Synthetic cross-slice `rel8`, unverified trailing bytes, bad fixup, and overlapping data symbol controls all failed closed.
- **Demonstrated facts (`[FACT]`):**
  1. Partial matching works cleanly and fail-closed on functions whose slice is branch-closed (`FarmPanelChanged`, `ScoreTickIncome`) and properly refuses non-closed shared-epilogue slices (`DialogHighlightOff`).
  2. **Probe 2** verified `partial_matcher.py:669`'s terminating-instruction check (`("ret", "retf", "jmp", "iret", "iretd")`): **0/539** `main@a21772b` T3s fail it, while **8/1010** in-scope functions do not end in those mnemonics (`0x10650` `nop`, `0x110a0`/`0x11530` data-in-code, `0x116a8` `nop`, `0x20258` `pop ebx` fallthrough, `0x208d4` `mov eax, eax`, `0x28074` `nop`, `0x2f694` `EndCheckSurvive` ending in `jge 0x2f746` fallthrough into `MissionDefeat`).
  3. **Review finding (`rev-e3-01` Nit 3):** `partial_matcher.py:206` drops E0's `trimmed_branch_target` diagnostic when checking branch targets into trimmed trailing filler.
- **Assumptions (`[ASSUMP]`):**
  1. Both real positive targets (`FarmPanelChanged`, `ScoreTickIncome`) have **zero local data segments**; E3's per-symbol local data matching was validated only on synthetic fixtures, never on a real multi-string `-ot` `CONST` segment (where Probe 3/7 shows uninitialized padding).
  2. Assumes terminating-instruction heuristic excludes `call noreturn` (currently harmless on `war.exe` since 0/539 T3s hit it, but needs an explicit `noreturn` allowlist for larger projects).
- **Limitations:** Standalone duplicate of E0 matcher logic (`761` lines) rather than one unified engine; both real positive targets (`0x28254`, `0x24e90`) are **already DONE as T4** on `main@a21772b` (0 M2-completion impact).
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §5 STANDS, BUT E3 SHOULD BE UNIFIED INTO E0'S ENGINE AND DEFERRED FOR BUILD INTEGRATION:** Partial *matching* (as a diagnostic / `FunctionMatch` capability in the unified E0 matcher, fixing E2 Cause B at the same time) is cheap and useful immediately so analysts see which functions inside a multi-function TU already match. Partial *Build A integration* (via E4) should be deferred post-M2.
- **Further experiment required? (`[OPEN]`):** None blocking; before enabling per-symbol data slicing in production, validate it under **EXP-1** (`CONST` alignment-gap rule).

---

### 2.5 E4 — Selective Object Extraction Feasibility

- **Artifacts:** Merge commit `7edf63b` (`@e6150b8`); report `docs/research/build-codegen/E4-omf-extraction.md@e6150b8`; contract `contracts/E4-contract.md@e6150b8`; prototype `experiments/build_codegen/e4/omf_extract.py@e6150b8` (`889` lines); tests `experiments/build_codegen/e4/test_e4_extract.py@e6150b8` (17 tests); results `results/e4/summary.json@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e4-01.md@e6150b8`.
- **Hypothesis:** A conservative OMF32 slice extractor can extract a `PartialRegionMatch` slice from a multi-function `.obj` into a standalone `.obj` satisfying RFC §6's `Post-Codegen Symbolic Relocation Equivalence`, linking Build A `IDENTICAL` and failing closed on all 6 unsupported reference classes (RFC §6.2).
- **Method actually executed:** Built `omf_extract.py` (`889` lines) re-emitting OMF32 records (`THEADR`..`MODEND32`), rebasing `_TEXT` offsets and `FIXUPP32` records, converting bare intra-segment `rel32` calls into `EXTDEF` + self-relative `FIXUPP32`, optionally dropping/anchoring `CONST`, and splitting `>1024B` slices across `LEDATA32` chunks; ran 17 tests.
- **Positive controls:**
  - Extracted `ScoreTickIncome` (`0x24e90`) and `FarmPanelChanged` (`0x28254`) from multi-function `.obj`s -> full Build A `IDENTICAL` (`summary.json@e6150b8`).
  - Controlled synthetic `A -> C` cross-slice call (both Watcom `EXTDEF` and NASM bare `rel32` -> synthesized `EXTDEF` `FIXUPP32`) -> oracle link `IDENTICAL`.
  - Controlled E5 `CONST` extraction and `1500B` `LEDATA32` split (`1022 + 478` bytes avoiding split-fixup boundary) -> oracle link `IDENTICAL`.
- **Negative controls:** 8/8 negative controls covering all 6 RFC §6.2 rejected classes (`external_rel8`, intra-slice jump table / indirect branch to non-slice, anonymous local symbol without external name, overlapping `PUBDEF`, unsupported fixup kind/location, cross-slice non-public fallthrough/tail) failed closed with `UnsupportedExtractionError`.
- **Demonstrated facts (`[FACT]`):**
  1. Selective OMF32 extraction is **technically feasible** for simple branch-closed slices (`ScoreTickIncome`, `FarmPanelChanged`) and preserves `Build A IDENTICAL`.
  2. **CRITICAL DEFECTS UNCOVERED BY PROBE 5 & CODE INSPECTION (`experiments/build_codegen/e4/omf_extract.py@e6150b8`):**
     - **Bug 5a (Cross-record `THREAD` crash — reproduced live in Probe 5):** `raw_fixups()` (`omf_extract.py:258`) and non-`_TEXT` `FIXUPP` emission (`:823`) instantiate `Threads()` *fresh inside the per-record loop*, wiping OMF32 `THREAD` slots `F0..F3`/`T0..T3` across record boundaries! Probe 5 fed a valid cross-record `THREAD` OMF32 module: `wc1.omf.parse_module` parsed `1` fixup cleanly, while `e4.raw_fixups` crashed with `UnsupportedExtractionError: unsupported_construct: undefined THREAD`.
     - **Bug 5b (Non-`_TEXT` `PUBDEF`/`LPUBDEF` corruption when `lo > 0`):** `omf_extract.py:798-807` filters *every* `PUBDEF`/`LPUBDEF` record with `if lo <= off < hi` and rebases `off - lo` **without checking `if pseg == ti:`**—silently dropping or corrupting `_DATA`/`_BSS`/`CONST` public symbols whenever extracting a slice starting at `lo > 0`.
     - **Bug 5c (Linear Capstone decode fails on leading/inline jump tables):** `scan_slice` (`omf_extract.py:378-384`) linearly disassembles `[lo, hi)` starting at `lo`, which will misdecode pre-function switch jump tables (B1) or inline jump tables as instructions.
     - **Bug 5d (Missing 64-fixup `FIXUPP32` chunking):** `omf_extract.py:766` emits all fixups for a 1024-byte `LEDATA32` chunk in one `FIXUPP32` record without E5's 64-fixup chunking (`omf_b3.py:409`), risking OMF record-length overflow on dense relocation runs.
     - Plus **`rev-e4-01`'s 4 Low findings**: F1 (`VerifiedRegion` can be forged by caller without matcher minting), F2 (pre- vs post-plan digest ambiguity), F3 (`Fix.encode` missing `0 <= doff < 1024` assertion), F4 (16-bit `big` `SEGDEF` 64 KiB widening).
- **Assumptions (`[ASSUMP]`):** Campaign `decisions.md@e6150b8` (D6) assumed E4's prototype is production-ready pending only minor `rev-e4-01` polish, and assumed selective extraction is a needed bridge during M2/CU consolidation. Both assumptions are false: Probe 5 revealed 4 additional material bugs, and E2+E7 showed whole-TU `-5r` matching succeeds on 23/23 contiguous runs while E4 unlocks **0/98** M2 functions.
- **Limitations:** `omf_extract.py` duplicates OMF parsing/emission instead of sharing a single hardened OMF codec with `wc1.omf`/`wc1.omfpatch`/E5.
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §6 INVARIANTS STAND; PRODUCTION ADOPTION OF E4 MUST BE DEFERRED POST-M2 (see `OBJ-C03`, `DEC-C08`).** Selective extraction is a fallback escape hatch, not a primary architecture path. Whole-TU integration (`RegionMatch`) is strictly preferred; E4 should only be hardened (fixing all 8 defects over a shared OMF32 codec) and shipped *if* post-M2 CU consolidation actually encounters persistent mismatching siblings that cannot be resolved by `-5r` presets or Wave 4B.
- **Further experiment required? (`[OPEN]`):** None before M2. If adopted post-M2, require negative/positive regression tests covering all 4 Probe-5 bugs (`THREAD`, non-`_TEXT` `PUBDEF` with `lo > 0`, B1/inline jump table slice, >64 fixups/chunk) plus `rev-e4-01` F1–F4.

---

### 2.6 E5 — Data-Anchor Decoupling (`Fix B3`)

- **Artifacts:** Merge commit `ed21ca3` (`@e6150b8`); report `docs/research/build-codegen/E5-data-anchor-b3.md@e6150b8`; contract `contracts/E5-contract.md@e6150b8`; prototype `experiments/build_codegen/e5/omf_b3.py@e6150b8` (`424` lines); tests `experiments/build_codegen/e5/test_e5_b3.py@e6150b8` (86 tests); results `results/e5/summary.json@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e5-02.md@e6150b8`.
- **Hypothesis:** Local read-only/initialized data segments (`CONST`, `_DATA`) emitted by C objects can be decoupled from Build A's physical segment placement by proving byte/relocation equivalence against `war.exe`'s ASM-provided data bytes, stripping the C object's physical data emission, and redirecting code fixups to external ASM anchors (`EXTDEF` + `FIXUPP32` target=extern), allowing natural C string literals / local data without duplicating data or violating Build A byte identity.
- **Method actually executed:** Implemented `omf_b3.py` supporting `whole_segment` and `per_symbol` data verification, all 4 OMF32 frame modes (`FLAT`, `DGROUP`, `Target`, `EXTDEF`), cross-record `THREAD` preservation, 64-fixup `FIXUPP32` chunking (`:409`), and Build A integration; ran 86 tests including 9 full Warcraft Build A links.
- **Positive controls:** **9/9 full Warcraft Build A `IDENTICAL` links** (`summary.json@e6150b8`), including `SaveErrorDialog` (`0x1aca8`) under `-os`, native `-ot` explicit `_DATA` char arrays, real 3-segment `GAMEDLG` TU, cross-record `F3/T3` `THREAD` fixture, all 4 OMF frame modes, and `per_symbol` `CONST` anchoring.
- **Negative controls:** Modified data bytes, unverified padding gaps (`omf_b3.py:172-173`), unsupported relocation inside data, missing anchor, and `_BSS`/unverified symbol cases all failed closed.
- **Demonstrated facts (`[FACT]`):**
  1. Rewriting C object fixups from local `CONST`/`_DATA` segments to ASM-provided `EXTDEF` anchors works reliably with `wlink` and produces Build A `IDENTICAL` across all 4 frame modes and cross-record `THREAD` records.
  2. **Two RFC/prior premises were REFUTED by E5:**
     - **0/514** baseline objects emit native OMF `THREAD` records (Watcom 10.0a's `wcc386` did not emit them on baseline objects, though E5 correctly supports them via synthetic fixtures).
     - Adding a neighbor function under `-ot` does **not** fix `SaveErrorDialog`'s `0x24` vs `0x22` string stride—that stride difference is `-ot` (4-byte padded) vs `-os` (byte-packed), not missing neighbor context.
  3. **CRITICAL GAP UNCOVERED BY PROBES 3 & 7 (not tested in E5):**
     - In `war.exe`'s `CONST` pool (`0x569d0..0x58440`), **157 of 293** fixup-bounded strings have **non-zero 1994 compiler heap residue** in their 1..3-byte 4-byte alignment gaps (e.g., `SaveSlotPath 0x14740`: `".net\0"` + `8d 75 e0` + `".sav\0"` + `08 00 e8` + `"save%d\0"` + `a5`).
     - Compiling a 2-string `-ot -5r` TU (`".net"`, `".sav"`) with live Watcom 10.0a emits **non-deterministic** uninitialized heap bytes in `[5:8]` (`73 00 2f` vs `76 00 61` on two consecutive runs; `war.exe` has `8d 75 e0`), while the string bytes and offsets (`0x0`, `0x8`) are 100% identical!
     - Because `omf_b3.py` requires either byte-identical `whole_segment` (`CONST` bytes equal `war.exe`) OR zero uncovered gap bytes in `per_symbol` (`omf_b3.py:172-173`), **E5 as prototyped will FAIL on the majority of real multi-string `-ot` `CONST` CUs in `war.exe`** (including `SaveSlotPath 0x14740`)!
- **Assumptions (`[ASSUMP]`):** E5 implicitly assumed that `-ot` `CONST` alignment padding is zero-filled or identical between 1994 Watcom 10.0a and Wine-hosted Watcom 10.0a. **Refuted by Probe 7d.**
- **Limitations:**
  - Unlocks **0/98** M2-completion functions (`SaveErrorDialog 0x1aca8` is already DONE as T4!).
  - `rev-e5-02` noted residual hardening items needed before production integration (strictly validating `CONST` vs `_DATA` mutability/aliasing and unifying with the shared OMF codec).
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §8.1 (`semantic_owner` vs `physical_provider`) IS VALIDATED AND BECOMES EVEN MORE IMPORTANT:** Because `war.exe`'s 157 non-zero heap-residue `CONST` pad gaps can *never* be reproduced byte-for-byte by C in Build A, ASM **must** remain Build A `physical_provider` for those `CONST` segments even after C becomes `semantic_owner`!
  - **RFC §8.2 (`Fix B3`) STANDS CONDITIONALLY:** Adopt post-M2 (Stage 3, for CU consolidation and natural C literals), **only after** adding explicit verified-gap support for unreachable 1..3-byte 4-byte-alignment padding strictly between verified NUL-terminated `CONST` strings.
- **Further experiment required? (`[OPEN]`):** **EXP-1** — verify E0 + E5 with the `CONST` alignment-gap rule on real `SaveSlotPath` (`0x14740`, 3 strings with non-zero heap residue `8d75e0`, `0800e8`, `a5`) linking Build A `IDENTICAL`, plus negative controls (non-zero byte inside a string, 4-byte gap, `_DATA` gap, pointer referencing a gap byte).

---

### 2.7 E6 — Multi-Function Differential Verification (`wc1.cemu`)

- **Artifacts:** Merge commit `bb3387b` (`@e6150b8`); report `docs/research/build-codegen/E6-multifunction-t4.md@e6150b8`; contract `contracts/E6-contract.md@e6150b8`; prototype `experiments/build_codegen/e6/mf_cemu.py@e6150b8` (`622` lines); tests `experiments/build_codegen/e6/test_e6_mf_cemu.py@e6150b8` (96 tests); results `results/e6/summary.json@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e6-01.md@e6150b8`.
- **Hypothesis:** Multi-function C objects can be differentially verified (T4) across three modes (`Isolated`, `Group`, `Integrated`) without silent intra-TU call leakage, callback ABI drift, or false pointer-identity mismatches, using an explicit `VerificationBoundary` + `DependencySubstitutionPolicy` and strictly typed logical pointer correspondence (R2).
- **Method actually executed:** Implemented `mf_cemu.py` (`622` lines) on top of `wc1.cemu`/`wc1.emu`: contiguous `VerificationBoundary` ownership (not reachability-truncated), 3 substitution mechanisms (`orig_addr_stub`, `symbol_aware_reloc`, `c_entry_hook`), generator-based real callback execution with pre-restore `watcall` ABI validation (checking 6 preserved regs `ebx/esi/edi/ebp/esp/ds` + callee stack-pop convention), and R2 typed logical pointer correspondence (`LogicalPtr`); ran 96 tests (10 positive across all 3 modes + 14 negative fail-closed variants).
- **Positive controls:** 10 positive controls across `Isolated`, `Group`, and `Integrated` modes, including real game functions (`IntroFrame` -> `IntroLoadCreditLines`, callback-bearing functions, NASM zero-FIXUPP intra-TU call fixture proving `c_entry_hook`, and R2 logical function-pointer comparison across C-side and original-side addresses).
- **Negative controls:** 14 negative variants all failed closed: unexpected unstubbed intra-TU call (`IsolationImpossibleError`), indirect jump/computed branch when `subs` non-empty, callback clobbering callee-saved register or misaligning `esp`, untyped raw integer masquerading as function pointer under R2, non-contiguous boundary gap, ambiguous symbol binding.
- **Demonstrated facts (`[FACT]`):**
  1. **RFC §11.3 premise partially refuted:** On `IntroFrame -> IntroLoadCreditLines`, Watcom 10.0a actually emitted **1 self-relative `EXTDEF` `FIXUPP`** rather than a zero-FIXUPP bare `rel32` call (making `symbol_aware_reloc` sufficient there); however, bare `rel32` intra-TU calls *can* occur (e.g., `static` calls or NASM), and E6 proved `c_entry_hook` intercepts them cleanly via a synthetic NASM control.
  2. Generator-based callback execution cleanly validates real `watcall` ABI preservation *before* restoring emulator state, closing a subtle soundness gap where stubbed callbacks could hide stack/register corruption.
  3. R2 typed logical pointer correspondence resolves legitimate C-vs-original function-pointer address differences without weakening raw integer equality checks.
- **Assumptions (`[ASSUMP]`):**
  1. Static scan rejects indirect jumps (`jmp reg`/`jmp [mem]`, e.g., switch jump tables!) whenever `subs` is non-empty (`mf_cemu.py`). This is safely fail-closed, but means multi-function TUs containing switch statements cannot use `Isolated` mode with `c_entry_hook` unless jump-table targets are proven strictly intra-function.
  2. R2 covers **function** pointer correspondence, not **data** pointer correspondence (e.g., if C allocates a local `CONST` string at a different virtual address than `war.exe` and returns a `char *` to it!).
- **Limitations:**
  - Tested on only 2 real game TUs plus synthetic fixtures.
  - Unlocks **0/98** M2-completion functions today (every single-function T4 already works under `tools/wc1/cemu.py@a21772b`).
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §§11.1–11.3 STAND WITH TWO ADDITIONS:** (1) Gate production adoption as a **mandatory prerequisite before migrating the first multi-function T4 file** (Stage 3, not blocking M2); (2) extend R2 before Build B / `CONST`-owning T4s to cover **typed read-only data-pointer correspondence** (or require Build A ASM data anchoring in T4), and allow proven intra-function switch tables under `Isolated` mode.
- **Further experiment required? (`[OPEN]`):** None before M2. Before multi-function T4 consolidation begins in Stage 3, run a targeted probe on a switch-bearing multi-function T4 TU and a string-pointer-returning T4 TU (**EXP-4**).

---

### 2.8 E7 — Original Compiler Calibration (Watcom 10.0a)

- **Artifacts:** Merge commit `c946f38` (`@e6150b8`); report `docs/research/build-codegen/E7-compiler-calibration.md@e6150b8`; contract `contracts/E7-contract.md@e6150b8`; tests `experiments/build_codegen/e7/test_e7_calibration.py@e6150b8` (20 tests); results `results/e7/summary.json@e6150b8`; review `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e7-01.md@e6150b8`. **Production landing:** `feature/e7-compiler-presets@3123a47` merged into `main@a21772b` (`docs/telemetry/campaigns/2026-11-27-e7-production/report.md@a21772b`).
- **Hypothesis:** Systematic empirical calibration of Watcom 10.0a across flag configurations (`-3r/-4r/-5r`, `-ot/-os/-oa/-ox/-od`, `-zp1/-zp2`, `-d1+`, etc.) will identify the actual 1994 build presets, recover T3 matches from existing T4s without C rewrites, and determine whether compatible-flag intersections `S(f)` partition modules into distinct original CUs.
- **Method actually executed:** Probed 31 compiler options for 10.0a support; executed **21,618 compiles** across **23,504 cells** (`519` T3 + `373` dependency-clean T4 × `26` flag configs; `12` dep-dirty T4 explicitly excluded and logged); verified all newly recovered T3s with E0 + Build A link; computed per-module `S(f)` intersections.
- **Positive controls:**
  - Confirmed 29/31 options supported by Watcom 10.0a (`-6r` rejected `E1073`, `-ob` rejected `E1074`).
  - Recovered **19** function matches, **14** whole/region matches, **13** buildable T3s (all 13 linked combined Build A `IDENTICAL`, `532/527`, and subsequently merged into `main@a21772b` via `3123a47`!), plus **218** improved T4s (closer instruction/byte distance).
  - **0/417** `-4r -> -5r` T3 regressions (proving `-5r` is strictly safe over `-4r` on every tested `-4r` T3).
- **Negative controls:**
  - Rejected unsupported flags `-6r`/`-ob` cleanly.
  - Explicitly retained **84/125** empty module `S(f)` intersections (`4/94` among T3-only modules) as contradictory/incomplete evidence rather than auto-splitting modules—critical protection against overfitting `S(f)` to imperfect T4 source spellings!
  - Discovered and isolated Watcom 10.0a's **~129-character path-buffer access violation** (`wcc386` crashes under Wine on long paths; independently corroborated in E2, E5, E8).
- **Demonstrated facts (`[FACT]`):**
  1. The original `war.exe` was predominantly compiled with **Watcom 10.0a `-5r`** (Pentium scheduling + 4-byte intra-CU alignment), with localized `-os` / `-oa` / `-od` / `-d1+` / `-zp1` regions.
  2. **Most of E7's production payoff is ALREADY LIVE on `main@a21772b`:** `tools/wc1/permuter.py@a21772b` has 14 Watcom 10.0a presets (`c06`, `c07`, `c19`, `c22`, `c10`, `c26` added) + 1 OW2, all 13 buildable T3s are promoted, and `t3_audit.py` + `wave4.py`/`wave4a.py` carry preset-aware provenance invalidation.
  3. **Production gap confirmed by code inspection (`tools/wc1/oldcc.py@a21772b`):** The short-path protection (`TMPDIR` / staging-path length guard against the ~129-char `wcc386` crash) discovered in E7 (and logged as Decision D9 in `decisions.md@e6150b8`) is **NOT yet implemented** in production `tools/wc1/oldcc.py@a21772b`!
  4. **Production hygiene gap confirmed by Probe 6 (`tools/wc1/t3_audit.py@a21772b`):** `t3_audit.py` on `main@a21772b` still carries the 3 subtle `R3` bugs surfaced by `research/model-calibration-engineering@cea804e`: `_default_system_headers(repo_root)` ignores `repo_root` whenever `oldcc.root()` succeeds (breaking checkout-rooted digests), `_git()` silently returns `None` on failure instead of failing closed, and `build_improved_audit_snapshot` compares `tool_sig` against itself rather than live tool state.
- **Assumptions (`[ASSUMP]`):**
  1. The 26-config grid did not include `-5r -d1+ -zp1` (the exact combination needed to test whether `OpenArchive` / `mod_319c0` matches under `-5r`) or `-od -5r`.
  2. `S(f)` for a T4 function depends strongly on the reconstructed C source spelling, not just the original compiler flags—hence empty `S(f)` intersections on T4s mostly measure *reconstruction spelling mismatch*, not original CU boundaries!
- **Limitations:** 12 dependency-dirty T4s remain untested; `-5r -d1+ -zp1` and `-od -5r` untested.
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §§12.1–12.2 STAND WITH ONE REFINEMENT:** Retain the three-layer calibration model and `S(f)` recording, but explicitly classify `S(f)` as **spelling-contingent** for T4s (only T3 `S(f)` differences are even weak boundary evidence, and never sufficient for auto-splitting). Promote short-path protection in `wc1.oldcc` (D9) to **Stage 0 immediate**.
- **Further experiment required? (`[OPEN]`):** **EXP-2** — cheap targeted preset probe (`-5r -d1+ -zp1` on `OpenArchive`/`mod_319c0` and `-od -5r` on existing `-od -4r` functions; <30 seconds total).

---

### 2.9 E8 — Original CU Boundary Evidence Validation

- **Artifacts:** Merge commit `9ae6dce` (`@e6150b8`); report `docs/research/build-codegen/E8-cu-boundaries.md@e6150b8`; contract `contracts/E8-contract.md@e6150b8`; code/tests `experiments/build_codegen/e8/{corpus.py,signals.py,test_e8_cu.py}@e6150b8` (30 tests); results `results/e8/summary.json@e6150b8`; reviews `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/{rev-e8-02.md,rev-e8-03.md}@e6150b8`.
- **Hypothesis:** Quantitative evaluation of 16 CU boundary/merge signals across independent ground-truth corpora (R4: never trained/evaluated on `analysis/modules.toml`) will identify which signals are trustworthy constraints vs unreliable heuristics for Original CU Recovery (RFC §9).
- **Method actually executed:** Built 3 R4-independent ground-truth corpora:
  - **Corpus A (Synthetic Watcom 10.0a + `wlink`):** 22 CUs, 65 functions, 64 adjacent pairs.
  - **Corpus B1 (`war.exe` runtime `clib3r`/`cstrtx3r` with full-segment byte verification & non-overlap, `dc1d028`):** 112 extents / 111 objects, 447 adjacent pairs (`186` pairs excluding `intxa386`).
  - **Corpus B2 (`setup.exe` boundary-only libsig after `MIN_LEN=12` filter):** 25 pairs (8/8 agreeing with B1 on shared pairs).
  - **Game range (`0x104b0..0x3024e`, 890 pairs, 58 chunks):** Kept strictly exploratory (no ground truth assumed).
  Evaluated precision, recall, and false-positive modes across all 16 signals (`30/30` tests passing, zero skips).
- **Positive controls:**
  - `shared_epilogue` (`6/6` true merges, **0 FP** across corpora) — rare, proven merge constraint.
  - `shared_const_string_literal` (`1/1`, **0 FP**) — rare, proven merge constraint.
  - `non_16_aligned_start` — **100% precision as a one-directional merge constraint** *under the premise* that the linker aligns separate `_TEXT` `SEGDEF`s to `PARA` (16B) while intra-CU functions align to `<16B` (`-5r` 4B / `-os` 1B).
- **Negative controls:**
  - **`_DATA`/`_BSS` staircase split (`RFC §9.3`) REFUTED:** Precision `0.250` on Corpus A, `0.281` on Corpus B1 (false-split rate >70%!).
  - **`call_locality_drop` (`RFC §9.3`) REFUTED:** Precision `0.323` on Corpus A, `0.179` on Corpus B1 (`0.519` excluding `intxa386`) — completely unusable as a boundary detector.
  - **`zero16` (zero-byte 16B padding) recall gap quantified:** High precision when present, but recall is only `0.524` on Corpus A and **`0.027`** on Corpus B1 (misses 97.3% of runtime CU boundaries!).
  - **`none16` (16B-aligned boundary with 0 pad bytes) unreliability quantified:** Precision only **`0.174`** on Corpus B1 (66 exploratory candidates in game range — mostly accidental 16B alignment of intra-CU 4B-aligned functions!).
- **Demonstrated facts (`[FACT]`):**
  1. Two flagship heuristics in RFC §9.3 (`_DATA`/`_BSS` staircase and `call_locality_drop`) are empirically **false** and would actively corrupt CU boundaries if automated.
  2. Alignment signals (`zero16`, `none16`, `non_16_aligned_start`) are strictly **asymmetric and premise-dependent**: `non_16_aligned_start` strongly implies same-CU (given `SEGDEF=PARA`), whereas 16B alignment with zero padding (`none16`) is overwhelmingly a false split (`82.6%` FP on B1).
  3. During `rev-e8-02` (`06235f6`), E8 independently stumbled onto Watcom 10.0a's non-deterministic `CONST` alignment padding digest—the exact compiler artifact whose full production impact on E0 and E5 we uncovered in **Probes 3 & 7**!
- **Assumptions (`[ASSUMP]`):** Corpus B1 (`clib3r`/`cstrtx3r`) is heavily skewed toward tiny assembly/C runtime objects (`intxa386` accounts for 261/447 pairs), so absolute recall numbers on B1 do not transfer linearly to large game CUs; however, the structural failure modes (non-monotonic `_DATA` reuse, inter-CU helper calls defeating call locality, accidental 16B alignment of 4B-aligned functions) apply directly to game code.
- **Limitations:** No independent ground truth exists for the 890 game-range pairs (save the few strings/filenames embedded in `war.exe`, e.g., `PLAYFLIC.C`, `BULLET.C`, `STATUS.C`, `GAMEDLG.C`, `PACKET.C`, `SND.C`, `PLACEBOX.C`).
- **Does RFC decision stand? (`[INTERP]` / `[DECISION]`):**
  - **RFC §§9.1–9.2 STAND; RFC §9.3 MUST BE REPLACED.** Replace the heuristic feature list (`_DATA`/`_BSS` staircase, `call_locality_drop`, weighted scoring) with a **premise-carrying constraint graph** (hard merge constraints, premise-dependent one-directional constraints, weak exploratory hints) operated strictly in **analyst-advisory mode**—never automatic consolidation or automatic splitting of `analysis/modules.toml`.
- **Further experiment required? (`[OPEN]`):** None before M2. Post-M2, if CU consolidation scales up, evaluate whether `CONST` address monotonicity (with verified gap tolerance) provides better precision than `_DATA`/`_BSS` staircases on game-like multi-function synthetic CUs.

---

## 3. Verification Architecture Proposal

Verification is the single highest-trust subsystem in the project: any soundness leak silently corrupts `make verify`, Build A proofs, or provenance caches. The revised verification architecture unifies E0's matcher and E3's slice logic into a **single fail-closed verification core (`tools/wc1/verify_core.py` or refactored `tools/wc1/match.py`)**, fixes the two critical flaws we discovered (E2 Cause B non-contiguous `FunctionMatch` and Probe 3/7 Watcom 10.0a `CONST` alignment padding), and enforces non-forgeable provenance from compilation through placement.

### 3.1 Core Abstractions and Verdict Hierarchy

```text
CompiledObject (.obj + CompileProvenance)
   │
   ├──► FunctionMatch       (local verdict for 1 function slice [lo, hi) against war.exe [base, base+len))
   │      Verdict: MATCH | MISMATCH | UNSUPPORTED
   │      Scope:   ONLY the function's own interval; NEVER grants Build A placement permission by itself.
   │
   ├──► RegionMatch         (closed verdict for 1 contiguous code region + ALL emitted object bytes/data/fixups)
   │      Verdict: MATCH | MISMATCH | UNSUPPORTED
   │      Scope:   Every byte of _TEXT [region_lo, region_hi), leading jump tables, trailing filler,
   │               all local data segments, and bidirectional obligations.
   │               WHOLE_OBJECT mode: region_lo == 0 and region_hi == len(_TEXT) (after verified trailing pad).
   │               PARTIAL_SLICE mode (deferred for Build A): [region_lo, region_hi) subset of _TEXT,
   │               branch-closed and relocation-equivalent (RFC §6).
   │
   └──► VerifiedRegion      (IMMUTABLE, matcher-minted token; CANNOT be constructed outside verifier)
          Carries: region_kind (WHOLE_OBJECT | PARTIAL_SLICE), object_sha256, source_digest,
                   preset_id, tool_sig, code_span (start, end, leading_table_span),
                   covered_functions, data_verification_report, obligations_digest, verifier_version.
```

### 3.2 Concrete Invariants and Fail-Closed Rules

1. **Invariant V1 — Bidirectional Normalized Addressing Obligations (from E0, mandatory):**
   - For every verified code span `[orig_start, orig_end)` and every verified local data span, construct:
     - `O_obj`: the complete set of addressing obligations in the compiled object (all OMF `FIXUPP`/`FIXUPP32` records + all internal `rel8`/`rel32` branch/call displacements + jump-table slot targets).
     - `O_orig`: the complete set of addressing obligations in `war.exe` over the exact corresponding span (all LE fixups + all internal/cross-function `rel8`/`rel32` branch/call targets + decoded jump-table slots).
   - **Rule:** `O_obj == O_orig` bidirectionally (equal offset, width, kind/relative-vs-linear, normalized target address/symbol, and addend). Neither extra object fixups nor missing object fixups may ever be silently ignored. Every unrelocated code byte outside verified obligations must be byte-identical to `war.exe`.
2. **Invariant V2 — Function-Scoped Branch Closure in `FunctionMatch` (FIX for E2 Cause B):**
   - In `FunctionMatch(obj, fn_pub, orig_fn)`, internal branch/call closure MUST be checked against **`[orig_fn.start, orig_fn.start + fn_len)`**, NOT against `[first_pub_base, first_pub_base + len(_TEXT))` (fixing `matcher_proto.py:358-359`).
   - Any intra-object branch leaving `[lo, hi)` (e.g., cross-function `rel8` shared epilogue, bare `rel32` to a sibling) makes `FunctionMatch` return `UNSUPPORTED(reason="cross_slice_branch", target=...)` unless the caller explicitly requests `RegionMatch` covering both source and target functions.
   - `FunctionMatch` NEVER mints a `VerifiedRegion` and NEVER authorizes Build A replacement on its own.
3. **Invariant V3 — Leading and Trailing Bytes Verification (FIX for E0 + E3 Nit 3):**
   - **Leading bytes (`lo > fn_entry_offset` or `code_start < first_fn_start`):** Forbidden by default (`MISMATCH`), permitted **only** when explicitly declared as a `LeadingJumpTableSpec` (B1) whose exact address range, 4-byte slot count, and LE/OMF target obligations match `war.exe` 1:1 (every slot resolves to an instruction inside the verified region).
   - **Trailing bytes (`obj_fn_end > orig_fn_end` or end-of-segment alignment pad):** Allowed **only** if every byte decodes strictly as Watcom alignment filler (`90`, `8d 76 00`, `8d b6 00 00 00 00`, `8d 40 00`, `89 f6`, `8b c0`, `00` after `ret`/`jmp` up to alignment boundary) AND **zero** instructions in the verified region branch into the trimmed filler (preserving E0's `trimmed_branch_target` check that E3 `partial_matcher.py:206` accidentally dropped!).
   - **Extent retry (`orig_fn_end` ambiguity):** Never silently truncate! If `obj_len != orig_len`, fail closed unless the excess matches the strict trailing-filler invariant above or an explicit `RegionMatch` spans multiple contiguous functions.
4. **Invariant V4 — Explicit Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (NEW — from Probes 3 & 7):**
   - Because Watcom 10.0a `-ot` leaves **non-deterministic uninitialized compiler heap memory** in the 1..3-byte 4-byte alignment padding between string literals in `CONST` (confirmed in 157/293 `war.exe` `CONST` strings and live across two runs of `wcc386` in Probe 7d), byte-for-byte comparison of the *entire* `CONST` segment produces deterministic false `MISMATCH`es on almost every multi-string `-ot` CU.
   - **Strict Fail-Closed Rule for `CONST` (and ONLY `CONST`):**
     - Partition the object's `CONST` segment into referenced items using the verified code/data fixups pointing into `CONST`.
     - For each item at offset `off_i` in `CONST` that is proven to be a NUL-terminated string literal (all fixups targeting `[off_i, nul_i]` point to `off_i`, no fixup targets `(nul_i, next_aligned)`), the verified literal span is `[off_i, nul_i + 1]` (inclusive of `0x00`).
     - Let `gap = [nul_i + 1, align4(nul_i + 1))` where `0 <= len(gap) <= 3` and `align4(nul_i + 1) <= off_{i+1}` (or segment end).
     - Bytes inside `gap` MAY be exempted from byte-equality **IF AND ONLY IF ALL 5 conditions hold**:
       1. Segment class/name is `CONST` (read-only string/constant pool; **NEVER** `_DATA`, **NEVER** `_BSS`, **NEVER** `_TEXT`).
       2. `1 <= len(gap) <= 3` and `gap.end == align4(gap.start)`.
       3. The immediately preceding byte `gap.start - 1` is `0x00` terminating a verified referenced literal `[off_i, gap.start)` whose bytes are 100% identical to `war.exe` at `[anchor + off_i, anchor + gap.start)`.
       4. **Zero** fixups in the compiled object AND **zero** LE fixups or decoded data references in `war.exe` target any byte inside `gap` (unreachable padding proof).
       5. The `VerifiedRegion` records `const_pad_exempted = True` and **forces `physical_provider = ASM`** for Build A (since C's non-deterministic pad bytes can never match `war.exe`'s 1994 heap bytes in Build A; in Build B, C may physically emit `CONST`).
     - Any non-matching byte outside such a proven 1..3B unreachable `CONST` alignment gap—any `_DATA` mismatch, any `>=4B` gap, any unreferenced gap between non-NUL binary constants, or any referenced byte—**fails closed with `MISMATCH`**.
5. **Invariant V5 — Non-Forgeable `VerifiedRegion` & Checkout-Portable Provenance (FIX for `rev-e4-01` F1 & Probe 6):**
   - `VerifiedRegion` is constructed exclusively by `verify_region()` via a private constructor/capability token (or frozen dataclass validated by digest against `verify_region`'s internal registry) so downstream builders/extractors cannot accept an unverified or manually forged region.
   - Provenance records `(source_digest, preset_id, compiler_id, tool_sig, verifier_version, object_sha256, region_kind)` where `source_digest` MUST be checkout-rooted (`repo_root`-relative system headers, fixing Probe 6's `_default_system_headers` bug in `tools/wc1/t3_audit.py@a21772b`), `tool_sig` is always compared against **live** tool state, and `_git()` failures fail closed (`dirty/unknown` rather than silently treated as clean).
6. **Invariant V6 — Compiler Short-Path Safety (D9, missing from `tools/wc1/oldcc.py@a21772b`):**
   - `wc1.oldcc` MUST stage compiler inputs/outputs and `TMPDIR` under a short path (`<= 48` chars total resolved path to `.c`/`.obj`, e.g., `/tmp/wc1-cc-<uid>/...`) and fail fast with `[TOOLCHAIN ERROR]` if the resolved Windows path (`Z:\...`) approaches Watcom 10.0a's confirmed ~129-character buffer-overflow threshold.

### 3.3 Lifecycle States and What to Defer

- **Lifecycle of a compiled code unit:**
  `UNVERIFIED_SOURCE` -> `COMPILED_OBJECT` -> (`FUNCTION_MATCHED` [diagnostic only, non-buildable] | `CANDIDATE_REGION`) -> `VERIFIED_REGION` (all V1–V5 invariants pass) -> `PLACED_IN_BUILD_A` (accepted by `BuildAPlacementPlan` + `wlink` + byte-identical check against `war.exe`).
- **Defer from Stage 0 verification core:**
  - `PARTIAL_SLICE` Build A minting (keep `FunctionMatch` diagnostic mode in Stage 0, defer `PARTIAL_SLICE` -> `VerifiedRegion` minting to Stage 3 only if E4 is actually needed).
  - Non-NUL binary `CONST` struct-padding relaxation (no real `war.exe` case requires it today; fail closed until an actual case provides evidence).

---

## 4. Compilation and Placement Architecture Proposal

The current production pipeline (`tools/wc1/build.py@a21772b` + `tools/wc1/emit.py@a21772b`) conflates three distinct concepts: a single C file (`src/.../*.c`), a single function extent (`[start, end)`), and a single Build A replacement cut. That 1:1:1 assumption is what breaks on leading jump tables (B1), shared epilogues and cross-piece `rel8` (B2), multi-function TUs (E1/E2), and local data segments (B3).

### 4.1 Concrete Entity Model and Relationships

```text
┌─────────────────────────┐      advisory / non-authoritative      ┌────────────────────────────┐
│  OriginalCUHypothesis   │ ◄····································► │    analysis/modules.toml   │
│ (E8 constraint graph;   │        (NEVER auto-mutated)            │  (human area navigation)   │
│  hypotheses + premises) │                                        └────────────────────────────┘
└────────────┬────────────┘
             │ informs (human-approved)
             ▼
┌─────────────────────────┐  1..N presets   ┌──────────────────────┐
│     ReconstructedTU     │ ──────────────► │    CompiledObject    │
│ (1 .c file + headers +  │   (Watcom 10.0a │ (.obj + OMF32 model  │
│  declared preset/flags; │    preferred,   │  + CompileProvenance)│
│  semantic_owner of fns  │    OW2 fallback)│                      │
│  and optionally data)   │                 └──────────┬───────────┘
└─────────────────────────┘                            │
                                                       │ proposes 1..K (1 for whole-TU)
                                                       ▼
                                            ┌──────────────────────┐
                                            │   CandidateRegion    │
                                            │ (contiguous VA span, │
                                            │  covered fns, leading│
                                            │  table spec, data    │
                                            │  anchoring mode)     │
                                            └──────────┬───────────┘
                                                       │ verify_region() [V1..V5]
                                                       ▼
                                            ┌──────────────────────┐
                                            │    VerifiedRegion    │
                                            │ (immutable proof;    │
                                            │  semantic_owner = C, │
                                            │  physical_provider   │
                                            │  for code/data)      │
                                            └──────────┬───────────┘
                                                       │ N non-overlapping regions
                                                       ▼
                                            ┌──────────────────────┐      ┌──────────────────────┐
                                            │  BuildAPlacementPlan │ ───► │  Build A war.exe     │
                                            │ (in-place fixed-VA   │      │  (SHA-256 IDENTICAL  │
                                            │  partition of _TEXT  │      │   to original)       │
                                            │  into ASM pieces +   │      └──────────────────────┘
                                            │  C cuts + cross-piece│
                                            │  branch plan + data  │      ┌──────────────────────┐
                                            │  provider map)       │      │ SemanticVerification │
                                            └──────────────────────┘      │ Unit (T4 cemu; E6    │
                                                                          │ VerificationBoundary)│
                                                                          └──────────────────────┘
```

### 4.2 Entity Responsibilities and Ownership Rules

1. **`OriginalCUHypothesis` (stored separately from `analysis/modules.toml`, e.g., `analysis/cu_hypotheses.toml` in Stage 3):**
   - Represents *hypotheses* about original 1994 `.c` translation units, backed by premise-carrying constraints (E8: `shared_epilogue`, `shared_const_string_literal`, `non_16_aligned_start`, filenames).
   - Explicitly supports **competing hypotheses** and **unknown boundaries**. Never overwrites `analysis/modules.toml` automatically.
2. **`ReconstructedTU` (`src/<area>/<file>.c` + metadata header):**
   - One C translation unit with explicit `codegen-compiler` (`10.0a` default, `ow2` fallback) and `codegen-preset` / flags (E7 presets already in `tools/wc1/permuter.py@a21772b`).
   - May contain **1 function** (standard M2 incremental unit) or **N contiguous functions** (e.g., E1 Group A/B shared-epilogue clusters, E2 contiguous `-5r` runs like `STATUS.C`).
   - **Rule on non-contiguous multi-function TUs:** Allowed for T4/organization only if paired with E6 `VerificationBoundary`; NOT eligible for whole-TU Build A `RegionMatch` unless contiguous (prefer splitting or completing the gap over E4 selective extraction).
3. **`CompiledObject`:**
   - The raw OMF32 `.obj` produced by `wc1.oldcc` (under short-path staging, V6) or OW2, parsed by **one shared OMF32 codec** (`tools/wc1/omf.py` extended with clean emission/patching primitives—eliminating the duplicate parsers in `omfpatch.py`, E4 `omf_extract.py`, and E5 `omf_b3.py`).
4. **`CandidateRegion` -> `VerifiedRegion`:**
   - A `CandidateRegion` declares:
     - `code_span = [region_start, region_end)` (may begin *before* `first_fn.start` when covering a B1 leading switch jump table!).
     - `covered_functions`: ordered list of all discovered function entries in `[region_start, region_end)`.
     - `leading_table_span`: optional `[region_start, first_fn.start)` B1 spec.
     - `data_mode`: `NONE` | `ASM_ANCHORED_B3` (Stage 3) | `C_OWNED` (Build B / M3 only).
   - `verify_region()` validates V1–V5 and mints an immutable `VerifiedRegion`.
5. **`semantic_owner` vs `physical_provider`:**
   - **Code in Build A:** For every `VerifiedRegion`, `semantic_owner = C` and `physical_provider = C` (its compiled `_TEXT` bytes are linked in-place into `war.exe`). For untouched functions, both are `ASM`.
   - **Data (`CONST`, `_DATA`, `_BSS`) in Build A:** Even when a `ReconstructedTU` owns the C literals/globals (`semantic_owner = C`), **`physical_provider = ASM`** remains the default in Build A whenever either (a) data layout is not yet C-owned (`analysis/data_layout.toml` does not exist yet), or (b) `CONST` has non-deterministic Watcom 10.0a alignment padding (`const_pad_exempted = True`, V4), or (c) data is shared across multiple TUs. In **Build B (M3)**, `physical_provider` flips to `C` under `analysis/data_layout.toml`.
6. **`BuildAPlacementPlan` (replaces ad-hoc cut filtering in `tools/wc1/build.py` + `tools/wc1/emit.py`):**
   - Given the set of active `VerifiedRegion`s and mode (`in_place` vs `--legacy`):
     1. **Non-overlap & alignment check:** Verify all `VerifiedRegion.code_span` intervals are pairwise disjoint. Because Watcom 10.0a emits `PARA` (16-byte) `_TEXT` `SEGDEF`s even under `-5r` (E2), `BuildAPlacementPlan` handles inter-cut padding identically to existing `wc1.build` (patching/splitting ASM pieces around exact byte spans, aligning C `_TEXT` `SEGDEF` to `BYTE` via `omfpatch` for non-16B-aligned cut starts—which `wc1.build` already does for single-function cuts!).
     2. **Leading jump tables (B1):** Because `VerifiedRegion.code_span` includes `[table_start, first_fn_start)` as part of the cut, ASM emission excludes the table bytes from the preceding ASM piece, redirects any external/internal references into `[table_start, first_fn_start)` to the C object's leading table offset (or exports an internal label at `table_start`), and preserves exact byte offsets.
     3. **Cross-piece branch classification (Unified B2):** Scans **every** remaining ASM instruction across all ASM pieces and classifies every branch whose target `t` lies **outside the source ASM piece** (`piece_of(ia) != piece_of(t)`):
        - **Cross-piece `rel32`:** Emitted via external symbol (`_sym` if `t` is a public entry, or synthesized `_loc_<addr>` public symbol at exact offset inside the target `VerifiedRegion` via `omfpatch` if `t` is cut-interior, or ASM `global loc_<addr>` if `t` is in another ASM piece).
        - **Cross-piece `rel8` (all 3 classes: cut-interior, cut-entry, cut-spanning):** Under **`--legacy`**, FAIL CLOSED (reject the cut—cannot guarantee fixed displacement). Under **`in_place`**, verify that (a) every byte strictly between the source ASM piece boundary and `t` is covered by fixed-size `VerifiedRegion` cuts and ASM pieces with exact original VAs, and (b) `-128 <= (t - (ia + 2)) <= 127`. Then emit a **piece-boundary local-label offset expression** in NASM (`<mnem> short loc_<piece_edge> + <signed_delta>`) which NASM resolves at assembly time to the exact 2-byte `rel8` instruction with **zero OMF32 relocation**!
        - **Cross-piece fallthrough:** If an ASM piece's last instruction falls through into the next piece (e.g., `EndCheckSurvive 0x2f694` ending in `0x2f73a jge 0x2f746` falling through into `MissionDefeat 0x2f73c`), `in_place` placement preserves exact adjacency automatically (because `piece_k` ends at `0x2f73c` and `MissionDefeat`'s C cut starts at `0x2f73c` with `BYTE`-aligned `_TEXT`); under `--legacy`, fallthrough across a cut boundary MUST fail closed!
     4. **Shared epilogues:** Handled at *two* levels without conflict:
        - **Preferred (whole-TU `VerifiedRegion`, E1):** Co-compile the cluster under `-5r`/`-oa -5r` into one `VerifiedRegion` -> the shared `rel8` is now strictly internal to the C cut, zero cross-piece branches exist!
        - **Incremental fallback (Unified B2):** While sibling functions are not yet C (or one sibling is still T4), `BuildAPlacementPlan` handles the cross-piece `rel8` safely under `in_place` mode, unlocking all 6 remaining M2 B2-blocked T3s immediately.
     5. **Whole-TU integration vs Selective Extraction (E4):**
        - **Primary rule:** Always prefer whole-TU `VerifiedRegion` integration (`-5r` 4B alignment, E2: 23/23 contiguous runs pass).
        - **No E4 in M2:** Selective extraction (`PARTIAL_SLICE`) is NOT wired into `BuildAPlacementPlan` for M2. It remains an optional Stage 3 extension behind a hardened shared OMF32 codec only if post-M2 consolidation encounters irreducible mismatching siblings.
     6. **`check_t3_buildable` consistency invariant:** `build.check_t3_buildable` MUST execute the **exact same `BuildAPlacementPlan` admissibility check** as `build.py` (never a separate partial regex/helper like `replaced_interior_refs`!), eliminating the `IntroOpSyncSound` class of false positives permanently.

---

## 5. B1 / B2 / B3 Evaluation

### 5.0 Essential Distinction: Local Match vs Region Match vs Integrated Buildability

A recurring source of confusion in both the legacy pipeline (`tools/wc1/build.py@a21772b`) and the `IntroOpSyncSound` (`0x23170`) incident is collapsing three strictly distinct properties into one word ("matched" / "T3"):

| Level | Formal Question Answered | What It Checks | What It Does **NOT** Prove | Example Where Next Level Fails |
|---|---|---|---|---|
| **1. Local Match (`FunctionMatch`)** | Does function `f`'s slice `[lo, hi)` match `war.exe`'s `[f.start, f.end)`? | Code bytes, normalized addressing obligations, function-scoped branch closure inside `[lo, hi)`. | Does NOT prove the rest of the `.obj` (leading bytes, trailing bytes, sibling functions, local data segments) is valid or placeable. | `FarmPanelChanged` (`0x28254`) in a multi-function TU whose sibling mismatches; `ChooseCampaignDialog` (`0x157e8`) if leading switch table bytes aren't verified. |
| **2. Region Match (`RegionMatch` -> `VerifiedRegion`)** | Does the entire closed code region `[region_start, region_end)` and ALL emitted object bytes/data/fixups match `war.exe`? | Bidirectional obligations, leading table bytes (B1), verified trailing filler, branch closure of the region, local `CONST`/`_DATA` verification (V4). | Does NOT prove that replacing `[region_start, region_end)` in Build A leaves all **external** ASM pieces assemblable/linkable or preserves Build A data anchoring! | **`IntroOpSyncSound` (`0x23170`)** — passes `FunctionMatch` AND `RegionMatch` 100%, yet fails **Integrated Buildability** because ASM `IntroOpWaitSound` has two `rel8` branches spanning across `0x23170`! **`MissionDefeat` (`0x2f73c`)** — passes `RegionMatch`, yet fails Build A because ASM `EndCheckSurvive` has `rel8` branches targeting both its entry and interior! |
| **3. Integrated Buildability (`BuildAPlacementPlan` + `wlink`)** | Can this `VerifiedRegion` be placed into Build A alongside all active cuts and untouched ASM pieces to link a SHA-256 `IDENTICAL` `war.exe`? | Disjoint placement, B1 table ownership handoff, B2 cross-piece `rel8`/`rel32`/fallthrough admissibility, B3 data-provider redirection, `wlink` + byte-identity check. | Does NOT prove Build B / M3 relocatability (e.g., if `physical_provider = ASM` for `CONST`, or if `I16` raw-address assumptions remain). | Any Build A T3 whose `CONST` still has `physical_provider = ASM` (cannot yet relocate data in Build B without `data_layout.toml`). |

Every tool in the pipeline—`wc1.match`, `wc1.build`, `wc1.t3_audit`, `wc1.m2_inventory`, `wc1.overnight`, `wc1.wave4`—MUST enforce this three-level distinction explicitly.

---

### 5.1 Blocker B1 — Leading Pre-Function Switch Jump Tables

- **Exact production failure:** Watcom 10.0a emits jump tables for `switch` statements in `_TEXT` **immediately before** the function's entry point (`PUBDEF` offset `> 0`, e.g., `off = 0x10` or `0x20`). Production `tools/wc1/match.py@a21772b` and `tools/wc1/build.py@a21772b` assume a function's cut begins at `f.start` (`off == 0`) and reject leading bytes (`ChooseCampaignDialog 0x157e8` — already matched in C, blocked from Build A; `MainMenu 0x15578` noted in `AGENTS.md`; `0x19c14` in `m2_inventory` has a pre-function jump table and will need B1 once reconstructed).
- **Experimental remedy:** E0 (`matcher_proto.py@e6150b8`) verified leading bytes synthetically via bidirectional obligation checks; RFC §7.2 specifies widening the `CandidateRegion` / `VerifiedRegion` cut span to `[table_start, fn_end)` so the C object owns both the jump table and the function body as one contiguous cut, while `BuildAPlacementPlan` excludes `[table_start, fn_start)` from the preceding ASM piece.
- **What experiments actually proved:**
  - E0 proved bidirectional obligation checking of leading jump-table bytes on synthetic controls (`controls.json@e6150b8`).
  - **Gap:** **0/539** existing T3s have `lead > 0`, and no E0–E8 experiment executed an end-to-end Build A `IDENTICAL` link of real `ChooseCampaignDialog` (`0x157e8`) with its leading switch table!
- **Residual risk:**
  1. Preceding ASM function's end address (`prev_fn.end`) in `analysis/functions` may or may not include the trailing jump table bytes—`BuildAPlacementPlan` must verify exact byte partitioning `[prev_piece_end == table_start]` and ensure no other function references `[table_start, fn_start)` without remapping.
  2. `omfpatch` must keep the `_TEXT` `PUBDEF` offset at `fn_start - table_start` (not `0`) while aligning the cut start to `table_start`.
  3. Linear disassemblers (like `wc1.emit` or E4's `scan_slice`) must NOT disassemble `[table_start, fn_start)` as instructions.
- **Required hardening:** Add an explicit `LeadingJumpTableSpec(table_start, table_end, slot_count, target_fn)` to `CandidateRegion`, verify every 4-byte LE/OMF slot resolves inside `[fn_start, fn_end)`, assert zero external references into the table from outside `fn`, and validate with a real Build A `IDENTICAL` test on `ChooseCampaignDialog` (`0x157e8`).
- **Recommendation:** **ADOPT NOW (Stage 1).** Directly unlocks 1 ready M2 T3 (`0x157e8`, +1 DONE) and unblocks `0x19c14` when reconstructed; tiny surface area, clean fit inside `VerifiedRegion` + `BuildAPlacementPlan`.

---

### 5.2 Blocker B2 — Inter-Function `rel8` / Shared Epilogues / Cross-Piece Branches (Including `IntroOpSyncSound` `0x23170`)

- **Exact production failure (and why `IntroOpSyncSound` `0x23170` slipped past `check_t3_buildable`):**
  - Production `tools/wc1/emit.py:45-84@a21772b` (`replaced_interior_refs`) ONLY checks branches targeting the **interior** of a replaced cut (`s < t < e` with `t not in entries`).
  - NASM OMF32 cannot emit an 8-bit external relocation (`error: OBJ format can only handle 16- or 32-byte relocations`). Therefore, **ANY** `rel8` branch in an ASM piece whose target `t` is **not in the same ASM piece** crashes NASM!
  - **Probe 1** ran a complete binary-wide census across all 1,710 functions in `war.exe` (**43** cross-function `rel8` branches total; **25** in game range `0x104b0..0x3024e` across 11 source and 10 target functions; plus **23** cross-function interior `rel32` branches binary-wide) and proved there are **THREE** distinct cross-piece `rel8` failure modes:
    1. **Mode B2-interior (29 binary-wide; 18 in game range):** ASM `piece_k` has a `rel8` targeting the interior (`s < t < e`) of a replaced C cut (e.g., `ApplyScenarioTerrainOwnerRects` `0x1e3c4 je` -> `0x1e3ac` inside `ApplyScenarioTerrainKindRects` `0x1e380`; `IssueOrderAt` `0x2f0b9 jne` -> `0x2f0a7` inside `SelectionClickUnit` `0x2efd0`; `fn_2e9c4` -> `0x2e9c1` inside `UnitFinalizeGone` `0x2e96c`; `ViewportLayerCallback` -> `0x1b008` inside `FogDrawViewport` `0x1af90`).
    2. **Mode B2-entry (14 binary-wide; 5 in game range — MISSED by BOTH `emit.py` AND RFC §7.2!):** ASM `piece_k` has a `rel8` targeting the **ENTRY** (`t == cs`, `t in entries`) of an adjacent C cut! Crucially, on an active M2 blocker: `EndCheckSurvive` (`0x2f694`) has **three** entry-targeting `rel8` branches (`0x2f718 jmp`, `0x2f722 je`, `0x2f72e jl` -> **`0x2f73c` `MissionDefeat` ENTRY, `interior=False`**) in addition to five interior-targeting `rel8` branches (`-> 0x2f746`) and a fallthrough at `0x2f73a jge 0x2f746`! Similarly, `SelectionHasNoWorkers` (`0x28074`) has `0x28088 jl` and `0x2808d jg` -> `0x28093` (`SelectionIsWorkersNext` ENTRY).
    3. **Mode B2-span (11 binary-wide; 7 in game range + 1 in `0x10424` — CAUSE OF `IntroOpSyncSound` `0x23170` FALSE POSITIVE!):** ASM `piece_{k+1}` has a `rel8` **spanning across an intervening C cut** into ASM `piece_k`! Specifically, when `IntroOpSyncSound` (`0x23170`, 92 bytes) is replaced by C while its neighbors remain ASM, `emit.py` splits `_TEXT` into `piece_A` (containing `IntroOpPlaySound` `0x2315c..0x23170`), C cut (`0x23170..0x231cc`), and `piece_B` (containing `IntroOpWaitSound` `0x231cc..`). `IntroOpWaitSound`'s two instructions `0x231d7 je 0x2316c` and `0x231e1 jne 0x2316c` do NOT target `[0x23170, 0x231cc)` at all (`replaced_interior_refs` returns empty!), so `build.check_t3_buildable` reported `IntroOpSyncSound` as BUILDABLE—yet NASM immediately crashed trying to emit an 8-bit external relocation from `piece_B` to `loc_2316c` in `piece_A`! The same spanning geometry also occurs in `DialogHighlightOff` (`0x16d50 je` -> `0x16d31` spanning `DialogHighlightOn` `0x16d34`) and `STATUS.C` (`0x28074`/`0x28093` spanning `0x28090`).
- **Experimental remedy (two complementary mechanisms):**
  - **Mechanism 1 (Preferred permanent fix — E1 Co-Compilation):** Co-compile the entire shared-epilogue cluster into one `VerifiedRegion` under `-5r` / `-oa -5r`. E1 already proved this links Build A `IDENTICAL` for **Group A** (`0x16cc8`/`0x16d34`/`0x16d48`) and **Group B** (`0x2315c`/`0x23170`/`0x231cc`, resolving `IntroOpPlaySound`, `IntroOpSyncSound`, AND `IntroOpWaitSound` simultaneously!).
  - **Mechanism 2 (Unified Incremental Fix B2 in `BuildAPlacementPlan`):** For incremental M2 unlocks where a cluster neighbor is still ASM (e.g., `0x1e380`, `0x2e96c`, `0x2efd0`, `0x2f73c`, or standalone `0x23170` before Group B consolidation): in strict **`in_place`** mode ONLY (never `--legacy`), whenever `piece_of(ia) != piece_of(t)` for a `rel8` branch in an ASM piece, `BuildAPlacementPlan` verifies that every byte between the ASM piece boundary and `t` is fixed-VA (`VerifiedRegion` cuts + ASM pieces, zero layout shift) and `-128 <= (t - (ia + 2)) <= 127`, and emits a **piece-boundary local-label expression** (`<mnem> short loc_<piece_edge> + <signed_delta>`). Because `loc_<piece_edge>` is local to the same NASM segment, NASM evaluates `(loc_<piece_edge> + delta) - ($ + 2)` to the exact 1-byte signed displacement with **zero OMF32 relocation**—uniformly handling B2-interior, B2-entry, AND B2-span! For cross-piece `rel32` into cut interiors, emit an explicit `_loc_<addr>` `PUBDEF` via `omfpatch` on the C object.
- **What experiments proved vs residual risk:**
  - E1 proved Mechanism 1 end-to-end on Group A & Group B (`Build A IDENTICAL`).
  - **Gap:** Mechanism 2 (piece-boundary local-label `rel8` rewrite in NASM) has NOT yet been run end-to-end on `war.exe` in E0–E8!
  - **Residual risk:** If Mechanism 2 were accidentally invoked under `--legacy` (where cuts can move/resize), it would silently branch to the wrong address! Therefore, **hard fail-closed gate:** Mechanism 2 MUST refuse `--legacy` mode unconditionally, MUST assert exact byte-length conservation of every intervening cut/piece, and MUST be paired with Build A's SHA-256 `IDENTICAL` link check.
- **Required hardening:**
  1. Immediately (Stage 0) fix `build.check_t3_buildable` to reject ALL cross-piece `rel8` (interior, entry, AND spanning) whenever unhandled—closing the `IntroOpSyncSound` false-positive hole.
  2. Run **EXP-3** (10-minute probe) verifying NASM piece-boundary `rel8` rewrite links Build A `IDENTICAL` on standalone `IntroOpSyncSound` (`0x23170`, B2-span) and standalone `MissionDefeat` (`0x2f73c`, B2-interior + B2-entry + fallthrough).
  3. Ship Unified Fix B2 in Stage 1 alongside `BuildAPlacementPlan`, and promote E1's Group B (`0x2315c`/`0x23170`/`0x231cc`) as a whole-TU `VerifiedRegion` (which also eliminates 1 of the 4 `PLAYFLIC` xfail divergences!).
- **Recommendation:** **ADOPT NOW (Stage 0 guard + Stage 1 Unified B2 after EXP-3).** Directly unlocks **6** ready M2 T3s (`0x1e380`, `0x2315c`, `0x23170`, `0x2e96c`, `0x2efd0`, `0x2f73c`, +6 DONE with 0 LLM effort; combined with B1 `0x157e8` = **+7 DONE -> 919/1010**).

---

### 5.3 Blocker B3 — Data-Anchor Decoupling (`CONST` / `_DATA`)

- **Exact production failure:** When a C TU uses natural string literals or local initialized arrays (e.g., `SaveErrorDialog` `0x1aca8` or `SaveSlotPath` `0x14740`), Watcom 10.0a emits a local `CONST`/`_DATA` segment in the `.obj`. Linking that `.obj` directly in Build A either duplicates the data (breaking Build A `IDENTICAL` and shifting addresses) or breaks anchor-order constraints (`AGENTS.md` ground rule: `CONST` anchors follow code order; shared literals need artificial `extern` workarounds like `str_ext_net`, `str_ext_sav`, `fmt_save_d` in `src/mod_13f60/save_slot_path.c@a21772b`).
- **Experimental remedy:** E5 (`omf_b3.py@e6150b8`) verifies local `CONST`/`_DATA` contents against `war.exe` (whole-segment or per-symbol), strips the C object's physical data segment emission, and rewrites code `FIXUPP32` records to point at external ASM-provided anchor symbols (`EXTDEF`), cleanly separating `semantic_owner = C` from `physical_provider = ASM` in Build A.
- **What E5 proved:** 9/9 full Warcraft Build A `IDENTICAL` links across `SaveErrorDialog` (`-os`), `-ot` explicit `_DATA` char arrays, 3-segment `GAMEDLG`, all 4 OMF32 frame modes (`FLAT`/`DGROUP`/`Target`/`EXTDEF`), cross-record `THREAD`, and 64-fixup splitting (`86/86` tests).
- **Residual risk (CRITICAL — uncovered by Probes 3 & 7):**
  1. **Watcom 10.0a uninitialized `CONST` alignment padding breaks E5 on real multi-string `-ot` CUs:** `war.exe` has non-zero 1994 compiler heap residue in **157/293** fixup-bounded `CONST` strings, and live Watcom 10.0a writes non-deterministic heap bytes into 1..3-byte alignment gaps (`Probe 7d`: `73 00 2f` vs `76 00 61` vs `war.exe` `8d 75 e0`). Both E5 `whole_segment` and `per_symbol` (`omf_b3.py:172-173`) reject these gaps today!
  2. **Zero M2-completion leverage:** Every known B3 candidate (`SaveErrorDialog 0x1aca8`, `SaveSlotPath 0x14740`, `GAMEDLG`) is **already DONE** (`0x1aca8` is T4; `0x14740` is T3 via `extern` symbols). Implementing B3 before M2 completion adds OMF-rewriting complexity without advancing `make goal` gate 1 by even 1 function.
  3. **Aliasing & mutability hazard:** `_DATA` (mutable) must never be casually merged or re-anchored across TUs without proving identical storage address and non-aliasing (RFC §6.3, `rev-e5-02`).
- **Required hardening:**
  1. Integrate E5's logic into the **shared OMF32 codec** (`tools/wc1/omf.py`, never a second bespoke re-serializer).
  2. Implement **Invariant V4** (strict 5-condition unreachable 1..3B `CONST` alignment-gap rule) and verify it via **EXP-1** on real `SaveSlotPath` (`0x14740`) linking Build A `IDENTICAL` with natural C string literals (`".net"`, `".sav"`, `"save%d"`).
  3. Enforce `rev-e5-02` hardening (strict mutability check distinguishing `CONST` vs `_DATA`, forbid `_BSS` silent stripping, validate frame-mode invariants).
- **Recommendation:** **ADOPT CONDITIONALLY — DEFER TO STAGE 3 (POST-M2 / CU CONSOLIDATION).** B3 is high-value for M3 readiness and eliminating artificial `extern str_*` boilerplate during CU consolidation, but has **0 M2 completion impact** and requires Invariant V4 (`CONST` gap rule) + shared OMF codec first.

---

## 6. Behavioral Verification Proposal (Multi-Function T4)

Single-function T4 (`tools/wc1/cemu.py@a21772b` + `tools/wc1/t4spec.py@a21772b`) already achieves 373 verified T4 functions on `main@a21772b` (plus 5 xfailed real behavioural divergences). E6 (`experiments/build_codegen/e6/mf_cemu.py@e6150b8`, 96/96 tests) proved how to scale T4 soundly to **multi-function C translation units** without introducing silent trust leaks.

### 6.1 Concrete Architectural Rules

1. **Three Explicit Verification Modes (RFC §11.1 retained & operationalized):**
   - **`Isolated`:** Tests a single function `f` inside a multi-function `.obj`. Every call leaving `f`—including calls to sibling functions inside the *same* `.obj`—MUST be explicitly substituted (either to `war.exe`'s original function or an explicit declared mock/stub). Zero unstubbed sibling execution is allowed!
   - **`Group`:** Tests a declared set `G = {f_1, ..., f_k}` inside one `.obj` jointly against `war.exe`. Calls strictly within `G` execute the C code under test; every call leaving `G` (including calls to non-`G` siblings in the same `.obj` or external functions) MUST be explicitly substituted.
   - **`Integrated`:** Tests an entire TU (or linked group of TUs) with `G = all_defined_functions`, stubbing only external boundaries (OS/DPMI/hardware/timer/random/unmodeled globals).
2. **Contiguous `VerificationBoundary` Ownership (from E6 — mandatory):**
   - A `VerificationBoundary` MUST partition the compiled `.obj`'s `_TEXT` into **contiguous, non-overlapping function byte ranges** (derived from `PUBDEF`/symbol extents, NOT reachability-truncated CFG walks!).
   - **Fail-closed rule:** If a compiled `.obj` contains code bytes outside known function boundaries, or if an indirect jump (`jmp reg` / `jmp [mem]`) cannot be proven strictly intra-boundary while `subs` is non-empty, fail closed with `IsolationImpossibleError` rather than silently letting execution escape the boundary.
   - **Required Stage-3 refinement over E6 prototype:** Allow indirect jumps *when* statically proven to be an intra-function switch jump table whose every slot targets inside the same function's `[lo, hi)` (so switch-bearing functions inside multi-function TUs remain testable in `Isolated` mode).
3. **Explicit `DependencySubstitutionPolicy` (3 Mechanisms, Zero Silent Leakage):**
   - Every target leaving `G` MUST bind to an explicit substitution strategy:
     1. **`orig_addr_stub`:** External calls resolved via OMF `EXTDEF` redirected to `war.exe`'s original address (existing single-function `cemu` behavior) or a declared test stub.
     2. **`symbol_aware_reloc`:** Intra-TU calls emitted by Watcom 10.0a as self-relative `EXTDEF` `FIXUPP`s (E6 proved Watcom 10.0a actually does this even for `IntroFrame -> IntroLoadCreditLines`!) redirected at load time to the original address or stub instead of the sibling's C offset.
     3. **`c_entry_hook`:** Bare `rel32` (zero-FIXUPP) intra-TU calls (e.g., `static` sibling calls or hand-assembled code) intercepted via an emulator execution hook at the sibling's C entry address (proved in E6 via NASM fixture).
   - **Rule:** If execution ever reaches a sibling outside `G` without a registered policy entry, raise `IsolationImpossibleError` immediately.
4. **Generator-Based Real Callback Execution & Pre-Restore `watcall` ABI Enforcement:**
   - When C code under test invokes a callback (e.g., UI layer callbacks, iterator callbacks, sort comparators), the harness MUST run callbacks via E6's generator-yield model rather than naive stub return values whenever real callback interaction matters.
   - **Mandatory Pre-Restore `watcall` ABI Gate:** Immediately upon callback return—*before* restoring saved harness state—assert all 6 `watcall` callee-saved registers (`ebx`, `esi`, `edi`, `ebp`, `ds`, and `esp` matching the expected callee stack-pop for stack-passed arguments!) plus direction flag `DF == 0`. Any violation fails the T4 test immediately, closing the ABI-masking bug where a test stub hides stack corruption.
5. **R2 Strictly Typed Logical Pointer Correspondence:**
   - Function pointers stored in globals, structs, or return values naturally differ numerically between C-side and original `war.exe` addresses.
   - **Rule:** Never relax raw integer comparison (`int == int`). Instead, explicitly declare pointer-typed fields/slots in the T4 spec (`LogicalFnPtr`), mapping both C-side and original-side addresses to a canonical symbol ID (`fn_id`) and comparing canonical IDs strictly. Unregistered pointers or raw integers fail closed.
   - **Stage-3 / Build-B extension:** Extend R2 to `LogicalConstDataPtr` (strictly typed pointer to verified `CONST` string/table content) before allowing T4s to return pointers to C-owned `CONST` segments at relocated addresses.
6. **Runtime Verification Gate & Trust Boundary (`docs/ANALYST_GUIDE.md` + `AGENTS.md` Next Step 7):**
   - Preserve the existing `t4spec` static + audit checks untouched (`fresh=True`), and keep single-function T4 (`tools/wc1/cemu.py`) untouched during M2 completion.
   - **Adoption gate:** Multi-function `wc1.cemu` (E6) is a **mandatory hard gate BEFORE consolidating any T4 function into a multi-function `.c` file** (Stage 3), NOT a prerequisite for completing M2!

---

## 7. Compilation-Unit Recovery Interpretation (E1 / E2 / E7 / E8)

Synthesizing **E1**, **E2**, **E7**, and **E8** yields a clear, evidence-based epistemic model of Original Compilation Unit (CU) recovery—and decisively rejects the naive heuristic/automation approach sketched in RFC §9.3.

### 7.1 Four-Tier Evidence Taxonomy (Premise-Carrying Constraint Graph)

Every piece of CU evidence MUST carry its **exact premise**, its **directionality** (`MUST_MERGE`, `MAY_SPLIT`, or `EXPLORATORY_HINT`), and its **falsification condition**:

| Evidence Class | Signals (E1/E2/E7/E8) | Empirical Precision / Reliability | Premise Required | Allowed Architectural Action |
|---|---|---|---|---|
| **Class 1: Hard Structural Merge Constraints (`MUST_MERGE`)** | `shared_epilogue` (cross-fn `rel8` tail sharing, E1/E8); `shared_const_string_literal` (two functions referencing same `CONST` string, E8); internal `static`/unnamed jump-table or fallthrough (`EndCheckSurvive -> MissionDefeat`). | `6/6` (`100%`, 0 FP) and `1/1` (`100%`, 0 FP) across E8 corpora; directly reproduced in E1 (`-5r` / `-oa -5r`). | Watcom 10.0a does not emit cross-object `rel8` tail jumps or merge unreferenced private literals across `.obj`s without linker COMDAT folding (absent here). | Authoritative **same-CU merge constraint** in `OriginalCUHypothesis`. |
| **Class 2: Premise-Dependent One-Directional Merge Constraint** | `non_16_aligned_start` (function starts at `addr % 16 != 0`, E2/E8). | `100%` precision on E8 Corpus A & B1 **strictly as a merge signal** (cannot be a new `PARA`-aligned `_TEXT` `SEGDEF`). | Valid **iff** Watcom 10.0a emitted `PARA` (16B) `_TEXT` `SEGDEF`s (confirmed in E2) AND the preceding function is not hand-written `BYTE`-aligned ASM. **One-directional only:** `addr % 16 == 0` does **NOT** imply a split! | Strong **merge edge** in `OriginalCUHypothesis` (annotated with `premise="SEGDEF=PARA"`). |
| **Class 3: Explicit Authorial / Linker Anchors** | Embedded source filenames (`PLAYFLIC.C`, `BULLET.C`, `STATUS.C`, `GAMEDLG.C`, `PACKET.C`, `SND.C`, `PLACEBOX.C`), `zero16` (1..15 zero padding bytes to 16B boundary where preceding code is `-5r` 4B-aligned). | `zero16` has high precision when present, but **very low recall** (`0.524` Corpus A, `0.027` Corpus B1). Filenames anchor a CU name, not exact start/end addresses. | `zero16` assumes linker inserted `0x00` `PARA` padding (not compiler `NOP`/alignment filler, and not accidental 16B landing). | **Soft split anchor / naming anchor**; requires human review to confirm exact start/end. |
| **Class 4: Weak / Contradictory / Explicitly Rejected Signals** | **`_DATA`/`_BSS` staircase** (`0.250` A / `0.281` B1); **`call_locality_drop`** (`0.323` A / `0.179` B1); **`none16`** (`0.174` B1, 66 game candidates); **T4 `S(f)` flag-set differences** (84/125 empty module intersections in E7 are mostly T4 spelling artifacts!). | Empirically **refuted** (false-positive rates `68%–83%`!). | None rescues them. | **EXPLICITLY REJECTED** as boundary rules. `S(f)` contradictions on **T3-only** functions (`4/94` modules in E7) may be logged strictly as *competing hypotheses* for human analysts, never auto-splits. |

### 7.2 Explicit Rejection of Unjustified Automatic Consolidation and Auto-Splitting

1. **No weighted-score CU partitioner:** Combining unreliable signals (`none16` 17% precision, `_DATA` staircase 28%, `call_locality_drop` 18%) into a weighted score creates an opaque pseudo-scientific classifier that cannot be falsified and will mis-group unrelated functions.
2. **No automatic mutation of `analysis/modules.toml`:** `analysis/modules.toml` is a human-curated area/workflow organization map (`docs/subsystems/modules.md`), NOT an auto-generated CU graph. `OriginalCUHypothesis` lives in a separate, non-authoritative artifact (Stage 3) that explicitly records **competing hypotheses** and **unknown spans**.
3. **No unjustified bulk consolidation before M2 completion:** Consolidating 539 working single-function T3 files into multi-function `.c` files does **not** advance M2 completion (`make goal` gate 1), risks introducing `CONST` addend dominoes (E2 domino probe: `SaveVersionDialog`), and requires E5+V4 (for multi-string `CONST`) and E6 (for any T4 siblings). Consolidation is strictly **opt-in, evidence-backed, and incremental**:
   - **Immediate exception (M2-justified):** Co-compiling proven shared-epilogue clusters like E1 Group B (`0x2315c`/`0x23170`/`0x231cc`) where co-compilation directly resolves an M2 blocker AND an xfail T4 divergence simultaneously.
   - **Post-M2 (Stage 3):** Incremental consolidation of high-confidence contiguous `-5r` runs (e.g., `STATUS.C`, `GAMEDLG.C`, `PACKET.C`) once B3+V4 and E6 are in place.

---

## 8. Production Roadmap (Dependency-Ordered, Anchored to `main@a21772b`)

### 8.0 Current Production Baseline (`main@a21772b`, post E7 `3123a47` & M2 Cleanup `dae45bd`)

Before sequencing work, note what has **already shipped** on `main@a21772b` vs what **actually blocks M2 completion** (`docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json}@a21772b`):

- **Already DONE:** **912 / 1,010 (`90.3%`)** (`539` T3 = `537` 10.0a + `2` OW2; `373` T4; `926` named `91.7%`; Build A `IDENTICAL` `539 fns / 534 files`; `make verify` green in `57.05s`). E7 compiler presets (`14` 10.0a + `1` OW2) and M2 mechanical cleanup (`+13` DONE) are **already merged**.
- **Exact Breakdown of the 98 Remaining Not-DONE Functions:**
  1. **61** `fn_*` placeholders without C (`40` cross-TOML + `21` same-TOML) — ALL 61 already referenced in `src/` -> blocked by **atomic cross-module symbol migration + Wave 3R (`upgrade-existing`)**.
  2. **10** clean `BULLET.C` functions — **already Wave-3 eligible** (`2456f0c` unskipped `BULLET.C`).
  3. **7** existing `low`-conf semantically named functions without C -> blocked by **Wave 2/3R `low`-conf admission**.
  4. **7** B1/B2-blocked already-matched T3s (`1` B1 `ChooseCampaignDialog 0x157e8` + `6` B2: `0x1e380`, `0x2315c`, `0x23170`, `0x2e96c`, `0x2efd0`, `0x2f73c`).
  5. **5** real reference-C behavioural divergences (`4` `PLAYFLIC`: `0x231cc`, `0x23530`, `0x23668`, `0x23ae0` + `1` `EndScreen`: `0x2fcfc`). Note: E1 Group B already matches `0x231cc` byte-identically!
  6. **8** user-governance scope/discovery artifacts (`2` data-in-code `0x110a0`/`0x11530`, `2` `STATUS.C` split blocks `0x28090`/`0x28093`, `4` Miles AIL mixer asm `0x3fe34..0x400b4` — require explicit user approval per `AGENTS.md`).

**Key Strategic Insight:** Stages 0–2 below directly drive `912 -> 1002/1010` (plus 8 user-governance decisions -> **100% M2 completion**). Stages 3–4 deliver CU consolidation, B3, E6, E8, conditional E3/E4, and M3 (Build B + T5) **without delaying M2**.

---

### Stage 0 — Immediate Verification Soundness & Toolchain Hygiene (Pre-requisite to Everything)

- **Scope:**
  1. **Land E0 strengthened matcher into `tools/wc1/match.py`** (unified `FunctionMatch` + `RegionMatch`, bidirectional obligations V1, function-scoped branch bounds V2 fixing E2 Cause B, leading/trailing checks V3 preserving `trimmed_branch_target`, and `CONST` 1..3B alignment-gap rule V4 validated by **EXP-1**).
  2. **Land D9 short-path protection in `tools/wc1/oldcc.py`** (V6: stage `.c`/`.obj` and `TMPDIR` under short paths `<= 48` chars, fail fast before ~129-char `wcc386` crash).
  3. **Fix `build.check_t3_buildable` cross-piece `rel8` false positive** (reject all unhandled cross-piece `rel8`—interior, entry, AND spanning—preventing `IntroOpSyncSound` regressions immediately).
  4. **Fix the 3 `R3` bugs in `tools/wc1/t3_audit.py@a21772b`** (Probe 6: checkout-rooted `_default_system_headers(repo_root)`, live `tool_sig` comparison, fail-closed `_git()`).
- **Entry criteria:** **EXP-1** (`CONST` alignment-gap rule probe) passed; consilium approval of V1–V6.
- **Exit criteria:** `make verify` green; all 539 existing T3s pass `RegionMatch=MATCH`; all 55 E0 controls + `CONST` gap controls + `oldcc` long-path negative test + `IntroOpSyncSound` `check_t3_buildable` negative test + `t3_audit` R3 tests green.
- **M2 impact:** 0 direct DONE count, **prevents silent soundness regressions and Wine path crashes** across all subsequent stages.
- **Regression risk & reversibility:** Low (all 539/539 current T3s already verified by E0 + Probe 4); atomic per-module commits (`oldcc`, `t3_audit`, `match`, `build`), trivially revertible.

---

### Stage 1 — Minimal `VerifiedRegion` + `BuildAPlacementPlan` + Fix B1 + Unified Fix B2

- **Scope:**
  1. Introduce non-forgeable `VerifiedRegion` (V5) and `BuildAPlacementPlan` in `tools/wc1/build.py` + `tools/wc1/emit.py` (making `check_t3_buildable` call the exact same `BuildAPlacementPlan` admissibility logic!).
  2. Implement **Fix B1** (`LeadingJumpTableSpec` widened cut `[table_start, fn_end)`) -> promote `ChooseCampaignDialog` (`0x157e8`).
  3. Implement **Unified Fix B2** (after **EXP-3** passes: strict `in_place`-only piece-boundary local-label `rel8` rewrite for B2-interior, B2-entry, B2-span + `omfpatch` interior `_loc_<addr>` `PUBDEF` for cross-piece `rel32`; explicit `--legacy` fail-closed guard) -> promote `0x1e380`, `0x2e96c`, `0x2efd0`, `0x2f73c`, plus either standalone `0x2315c`/`0x23170` OR E1 Group B whole-TU `VerifiedRegion` (`0x2315c`+`0x23170`+`0x231cc`, simultaneously eliminating 1 `PLAYFLIC` xfail!).
- **Entry criteria:** Stage 0 merged & green; **EXP-3** (NASM piece-boundary `rel8` Build A probe on `0x23170` & `0x2f73c`) passed.
- **Exit criteria:** `make verify` green; Build A `IDENTICAL` with **+7** (or **+8** with `0x231cc`) new T3s (`912 -> 919/920` DONE); negative tests prove `--legacy` refuses cross-piece `rel8` and fallthrough cuts.
- **Regression risk & reversibility:** Low-to-moderate (touches `emit.py`/`build.py`, bounded by Build A SHA-256 `IDENTICAL` oracle); cleanly revertible per commit.

---

### Stage 2 — Genuine M2 Completion Critical Path (`919 -> 1002/1010` + User Governance)

*Note: This stage is intentionally decoupled from B3/E4/E6/E8 so M2 completion is never held hostage by post-M2 consolidation tooling.*

- **Scope:**
  1. **Deterministic atomic symbol migration tool (`wc1.symbol_migrate`):** Atomically renames a `fn_*` placeholder across `analysis/symbols/*.toml`, `src/**/*.{c,h}`, `tests/**/*.py`, and `analysis/modules.toml` in one verified transaction (unblocking all **61** referenced `fn_*` functions).
  2. **Wave 3R (`upgrade-existing`) & `low`-conf admission** in `wc1.overnight` / `wc1.batch_driver` (unlocking the **61** `fn_*` + **7** `low`-conf = **68** functions).
  3. **Run Wave 3 on `BULLET.C` (10 functions)** and **Wave 3R across the 14 stub areas** (including `0x19c14` which automatically uses Stage 1's B1!).
  4. **Fix remaining 4–5 real ref-C bugs** (`PLAYFLIC` `0x23530`, `0x23668`, `0x23ae0`, and `0x231cc` if not already replaced by E1 Group B; `EndScreen` `0x2fcfc` `LayerAdd` swapped args).
  5. **User governance proposal** (per `AGENTS.md` fixed finish line — proposal only, never unilateral): resolve the **8** discovery/scope artifacts (`0x110a0`/`0x11530` data-in-code, `0x28090`/`0x28093` `STATUS.C` shared-return split, `0x3fe34..0x400b4` Miles AIL mixer asm).
- **Entry criteria:** Stage 0 & Stage 1 green (for clean `check_t3_buildable`, B1/B2, and short-path `oldcc`).
- **Exit criteria:** **1,002/1,010 DONE** (100% of non-governance M2 scope), unchecked `ref` = `0`, `make verify` green, Build A `IDENTICAL`; upon user governance decision on the 8 artifacts, **M2 Gate 1 PASS**.
- **What is explicitly DEFERRED past Stage 2 (does NOT block M2):** Shared OMF32 codec refactor, Fix B3 (`CONST`/`_DATA` decoupling), E6 multi-function `wc1.cemu`, E8 CU constraint-graph advisor, E3/E4 selective extraction, and bulk CU consolidation.

---

### Stage 3 — Post-M2 Progressive CU Reconstruction, T4->T3 Quality & Multi-Function T4

- **Scope (in strict internal dependency order):**
  1. **Step 3A — Unified OMF32 Codec (`tools/wc1/omf.py`):** Consolidate OMF parsing, cross-record `THREAD` state, 64-fixup chunking, and record re-emission into one tested library (replacing ad-hoc code in `omfpatch.py`, E4, and E5).
  2. **Step 3B — Hardened Fix B3 (`CONST`/`_DATA` decoupling with Invariant V4):** Implement E5 over the unified OMF32 codec with explicit V4 1..3B unreachable `CONST` gap verification + `rev-e5-02` mutability/aliasing guards -> removes artificial `extern str_*` workarounds (`SaveSlotPath`, `SaveErrorDialog`, `GAMEDLG`).
  3. **Step 3C — Multi-Function T4 Harness (`wc1.cemu` E6):** Mandatory gate BEFORE consolidating any T4 function into a multi-function `.c` file; includes contiguous `VerificationBoundary`, 3 substitution mechanisms, generator callbacks with pre-restore `watcall` ABI checks, R2 typed logical function & `CONST` data pointers, and intra-function switch-table allowance (**EXP-4**).
  4. **Step 3D — Analyst-Only CU Constraint Advisor (E8) + Opt-In Contiguous CU Consolidation:** Produce `analysis/cu_hypotheses.toml` using strictly Class 1–3 premise-carrying signals; run Wave 4B / `-5r` sweeps on remaining T4s (`+` **EXP-2** presets `-5r -d1+ -zp1`, `-od -5r`) and incrementally consolidate high-confidence contiguous CUs (e.g., `STATUS.C`, `GAMEDLG.C`, E1 Group A) via whole-TU `VerifiedRegion`.
  5. **Step 3E — Conditional E3/E4 Selective Extraction (ONLY IF NEEDED):** Implement *only* if Step 3D leaves persistent, irreducible mismatching siblings blocking genuine CU consolidation; MUST fix all 8 E4 defects (Probe 5 Bugs 5a–5d + `rev-e4-01` F1–F4) over the Step 3A unified OMF32 codec.
- **Entry criteria:** M2 complete (or explicitly authorized post-M2 track); EXP-1/EXP-2/EXP-4 green.
- **Exit criteria:** Natural C literals/data ownership (`semantic_owner = C`), multi-function T4 soundness enforced, zero regressions in `make verify` and Build A `IDENTICAL`.

---

### Stage 4 — M3: Build B (All-C Relocatable Build) & T5 Scenario Verification

- **Scope:**
  1. Author `analysis/data_layout.toml` and flip data `physical_provider` from `ASM` to `C` (where `CONST` padding no longer needs to match 1994 heap residue!).
  2. Complete **`I16` Relocatability Audit** (eliminate raw fixed-VA assumptions, hardcoded segment offsets, and Build-A-only ASM data anchors).
  3. Propose M3 **T5 scenario set** to the user for explicit approval (`AGENTS.md` governance) and bring `make goal` Gate 3 to PASS.
- **Entry criteria:** Stage 2 (M2) + Stage 3 (data `semantic_owner = C` and unified TUs).

---

## 9. Scale and Generalization

To ensure this architecture applies cleanly to substantially larger reverse-engineering projects (10,000–100,000+ functions, multi-megabyte binaries, multiple compilers/object formats) without over-engineering Warcraft I (`1,010` in-scope functions, ~`150 KB` game `_TEXT`), we separate mechanisms into three strict layers:

### 9.1 Layer 1 — Genuinely General Architectural Principles (Transferable to Any Large Decompilation Project)
- **Three-level verification separation:** `FunctionMatch` (local diagnostic) vs `RegionMatch` / `VerifiedRegion` (closed immutable proof) vs `PlacementPlan` (integrated binary buildability).
- **Bidirectional Normalized Addressing Obligations (`O_obj == O_orig`):** Format-agnostic (works identically whether obligations come from OMF32/LE, COFF/PE, ELF, or Mach-O).
- **Explicit separation of `semantic_owner` vs `physical_provider`:** Essential at scale whenever incremental C reconstruction must coexist with an un-relocated original binary's data/rodata layout (and whenever historical compilers leave non-deterministic padding bytes in read-only pools!).
- **Explicit `VerificationBoundary` + `DependencySubstitutionPolicy` + ABI-checked callbacks + typed logical pointer correspondence (R2):** Solves multi-function differential testing cleanly for any ISA/ABI (`watcall`, `cdecl`, `fastcall`, `SysV`, `ARM AAPCS`).
- **Premise-carrying CU constraint graphs (rejecting opaque weighted heuristics):** Keeping human area maps (`modules.toml`) strictly decoupled from falsifiable CU hypotheses scales to thousands of CUs without corrupting navigation trees.
- **Checkout-portable, live-verified provenance & content-addressed dependency caches:** Already proved critical for verification speed (`52–57s` `make verify`) and scales linearly to 100k-function repos.

### 9.2 Layer 2 — Watcom / OMF32 / DOS-LE Specific Mechanisms (Isolated Behind Interfaces)
- Watcom 10.0a flag-dependent alignment rules (`-4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`).
- Watcom 10.0a uninitialized 1..3-byte `CONST` string alignment padding (Invariant V4) and ~129-character DOS/Wine path buffer limit (Invariant V6).
- OMF32-specific encoding constraints: no 8-bit external relocations (driving NASM piece-boundary `rel8` B2), `FIXUPP32` 64-fixup chunking, cross-record `THREAD` state, `FLAT`/`DGROUP`/`Target`/`EXTDEF` frames, `PUBDEF`/`LEDATA32` 1024-byte chunks.
- `watcall` register-passing ABI checks (`eax/edx/ebx/ecx` inputs, 6 callee-saved regs + callee stack-pop).

### 9.3 Layer 3 — Warcraft I Specific Details (Data/Config Only, Never Hardcoded in Core Logic)
- Specific B1/B2 target lists (`0x157e8`, `0x2315c`/`0x23170`/`0x231cc`, `0x2f694`/`0x2f73c`, etc.).
- Specific `war.exe` game range (`0x104b0..0x3024e`), embedded CU filenames (`PLAYFLIC.C`, `BULLET.C`, `STATUS.C`), and the 8 M2 discovery/scope artifacts.
- `original/war.exe` Build A SHA-256 oracle and `wc1.overnight` Wave 2/3/3R/4B orchestration policy.

### 9.4 What Frameworks We Explicitly REJECT as Premature Over-Engineering
- **No plugin-architecture / multi-backend compiler abstraction framework** (`ICompilerBackend`, `IObjectFormatPlugin`, `IRegionPlacementStrategy` factories) in Warcraft I: clean module boundaries (`omf.py`, `match.py`, `build.py`, `cemu.py`) with well-typed dataclasses achieve full conceptual transferability at 1/5 the code size.
- **No automated ML/weighted CU clustering engine:** Premise-carrying constraint graphs are both simpler and scientifically superior (E8).
- **No generalized binary-rewriting / OMF-slicing framework before M2:** Keeping E4 out of M2 avoids maintaining a brittle binary-to-binary OMF synthesizer when whole-TU `-5r` integration works on 23/23 contiguous runs.

---

## 10. Proposed RFC Changes (Section-by-Section Against `rfc-build-codegen-infrastructure.md@6f319ac`)

Target document: `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13` (`§§1–20`).

| RFC Section | Action | Concrete Change & Justification |
|---|---|---|
| **§1. Executive summary** | **REVISE** | Update baseline numbers to `main@a21772b` (`912/1010 DONE`, E7 presets + M2 cleanup landed); summarize E0–E8 outcomes; reorder production priorities so M2 completion (Stage 0–2) precedes B3/E6/E8/E4 consolidation (Stage 3). |
| **§2.1. Confirmed strengths** | **RETAIN** | Remains accurate (`make verify` now `52–57s`, E7 presets landed). |
| **§2.2. Confirmed limitations** | **REPLACE (§2.2.5) / REVISE (rest)** | **Replace §2.2.5** ("Watcom 10.0a always aligns to 4B") with E2's verified matrix (`-4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`, `OW2 = 16B`). Add two newly discovered compiler/build limitations: (1) Watcom 10.0a uninitialized 1..3B `CONST` alignment padding (Probes 3 & 7) and ~129-char path limit (E7 D9); (2) `emit.py`/`check_t3_buildable` missing entry-targeting & cut-spanning `rel8` (Probe 1, `IntroOpSyncSound` `0x23170`, `MissionDefeat` `0x2f73c`). |
| **§3. All 17 agreed architectural decisions** | **REVISE** | Update status of each decision post E0–E8: mark E7 presets as LANDED; revise alignment/CU/B2/B3/E4 decisions per `DEC-C01..DEC-C14`; add V4 (`CONST` gap rule), V6 (`oldcc` short-path guard), and explicit deferral of E4 selective extraction. |
| **§4. Conceptual entity model & relations** | **REVISE** | Retain the 4 entities + 2 derived artifacts; tighten `VerifiedRegion` to be strictly matcher-minted (non-forgeable, V5) and add explicit `BuildAPlacementPlan` ownership of cross-piece branches and data providers. |
| **§5. Contract `FunctionMatch` & `RegionMatch`** | **REVISE** | **§5.1:** Retain split; add explicit 3-level table distinguishing `FunctionMatch` vs `RegionMatch` vs Integrated Buildability. **§5.2:** Add **Invariant V2** (function-scoped branch bounds fixing E2 Cause B) and **Invariant V4** (strict 5-condition Watcom 10.0a 1..3B `CONST` alignment-gap rule). **§5.3:** Preserve `trimmed_branch_target` explicitly across both whole and partial modes (fixing E3 `partial_matcher.py:206`). |
| **§6. `Post-Codegen Symbolic Relocation Equivalence`** | **REVISE** | Retain §§6.1–6.4 formal invariants, but demote selective OMF32 extraction (E4) from a planned near-term production path to a **Stage 3 conditional fallback** gated on fixing all 8 uncovered defects (Probe 5 Bugs 5a–5d + `rev-e4-01` F1–F4) over a unified OMF32 codec. Update §6.3 to document Watcom 10.0a's uninitialized `CONST` padding constraint. |
| **§7. `Verified Code Regions` & `PlacementPlan`** | **REVISE** | **§7.1:** Add non-forgeability invariant (V5). **§7.2:** **Replace** the interior-only B2 description with **Unified Fix B2** covering ALL three cross-piece `rel8` classes (interior, cut-entry like `EndCheckSurvive -> MissionDefeat`, and cut-spanning like `IntroOpSyncSound` `0x23170`) plus cross-piece fallthrough, strictly restricted to `in_place` mode (never `--legacy`), plus mandatory `check_t3_buildable` unification. Clarify E1 whole-TU co-compilation as preferred permanent fix for shared-epilogue clusters. |
| **§8. Data ownership & data-anchor decoupling** | **REVISE** | **§8.1:** Strengthen `semantic_owner` vs `physical_provider` with the Probe 3/7 proof that 157/293 `war.exe` `CONST` strings contain non-reproducible 1994 heap-residue pad bytes (making `physical_provider = ASM` mandatory in Build A whenever `const_pad_exempted = True`). **§8.2:** Update Fix B3 status from `[HYPOTHESIS]` to `E5 CONFIRMED WITH CONDITION` (requires Invariant V4 `CONST` gap rule + unified OMF32 codec; deferred to Stage 3 post-M2). **§8.3:** Retain M3 evolution. |
| **§9. `Original Compilation Unit Recovery`** | **REPLACE (§9.3) / RETAIN (§§9.1–9.2)** | Retain §§9.1–9.2 separation from `modules.toml` and epistemic tagging. **Replace §9.3** completely: remove refuted `_DATA`/`_BSS` staircases (`0.250`/`0.281`) and `call_locality_drop` (`0.323`/`0.179`), reject weighted scoring and `none16` (`0.174`) splits, and replace with the 4-tier premise-carrying constraint graph (Class 1–4, E8) operating strictly in analyst-advisory mode. |
| **§10. T3 provenance & evidence invalidation** | **REVISE** | Retain §§10.1–10.3; add explicit checkout-portable `source_digest` rule, live `tool_sig` check, and fail-closed `_git()` rule (closing Probe 6's `t3_audit.py` R3 bugs on `main@a21772b`). |
| **§11. Multi-function T4 verification** | **REVISE** | Update §11.3 from `[HYPOTHESIS]` to `E6 PARTIALLY_CONFIRMED`: note Watcom 10.0a actually emitted `EXTDEF` FIXUPP on `IntroFrame -> IntroLoadCreditLines` (`symbol_aware_reloc`), while `c_entry_hook` remains required for bare `rel32`; codify generator callbacks with pre-restore `watcall` ABI checks, R2 `LogicalFnPtr` (plus Stage-3 `LogicalConstDataPtr` and proven intra-function switch tables), and gate adoption before the first multi-function T4 migration (Stage 3). |
| **§12. Compiler calibration & search** | **REVISE** | Record E7 (`21,618` compiles) and production landing (`3123a47`, 14 10.0a presets); classify T4 `S(f)` intersections as **spelling-contingent** (never auto-split on empty `S(f)`); add mandatory short-path staging in `wc1.oldcc` (V6 / D9); log `-5r -d1+ -zp1` and `-od -5r` as **EXP-2**. |
| **§13. Fundamental correctness invariants** | **REVISE** | Retain all existing invariants; append **V2** (function-scoped `FunctionMatch` bounds), **V4** (`CONST` 1..3B unreachable alignment-gap rule), **V5** (non-forgeable `VerifiedRegion` + portable provenance), **V6** (`oldcc` short-path guard), and **B2-in-place-only** (`--legacy` must refuse cross-piece `rel8`/fallthrough). |
| **§14. Experimental program `E0–E8`** | **REVISE** | Convert from prospective plan to **completed campaign record** pinned to `e6150b8` with exact verdicts, refutations, and the 4 remaining targeted probes (`EXP-1`..`EXP-4` + M3 `I16` audit). |
| **§15. Mandatory re-audit of existing T3s** | **REVISE** | Mark **COMPLETED** for baseline 519/519 (E0 `t3_reaudit.json@e6150b8`) + 20/20 new `main@a21772b` T3s (**Probe 4**, total **539/539**); require re-running automatically on `make verify` once E0 lands in `tools/wc1/match.py` (Stage 0). |
| **§16. Production admission criteria** | **REVISE** | Add explicit gate: no mechanism enters the M2 critical path unless it directly protects soundness (Stage 0) or directly unlocks remaining M2 functions (Stage 1–2); post-M2 mechanisms (B3, E6, E8, conditional E4) must pass unified-codec + negative-control gates in Stage 3. |
| **§17. Deferred architectural decisions** | **REPLACE** | Resolve decisions settled by E0–E8 (alignment, `-5r` default, CU heuristics, E6 boundary model) and list actual remaining deferred items (Stage 3 B3/E6/E8/conditional E4, Stage 4 `data_layout.toml`, `I16` audit, user-approved M3 T5 scenario set). |
| **§18. Incremental migration & portability** | **REPLACE (§18.1) / REVISE (§18.2)** | **Replace §18.1** with the 5-stage dependency-ordered roadmap anchored to `main@a21772b` (Section 8 above), explicitly aligning build/codegen work behind genuine M2 completion (68-fn symbol migration + Wave 3R + B1/B2 + 5 ref-C fixes). **Revise §18.2** with the 3-layer scale/generalization partition (Section 9) rejecting premature framework abstractions. |
| **§19. Risks, limitations & excluded directions** | **REVISE** | Add newly confirmed exclusions: weighted CU classifiers, `_DATA`/`_BSS` staircase & `call_locality_drop` splits, empty `S(f)` auto-splitting, unhardened E4 OMF extraction in M2, and whole-segment `CONST` byte-matching without V4 gap handling. |
| **§20. References** | **REVISE** | Pin all citations to exact commit SHAs (`e6150b8`, `6f319ac`, `a21772b`, `3123a47`, `dae45bd`, `cea804e`, and E0–E8 merge commits). |

---

## 11. Structured Decision Proposals

### `DEC-C01`
- **Decision:** `DEC-C01`
- **Title:** Retain RFC Core Entity Separation & Three-Level Verification Hierarchy
- **Proposition:** Retain the separation between `FunctionMatch` (local diagnostic), `RegionMatch` -> immutable `VerifiedRegion` (closed object/region proof), and `BuildAPlacementPlan` (integrated Build A admissibility), and require all pipeline tools (`wc1.match`, `wc1.build`, `wc1.t3_audit`, `wc1.m2_inventory`, `wc1.overnight`, `wc1.wave4`) to distinguish these three levels explicitly.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Collapsing local match, region match, and integrated buildability caused the `IntroOpSyncSound` (`0x23170`) false positive and makes multi-function TUs impossible to reason about safely.
- **Evidence:** `E0-matcher-soundness.md@e6150b8`; `E1-shared-epilogue.md@e6150b8`; `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/report.md@a21772b`; Probe 1 & Probe 4.
- **Assumptions:** Existing `make verify` and `make goal` gates remain unchanged.
- **Dependencies:** None.

### `DEC-C02`
- **Decision:** `DEC-C02`
- **Title:** Land Hardened E0 Verification Core in Stage 0 With Function-Scoped `FunctionMatch` Bounds (V1–V3)
- **Proposition:** Replace `tools/wc1/match.py`'s one-directional matcher with E0's bidirectional Normalized Addressing Obligation engine in Stage 0, fixing E2 Cause B (`FunctionMatch` MUST check branch closure against `[orig_fn.start, orig_fn.start + fn_len)`, NOT the first public's linear region) and preserving `trimmed_branch_target` checks across all modes (fixing E3 `partial_matcher.py:206`).
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Closes all 39 E0 negative-control soundness holes with 0 regressions across all 539 production T3s on `main@a21772b`, while preventing E2's 9 false `external_rel8` rejections on non-contiguous multi-function diagnostics.
- **Evidence:** `E0-matcher-soundness.md@e6150b8` (`519/519`, `55/55` controls); `E2-context-alignment.md@e6150b8` (Cause B: 9 losses); `rev-e3-01.md@e6150b8` (Nit 3); Probe 4 (`20/20` new `main@a21772b` T3s = `539/539` total).
- **Assumptions:** Performance stays within the `52–57s` `make verify` budget (E0 re-audited 519 T3s in seconds).
- **Dependencies:** `DEC-C01`, `DEC-C03`.

### `DEC-C03`
- **Decision:** `DEC-C03`
- **Title:** Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (Invariant V4)
- **Proposition:** In both E0 `RegionMatch` and Stage-3 Fix B3, explicitly exempt 1..3-byte alignment padding gaps in `CONST` **if and only if** all 5 conditions hold: (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Watcom 10.0a `-ot` leaves non-deterministic uninitialized heap memory in 1..3B `CONST` string alignment gaps (present in 157/293 `war.exe` `CONST` strings and confirmed non-deterministic across consecutive live compiles). Without V4, both E0 and E5 fail on almost every real multi-string `-ot` CU (`SaveSlotPath`, etc.).
- **Evidence:** Probes 3 & 7 (`157/293` fixup-bounded `war.exe` `CONST` strings have non-zero gaps; live `-ot -5r` emitted `73 00 2f` vs `76 00 61` vs `war.exe` `8d 75 e0` at `0x56b1c`; all 11/11 E0 local-data T3s had 1 string each; E2 `GAMEDLG` had `40B`/`36B` `mod 4 == 0` strings); `06235f6` (`rev-e8-02` CONST pad digest drift).
- **Assumptions:** Verified via **EXP-1** before merging Stage 0 matcher / Stage 3 B3.
- **Dependencies:** `EXP-1`.

### `DEC-C04`
- **Decision:** `DEC-C04`
- **Title:** Mandatory Short-Path Guard in `wc1.oldcc` (V6 / D9) and `t3_audit.py` R3 Provenance Fixes in Stage 0
- **Proposition:** Immediately implement Watcom 10.0a short-path staging/length guard (`<= 48` char staging path + fail-fast `[TOOLCHAIN ERROR]` before ~129-char crash) in `tools/wc1/oldcc.py`, and fix the 3 `R3` provenance defects in `tools/wc1/t3_audit.py@a21772b` (checkout-rooted `_default_system_headers(repo_root)`, live `tool_sig` comparison, fail-closed `_git()`).
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** `wcc386` path-buffer crashes were observed independently in E2, E5, E7, and E8 and remain unguarded in `tools/wc1/oldcc.py@a21772b`; `t3_audit.py` provenance bugs undermine checkout-portable audit guarantees.
- **Evidence:** `E7-compiler-calibration.md@e6150b8`; `decisions.md@e6150b8` (D9); `tools/wc1/oldcc.py@a21772b`; `docs/research/model-calibration-engineering/report.md@cea804e`; Probe 6.
- **Assumptions:** Short staging dir (e.g., `/tmp/wc1-cc-...`) is writable in Nix/CI environments.
- **Dependencies:** None.

### `DEC-C05`
- **Decision:** `DEC-C05`
- **Title:** Adopt Minimal `VerifiedRegion` + `BuildAPlacementPlan` + Fix B1 + Unified Fix B2 in Stage 1
- **Proposition:** Introduce non-forgeable `VerifiedRegion` (V5) and `BuildAPlacementPlan` in Stage 1, unifying `build.check_t3_buildable` with `BuildAPlacementPlan`, implementing Fix B1 (`LeadingJumpTableSpec` widened cut `[table_start, fn_end)`), and implementing **Unified Fix B2** handling ALL three cross-piece `rel8` classes (interior, cut-entry, cut-spanning) plus cross-piece fallthrough via NASM piece-boundary local-label offset expressions strictly in `in_place` mode (unconditionally forbidden under `--legacy`), plus `omfpatch` interior `_loc_<addr>` `PUBDEF` for cross-piece `rel32`.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Immediately fixes the `IntroOpSyncSound` (`0x23170`) false-positive hole, closes the newly discovered entry-targeting `rel8` gap (`EndCheckSurvive -> MissionDefeat` `0x2f73c`), and unlocks all **7** remaining B1/B2-blocked ready T3s (`+7` DONE -> `919/1010`, 0 LLM cost).
- **Evidence:** Probe 1 (43 binary-wide / 25 game-range cross-fn `rel8`: 29 interior, 14 entry, 11 spanning; `0x23170` spanning, `0x2f73c` entry+interior+fallthrough); `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/candidate_ledger.json@a21772b`; `E0-matcher-soundness.md@e6150b8`; `E1-shared-epilogue.md@e6150b8`.
- **Assumptions:** **EXP-3** confirms NASM piece-boundary `rel8` rewrite links Build A `IDENTICAL` on `0x23170` and `0x2f73c`.
- **Dependencies:** `DEC-C02`, `EXP-3`.

### `DEC-C06`
- **Decision:** `DEC-C06`
- **Title:** Promote E1 Whole-TU Co-Compilation for Shared-Epilogue Clusters Over Ad-Hoc Splits
- **Proposition:** Where all functions in a shared-epilogue cluster have C sources, prefer co-compiling them into a single contiguous multi-function `VerifiedRegion` under `-5r` / `-oa -5r` (starting with E1 Group B: `IntroOpPlaySound` `0x2315c` + `IntroOpSyncSound` `0x23170` + `IntroOpWaitSound` `0x231cc`), using Unified Fix B2 strictly as the incremental bridge while siblings remain ASM.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Co-compiling Group B eliminates the cross-piece `rel8` boundary cleanly AND resolves `0x231cc` (one of the 4 remaining `PLAYFLIC` xfail divergences on `main@a21772b`) with a Build A `IDENTICAL` proof already demonstrated in E1.
- **Evidence:** `E1-shared-epilogue.md@e6150b8` (`Group A` `-oa -5r` & `Group B` `-5r` Build A `IDENTICAL`); `candidate_ledger.json@a21772b` (`0x231cc` xfail).
- **Assumptions:** Group B's E1 C source passes all existing `PLAYFLIC` tests cleanly once `0x231cc` is promoted to T3.
- **Dependencies:** `DEC-C02`, `DEC-C05`.

### `DEC-C07`
- **Decision:** `DEC-C07`
- **Title:** Prioritize Genuine M2 Completion (Atomic Symbol Migration + Wave 3R + Ref-C Fixes) Ahead of Post-M2 Consolidation Tooling
- **Proposition:** Sequence Stage 2 (deterministic atomic cross-module symbol renamer `wc1.symbol_migrate`, Wave 3R `upgrade-existing` + `low`-conf admission, `BULLET.C`, remaining 4–5 ref-C bugfixes, and user governance proposal on the 8 discovery/scope artifacts) immediately after Stage 1, and defer B3 (E5), multi-function T4 (E6), CU advisor (E8), and selective extraction (E4) to Stage 3 (post-M2).
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Of the 98 remaining not-DONE functions on `main@a21772b`, 68 are blocked by symbol migration / Wave 3R, 10 are ready `BULLET.C`, 7 are B1/B2, 5 are ref-C bugs, and 8 are user governance—whereas B3, E4, E6, and E8 unlock **0/98** M2 functions. Charter explicitly forbids optimizing T3 count at the expense of genuine M2 completion.
- **Evidence:** `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json}@a21772b`; `docs/research/m2-completion/blocker-analysis.md@ca82750`.
- **Assumptions:** User governance decision on the 8 scope/discovery artifacts remains strictly user-approved per `AGENTS.md`.
- **Dependencies:** `DEC-C05`.

### `DEC-C08`
- **Decision:** `DEC-C08`
- **Title:** Reject Near-Term Production Rollout of E4 Selective OMF Extraction; Defer Conditionally to Stage 3
- **Proposition:** REJECT adopting `experiments/build_codegen/e4/omf_extract.py@e6150b8` into production during M2 or as a default consolidation path. Whole-TU `RegionMatch` under `-5r` is the primary integration mechanism. Selective OMF extraction may only be introduced conditionally in Stage 3 if irreducible mismatching siblings remain after `-5r`/Wave 4B, and ONLY after rebuilding it over a unified OMF32 codec fixing all 8 defects (Probe 5 Bugs 5a–5d + `rev-e4-01` F1–F4).
- **Revision:** 1
- **Position:** `REJECT` (rejecting immediate/default E4 production rollout as recommended in `decisions.md@e6150b8` D6)
- **Reason:** E4 prototype has 4 newly uncovered production-blocking bugs (cross-record `THREAD` crash, non-`_TEXT` `PUBDEF` corruption when `lo > 0`, linear jump-table misdecode, missing 64-fixup chunking) plus 4 `rev-e4-01` findings, unlocks 0/98 M2 functions, and E2 showed 23/23 contiguous runs pass whole-TU `RegionMatch` under `-5r`.
- **Evidence:** Probe 5 (reproduced `THREAD` crash + `omf_extract.py:258,378,766,798-807,823`); `rev-e4-01.md@e6150b8`; `E2-context-alignment.md@e6150b8` (`23/23` contiguous runs); `candidate_ledger.json@a21772b` (`0x28254`, `0x24e90` already T4 DONE).
- **Assumptions:** Post-M2 `-5r` + Wave 4B resolves most mismatching siblings cleanly.
- **Dependencies:** `DEC-C09`.

### `DEC-C09`
- **Decision:** `DEC-C09`
- **Title:** Consolidate All OMF32 Parsing and Re-Emission Into One Unified Codec Before B3 or E4
- **Proposition:** Before landing Fix B3 (Stage 3B) or any optional OMF extraction (Stage 3E), consolidate OMF32 parsing, persistent cross-record `THREAD` tracking, 64-fixup `FIXUPP32` chunking, and record emission into one tested module (`tools/wc1/omf.py`), removing duplicate ad-hoc OMF serializers.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Duplicating OMF32 codecs across `omf.py`, `omfpatch.py`, E4 `omf_extract.py`, and E5 `omf_b3.py` directly caused E4's cross-record `THREAD` bug (`omf_extract.py:258`) and missing 64-fixup chunking (`:766`) even though E5 (`omf_b3.py:409`) and `wc1.omf` had already solved both.
- **Evidence:** Probe 5 (`wc1.omf.parse_module` succeeded where `e4.raw_fixups` crashed); `omf_b3.py:409@e6150b8` vs `omf_extract.py:258,766@e6150b8`.
- **Assumptions:** Single-function `omfpatch.py` remains untouched during M2 (Stages 0–2) except minimal B1/B2 interior `_loc_` `PUBDEF` emission.
- **Dependencies:** `DEC-C07`.

### `DEC-C10`
- **Decision:** `DEC-C10`
- **Title:** Adopt Hardened Fix B3 Conditionally in Stage 3 With Invariant V4 (`CONST` Gap Rule)
- **Proposition:** Adopt E5's data-anchor decoupling (`semantic_owner = C`, `physical_provider = ASM` in Build A) in Stage 3B over the unified OMF32 codec, strictly conditioned on implementing Invariant V4 (1..3B unreachable `CONST` alignment-gap verification), passing **EXP-1** on `SaveSlotPath` (`0x14740`), and enforcing `rev-e5-02` `_DATA` mutability/aliasing guards.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Eliminates artificial `extern str_*` workarounds and prepares C data ownership for M3, while V4 fixes the fatal multi-string `-ot` `CONST` padding failure E5 did not encounter.
- **Evidence:** `E5-data-anchor-b3.md@e6150b8` (`9/9` Build A `IDENTICAL`, `86/86` tests); `rev-e5-02.md@e6150b8`; Probes 3 & 7 (`157/293` `war.exe` `CONST` strings, `SaveSlotPath` `0x56b1c`).
- **Assumptions:** **EXP-1** passes with zero false positives on negative controls.
- **Dependencies:** `DEC-C03`, `DEC-C09`, `EXP-1`.

### `DEC-C11`
- **Decision:** `DEC-C11`
- **Title:** Gate Multi-Function T4 Consolidation Strictly Behind E6 `wc1.cemu` in Stage 3
- **Proposition:** Adopt E6's multi-function T4 architecture (`Isolated`/`Group`/`Integrated` modes, contiguous `VerificationBoundary`, 3-mechanism `DependencySubstitutionPolicy`, generator callbacks with pre-restore `watcall` ABI checks, R2 typed `LogicalFnPtr` extended with `LogicalConstDataPtr` and proven intra-function switch tables) in Stage 3C as a **hard prerequisite before consolidating any T4 function into a multi-function `.c` file**, while keeping single-function `wc1.cemu` unchanged during M2.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Multi-function T4 without E6 leaks intra-TU sibling calls and hides callback ABI errors, whereas E6 has 0 M2-completion impact while all T4s remain single-function.
- **Evidence:** `E6-multifunction-t4.md@e6150b8` (`96/96` tests, 14 negative variants fail closed); `rev-e6-01.md@e6150b8`; `candidate_ledger.json@a21772b`.
- **Assumptions:** **EXP-4** validates intra-function switch tables and `LogicalConstDataPtr` cleanly.
- **Dependencies:** `DEC-C07`, `EXP-4`.

### `DEC-C12`
- **Decision:** `DEC-C12`
- **Title:** Reject `_DATA`/`_BSS` Staircases, `call_locality_drop`, Weighted CU Scoring, and Empty-`S(f)` Auto-Splitting
- **Proposition:** Explicitly REJECT `_DATA`/`_BSS` staircase splits, `call_locality_drop`, `none16` auto-splits, weighted CU boundary scoring, empty-`S(f)` auto-splitting, and any automatic mutation of `analysis/modules.toml`. Adopt instead an analyst-only **premise-carrying CU constraint graph** (`analysis/cu_hypotheses.toml` in Stage 3D) distinguishing Class 1 hard merges (`shared_epilogue`, `shared_const_string_literal`), Class 2 premise-dependent one-directional merges (`non_16_aligned_start` under `SEGDEF=PARA`), and Class 3 soft anchors (filenames, `zero16`), explicitly preserving competing hypotheses.
- **Revision:** 1
- **Position:** `REJECT` (rejecting RFC §9.3 heuristics and any automated CU consolidation/splitting)
- **Reason:** E8 empirically refuted `_DATA`/`_BSS` staircases (`0.250`/`0.281`), `call_locality_drop` (`0.323`/`0.179`), and `none16` (`0.174`), and E7 showed 84/125 empty module `S(f)` intersections are mostly T4 spelling artifacts.
- **Evidence:** `E8-cu-boundaries.md@e6150b8` (3 R4-independent corpora, `30/30` tests); `E7-compiler-calibration.md@e6150b8` (`84/125` empty `S(f)`).
- **Assumptions:** `analysis/modules.toml` remains human-curated area navigation.
- **Dependencies:** None.

### `DEC-C13`
- **Decision:** `DEC-C13`
- **Title:** Replace RFC §2.2.5 Alignment Model With Verified Watcom 10.0a / OW2 Alignment Matrix
- **Proposition:** Replace RFC §2.2.5's incorrect "10.0a always aligns to 4B" premise with E2's empirically verified matrix (`10.0a -4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`; `OW2 -4r/-5r = 16B`), codify `-5r` as the primary Watcom 10.0a default family for contiguous CU reconstruction, and run **EXP-2** to evaluate `-5r -d1+ -zp1` and `-od -5r`.
- **Revision:** 1
- **Position:** `PROPOSE`
- **Reason:** Corrects a foundational factual error in the RFC and explains why `-5r` matches `war.exe`'s 4B intra-CU layout (`0/417` regressions in E7, `23/23` contiguous runs in E2) while separate `.obj`s still link on 16B `PARA` boundaries.
- **Evidence:** `E2-context-alignment.md@e6150b8` (`28`-cell matrix, `23/23` contiguous runs); `E7-compiler-calibration.md@e6150b8` (`0/417` `-4r -> -5r` regressions).
- **Assumptions:** None (directly observed from live compiler binaries).
- **Dependencies:** None (`EXP-2` is additive).

### `DEC-C14`
- **Decision:** `DEC-C14`
- **Title:** Reject Premature Multi-Backend Framework Abstractions in Warcraft I
- **Proposition:** REJECT introducing abstract multi-backend/plugin frameworks (`ICompilerBackend`, `IObjectFormatPlugin`, generic binary-rewriting frameworks) into `tools/wc1/`. Enforce architectural portability strictly via clean module boundaries and data-oriented contracts (`omf.py`, `match.py`, `build.py`, `cemu.py`).
- **Revision:** 1
- **Position:** `REJECT`
- **Reason:** Warcraft I has 1,010 in-scope functions on one target format (Watcom OMF32/LE). Speculative abstraction layers add maintenance cost and bug surface (as seen in duplicated OMF code) without adding real portability over well-factored interfaces.
- **Evidence:** Section 9 analysis; `tools/wc1/@a21772b`; Probe 5 (duplication cost).
- **Assumptions:** Future larger projects reuse the *architectural contracts* (Section 9.1), not a premature Warcraft plugin framework.
- **Dependencies:** `DEC-C09`.

---

## 12. Objections

### `OBJ-C01`
- **Severity:** `correctness/verification` (blocking for E0 production merge & E5 B3 rollout)
- **Exact proposition challenged:** That E0 `RegionMatch` (`experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`) and E5 Fix B3 (`experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`, `decisions.md@e6150b8` D1/D5) can verify real multi-string Watcom 10.0a `-ot` `CONST` segments via whole-segment byte equality or zero-gap `per_symbol` checking.
- **Source:** `experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`; `experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`; `docs/research/build-codegen/decisions.md@e6150b8` (D1, D5).
- **Supporting evidence & concrete counterexample:**
  - **Probe 3:** In `war.exe` `0x569d0..0x58440`, **157 of 293** fixup-bounded `CONST` strings have **non-zero 1994 compiler heap bytes** in their 1..3B 4-byte alignment gaps (e.g., `SaveSlotPath` `0x14740` at `0x56b1c`: `".net\0"` + `8d 75 e0` + `".sav\0"` + `08 00 e8` + `"save%d\0"` + `a5`).
  - **Probe 7d:** Compiling a real 2-string `-ot -5r` TU (`".net"`, `".sav"`) with live Watcom 10.0a emitted `2e6e657400 73002f 2e73617600` in Run 1 and `2e6e657400 760061 2e73617600` in Run 2 vs `war.exe` `2e6e657400 8d75e0 2e73617600`—3 non-deterministic byte diffs strictly inside `[5:8]`.
  - **Probe 7b:** E0/E2/E5 missed this only because 11/11 E0 local-data T3s have 1 string each and E2 `GAMEDLG`'s 2 strings happen to be `40B` and `36B` (`mod 4 == 0`).
- **Necessary assumptions:** Watcom 10.0a `-ot` aligns `CONST` strings to 4 bytes without zero-initializing the 1..3B pad (directly observed).
- **Practical consequences:** Shipping E0 or E5 without Invariant V4 (`DEC-C03`) will falsely reject almost every multi-string `-ot` CU (`SaveSlotPath`, etc.) and cause flaky non-deterministic match failures across runs.

### `OBJ-C02`
- **Severity:** `blocking architectural` + `correctness/verification`
- **Exact proposition challenged:** RFC §7.2 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) and `tools/wc1/emit.py:45-84@a21772b` (`replaced_interior_refs`) modeling Fix B2 solely as branches targeting the *interior* of a replaced cut (`s < t < e`, `t not in entries`).
- **Source:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (§7.2); `tools/wc1/emit.py:45-84@a21772b`; `tools/wc1/build.py@a21772b` (`check_t3_buildable`).
- **Supporting evidence & concrete counterexample:**
  - **Probe 1** proved two additional cross-piece `rel8` failure modes missed completely by RFC §7.2 and `replaced_interior_refs`:
    1. **Cut-spanning `rel8` (`11` binary-wide):** `IntroOpWaitSound` (`0x231d7 je`, `0x231e1 jne` -> `0x2316c` in `IntroOpPlaySound`) spans across `IntroOpSyncSound` (`0x23170`), causing `check_t3_buildable` to emit a **false positive** in M2 cleanup (`e1a4178`) and crashing NASM on Build A!
    2. **Cut-entry `rel8` (`14` binary-wide):** `EndCheckSurvive` (`0x2f718 jmp`, `0x2f722 je`, `0x2f72e jl`) targets `0x2f73c` (`MissionDefeat` **ENTRY**, `interior=False`), plus `0x28088 jl`/`0x2808d jg` -> `0x28093` ENTRY. Even fixing interior labels alone leaves `MissionDefeat` unbuildable!
- **Necessary assumptions:** NASM OMF32 cannot encode 8-bit external relocations (verified in E1).
- **Practical consequences:** Any B2 implementation that only handles cut-interior labels will still fail on `IntroOpSyncSound` (`0x23170`) and `MissionDefeat` (`0x2f73c`) and leave false positives in `check_t3_buildable`. Must be replaced with Unified Fix B2 (`DEC-C05`).

### `OBJ-C03`
- **Severity:** `implementation risk` + `correctness/verification`
- **Exact proposition challenged:** `docs/research/build-codegen/decisions.md@e6150b8` (Decision D6) and `E4-omf-extraction.md@e6150b8` treating `experiments/build_codegen/e4/omf_extract.py` as ready for near-term production adoption pending only minor `rev-e4-01` polish.
- **Source:** `docs/research/build-codegen/decisions.md@e6150b8` (D6); `experiments/build_codegen/e4/omf_extract.py@e6150b8` (`:258, :378-384, :766, :798-807, :823`).
- **Supporting evidence & concrete counterexample:**
  - **Probe 5a (live reproduction):** Feeding a valid cross-record OMF32 `THREAD` module causes `wc1.omf.parse_module` to parse `1` fixup cleanly while `e4.raw_fixups` crashes (`UnsupportedExtractionError: unsupported_construct: undefined THREAD`) because `Threads()` is reset per record at `:258` and `:823`.
  - **Probe 5b (code inspection):** `omf_extract.py:798-807` rebases ALL `PUBDEF`/`LPUBDEF` records by `lo <= off < hi` without checking `if pseg == ti:`, silently dropping/corrupting `_DATA`/`_BSS`/`CONST` publics whenever `lo > 0`.
  - **Code inspection (`:378-384`, `:766`):** Linear Capstone decode breaks on B1/inline jump tables, and `:766` omits E5's 64-fixup `FIXUPP32` chunking. Plus `rev-e4-01` F1–F4.
- **Necessary assumptions:** Production objects can have `lo > 0` with `_DATA` symbols, cross-record `THREAD`, >64 fixups/1024B, or jump tables.
- **Practical consequences:** Adopting E4 in M2 introduces silent symbol corruption and crashes while unlocking 0/98 M2 functions (`DEC-C08`).

### `OBJ-C04`
- **Severity:** `blocking architectural`
- **Exact proposition challenged:** `docs/research/build-codegen/summary.md@e6150b8` and `decisions.md@e6150b8` (§18.9 rollout priority) sequencing B3 (E5) and multi-function T4 (E6) ahead of or on the M2 completion critical path without accounting for the actual 98-function M2 blocker distribution on `main@a21772b`.
- **Source:** `docs/research/build-codegen/decisions.md@e6150b8`; `docs/research/build-codegen/summary.md@e6150b8`.
- **Supporting evidence & concrete counterexample:** `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/candidate_ledger.json@a21772b` proves `main@a21772b` sits at `912/1010 DONE`, and of the 98 remaining functions, **68** are blocked by atomic cross-module symbol migration + Wave 3R, **10** are ready `BULLET.C`, **7** are B1/B2, **5** are real ref-C bugs, and **8** are user-governance decisions. **B3, E4, E6, and E8 unlock 0 of the 98 remaining M2 functions** (`SaveErrorDialog 0x1aca8`, `FarmPanelChanged 0x28254`, `ScoreTickIncome 0x24e90` are already DONE as T4!).
- **Necessary assumptions:** Consilium charter mandate: "Do not optimize T3 count at the expense of genuine M2 completion."
- **Practical consequences:** Implementing B3/E4/E6/E8 before Stage 2 delays genuine M2 completion (`make goal` Gate 1) for zero DONE progress (`DEC-C07`).

### `OBJ-C05`
- **Severity:** `correctness/verification`
- **Exact proposition challenged:** E0 `matcher_proto.py:358-359@e6150b8` validating `FunctionMatch` branch closure against `[first_pub_base, first_pub_base + len(_TEXT))` instead of the target function's own `[base, base + fn_len)`.
- **Source:** `experiments/build_codegen/e0/matcher_proto.py:358-359@e6150b8`.
- **Supporting evidence & concrete counterexample:** `E2-context-alignment.md@e6150b8` (Cause B): caused **9 false `UNSUPPORTED: external_rel8`** rejections on ordinary intra-function short branches inside non-contiguous multi-function TUs where the code bytes were 100% identical to `war.exe`.
- **Necessary assumptions:** Multi-function diagnostic compilation can include non-contiguous functions.
- **Practical consequences:** Breaks `FunctionMatch` as a diagnostic tool on multi-function TUs until fixed by Invariant V2 (`DEC-C02`).

### `OBJ-C06`
- **Severity:** `unsupported factual claim`
- **Exact proposition challenged:** RFC §2.2.5 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) asserting that Watcom 10.0a always aligns functions to 4 bytes while OW2 aligns to 16 bytes.
- **Source:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (§2.2.5).
- **Supporting evidence & concrete counterexample:** `E2-context-alignment.md@e6150b8` (`alignment_matrix.json@e6150b8`) proved Watcom 10.0a aligns functions to **16 bytes** under `-4r -ot`, **4 bytes** under `-3r/-5r -ot`, and **1 byte** under `-os/-od`, while emitting `PARA` (16-byte) `_TEXT` `SEGDEF`s under all of them.
- **Necessary assumptions:** None (directly observed).
- **Practical consequences:** Misleads analysts into thinking `-4r` multi-function TUs match `war.exe`'s 4B layout, when `-5r` (not `-4r`) is actually required (`DEC-C13`).

### `OBJ-C07`
- **Severity:** `unsupported factual claim` + `blocking architectural`
- **Exact proposition challenged:** RFC §9.3 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) proposing `_DATA`/`_BSS` staircases and `call_locality_drop` as primary CU boundary recovery signals.
- **Source:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (§9.3).
- **Supporting evidence & concrete counterexample:** `E8-cu-boundaries.md@e6150b8` evaluated both across R4-independent ground-truth corpora: `_DATA`/`_BSS` staircase precision is **`0.250`** (Corpus A) / **`0.281`** (Corpus B1), and `call_locality_drop` precision is **`0.323`** (A) / **`0.179`** (B1)—worse than a coin flip (`>70%` false splits!).
- **Necessary assumptions:** None (empirically refuted).
- **Practical consequences:** Implementing §9.3 would fragment true CUs and misdirect consolidation; must be replaced with the E8 premise-carrying constraint graph (`DEC-C12`).

### `OBJ-C08`
- **Severity:** `correctness/verification`
- **Exact proposition challenged:** Production `tools/wc1/t3_audit.py@a21772b` claiming checkout-portable, fail-closed improved-T4 audit provenance, and `tools/wc1/oldcc.py@a21772b` omitting E7 D9 short-path protection.
- **Source:** `tools/wc1/t3_audit.py@a21772b` (`_default_system_headers`, `build_improved_audit_snapshot`, `_git`); `tools/wc1/oldcc.py@a21772b`.
- **Supporting evidence & concrete counterexample:** Probe 6 confirmed `_default_system_headers(repo_root)` ignores `repo_root` whenever `oldcc.root()` succeeds (breaking checkout-portability across worktrees), `_git()` returns `None` on failure instead of failing closed, and `build_improved_audit_snapshot` compares `tool_sig` against itself (independently identified in `research/model-calibration-engineering@cea804e`). Inspection of `tools/wc1/oldcc.py@a21772b` confirmed zero path-length staging/guard against Watcom 10.0a's ~129-char crash.
- **Necessary assumptions:** Audits and builds run across worktrees with varying checkout path lengths (like `/mnt/data/projects/warcraft-1-decompile-wt/...`).
- **Practical consequences:** Subtle provenance leaks across worktrees and intermittent Wine `wcc386` crashes in deep worktree paths; both fixed cheaply in Stage 0 (`DEC-C04`).

---

## 13. Open Questions and Required Experiments

| ID | Question | Falsification Criterion | Cheapest Decisive Probe | Decision Affected |
|---|---|---|---|---|
| **EXP-1** | Does Invariant V4 (5-condition 1..3B unreachable `CONST` alignment-gap rule) cleanly verify real multi-string `-ot` CUs with non-zero 1994 heap residue (`SaveSlotPath 0x14740`, `GAMEDLG`) while rejecting every crafted corruption? | Fails if `SaveSlotPath` fails `RegionMatch` or Build A `IDENTICAL` with natural C literals (`".net"`, `".sav"`, `"save%d"`), OR if ANY negative control (mutated literal byte, 4-byte gap, `_DATA` gap, pointer into gap byte) returns `MATCH`. | Prototype V4 in `matcher_proto` + `omf_b3` on `SaveSlotPath` (`0x14740`) + 6 negative controls (<15 min, 1 Build A link). | `DEC-C03`, `DEC-C10` (Stage 0 matcher & Stage 3 B3). |
| **EXP-2** | Do untested Watcom 10.0a presets `-5r -d1+ -zp1` (for `OpenArchive`/`mod_319c0`) and `-od -5r` (for existing `-od -4r` frames) recover additional T3 matches? | Fails if 0 new T3 matches or regressions occur across target functions. | Compile the ~20 target functions under `-5r -d1+ -zp1` and `-od -5r` via `wc1.oldcc` + E0 check (<1 min). | `DEC-C13` (preset table completeness). |
| **EXP-3** | Does Unified Fix B2 (NASM piece-boundary local-label `rel8` expression `short loc_<edge> + delta`) assemble cleanly with zero OMF32 relocations and link Build A `IDENTICAL` on ALL 3 B2 classes (B2-span `IntroOpSyncSound 0x23170`, B2-entry+interior+fallthrough `MissionDefeat 0x2f73c`, B2-interior `SelectionClickUnit 0x2efd0`)? | Fails if NASM rejects the expression, emits an OMF relocation, miscomputes displacement, or fails Build A SHA-256 `IDENTICAL`, OR if `--legacy` fails to reject it. | Targeted Build A link probe on `0x23170` and `0x2f73c` + `--legacy` negative control (<15 min). | `DEC-C05` (Stage 1 Unified Fix B2 unlocking +6 M2 DONE). |
| **EXP-4** | Can E6 `mf_cemu` soundly allow proven intra-function switch jump tables in `Isolated` mode and R2 `LogicalConstDataPtr` without breaking fail-closed isolation? | Fails if an inter-function indirect jump slips through, or if a raw integer masquerading as a `CONST` string pointer passes R2. | Extend E6 test suite with 1 real switch-bearing multi-function TU + 1 string-returning T4 + 4 negative controls (Stage 3 pre-gate). | `DEC-C11` (Stage 3C multi-function T4 gate). |
| **EXP-5 (M3)** | What is the exact inventory of `I16` relocatability blockers (hardcoded VAs, segment assumptions, ASM-only data anchors) preventing Build B (all-C relocatable `war.exe`)? | N/A (inventory required to scope Stage 4 / M3 accurately). | Static scan over `src/` + `analysis/symbols/` after Stage 2 M2 completion. | Stage 4 (M3 Build B & `data_layout.toml`). |

---

## 14. Probe and Reproduction Log

All probes were executed strictly read-only against the pinned baseline (`e6150b8`), read-only exports in `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main` (`main@a21772b`), and disposable scratch files in `/tmp/opencode/cn-gemini` using the pre-warmed Wine prefix `/mnt/data/projects/warcraft-1-decompile-wt/cons-c/build/oldcc/wineprefix` inside `nix develop`. Zero tracked files or shared assets were modified.

- **Common environment:**
  - Worktree: `/mnt/data/projects/warcraft-1-decompile-wt/cons-c` (`HEAD = e6150b856106ae113bb023300b956fff318da7ef`)
  - Exported `main`: `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main` (`a21772b8140b4b07012cde8da7da18ad3f6d56b6`)
  - Probe scripts preserved at: `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/{run_probes.py,run_probes2.py,run_probe7.py,run_probe7b.py}`
  - Short compiler temp dir: `TMPDIR=/tmp/opencode/cn-gemini`

### Probe 1 — Binary-Wide Cross-Function `rel8` and Interior `rel32` Census
- **Command:** `nix develop -c python3 -c "import pathlib; src = pathlib.Path('/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/run_probes.py').read_text(); exec(src.split('# --- PROBE 2')[0])"`
- **Exact Output Summary:**
  - Total cross-function `rel8` branches in `war.exe`: **43** (`29` targeting interior `tgt != tgt_fn`, **14** targeting entry `tgt == tgt_fn`, **11** spanning `>= 1` intervening function).
  - Total cross-function `rel32` branches targeting interior: **23**.
  - Game range (`0x104b0..0x3024e`): **25** cross-function `rel8` branches across **11** source functions and **10** target functions, notably:
    - Spanning `0x23170` (`IntroOpSyncSound`): `0x231d7 je` & `0x231e1 jne` in `IntroOpWaitSound` (`0x231cc`) -> `0x2316c` in `IntroOpPlaySound` (`0x2315c`).
    - Entry-targeting + interior-targeting + fallthrough on `0x2f73c` (`MissionDefeat`): `EndCheckSurvive` (`0x2f694`) has `0x2f718 jmp`, `0x2f722 je`, `0x2f72e jl` -> **`0x2f73c` ENTRY (`interior=False`)**, plus `0x2f6ed/0x2f6f7/0x2f70a/0x2f716/0x2f73a` -> `0x2f746` interior.
    - Spanning `0x16d34` (`DialogHighlightOn`): `0x16d50 je` in `DialogHighlightOff` (`0x16d48`) -> `0x16d31` in `DialogItemHitTest` (`0x16cc8`).
    - Spanning `0x28090` (`SelectionIsWorkersFalse`): 4 branches in `0x28074`/`0x28093` (including `0x28088 jl` & `0x2808d jg` -> `0x28093` ENTRY).
    - Adjacent interior `rel8`: `0x1e3c4 -> 0x1e3ac` (`0x1e380`), `0x2c206 -> 0x2c228` (`0x2c208`), `0x2e9db/0x2e9e6 -> 0x2e9c1` (`0x2e96c`), `0x2f0b9 -> 0x2f0a7` (`0x2efd0`), `0x1b019/0x1b028/0x1b037/0x1b046 -> 0x1b008` (`0x1af90`).
- **Limitation:** Relies on `wc1.analysis` decoded function boundaries (excludes indirect/computed jumps).

### Probe 2 — Terminating Instruction Census Against E3's `partial_matcher.py:669` Rule
- **Command:** `nix develop -c bash -lc 'TMPDIR=/tmp/opencode/cn-gemini python3 /mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/run_probes2.py'` (Section 2)
- **Exact Output:**
  - `In-scope functions NOT ending in ('ret', 'retf', 'jmp', 'iret', 'iretd'): 8`
  - `Main T3 functions NOT ending in ('ret', 'retf', 'jmp', 'iret', 'iretd'): 0`
  - Exact 8 functions: `0x10650 UnitApplyDamage (nop)`, `0x110a0 fn_110a0 (inc dword ptr [eax], data-in-code)`, `0x11530 fn_11530 (push es, data-in-code)`, `0x116a8 UnitCancelProduction (nop)`, `0x20258 NetSerialPushBytes (pop ebx, fallthrough)`, `0x208d4 NetModemAnswer (mov eax, eax)`, `0x28074 SelectionHasNoWorkers (nop)`, `0x2f694 EndCheckSurvive (jge 0x2f746, fallthrough into MissionDefeat)`.
- **Limitation:** Checks static last decoded instruction only; `call noreturn` would still be flagged on larger binaries.

### Probes 3 & 7 — `war.exe` `CONST` Alignment Padding Scan, E0/E2 Baseline Audit, and Live Watcom 10.0a `-ot -5r` Compile
- **Command:** `run_probes2.py` (Section 3) + `run_probe7b.py` under `nix develop` with `TMPDIR=/tmp/opencode/cn-gemini`.
- **Exact Output:**
  - Linear scan of `war.exe` `0x569d0..0x58440`: `288` strings, `61` all-zero 4B pads, **`161` non-zero bytes in `[s_end, next4)`**.
  - Fixup-bounded `CONST` strings: **`293` total**, `64` zero-padded, **`157` with NON-ZERO pad bytes** (e.g., `0x56ab8` `"Need lumber to finish repairs\0"` + `e8ee`; `0x56af4` `"Cannot create more units\0"` + `45f4e8`; `0x56b1c` `".net\0"` + `8d75e0`; `0x56b24` `".sav\0"` + `0800e8`; `0x56b2c` `"save%d\0"` + `a5` — owned by `SaveSlotPath 0x14740`, `src/mod_13f60/save_slot_path.c`).
  - E0 baseline `t3_reaudit.json` audit: **11/11** local-data T3s (`0x1a8e4`, `0x1a914`, `0x1a95c`, `0x1ab28`, `0x21554`, `0x21844`, `0x21c68`, `0x312f0`, `0x31360`, `0x31a80`, `0x32540`) each contain **exactly 1** string literal in `CONST` (0 inter-string gaps!).
  - E2 `GAMEDLG` `VersionMismatchDialog` (`0x1a8e4`) & `SaveVersionDialog` (`0x1a914`) have string lengths `40B` (`40 % 4 == 0`) and `36B` (`36 % 4 == 0`) — 0 gap bytes!
  - Live Watcom 10.0a `-ot -5r` compile of 2-string TU (`".net"`, `".sav"`):
    - Run 1: `2e6e657400 73002f 2e73617600` (diffs at `[5:8]`: `0x73/0x00/0x2f` vs `war.exe` `0x8d/0x75/0xe0`)
    - Run 2 (exact same C file!): `2e6e657400 760061 2e73617600` (diffs at `[5:8]`: `0x76/0x00/0x61` vs `war.exe` `0x8d/0x75/0xe0`) -> proves **non-deterministic uninitialized compiler heap memory**!
- **Limitation:** Tested under `-ot -5r` on Wine-hosted Watcom 10.0a; `-os` emits packed strings with 0 pad bytes (matching E5 `SaveErrorDialog`).

### Probe 4 — Extending E0 `matcher_proto` Re-Audit to All 20 New T3 Functions on `main@a21772b`
- **Command:** `run_probes2.py` (Section 4) running `experiments.build_codegen.e0.matcher_proto.match_module` against compiled objects of all 20 T3s added between `e14d5c0` (`519` T3s) and `main@a21772b` (`539` T3s).
- **Exact Output:** **20/20 `fn=MATCH reg=MATCH`**, all with `data_segs=0 lead=0` (`0x1132c`, `0x123cc`, `0x13c04`, `0x13c84`, `0x13dd0`, `0x13e94`, `0x15170`, `0x15230`, `0x15314`, `0x15558`, `0x19478 [ow2]`, `0x1a800`, `0x1af20`, `0x21df0`, `0x22a4c`, `0x22a98`, `0x29f40`, `0x2ab54`, `0x34060`, `0x348c0`). Combined with E0's 519/519 baseline = **539/539 (`100%`)** production T3s verified.
- **Limitation:** Does not re-verify the 519 baseline T3s already recorded in `t3_reaudit.json@e6150b8`.

### Probe 5 — Live Reproduction of E4 `omf_extract.py` Bugs
- **Command:** `run_probes2.py` (Section 5) constructing a minimal valid OMF32 module with a `THREAD` definition (`T0`) in one `FIXUPP32` record referenced by a fixup in the next `FIXUPP32` record, plus direct code inspection of `experiments/build_codegen/e4/omf_extract.py@e6150b8`.
- **Exact Output:**
  - `5a: wc1.omf.parse_module parsed cross-record THREAD fixups: 1`
  - `5a: e4.raw_fixups FAILED (CONFIRMED BUG): UnsupportedExtractionError: unsupported_construct: undefined THREAD`
  - Code-verified additional bugs: `omf_extract.py:798-807` (rebases all `PUBDEF`/`LPUBDEF` by `lo <= off < hi` without checking `pseg == ti`), `:378-384` (linear Capstone decode), `:766` (no 64-fixup chunking).
- **Limitation:** `5b` (`PUBDEF` corruption) verified by static code path analysis; trivial to turn into a 10-line unit test if Stage 3E is ever activated.

### Probe 6 — Verification of Calibration-Reported `t3_audit.py` R3 Bugs on `main@a21772b`
- **Command:** `run_probes2.py` (Section 6) inspecting `export-main/tools/wc1/t3_audit.py@a21772b`.
- **Exact Output:** Confirmed all 3 R3 bugs exist in `main@a21772b`: `_default_system_headers(repo_root)` (`pos=5956`) returns `Path(oldcc.root()) / "h"` ignoring `repo_root` whenever `oldcc.root()` succeeds; `_git(*args)` (`pos=26573`) swallows failures returning `None`; `build_improved_audit_snapshot` (`pos=34936`) does not validate against live `tool_sig`.
- **Limitation:** Did not inspect unmerged post-`main` commits on `feature/m2-mechanical-cleanup` (`28839d3a`) outside pinned `main@a21772b`.

---

## 15. Source Index

Every evidence-dependent claim in this document is pinned to an exact repository commit SHA or stable artifact ID:

- **Consilium Baseline (`research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`):**
  - `docs/research/build-codegen/{README.md,summary.md,decisions.md,ledger.json}@e6150b8` (integrated in `7233303`)
  - `docs/research/build-codegen/contracts/E{0..8}-contract.md@e6150b8`
  - E0 (`7c23d23`): `docs/research/build-codegen/E0-matcher-soundness.md@e6150b8`, `experiments/build_codegen/e0/{matcher_proto.py,test_e0_matcher.py}@e6150b8`, `docs/research/build-codegen/results/e0/{controls.json,t3_reaudit.json,summary.json}@e6150b8`
  - E1 (`b2965ba`): `docs/research/build-codegen/E1-shared-epilogue.md@e6150b8`, `experiments/build_codegen/e1/{run_e1.py,test_e1.py}@e6150b8`, `docs/research/build-codegen/results/e1/{summary.json,variants.json,build_a.json}@e6150b8`
  - E2 (`c30f3f5`): `docs/research/build-codegen/E2-context-alignment.md@e6150b8`, `experiments/build_codegen/e2/{run_e2.py,test_e2.py}@e6150b8`, `docs/research/build-codegen/results/e2/{alignment_matrix.json,loop_sensitivity.json,census_96.json,domino_probe.json,summary.json}@e6150b8`
  - E3 (`13963fb`): `docs/research/build-codegen/E3-partial-matching.md@e6150b8`, `experiments/build_codegen/e3/{partial_matcher.py,test_e3_partial.py}@e6150b8`, `docs/research/build-codegen/results/e3/summary.json@e6150b8`
  - E4 (`7edf63b`): `docs/research/build-codegen/E4-omf-extraction.md@e6150b8`, `experiments/build_codegen/e4/{omf_extract.py,test_e4_extract.py}@e6150b8`, `docs/research/build-codegen/results/e4/summary.json@e6150b8`
  - E5 (`ed21ca3`): `docs/research/build-codegen/E5-data-anchor-b3.md@e6150b8`, `experiments/build_codegen/e5/{omf_b3.py,test_e5_b3.py}@e6150b8`, `docs/research/build-codegen/results/e5/summary.json@e6150b8`
  - E6 (`bb3387b`): `docs/research/build-codegen/E6-multifunction-t4.md@e6150b8`, `experiments/build_codegen/e6/{mf_cemu.py,test_e6_mf_cemu.py}@e6150b8`, `docs/research/build-codegen/results/e6/summary.json@e6150b8`
  - E7 (`c946f38`): `docs/research/build-codegen/E7-compiler-calibration.md@e6150b8`, `experiments/build_codegen/e7/test_e7_calibration.py@e6150b8`, `docs/research/build-codegen/results/e7/summary.json@e6150b8`
  - E8 (`9ae6dce`, `06235f6`, `dc1d028`): `docs/research/build-codegen/E8-cu-boundaries.md@e6150b8`, `experiments/build_codegen/e8/{corpus.py,signals.py,test_e8_cu.py}@e6150b8`, `docs/research/build-codegen/results/e8/summary.json@e6150b8`
  - Adversarial review telemetry: `docs/telemetry/campaigns/2026-11-25-build-codegen/{report.md,reviews.csv}@e6150b8` and `summaries/{rev-e0-01,rev-e3-01,rev-e4-01,rev-e5-02,rev-e6-01,rev-e7-01,rev-e8-02,rev-e8-03}.md@e6150b8`
- **RFC Under Reconsideration (`architecture/build-codegen-rfc@6f319ac8ff780bb45ff028d006216016fc932a13`):**
  - `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (blob `e81b117a1ece4f90e8b5cf17c0085b9cfb441b19`)
- **M2 Blocker Analysis (`analysis/m2-completion-blockers@ca82750f4f8a5e7972aaf92aa38c6037a0305190`, merged at `e14d5c0`):**
  - `docs/research/m2-completion/{blocker-analysis.md,roadmap.md,dependency-groups.json}@ca82750`
- **Production Mainline (`main@a21772b8140b4b07012cde8da7da18ad3f6d56b6`, post E7 `3123a47` & M2 cleanup `dae45bd`):**
  - `docs/telemetry/campaigns/2026-11-27-e7-production/report.md@a21772b`
  - `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json}@a21772b`
  - `tools/wc1/{match.py,build.py,emit.py,omf.py,omfpatch.py,cemu.py,emu.py,t4spec.py,permuter.py,oldcc.py,t3_audit.py,m2_inventory.py,overnight.py,wave4.py,wave4a.py}@a21772b`
  - `src/mod_13f60/save_slot_path.c@a21772b`, `analysis/modules.toml@a21772b`
  - `docs/{GOAL.md,METHODOLOGY.md,ANALYST_GUIDE.md,HISTORY.md,STATUS.md}@a21772b`, `docs/subsystems/{build.md,codegen.md,compiler.md,modules.md}@a21772b`
- **Model Calibration Reference (`research/model-calibration-engineering@cea804e1c0f9fb78de29a2e51888860e6840c9a3`):**
  - `docs/research/model-calibration-engineering/{report.md,recommendations.md}@cea804e`
- **Private Probe Artifacts (Architect C runtime directory):**
  - `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/{run_probes.py,run_probes2.py,run_probe7.py,run_probe7b.py}`
