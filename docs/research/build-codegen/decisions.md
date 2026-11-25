# Build & Codegen Infrastructure — RFC Architectural Decision Register

- **Campaign:** `2026-11-25-build-codegen` (`research/build-codegen-experiments`)
- **RFC Evaluated:** [`docs/architecture/rfc-build-codegen-infrastructure.md`](../architecture/rfc-build-codegen-infrastructure.md) (`6f319ac8`)
- **Production Changes Made:** **None** (`git diff 6f319ac8 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty). All recommendations below are decision-ready proposals for subsequent production implementation PRs.

---

## 1. Decision Summary Matrix

| ID | RFC Topic / Component | Experiments | Verdict | Recommended Production Action |
|---|---|---|---|---|
| **D1** | Strengthened Matcher (`FunctionMatch` / `RegionMatch`, leading `_TEXT`, reverse LE obligations, local data pointer relocations, unrestricted multi-finding diagnostics) | E0 | **ADOPT** | Promote E0 matcher semantics into `tools/wc1/match.py` as Gate 0 before any multi-function or extraction build features. Zero regressions across all 519 existing T3 functions. |
| **D2** | Additive Watcom 10.0a `-5r` (Pentium) & `-5r -d1+` Presets + Alignment Model | E1, E2, E7 | **ADOPT (REVISED)** | Add `-5r` (`-s -ot -ol -5r -zp2`, `-s -ot -oa -ol -5r -zp2`, `-s -ot -ol -5r -d1+ -zp2`) as additive presets in `wc1.match`/`wc1.permuter`/`wc1.codegen_survey`. **Revise RFC alignment claim:** Watcom 10.0a uses 16B under `-4r -ot`, **4B** under `-3r/-5r -ot` (with PARA=16B `SEGDEF`), and 1B under `-os/-od`. Zero existing T3 regressions (`417/417` identical). Immediately unlocks **13 buildable T3s** + **40-function contiguous `STATUS.C` RegionMatch** + **Group A & B shared epilogues**. |
| **D3** | Pure-C Shared Epilogue Reproduction (no inline ASM) | E1 | **ADOPT** | Compile shared-epilogue groups in original order inside one TU with `-5r` (Group A: `-oa -5r`; Group B: `-5r`). Both link Build A `IDENTICAL` (`0` byte diffs, `8,770/8,770` LE fixups). No ASM stubs or `rel8` widening needed. |
| **D4** | Data-Anchor Decoupling (`Fix B3` — single ASM data provider + `wc1_anchor_*` aliases + full `THREAD` expansion) | E5 | **ADOPT** | Promote E5's Fix B3 into `tools/wc1/omfpatch.py` and `tools/wc1/build.py` / `emit.py` **gated behind E0's full data-byte + bidirectional pointer verification** and full cross-record `F0–F3`/`T0–T3` `THREAD` expansion. Eliminates the code-order data-anchor blocker (unblocks `SaveErrorDialog` and arbitrary multi-function `CONST`/`_DATA`/`_BSS` consolidation). |
| **D5** | Region-Scoped Partial Matching (`VerifiedRegion`) | E3 | **ADOPT (SCOPED)** | Promote E3's region-scoped matcher for clean multi-function TUs (`FarmPanelChanged`, `ScoreTickIncome`, verified shifted `CONST` literals), strictly fail-closed on outgoing `rel8`, folded symbols, unproven mutable shifts, and unverified sibling targets. **Refuted case:** standalone `DialogHighlightOff` (`0x16d48`) under `-os -4r` is genuinely unmatchable standalone and MUST be compiled as a joint Group A region (D3). |
| **D6** | Selective OMF32 Slice Extraction (`VerifiedRegion` -> linkable `.obj`) | E4 | **ADOPT (CONDITIONAL)** | Feasible and proven Build A `IDENTICAL` (`ScoreTickIncome`, `FarmPanelChanged`, `A->C` intra-TU `call rel32`, E5 `CONST` anchors, >1024 B `LEDATA32` splitting). Adopt **only as a conservative interim bridge** for multi-function TUs with mismatching siblings, **after** applying the 4 Low production-hardening guards from `rev-e4-01` (F1–F4 below). Prefer native whole-TU `-5r` matching (D2/D3) whenever siblings match. |
| **D7** | Multi-Function T4 Verification (`wc1.cemu` Isolated / Group / Integrated + R2 Logical Pointer Correspondence) | E6 | **ADOPT (REVISED)** | Promote E6's explicit `VerificationBoundary`, `DependencySubstitutionPolicy`, callback ABI preservation checks, contiguous symbol ownership, and R2 typed logical pointer correspondence into `tools/wc1/cemu.py`. **Revise RFC premise:** Watcom 10.0a emits `EXTDEF` FIXUPP for intra-TU calls (`IntroFrame -> IntroLoadCreditLines`), so `symbol_aware_reloc` handles real C calls while `c_entry_hook` remains a defense-in-depth mechanism for zero-fixup calls. |
| **D8** | Original CU Boundary Recovery Model | E8 | **REVISE SIGNIFICANTLY** | **Reject weighted heuristic scoring and reject automatic splitting from `_DATA`/`_BSS` staircases or call-locality drops** (both refuted on independent ground truth). Adopt a **premise-carrying constraint graph**: treat `shared_epilogue` (`6/6`, `0 FP`) and `shared_const_string_literal` (`1/1`, `0 FP`) as rare proven merge constraints, `non_16_aligned_start` as a one-directional constraint (valid only when next object requests PARA alignment), and `zero16`/`none16`/`S(f)` as analyst-facing candidate generators with explicit recall-gap caveats. |
| **D9** | Watcom 10.0a Short-Path Compilation Hygiene (Toolchain Discovery) | E2, E5, E7, E8 | **ADOPT (MANDATORY)** | **Cross-cutting empirical finding:** Watcom 10.0a `wcc386.exe` access-violates when source or `-i=` paths exceed ~128–130 chars, and emits uninitialized heap residue in `CONST` alignment gaps. Production `wc1.oldcc` and test harnesses MUST keep compiler-facing paths and `TMPDIR` short (`<= 112` chars) and hash loadable/semantic records rather than raw `THEADR`/`COMENT`/uninitialized-pad bytes. |

---

## 2. Empirically Refuted RFC Premises (Honest Negative Results)

1. **Refuted (E2): "Watcom 10.0a always uses 4-byte inter-function alignment (unlike OW2's 16-byte)."**
   - *Truth:* Watcom 10.0a uses **16-byte** alignment under `-4r -ot`, **4-byte** under `-3r -ot` and `-5r -ot` (while keeping `_TEXT` `SEGDEF` at PARA=16B), and **1-byte** under `-os` or `-od`. OW2 uses 16-byte under both `-4r` and `-5r`. This single discovery explains why `-5r` simultaneously reproduces Warcraft's 4-byte intra-CU spacing *and* 16-byte inter-CU `zero16` boundaries!
2. **Refuted (E6): "Watcom 10.0a emits zero FIXUPP records for intra-TU calls (`IntroFrame -> IntroLoadCreditLines`), requiring code-hook substitution for real C."**
   - *Truth:* Watcom 10.0a emits **1 self-relative `EXTDEF` FIXUPP** for `IntroLoadCreditLines_`. Legacy `CModule` bypassed the stub because `local_names` took priority over external stubs — solvable cleanly at relocation time (`symbol_aware_reloc`). Entry-hook substitution (`UC_HOOK_CODE`) was still verified on a zero-fixup NASM fixture.
3. **Refuted (E3 & E4): "`DialogHighlightOff` (`0x16d48`) is standalone-matchable and extractable from `dialog_hit_test_reference.c` under `-s -os -ol -4r -zp2`."**
   - *Truth:* Under `-os`, Watcom 10.0a folds `DialogHighlightOn_` and `DialogHighlightOff_` onto identical offset `0x5f`, and its original `je 0x16d31` (`74 df`) jumps outside the slice into `DialogItemHitTest`'s epilogue. E3 and E4 correctly reject it fail-closed (`outgoing_rel8` / `blocked_by_sibling_dependency`); E1 proves the entire 3-function Group A reproduces cleanly in pure C under `-oa -5r`.
4. **Refuted (E8): "Private `_DATA`/`_BSS` staircases and call/reference locality drops are reliable CU boundary split signals."**
   - *Truth:* On independent ground truth (Corpus A synthetic + Corpus B1 full-segment-verified `clib3r.lib`), `data_bss_staircase_break` achieved precision **0.250 (A) / 0.281 (B1)** (explicitly hitting RFC §14's falsification criterion), and `call_locality_drop` achieved precision **0.323 (A) / 0.179 (B1)** (`0.519` without `intxa386`). Neither may create boundaries automatically.
5. **Refuted (E5): "Real baseline Warcraft T3 objects contain native `THREAD` subrecords."**
   - *Truth:* Scanning all 514 baseline T3 objects + `gamedlg_data.obj` found **0 native `THREAD` subrecords**. Full cross-record `F0–F3`/`T0–T3` expansion (including definitions on discarded data segments) is still mandatory defensive infrastructure and was proven via controlled real-object `THREAD` fixtures + 60 parameterized tests.
6. **Refuted (E5): "Adding a neighboring function in native `-ot` fixes `SaveErrorDialog`'s `CONST` string stride (`0x24` -> `0x22`)."**
   - *Truth:* Native `-ot` aligns pooled `CONST` literals to 4 bytes (`0x24` stride) even in multi-function context. Reproducing `0x22` requires either `-os` (canonical literal source) or explicit initialized `char[]` arrays in `_DATA` under `-ot` (both proven Build A `IDENTICAL`).

---

## 3. Production-Hardening Prerequisites (Captured from Independent Reviews)

Before promoting any experimental prototype into `tools/wc1/`, address these non-blocking Low/Info items recorded by our independent reviewers:

1. **From `rev-e4-01` (E4 selective extractor):**
   - **F1:** Never accept an unvalidated caller-constructed `VerifiedRegion` dataclass without checking provenance/running `evaluate_region` (narrow API to `Evaluation` or minted proof object).
   - **F2:** Compute and log the post-`apply_data_plan` loadable digest alongside the pre-plan digest.
   - **F3:** Assert `0 <= doff < 1024` inside `Fix.encode` so any chunking regression fails closed rather than silently mutating `loc`.
   - **F4:** Handle 16-bit "big" (`64 KiB`, `attr bit 1`, length `0`) `SEGDEF` records explicitly during OMF16->OMF32 widening (map to `0x10000` or reject fail-closed).
2. **From `rev-e5-02` (E5 Fix B3):**
   - Keep `THEADR`/`COMENT`/`$$SYMBOLS`/`$$TYPES` path metadata clearly distinguished from loadable segments when reporting object digest identity.
   - Use randomized/private temp mirror directories (instead of predictable `/tmp/wc1e5-<hash>`) and call `oldcc.kill_wineserver` on outer helper timeouts too.
3. **From `rev-e0-02`, `rev-e6-02`, `rev-e8-03`:**
   - Never admit single-function `clib_sig` hits as CU extents without full-segment masked byte + non-self-relative relocation verification (E8 Round 1 lesson).
   - Keep `TMPDIR` short (`/tmp/wc1-...`, <= 32 chars) in `wc1.oldcc`, pytest harnesses, and build runners so Watcom 10.0a never hits its ~129-char path-buffer access violation.
   - Normalize or exclude compiler-inserted uninitialized `CONST` pad bytes when hashing Watcom 10.0a data outputs across environments (E2/E8 lesson).
