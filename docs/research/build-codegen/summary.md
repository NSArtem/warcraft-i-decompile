# Build & Codegen Infrastructure — Final Experimental Research Report (E0–E8)

- **Campaign ID:** `2026-11-25-build-codegen`
- **Repository:** `NSArtem/warcraft-i-decompile`
- **Campaign Branch:** `research/build-codegen-experiments` (HEAD before final consolidation commit: `9ae6dce53dfbe9568e52269afc485770c206c7ee`)
- **Evaluated RFC:** [`docs/architecture/rfc-build-codegen-infrastructure.md`](../architecture/rfc-build-codegen-infrastructure.md) (`architecture/build-codegen-rfc` @ `6f319ac8ff780bb45ff028d006216016fc932a13`)
- **Production Baseline (`main`):** `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da` (`1,010` in-scope functions: `899` DONE, `519` T3 across `514` C files, `385` T4, `6` unchecked ref, `100` no C)
- **Production Integrity:** **0 production files modified** (`git diff 6f319ac8 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty); serialized global `make verify` **PASS** (`2257 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`).

---

## 18.1 Executive Summary

All **9 experiments (E0–E8)** defined in the Build & Codegen Infrastructure RFC were implemented in isolated Git worktrees, adversarially verified by fresh independent Reviewers, and integrated (`--no-ff`) into `research/build-codegen-experiments`. Every integrated experiment passed its full test suite (**401/401 experimental + infrastructure tests passing, 0 skipped, 0 failed**) while preserving 100% baseline repository verification.

### Campaign Scorecard

| Exp | Title | Scientific Verdict | Key Quantitative Result | Independent Review | Integration Commit |
|---|---|---|---|---|---|
| **E0** | Matcher Soundness & 519-T3 Re-Audit | `CONFIRMED` | **55/55** controls pass (16 positive, 39 negative fail-closed); **519/519** existing T3 functions across 514 files pass `FunctionMatch` & `RegionMatch` (**0** false matches) | `rev-e0-01` (`RC`, 6 findings) → `rev-e0-02` (**`APPROVE`**) | `7c23d23` |
| **E1** | Shared Epilogue Reproduction | `CONFIRMED` | Both Group A (`DialogItemHitTest+On+Off`, `-oa -5r`) and Group B (`IntroOpPlaySound+Sync+Wait`, `-5r`) reproduce exact cross-function `rel8` epilogues in pure C and link **Build A `IDENTICAL`** (`0` diffs, `8,770/8,770` fixups) | `rev-e1-01` (`RC`, 1 finding) → `rev-e1-02` (**`APPROVE`**) | `b2965ba` |
| **E2** | Compilation-Context Sensitivity & Alignment | `PARTIALLY_CONFIRMED` | **0** same-flags instruction changes across 96-T3 census (`GAMEDLG 14 + PLAYFLIC 24 + STATUS 58`). Discovered Watcom 10.0a uses **16B** under `-4r -ot`, **4B** under `-3r/-5r -ot` (with PARA=16B `SEGDEF`), **1B** under `-os/-od`. Under `-5r`, **23/23** contiguous runs pass E0 `RegionMatch` (incl. **40-function `STATUS.C`** run) | `rev-e2-01` (`RC`, 3 findings) → `rev-e2-02` (**`APPROVE`**) | `c30f3f5` |
| **E3** | Partial Object Matching | `PARTIALLY_CONFIRMED` | `FarmPanelChanged` (`0x28254`) and `ScoreTickIncome` (`0x24e90`) pass `REGION_MATCH` inside mismatching-sibling TUs; shifted `CONST` passes via independent literal boundaries. **Refuted** standalone `DialogHighlightOff` (`0x16d48`, folded + outgoing `rel8`) | `rev-e3-01` (**`APPROVE`**) | `13963fb` |
| **E4** | Selective OMF32 Extraction Feasibility | `CONFIRMED` | Both `ScoreTickIncome` (`0x24e90`) and `FarmPanelChanged` (`0x28254`) extract from whole-TU Watcom 10.0a objects and link **Build A `IDENTICAL`** (`0` diffs, `8,770/8,770` fixups); controlled `A->C` (`EXTDEF` + bare `rel32`), E5 `CONST` anchor, >1024 B `LEDATA32` split (`1022+478`), and **8/8** negative controls (all 6 RFC §6.2 classes) pass | `rev-e4-01` (**`APPROVE`**) | `7edf63b` |
| **E5** | Data-Anchor Decoupling (`Fix B3`) | `CONFIRMED` | **9/9** complete Warcraft **Build A `IDENTICAL`** links (`0` diffs, `8,770/8,770` fixups): `SaveErrorDialog` decreasing anchor, native `-ot` explicit `_DATA` arrays, real 3-segment GAMEDLG (`_DATA`+`CONST`+`_BSS`), cross-record `F3/T3` `THREAD` fixture, all 4 frame modes (`FLAT`/`DGROUP`/`Target`/`EXTDEF`), per-symbol `CONST`; 0 `wc1_anchor_*` leaks | `rev-e5-01` (`TO` + path crash) → `rev-e5-02` (**`APPROVE`**) | `ed21ca3` |
| **E6** | Multi-Function T4 Verification (`wc1.cemu`) | `PARTIALLY_CONFIRMED` | **96/96** tests pass (Isolated/Group/Integrated, R2 logical pointer correspondence, callback ABI verification, **14/14** negative variants fail-closed). **Refuted** zero-FIXUPP premise on real `IntroFrame->IntroLoadCreditLines` (Watcom emits 1 `EXTDEF` FIXUPP; NASM fixture proves zero-fixup hook fallback) | `rev-e6-01` (`RC`, 2 HIGH) → `rev-e6-02` (**`APPROVE`**) | `bb3387b` |
| **E7** | Original Compiler Calibration (Watcom 10.0a) | `CONFIRMED` | **21,618** compiles (`519` T3 + `373` dep-clean T4 × 26 configs = `23,504` cells): **19** new T4 function matches, **14** whole-object/E0 `RegionMatch`es, **13 buildable T3s** (all 13 link together to **Build A `IDENTICAL`**, `532` fns / `527` files), **218** improved T4s; **0** existing T3 regressions switching `-4r -> -5r` (`417/417` identical) | `rev-e7-01` (`RC`, path crash) → `rev-e7-02` (**`APPROVE`**) | `c946f38` |
| **E8** | Original CU Boundary Evidence Validation | `PARTIALLY_CONFIRMED` | Evaluated **16** signals across 3 independent R4 corpora (`A` 64 pairs, `B1` 447 pairs / 112 verified extents, `B2` 25 pairs). **Refuted** `_DATA`/`_BSS` staircase splits (`0.250`/`0.281` prec) and call-locality drops (`0.323`/`0.179` prec); quantified `zero16` recall gap (`0.524` A / `0.027` B1); confirmed `shared_epilogue` (`6/6`, `0 FP`) as proven merge constraint | `rev-e8-01` (`TO` + B1 bug) → `rev-e8-02` (`RC`, pad drift) → `rev-e8-03` (**`APPROVE`**) | `9ae6dce` |

### The Single Biggest Discovery of the Campaign
Combining **E1 + E2 + E7** uncovered a unifying root cause behind much of Warcraft's historical codegen mystery: **Watcom 10.0a `-4r -ot` uses 16-byte inter-function alignment, whereas `-5r -ot` (and `-3r -ot`) uses 4-byte inter-function alignment while keeping `_TEXT` `SEGDEF` at PARA = 16 bytes.** That single compiler setting simultaneously explains:
1. Why `war.exe` exhibits 4-byte alignment *inside* compilation units alongside 16-byte `zero16` padding *between* `.obj` files;
2. Why switching `-4r -> -5r` incurs **0/417 regressions** on existing default-OPT T3 functions while immediately unlocking **13 buildable T3s** (linking to Build A `IDENTICAL`) and **218 improved T4s** (E7);
3. Why pure C reproduces **both Group A and Group B shared epilogues** without ASM (E1); and
4. Why **all 23/23 contiguous multi-function T3 runs** — including a **40-function contiguous `STATUS.C` object (`0x27b98..0x28050`)** — achieve E0 `RegionMatch` under `-5r` (E2).

---

## 18.2 Matcher Soundness & Verification Contract (E0)

- **Artifact:** [`E0-matcher-soundness.md`](E0-matcher-soundness.md), [`experiments/build_codegen/e0/`](../../../experiments/build_codegen/e0/), [`results/e0/`](results/e0/).
- **Gaps Closed:** The E0 prototype ([`matcher_proto.py`](../../../experiments/build_codegen/e0/matcher_proto.py)) reproduces and closes all three verified gaps in legacy `wc1.match`:
  1. **Leading `_TEXT` bytes** (e.g., pre-function switch jump tables before the first public symbol);
  2. **Reverse original-to-compiled LE fixup obligations** (catching missing relocations when compiled code emits a bare constant where `war.exe` has a loader fixup); and
  3. **Module-local runtime data pointer relocations** (checking both ordinary bytes and forward/reverse pointer fixups inside `CONST`/`_DATA`/`_BSS`, while strictly excluding non-loadable `$$SYMBOLS`/`$$TYPES` metadata).
- **Mandatory Correction R3 Enforcement:** Implements mutually exclusive verdicts (`MATCH`, `MISMATCH`, `UNSUPPORTED`, `ERROR`) with `UNSUPPORTED` taking precedence over `MISMATCH`, separate `FunctionMatch` vs `RegionMatch` scopes, and unrestricted full finding arrays (zero truncation).
- **Controls & Re-Audit:** After resolving 6 adversarial findings from `rev-e0-01` (diagnostic truncation, trimmed-tail branch targets, local symbol defs/metadata refs, extra CODE segments, out-of-bounds fixups, and CLI error exits), all **55/55 controls pass** (16 positive `MATCH`, 39 negative fail-closed: 25 `MISMATCH`, 14 `UNSUPPORTED`), **77/77 pytest tests pass**, and **519/519 existing T3 functions across 514 C files** return `MATCH` on both `FunctionMatch` and `RegionMatch` (**0 MISMATCH, 0 UNSUPPORTED, 0 ERROR**).
- **Important Qualification:** None of the 514 current baseline T3 objects contain leading jump tables or module-local data pointer fixups; confidence for those two checks comes from E0's real-image-derived synthetic/compiled controls rather than the baseline T3 population alone.

---

## 18.3 Compilation-Context Sensitivity, Alignment & Shared Epilogues (E1 & E2)

### E1 — Shared Epilogue Reproduction
- **Artifact:** [`E1-shared-epilogues.md`](E1-shared-epilogues.md), [`experiments/build_codegen/e1/`](../../../experiments/build_codegen/e1/), [`results/e1/`](results/e1/).
- **Empirical Scope:** 97 compiled variants / 196 function observations across Group A (`DialogItemHitTest`, `DialogHighlightOn`, `DialogHighlightOff`), Group B (`IntroOpPlaySound`, `IntroOpSyncSound`, `IntroOpWaitSound`), standalone controls, reversed-order controls, pair-only controls, and 5 flag sets.
- **Confirmed Results (R1 separated):**
  - **Group A (`-s -ot -oa -ol -5r -zp2`):** Pure C (zero ASM) reproduces exact original cross-function `rel8` epilogue branches (`74 f3` and `74 df` into `DialogItemHitTest`'s `ret`), passes E0 `FunctionMatch` & `RegionMatch`, and links **Build A `IDENTICAL`** (`0` byte diffs, `8,770/8,770` LE fixups).
  - **Group B (`-s -ot -ol -5r -zp2`):** Unmodified canonical C in original order reproduces exact `74 93` and `75 89` epilogue jumps *crossing an intervening function (`IntroOpSyncSound`)*, matching exact original offsets `0 / 0x14 / 0x70`, passing E0 `RegionMatch`, and linking **Build A `IDENTICAL`**.
  - **R6 Preservation (`74 f5` vs `74 f3`):** Exact +2 displacement delta fully explained: original has 2 filler bytes (`8b c0`) between `DialogItemHitTest`'s `ret` (`+0x69`) and `DialogHighlightOn` (`+0x6c`), whereas the supplied longer body ended on an aligned boundary (`+0x83` -> `+0x84`). Under `-4r`, 16-byte inter-function padding broke Group B's `rel8` displacements; `-5r` 4-byte padding restored exact offsets.

### E2 — Compilation-Context Sensitivity & Intra-TU Alignment
- **Artifact:** [`E2-compilation-context.md`](E2-compilation-context.md), [`experiments/build_codegen/e2/`](../../../experiments/build_codegen/e2/), [`results/e2/`](results/e2/).
- **Synthetic Alignment Matrix (28 objects, 12 Watcom 10.0a + 2 OW2 configs):**
  - Watcom 10.0a: `-4r -ot` → **16B** (`SEGDEF` PARA=16B); `-3r -ot` and `-5r -ot` → **4B** (`SEGDEF` PARA=16B); `-os` and `-od` → **1B** (`SEGDEF` BYTE=1B).
  - OW2: both `-4r -ot` and `-5r -ot` → **16B**.
- **96-T3 Census (`14 GAMEDLG + 24 PLAYFLIC + 58 STATUS`, 769 standalone + 225 group contexts = 2,097 observations):**
  - **Zero instruction-body changes** relative to same-flags standalone controls under native optimization (`0/96`).
  - Forced whole-area `-4r` consolidation retained **83/96** strict E0 `FunctionMatch` (losses driven by placement/data-anchor conflicts, 1 `-oa` flag mismatch on `StatusPanelDraw`, and non-contiguous bounds — not codegen drift).
  - Under **`-5r`**, **all 23/23 contiguous runs** achieved strict E0 `RegionMatch`, including a **40-function contiguous `STATUS.C` object (`0x27b98..0x28050`)**.
- **Domino-Sensitivity Probe (63 edits / 210 neighbor observations):** **0** neighbor instruction changes; **1** `CONST` data-anchor domino (`SaveVersionDialog` addend shifted `0x28 -> 0x3c` when an earlier neighbor's string length grew) — directly validating why E5 (`Fix B3`) is needed for safe multi-function data anchoring.

---

## 18.4 OMF32 Build Infrastructure: Partial Matching, Selective Extraction & Data-Anchor Decoupling (E3, E4, E5)

### E5 — Data-Anchor Decoupling (`Fix B3`)
- **Artifact:** [`E5-data-anchors.md`](E5-data-anchors.md), [`experiments/build_codegen/e5/`](../../../experiments/build_codegen/e5/), [`results/e5/`](results/e5/).
- **Verified Mechanism ([`omf_b3.py`](../../../experiments/build_codegen/e5/omf_b3.py)):** Emits all original data once in a single ASM provider with `GLABEL wc1_anchor_<addr>` aliases; rewrites compiled C data segment references to `EXTDEF wc1_anchor_<addr>` **only after running E0's full data-byte + bidirectional pointer relocation verification**; empties data `SEGDEF32`s and drops data `LEDATA`/fixups; renumbers surviving `EXTDEF`/`LEXTDEF`; expands cross-record `F0–F3`/`T0–T3` `THREAD` subrecords (including definitions on discarded data records).
- **Build A Verification:** **9/9 full Warcraft Build A links `IDENTICAL`** (`0` byte diffs, `8,770/8,770` LE fixups, `520` functions / `515` C objects, `1` ASM data piece):
  1. `war_s1.exe` — baseline + `SaveErrorDialog -os` (reproducing & bypassing legacy `"C objects' data anchors are not in code order"` between `DefeatDialog 0x56c0c` and `SaveErrorDialog 0x51ea6`);
  2. `war_native_ot_data.exe` — explicit `_DATA` char arrays under native `-ot` reproducing `0x22` stride;
  3. `war_s2_real_multi.exe` — real 3-segment GAMEDLG (`_DATA` + `CONST` + `_BSS`);
  4. `war_s3_thread.exe` — cross-record `F3`/`T3` `THREAD` fixture placed on discarded data records;
  5. `war_s4_{flat,dgroup,target,external}.exe` — all 4 OMF frame modes (`FLAT`, `DGROUP`, `Target`, `EXTDEF`);
  6. `war_per_symbol.exe` — full partition of verified `CONST` literals into per-symbol anchors.
- **Controls:** 5/5 synthetic 3-segment links identical; 60 parameterized `THREAD` tests; N1–N4 fail closed; **0** `wc1_anchor_*` leaks in `src/`, `analysis/`, `tests/`; **86/86 tests passing**.

### E3 — Partial Object Matching (`VerifiedRegion`)
- **Artifact:** [`E3-partial-matching.md`](E3-partial-matching.md), [`experiments/build_codegen/e3/`](../../../experiments/build_codegen/e3/), [`results/e3/`](results/e3/).
- **Verified Real Cases:**
  - `FarmPanelChanged` (`0x28254`, `[0x80, 0xc4)`): passes `REGION_MATCH` (`proven_standalone_region`) while sibling `UnitPanelStateChanged` (`0x281f4`) mismatches in 61 bytes; its call at `0x28291` carries an `EXTDEF` self-relative FIXUPP targeting DB address `0x281f4`.
  - `ScoreTickIncome` (`0x24e90`, `[0, 77)` with `sum = delta + score`): passes `REGION_MATCH` (trimming 3 verified alignment bytes) while siblings `RankName` (32 diffs) and `ScoreSetPage` (23 diffs) mismatch.
  - **Refuted Case:** `DialogHighlightOff` (`0x16d48`) under `-s -os -ol -4r -zp2` fails closed (`MISMATCH` / `blocked_by_sibling_dependency`) because Watcom folds `DialogHighlightOn_` and `DialogHighlightOff_` onto offset `0x5f` and its `je 0x16d31` branches outside the slice.
- **Synthetic Controls:** Shifted `CONST` pool passes via independently certified literal boundaries (`per_symbol_const`), while unproven mutable shifts, outgoing `rel8`, unresolved sibling targets, literal byte corruption, and false equal-string aliasing all fail closed (**24/24 tests passing**).

### E4 — Selective OMF32 Extraction Feasibility
- **Artifact:** [`E4-omf-extraction.md`](E4-omf-extraction.md), [`experiments/build_codegen/e4/`](../../../experiments/build_codegen/e4/), [`results/e4/`](results/e4/).
- **Verified Invariants ([`omf_extract.py`](../../../experiments/build_codegen/e4/omf_extract.py)):** Enforces RFC §6.1 *Post-Codegen Symbolic Relocation Equivalence*: E3 `RegionMatch` precondition, linear Capstone closure scan, double byte-invariance self-check (every non-relocated byte identical to both original and compiled slice — zero opcode/length/register/non-address-immediate mutations, zero `rel8` widening), `LEDATA32` <= 1024 B re-chunking before any straddling 4-byte fixup field, `THREAD` expansion, and reuse of E5's `omf_b3` for data anchors.
- **Verified Positives & Negatives (17/17 tests passing):**
  - **Real Build A `IDENTICAL` #1 (`ScoreTickIncome` `0x24e90`, `[0, 77)`):** `0` byte diffs, `8,770/8,770` LE fixups, verified defined by `c_306.obj` in `war.map` (not ASM fallback).
  - **Real Build A `IDENTICAL` #2 (`FarmPanelChanged` `0x28254`, `[0x80, 0xc4)`):** `0` byte diffs, `8,770/8,770` LE fixups, verified defined by `c_400.obj` in `war.map`, call to mismatching `UnitPanelStateChanged_` preserved as `EXTDEF` self-relative FIXUPP32.
  - **Controlled Positives:** `A -> C` across mismatching `B` (both Watcom `EXTDEF`+`FIXUPP32` and NASM bare `call rel32` -> `EXTDEF`+`FIXUPP32`) + E5 Fix B3 `wc1_anchor_20000` `CONST` literal -> oracle `IDENTICAL`; 1,500-byte `LEDATA32` with fixup at byte `1022` cleanly split into `1022 + 478` -> oracle `IDENTICAL`.
  - **All 8 Negative Controls (all 6 RFC §6.2 classes):** `N1_on` & real `N1_off` (`DialogHighlightOff` `0x16d48`) → `outgoing_rel8`; `N2` → `interior_target`; `N3` → `ambiguous_symbol`; `N4`/`N4b` → `data_layout_mismatch`; `N5` → `relocation_target_mismatch`; `N6` → `incomplete_closure`.

---

## 18.5 Multi-Function T4 Verification (`wc1.cemu`, E6)

- **Artifact:** [`E6-multifunction-t4.md`](E6-multifunction-t4.md), [`experiments/build_codegen/e6/`](../../../experiments/build_codegen/e6/), [`results/e6/`](results/e6/).
- **Verified Architecture ([`mf_cemu.py`](../../../experiments/build_codegen/e6/mf_cemu.py)):** Implements explicit `VerificationBoundary` (contiguous symbol ownership without trailing-code truncation), `DependencySubstitutionPolicy` (`orig_addr_stub`, `symbol_aware_reloc`, `c_entry_hook`), generator-based real compiled callback execution under Unicorn with strict watcall preserved-register (`ebx`/`ecx`/`edx`/`esi`/`edi`/`ebp`) and stack-cleanup ABI checks, and Mandatory Correction R2 strictly typed logical pointer correspondence (4 typed pointer slots, exact logical targets, preserved equality relations, zero redirection of verified C to original code).
- **Refuted Premise & Controls:** Empirically refuted the RFC zero-FIXUPP assumption on real `PLAYFLIC` `IntroFrame -> IntroLoadCreditLines` (Watcom 10.0a emits 1 self-relative `EXTDEF` FIXUPP; legacy `CModule` bypassed the stub due to `local_names` precedence). A supplemental NASM fixture proves `c_entry_hook` (`UC_HOOK_CODE`) works cleanly with zero call fixups and intact code bytes. **96/96 tests pass** (10 positive scenarios across Isolated/Group/Integrated modes, 14 negative control variants all failing closed, including trailing-code entry bypasses and callback ABI violations).

---

## 18.6 Original Compiler Calibration — Watcom C/C++ 10.0a (E7)

- **Artifact:** [`E7-compiler-calibration.md`](E7-compiler-calibration.md), [`experiments/build_codegen/e7/`](../../../experiments/build_codegen/e7/), [`results/e7/`](results/e7/).
- **Capability Database:** Probed 31 Watcom 10.0a options on a multi-pattern synthetic TU: **29/31 accepted** (`-6r` rejected `E1073`, `-ob` rejected `E1074`); **21** produced measurable runtime byte/relocation deltas.
- **Exhaustive Calibration Grid (`21,618` compiles; `519` T3 + `373` dep-clean T4 × 26 configs = `23,504` cells; 12 dep-dirty T4 files explicitly recorded as untested):**
  - Recovered **19 new T4 function matches**, **14 whole-object / E0 `RegionMatch`es**, and **13 immediately buildable T3 opportunities** (vs only `3 / 1 / 0` from the legacy 8 presets).
  - **Combined Build A Proof:** All **13** buildable T3 candidates link together with the 519 baseline T3s to **Build A `IDENTICAL`** (`532` functions from `527` C files, `0` byte diffs, `8,770/8,770` LE fixups).
  - **Score Improvements:** Strictly improves mismatch scores for **218** unique dep-clean T4 functions over declared flags (**+67** over legacy 8 presets; **239** vs fixed default).
  - **Zero-Regression Control:** Toggling only `-4r -> -5r` on fixed default loses **0/417** existing T3 matches (identical matched set).
  - **R6 Qualification:** All 14 historically named R6 functions have an observed `-5r` match (11 buildable, 3 function-only); `OpenArchive` matched under `c19` (`-5r -d1+ -zp2`) while declared `c24` uses `-zp1` (so `-5r -d1+ -zp1` remains explicitly untested).
  - **CU Compatibility (`cu_hypotheses.json`):** 84 empty CU intersections are explicitly recorded as non-inferred rather than forced.

---

## 18.7 Original CU Boundary Evidence Validation (E8)

- **Artifact:** [`E8-cu-boundaries.md`](E8-cu-boundaries.md), [`experiments/build_codegen/e8/`](../../../experiments/build_codegen/e8/), [`results/e8/`](results/e8/).
- **R4-Compliant Independent Corpora (strictly separated from exploratory game observations):**
  - **Corpus A (Synthetic Watcom 10.0a + `wlink` + NASM):** 22 CUs (19 C + 3 NASM), 65 functions, 64 pairs (21 boundaries, 43 same-CU), map-verified recipe ground truth covering all 7 adversarial edge cases.
  - **Corpus B1 (Real `war.exe` `clib3r.lib` / `cstrtx3r`):** Full-segment masked byte + non-self-relative relocation verification (enforced after `rev-e8-01` caught phantom `cstrtx32` overlap!) admitted **112 non-overlapping extents / 111 objects** (`447` pairs: 75 boundaries, 372 same-CU; rejected `cstrtx32` [455 diffs] and `vsprintf` [13 diffs]). Stratified sensitivity excluding the genuine 990-byte `intxa386` stub table: **186 pairs** (73 boundaries, 113 same-CU).
  - **Corpus B2 (Real `war.exe` vs `setup.exe`):** 25 boundary-only pairs (after filtering <12 B functions that caused 23 construction artefacts); **8/8** overlapping pairs agree with B1.
  - **Exploratory Game Range (`0x104b0..0x3024e`, 890 pairs, 58 chunks):** Kept strictly outside all precision/recall tables.

### Key Signal Validation Results

| Signal | Role | Corpus A (P / R) | Corpus B1 Full (P / R) | B1 No-`intxa386` (P / R) | Epistemic Class (RFC §9.2) |
|---|---|---:|---:|---:|---|
| `shared_epilogue` | Merge | **1.000** / 0.047 (2/2) | **1.000** / 0.011 (4/4) | **1.000** / 0.035 (4/4) | **Proven constraint** (rare) |
| `shared_const_string_literal` | Merge | **1.000** / 0.023 (1/1) | — / 0.000 | — / 0.000 | **Proven constraint** (rare, C only) |
| `non_16_aligned_start` | Merge | 0.800 / 0.465 | 0.836 / 0.944 | 0.618 / 0.805 | **Proven one-directional** (only if next obj is PARA) |
| `zero16` | Split | **0.846** / 0.524 (11/13) | **1.000** / 0.027 (2/2) | **1.000** / 0.027 (2/2) | **Strong conditional / candidate generator** (high recall gap) |
| `style_transition` | Split | 1.000 / 0.143 (3/3) | 1.000 / 0.027 (2/2) | 1.000 / 0.027 (2/2) | **Weak/Ambiguous** (low sample & recall) |
| `flag_set_S_disjoint` | Split | 1.000 / 0.176 (3/3) | n/a (0) | n/a (0) | **Weak/Ambiguous** (context-scoped `S(f)`) |
| `none16` | Split | 0.800 / 0.190 | **0.174** / 0.053 | 0.571 / 0.055 | **Unreliable** (candidate generator only; 66 in game range) |
| `data_bss_staircase_break` | Split | **0.250** / 0.333 (1/4) | **0.281** / 0.692 (9/32) | 0.281 / 0.692 | **Refuted / Unreliable** (fails RFC §14 criterion) |
| `call_locality_drop` | Split | **0.323** / 0.952 | **0.179** / 0.933 | 0.519 / 0.932 | **Refuted / Unreliable** |

---

## 18.8 Consolidated RFC Architectural Decisions

See the full decision register in [`decisions.md`](decisions.md). In short:
- **Adopt directly:** E0 matcher soundness (**D1**), E1 pure-C shared epilogues (**D3**), E5 Fix B3 data-anchor decoupling (**D4**), and Watcom 10.0a short-path / padding-normalized hygiene (**D9**).
- **Adopt with empirical revisions:** E7/E2 additive `-5r` presets & corrected 16B/4B/1B alignment model (**D2**), E3 region-scoped matching (**D5**), E4 conservative OMF32 extraction gated by `rev-e4-01` F1–F4 hardening (**D6**), and E6 multi-function `wc1.cemu` using `symbol_aware_reloc` + R2 logical pointers (**D7**).
- **Redesign per E8:** Replace weighted CU heuristic scoring with a premise-carrying constraint graph (**D8**).

---

## 18.9 Implications for M2 Completion & Recommended Production Rollout Order

If the project owner approves moving from research to production PRs on `main`, the highest-ROI, lowest-risk sequence is:
1. **PR 1 — Matcher Soundness & Short-Path Hygiene (D1 + D9):** Land E0's leading-`_TEXT`, reverse-LE, and local-data-pointer checks in `wc1.match`, plus short-path/short-`TMPDIR` guards in `wc1.oldcc`. Zero T3 regressions guaranteed (`519/519`).
2. **PR 2 — Additive `-5r` Presets (D2):** Add `-5r` (`c06`, `c07`, `c19`) presets to `wc1.match`/`wc1.permuter`/`wc1.wave4`. Immediately unlocks **+13 buildable T3 promotions** (`519 -> 532`, Build A `IDENTICAL`), improves **218** T4s for Wave 4B search, and unlocks pure-C Group A & Group B shared epilogues (**+5–6 more T3s** via E1).
3. **PR 3 — Data-Anchor Decoupling Fix B3 (D4):** Land E5's single-ASM-data-provider + `wc1_anchor_*` + `THREAD` expander in `wc1.omfpatch`/`wc1.build`/`wc1.emit`, unblocking `SaveErrorDialog` and removing data-order coupling for all future multi-function CUs.
4. **PR 4 — Multi-Function `wc1.cemu` (D7):** Land E6's `VerificationBoundary`, `DependencySubstitutionPolicy`, callback ABI verification, and R2 logical pointer correspondence for multi-function T4 development.
5. **PR 5 (Optional / As Needed) — Partial Matching & Conservative OMF Extraction (D5 + D6):** Land E3 + hardened E4 (`rev-e4-01` F1–F4) only if remaining M2 blockers still have mismatching siblings that cannot be matched natively under `-5r`.
6. **PR 6 — Constraint-Graph CU Advisor (D8):** Expose E8's premise-labeled signals (`zero16`, `shared_epilogue`, `S(f)`, `none16` candidates) as analyst-facing diagnostics without automated heuristic splitting.

---

## 18.10 Reproducibility & Final Verification Record

Verified on `research/build-codegen-experiments` at `9ae6dce53dfbe9568e52269afc485770c206c7ee` (2026-11-26):
- **Production diff check:** `git diff 6f319ac8 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` → **empty**.
- **Experimental & infra suites (`401 passed, 0 failed, 0 skipped`):**
  - `_infra/test_infra.py`: `6 passed` (`0.05 s`)
  - `e0/test_e0.py`: `77 passed` (`2.83 s`)
  - `e1/test_e1.py`: `18 passed` (`11.76 s`)
  - `e2/test_e2.py`: `27 passed` (`8.00 s`)
  - `e3/test_e3.py`: `24 passed` (`5.82 s`)
  - `e4/test_e4.py`: `17 passed` (`28.81 s`)
  - `e5/test_e5.py`: `86 passed` (`27.00 s`)
  - `e6/test_e6.py`: `96 passed` (`21.96 s`)
  - `e7/test_e7.py`: `20 passed` (`8.34 s`)
  - `e8/test_e8.py`: `30 passed` (`175.92 s`)
- **Serialized global `make verify` (`verify-f2cf504d1b80`, `83.41 s`, `exit_code=0`):**
  - `wc1.symbols`: `1370 functions, 954 data symbols`
  - `wc1.roundtrip`: `mismatching insns=0 image_identical=True` (`366 raw of 64173`)
  - `wc1.match --all`: `514 files, 0 failed`
  - `wc1.match --compile-check`: `879 files x 2 compilers, 0 failures`
  - `wc1.build`: `519 functions from 514 C files (514 placed in sequence, 0 legacy layout)` → **`IDENTICAL (loaded image, entry, stack, fixups)`**
  - `pytest -q -n auto tests`: **`2257 passed, 11 skipped, 5 xfailed in 68.23s`**
