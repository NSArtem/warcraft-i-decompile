# Build & Codegen Infrastructure — Architecture Consilium
## Round 1 — Cross-Review (Architect C — Gemini)

- **Author:** Architect C — Gemini (`Gemini 4 Neon (High)`, harness `agy 1.5.17`)
- **Consilium Baseline (unchanged):** `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`
- **RFC Under Reconsideration:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`
- **Evidence Revisions Processed:** `EV-1` (`main@a21772b8`), `EV-2` (`d5d4d2c6`), `EV-3` (`main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`, Secretary-verified `2505 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`)
- **Reviewed Round 0 Positions (verified SHA-256):**
  - `00-PROPOSITION-INDEX.json` (`1ade8e0e1d3c20b924386f67407d808f28ec0f6eb958a92c70bf27ba1d76558`)
  - Architect A — GPT (`01-architect-gpt-opening.md`, `22477c0cf5f8f211d459c5ec72f26cdb7b0c24903bc6dc5e659f696b6b53b7c1`)
  - Architect B — Claude (`02-architect-claude-opening.md`, `9905f1b405acd6e3bef445fd697d255de6aebb0f29d10d2c328035aadc047203`)

---

## 1. Agreements

### 1.1 Agreements That Cut Against or Materially Extend My Round 0 Position

1. **T4 paired-execution writable-state asymmetry (`DEC-B07`, `OBJ-B06`, Architect B P4 — strongly confirmed & extended by my R1-Probe 2):**
   - My Round 0 (§8) repeated `AGENTS.md`'s characterization of all 5 xfailed T4 functions as genuine reference-C divergences. Architect B proved that `tools/wc1/cemu.py:349-391@a21772b` (`run_pair`) restores only `watch` ranges between original and C runs, making `IntroOpWaitSound` (`0x231cc`) fail even for byte-exact C.
   - My **R1-Probe 2** tested **all 5** xfailed functions under full writable-RAM restoration and proved that **3 of the 5** (`IntroOpWaitSound 0x231cc`, **`IntroRunScript 0x23668`**, **`IntroPlay 0x23ae0`**) are harness state-asymmetry artifacts that **pass 100% verbatim on existing `player_reference.c`**, while only **2** (`IntroOpStartCredits 0x23530` and `EndScreen 0x2fcfc`) are genuine reference-C bugs! I will revise my Round 0 Stage 0/Stage 2 in Round 2 to elevate `DEC-B07` (with hardening in §6.3) onto the M2 path.
2. **Legacy OMF parser lossiness & `wc1.compare` loader-attribute blindness (`DEC-A02`, `DEC-A03`, `OBJ-A02`, `OBJ-A03`, Architect A Q3):**
   - My Round 0 did not examine `tools/wc1/compare.py` or `tools/wc1/omf.py` for checksum/frame lossiness. Direct code inspection on `main@17733f9` (R1-Probe 3) confirmed both findings verbatim: `omf.py` performs zero checksum validation (`0` hits) and drops explicit `DGROUP` vs `FLAT` `FRAME` distinctions, while `compare.py:24-27,45-47` prints `o.flags` (`0x2045` / `0x2043`) without checking them and omits `src_type` (`7`) from its fixup comparison tuples. I will incorporate strict raw-OMF admission and `wc1.compare` loader-attribute hardening into Stage 0 in Round 2.
3. **Gate-2 governance prerequisite for partial-region T3 / E3 / E4 (`DEC-B09`, `OBJ-B04`, Architect B):**
   - Neither my Round 0 nor Architect A caught that `tools/wc1/match.py:368-390` (`match --all`) fails any `src =` file containing a mismatching public, making partial-region `src =` a Gate-2 semantics change requiring explicit owner approval under `AGENTS.md`. Fully accepted.
4. **Minimal M2 entity set—no standalone `CandidateRegion` type or persistent provenance DB (`DEC-B14`, `OBJ-B09`, Architect B):**
   - My Round 0 (§3.1/§4.1) proposed a separate `CandidateRegion` class in Stage 1. Architect B persuasively argues that for M2, candidate inputs are simply arguments to `verify_region()`, so only immutable matcher-minted `VerifiedRegion` and one derived `PlacementPlan` need concrete production types, keeping persistent `evidence_digest` and `compilation_units.toml` deferred until a real consumer exists.
5. **Keep `-4r` as single-file global default with additive E7 presets; avoid overclaiming `-5r` as the unique original flag (`DEC-A09`, `DEC-B10`, `DEC-B11`, `OBJ-B07`):**
   - My Round 0 (§2.8, `DEC-C13`) overstated `-5r` as the predominant 1994 build flag. E7 records `51` `only_4r` T3s (due to untested `-5r -od`/debug variants) and `-3r` also produces 4-byte spacing. I accept `DEC-B10` and `DEC-B11`: keep `-4r` as the single-file default, keep E7 presets additive, keep `H1/H2/H3` open, and state `-5r` strictly as the empirically validated alignment-matching preset for contiguous `-ot` runs.
6. **Downgrading `shared_const_string_literal` from unconditional Class 1 to premise-dependent Class 2 (Architect A §7 & Architect B §7):**
   - My Round 0 (`DEC-C12`) placed `shared_const_string_literal` in Class 1 (`MUST_MERGE`). Both A and B rightly note E8 had only 1 synthetic positive (0 game/B1 positives) and that an explicit `extern const char` or linker pooling could produce cross-object sharing. I will downgrade it to premise-dependent Class 2 in Round 2.
7. **Precision fix on NASM `-f obj` vs OMF `LOBYTE` (`OBJ-B08`, Architect B):**
   - Confirmed: the observed error is NASM's `-f obj` backend (`"OBJ format can only handle 16- or 32-byte relocations"`), not an OMF format impossibility; `wlink` self-relative `LOBYTE` support is untested.
8. **EV-3 update on `t3_audit.py` R3 bugs (partially resolving my Round 0 `DEC-C04` / `OBJ-C08`):**
   - On `main@17733f9` (EV-3), all 3 `t3_audit.py` R3 provenance defects I flagged at `a21772b` have been fixed and verified (`2505 passed`), and the historical `t4_improved_audit.json` snapshot was revalidated (`0/202` fresh, confirming `DEC-A09`). Conversely, `tools/wc1/oldcc.py` is unchanged (`git diff a21772b 17733f9 -- tools/wc1/oldcc.py` is empty), so the D9 short-path guard remains an active production defect.

### 1.2 Shared Three-Way Architectural Agreements

- **M2 completion priority (`DEC-A01`, `DEC-B01`, `DEC-C07`):** 98 remaining not-DONE functions (`main@17733f9` still `912/1010 DONE`); Fix B3 (E5), selective extraction (E3/E4), full E6 Group/Integrated, and CU recovery (E8) move **0 DONE** today and belong post-M2.
- **Three-level verification separation & single planner (`DEC-A02`/`A03`, `DEC-B02`/`B03`, `DEC-C01`/`C02`/`C05`):** Local `FunctionMatch` != closed `RegionMatch` (`VerifiedRegion`) != integrated `BuildAPlacementPlan`; `check_t3_buildable` and `wc1.build`/`emit` must share one planner.
- **Fix B1 (`DEC-A04`, `DEC-B05`, `DEC-C05`):** Leading-byte region base `first_entry_addr - first_entry_off` gated on E0 leading-byte verification (`ChooseCampaignDialog` `0x157e8`, proved Build A `IDENTICAL` in Architect B P6).
- **Preferred E1 whole-TU co-compilation + Unified Fix B2 fallback (`DEC-A05`, `DEC-B04`, `DEC-B06`, `DEC-C05`, `DEC-C06`):** Prefer joint `-5r` TUs where all members match (Group B proved Build A `IDENTICAL` in Architect B P3); use Build A in-place cross-piece `rel8` bridge only as incremental debt (forbidden under `--legacy`).
- **Analyst-facing premise-carrying CU constraint graph (`DEC-A10`, `DEC-B13`, `DEC-C12`):** Reject `_DATA`/`_BSS` staircases, `call_locality_drop`, weighted scoring, empty-`S(f)` auto-splitting, and automatic consolidation.
- **No `experiments/` imports in production (`DEC-B15`) & no premature plugin/DB frameworks (`DEC-A10`, `DEC-B14`, `DEC-C14`).**

---

## 2. Substantive Disagreements

### 2.1 Uninitialized Watcom 10.0a `CONST` Alignment Padding Omitted From E0 & B3 Contracts
- **Challenged propositions:** `DEC-A06` (GPT: *"Admit B3 initially for fully verified whole segments only"*), `DEC-B02` (Claude: adopting E0 semantics directly without fixing `CONST` padding), `DEC-B08` (Claude: keeping RFC §8.2 constraints 1–5 as-is for B3).
- **Dispute type:** Factual + architectural (correctness/verification).
- **Evidence:** Round 0 Probes 3 & 7 (`run_probes2.py`, `run_probe7b.py`) on `war.exe` `0x569d0..0x58440` and live Watcom 10.0a `-ot -5r`; `experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`; `experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`; `06235f6` (`rev-e8-02` `CONST` pad digest drift).
- **Counterexample / failure mode:** In `war.exe`, **157 of 293** fixup-bounded `CONST` strings contain **non-zero 1994 compiler heap residue** in 1..3-byte 4-byte alignment gaps (e.g., `SaveSlotPath 0x14740` at `0x56b1c`: `".net\0"` + `8d 75 e0` + `".sav\0"` + `08 00 e8` + `"save%d\0"` + `a5`). Live Watcom 10.0a `-ot -5r` compiling `(".net", ".sav")` emitted **different uninitialized heap bytes across two consecutive runs** (`73 00 2f` vs `76 00 61` vs `war.exe` `8d 75 e0`). E0 (`matcher_proto.py:333`), E2 (`GAMEDLG` `40B`/`36B` `mod 4 == 0`), and E5 (`omf_b3.py:172-173`) never hit this purely because all 11/11 E0 baseline local-data T3s have 1 string each and E2's 2 strings happened to be 4-byte multiples.
- **Practical consequence:** Under `DEC-A06` ("fully verified whole segments only" via byte equality) or unmodified `DEC-B02`/`DEC-B08`, virtually every real multi-string `-ot` CU (`SaveSlotPath`, `GAMEDLG` beyond 2 strings, etc.) will fail E0 `RegionMatch` and fail B3 with **flaky, non-deterministic false mismatches**.
- **Concrete alternative:** Adopt **Invariant V4 (`DEC-C03`)**: exempt 1..3B 4B-alignment gaps **if and only if** (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A. Validate via **EXP-1** on `SaveSlotPath`.
- **What would change my position:** Live proof that Watcom 10.0a `-ot` can be forced via a flag/pragma to emit deterministic zero-filled `CONST` padding matching `war.exe`'s 157 non-zero 1994 residue gaps—which is impossible for the 1994 binary's heap bytes, making V4 + ASM `physical_provider` unavoidable for Build A.

### 2.2 Fix B2 Emission: Raw Literal Bytes (`DEC-B04`) vs Piece-Local Expressions (`DEC-A05`/`DEC-C05`), Cross-Object `rel32-interior`, and Cross-Piece Fallthrough
- **Challenged propositions:** `DEC-B04` (Claude: emitting ALL cross-object relative branches other than `rel32` to exported entries as *original literal displacement bytes*, relying on `wc1.compare` as "a complete check"); `DEC-A05` (GPT: omits explicit cut-entry `rel8` and cross-piece fallthrough guards).
- **Dispute type:** Architectural + correctness/verification.
- **Evidence:** R1-Probe 1 (found **9** game-range cross-function `rel32` targeting cut interiors: `0x20301`, `0x2030b`, `0x20719`, `0x2072f`, `0x2073c`, `0x207a9`, `0x23310`, `0x23321`, `0x2f6df`); Round 0 Probe 1 (14 binary-wide entry-targeting `rel8` including `0x2f718/0x2f722/0x2f72e -> 0x2f73c` `MissionDefeat` entry; fallthrough `0x2f73a jge 0x2f746` into `0x2f73c`, `0x20258` `pop ebx` fallthrough); GPT Q2 (proved NASM piece-local expression emits exact `74 93`/`75 89` with zero fixups); GPT Q3 (`OBJ-A02`: `wc1.compare` ignores LE object flags & fixup `src_type`).
- **Counterexample / failure mode:**
  1. **Unnecessary literal-byte debt on `rel32-interior`:** Under `DEC-B04`, `0x2f6df jne 0x2f746` (`EndCheckSurvive -> MissionDefeat + 0xa`) and 8 other game-range `rel32-interior` branches are emitted as raw literal bytes even though NASM+OMF32+`wlink` natively relocate 32-bit self-relative external symbols (`_loc_2f746` exported via `omfpatch` `PUBDEF` on the C object).
  2. **Silent offset-bug masking by raw `db` bytes:** Raw `db` bytes (`raw_insns.txt`, Claude P5) bypass NASM's displacement calculation and signed-8-bit range check `[-128, 127]`, deferring error detection solely to `wc1.compare` (which itself has `OBJ-A02` blindness!). Piece-local NASM expressions (`<mnem> short loc_<piece_edge> + <delta>`) make NASM verify the assembled instruction's offset `$` and signed-8-bit range *at assembly time* with zero OMF relocation.
  3. **Unguarded cross-piece fallthrough:** Neither `DEC-B04` nor `DEC-A05` explicitly validates cross-piece fallthrough (`0x2f73a jge` -> `0x2f73c`, `0x20258` -> `0x202c0`). Under `--legacy`, cutting either side of a fallthrough silently corrupts control flow even with zero cross-piece branches!
- **Practical consequence:** Adopting `DEC-B04` verbatim creates unnecessary Build A debt on `rel32-interior`, drops assembly-time displacement verification on `rel8`, and leaves fallthrough cuts unguarded in `--legacy`.
- **Concrete alternative:** Unified planner rule (§6.2): (1) cross-object `rel32` -> always symbolic (`extern` to exported entry, or synthesized `_loc_<addr>` `PUBDEF` via `omfpatch` for cut interior); (2) cross-object `rel8` (all 3 classes: interior, entry, spanning) -> NASM piece-local expression `short loc_<edge> + <delta>`, strictly `in_place` only (never `--legacy`), logged as Build A placement debt; (3) cross-piece fallthrough -> explicitly checked and forbidden under `--legacy`; (4) verified by hardened `wc1.compare` (`DEC-C15`).
- **What would change my position:** Evidence that synthesizing an internal `_loc_<addr>` `PUBDEF` on a C object breaks `wlink` or `omfpatch` invariants (easy to falsify in **EXP-3b**).

### 2.3 Factual Refutation of `DEC-B16` (5 Xfailed T4 Divergences) & Hardening `DEC-B07`
- **Challenged propositions:** `DEC-B16` (Claude: reclassifies *only* `IntroOpWaitSound` as T4 harness state asymmetry and projects S4 as `"up to +4"` DONE); `DEC-B07` (Claude: restores written memory without addressing Python-closure stub state or unwatched global output-comparison blindness).
- **Dispute type:** Factual (settled by R1-Probe 2) + correctness/verification.
- **Evidence:** **R1-Probe 2** (`probes/r01_probes.py`) executed all 5 xfailed tests on `main@a21772b` (`test_playflic_t4.py`, `test_mod_2efd0_t4.py`, `cemu.py` identical at `17733f9`) with full writable-RAM snapshot/restore (`0x50000..0x6ffff`, `0x800000..0xffffff`, `0xef00000..0xeffffff`); `tests/test_playflic_t4.py:114-121,406-411,480-556@17733f9`.
- **Counterexample / failure mode:**
  1. `make_op_stub(S)` (`test_playflic_t4.py:114-121`) mutates unwatched `S + 0x20` (`n + 1`) during the original run, causing **both `test_intro_run_script` (`0x23668`) AND `test_intro_play` (`0x23ae0`)** to fail stock `run_pair` yet **PASS 100%** with full writable-RAM restore! Meanwhile `test_intro_op_start_credits` (`0x23530`: `0x59eb9 01 != 00`) and `test_end_screen` (`0x2fcfc`: `0x80054c 70 != 50`) **still fail** under full restore (confirmed real ref-C bugs). Thus `DEC-B16` is factually outdated: the exact split is **3 harness artifacts (`0x231cc`, `0x23668`, `0x23ae0`) + 2 real ref-C bugs (`0x23530`, `0x2fcfc`)**.
  2. `test_intro_play` mutated unwatched globals (`0x52c69`, `0x55438`, `0x5ab96`) during execution. Restoring full RAM fixes *input* symmetry, but does not verify *output* equality on unwatched globals, and cannot reset *Python-closure* state inside custom `T4Stub(fn=...)` callbacks.
- **Practical consequence:** Keeping `DEC-B16` misclassifies `IntroRunScript` and `IntroPlay` as "fix C bugs" when their existing C is already correct (wasting analyst effort on +2 immediate DONE); implementing `DEC-B07` without banning/resetting Python-closure stub state leaves a parallel asymmetry channel open.
- **Concrete alternative:** **Propose `DEC-C16`** (replace `DEC-B16`): reclassify all three (`0x231cc`, `0x23668`, `0x23ae0`) as T4 harness state asymmetry, keep only `0x23530` and `0x2fcfc` as real ref-C divergences, restore full writable RAM (or dirty pages) in `cemu.run_pair`, require `T4Stub` callbacks to keep mutable state in emulator RAM (or declare a per-run reset hook), and log unwatched global writes in the T4 audit log.
- **What would change my position:** Evidence that `Q-B05` (full T4 test suite under full-RAM restore) reveals a legitimate passing test that depends on cross-run dirty state (which would itself be a test bug!).

### 2.4 Sequencing Group B (`DEC-B06`) Before E0 Matcher (`DEC-B02`) & `DEC-B03`/`DEC-B04` Test Contradiction
- **Challenged propositions:**
  1. Claude §8 Stage S1 (`DEC-B06`) promotes Group B joint TU into `src/` **before** Stage S2 (`DEC-B02` E0 matcher in `tools/wc1/match.py`).
  2. `DEC-B03` (Claude) requires `"Regression tests: IntroOpSyncSound standalone is rejected; Group B is accepted"`, which **directly contradicts `DEC-B04`** once B2 fixed-displacement emission is enabled in `in_place` mode!
- **Dispute type:** Architectural + correctness/verification.
- **Evidence:** `tools/wc1/match.py@17733f9` still lacks E0 bidirectional/leading/local-data checks; `DEC-B03` vs `DEC-B04` text (`00-PROPOSITION-INDEX.json:107,115`).
- **Counterexample / failure mode:** Under `DEC-B04` (I-3), `IntroOpWaitSound`'s `0x231d7`/`0x231e1 -> 0x2316c` spanning standalone `IntroOpSyncSound` satisfies all three clauses (a) fixed in-place cover, (b) target in ASM piece, (c) Build A IDENTICAL—so standalone `IntroOpSyncSound` IS **accepted** under `DEC-B04` (and rejected only under `--legacy` or with B2 disabled)! And promoting Group B before `DEC-B02` establishes a multi-function `src =` precedent under the legacy matcher.
- **Practical consequence:** Implementing `DEC-B03` and `DEC-B04` together fails `DEC-B03`'s own regression test unless the test condition is qualified.
- **Concrete alternative:** (1) Land E0 matcher (`Stage 0`) **before** Group B (`Stage 1`), costing zero calendar risk because all 539/539 current T3s already pass E0. (2) State `DEC-B03`'s regression contract precisely: standalone `IntroOpSyncSound` is **rejected when B2 is disabled or under `--legacy`**, **accepted with explicit B2-span debt under in-place B2**, and **accepted with zero debt as Group B joint TU**.
- **What would change my position:** Nothing on the `DEC-B03`/`DEC-B04` contradiction—it is a logical contradiction in the stated assertions. On S1-before-S2, only if E0 matcher integration were blocked for weeks (it is not; 539/539 already pass).

### 2.5 Missing M2 Critical-Path Tooling: `wc1.oldcc` Short-Path Guard (D9) & 68-Function Symbol-Migration / Wave 3R
- **Challenged propositions:** `DEC-B01` (Claude: restricting M2 infrastructure solely to E0, planner, B2, B1, joint TUs, T4 state symmetry—assigning the 78 remaining functions to `"existing drivers"`); omission of E7 D9 (`wc1.oldcc` short-path guard) from both A's and B's Stage 0 / M2 decisions.
- **Dispute type:** Architectural + implementation risk.
- **Evidence:** `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md@17733f9` ("Operational notes": ~130-char pytest tmp path crashed `wcc386` with `rc=5` in `test_t4spec`); `git diff a21772b 17733f9 -- tools/wc1/oldcc.py` is empty; `candidate_ledger.json@a21772b` / `17733f9` (`61` referenced `fn_*` stubs + `7` `low`-conf = `68` of `76` `needs_human` rows blocked from `wc1.overnight`).
- **Counterexample / failure mode:** Even in EV-3's own verification (`17733f9`), a long path crashed Watcom 10.0a inside `test_t4spec`. And running "existing drivers" (`wc1.overnight`) only picks up `14` eligible functions while filtering out `76` `needs_human` rows—68 of which need atomic cross-TOML symbol renaming / `low`-conf admission (`Wave 3R`).
- **Practical consequence:** Unnecessary Wine crashes in deep worktree/CI paths, and manual hand-editing of 68 cross-referenced symbols across `analysis/symbols/*.toml`, `src/`, and `tests/`.
- **Concrete alternative:** Admit **both** into M2 scope (consistent with `DEC-B01`'s own rule *"directly unblocks not-done in-scope functions"*): (1) `wc1.oldcc` short-path staging/guard (V6/D9) in Stage 0; (2) lightweight deterministic `wc1.symbol_migrate` + Wave 3R routing in Stage 2 (no framework—just syntax-aware atomic rename + verification, matching Architect A's Stage 1 note).
- **What would change my position:** Evidence that an existing production command already atomically renames cross-TOML `fn_*` symbols across `analysis/symbols/`, `src/`, and `tests/` and admits `low`-conf functions into `wc1.overnight` (it does not on `17733f9`).

### 2.6 E4 Selective OMF Extraction Prototype Defects Omitted by Both A & B (`DEC-A07`, `DEC-B09`)
- **Challenged propositions:** `DEC-A07` (GPT) and `DEC-B09` (Claude) listing only `rev-e4-01` F1–F4 (plus Claude's Gate-2 governance check) as E4's remaining prerequisites before any future pilot.
- **Dispute type:** Factual + correctness/verification.
- **Evidence:** Round 0 Probe 5 (`run_probes2.py`) and direct code inspection of `experiments/build_codegen/e4/omf_extract.py@e6150b8` (`:258`, `:378-384`, `:766`, `:798-807`, `:823`).
- **Counterexample / failure mode:** Four uncaught bugs exist in `e4/omf_extract.py` beyond `rev-e4-01` F1–F4: (1) cross-record `THREAD` crashes (`raw_fixups` resets `Threads()` per record at `:258, :823`—reproduced live vs `wc1.omf.parse_module` succeeding); (2) non-`_TEXT` `PUBDEF`/`LPUBDEF` records are filtered/rebased by `lo <= off < hi` without checking `if pseg == ti:` (`:798-807`), silently corrupting `_DATA`/`_BSS`/`CONST` publics whenever `lo > 0`; (3) linear Capstone disassembly at `:378-384` misdecodes B1/inline jump tables; (4) `:766` lacks E5's 64-fixup `FIXUPP32` chunking (`omf_b3.py:409`).
- **Practical consequence:** Even a narrow post-M2 pilot built on `omf_extract.py` risks silent symbol corruption on `lo > 0` slices or crashes on dense fixups/threads.
- **Concrete alternative:** Keep E4 deferred post-M2, require the owner's Gate-2 governance decision (`DEC-B09`), AND require any future implementation to be built over **one unified strict OMF32 codec (`DEC-C09`)** with regression tests covering all 4 Probe-5 bugs + `rev-e4-01` F1–F4.
- **What would change my position:** Nothing—these 4 bugs are directly present in `e4/omf_extract.py@e6150b8`.

---

## 3. Unsupported Conclusions

1. **Claude (`DEC-B04`, §5 line 317, §8 line 388): "`wc1.compare` IDENTICAL is a complete check for Build A."**
   - *Missing link:* `tools/wc1/compare.py:24-27,45-47@17733f9` prints `o.flags` without comparing them and omits `f.src_type` from its fixup tuples (proved by Architect A's Q3 `OBJ_EXEC` mutant returning `IDENTICAL`, verified by R1-Probe 3). Until `compare.py` checks loader-relevant object flags and fixup `src_type`, `IDENTICAL` is necessary but not strictly complete for loader metadata.
2. **Claude (`DEC-B02`, §2 E0 line 40–41): E0 semantics adopted as-is cover local data verification soundly for future CUs.**
   - *Missing link:* Both Claude (P1) and my Round 0 (Probe 7b) confirmed `0/539` current T3s exercise leading bytes or local data pointer fixups, AND my Probe 7b proved `11/11` local-data T3s contain only **1 string each** (`0` inter-string alignment gaps). E0's whole-segment `CONST` check (`matcher_proto.py:333`) was never tested on a real multi-string `-ot` `CONST` segment with `len % 4 != 0`—where Watcom 10.0a emits non-deterministic heap residue (Probes 3 & 7).
3. **Claude (`DEC-B16`, §8 S4): Reclassifying only `IntroOpWaitSound` as harness state asymmetry and estimating S4 as "up to +4 DONE".**
   - *Missing link:* Claude only probed `IntroOpWaitSound` (P4) and left the other 4 as open question `Q-B01`. My R1-Probe 2 closed `Q-B01` and proved the exact count is **3 harness artifacts (`0x231cc`, `0x23668`, `0x23ae0`) and 2 genuine ref-C bugs (`0x23530`, `0x2fcfc`)** (so S4 after Group B yields exactly **+2**, not "up to +4").
4. **GPT (`DEC-A02` / §2 E0): Treating E0's 519-T3 cohort as unverified on `main@a21772b` without running E0 on the 20 new T3s.**
   - *Missing link:* GPT explicitly did not invoke Watcom 10.0a in Q1–Q4. Both Claude (P1) and I (Probe 4) independently ran E0 on all 20 new T3 functions on `main@a21772b` (`539/539` `FunctionMatch=MATCH` & `RegionMatch=MATCH`, unchanged on `17733f9`), closing that empirical gap (while GPT's demand for raw-record strictness + live re-audit at cutover remains completely valid!).
5. **GPT (§2 E4 / `DEC-A07`): Relying on `rev-e4-01` F1–F4 as the complete defect list of `e4/omf_extract.py`.**
   - *Missing link:* Neither GPT nor Claude audited `e4/omf_extract.py` line-by-line for cross-record `THREAD` or non-`_TEXT` `PUBDEF` rebasing (Probe 5 caught 4 additional production-blocking bugs).
6. **GPT (§2 E5 / `DEC-A06`): "Admit B3 initially for fully verified whole segments only" as sufficient for real Warcraft `-ot` CUs.**
   - *Missing link:* Unverified on real multi-string `-ot` `CONST` segments (`SaveSlotPath`), where 157/293 `war.exe` strings have non-zero 1994 heap residue and live Watcom 10.0a emits non-deterministic pad bytes (Probes 3 & 7).
7. **My Own Round 0 (§8, §2.8, `DEC-C12`):** Three overclaims cleanly exposed by Round 1 cross-review: (a) calling all 5 xfails "real ref-C bugs" (refuted by Claude P4 + R1-Probe 2: 3 are harness state asymmetry); (b) calling `-5r` the predominant 1994 flag (overstated per Claude `OBJ-B07` / E7 `51 only_4r`); (c) placing `shared_const_string_literal` in unconditional Class 1 `MUST_MERGE` (overstated per GPT §7 & Claude §7; only 1 synthetic positive).

---

## 4. Missing Assumptions and Hidden Dependencies

1. **Hidden Contradiction: `DEC-B03` + `DEC-B04` (`IntroOpSyncSound` regression test):**
   - Individually, `DEC-B03` asserts `"IntroOpSyncSound standalone is rejected"` and `DEC-B04` admits any fixed-layout in-place cross-object `rel8` (including B2-a spanning cuts). Combined, **`DEC-B04` makes standalone `IntroOpSyncSound` ACCEPTED** in `in_place` mode, contradicting `DEC-B03`'s regression test unless qualified by mode (`--legacy` / B2-off vs `in_place` B2-debt)!
2. **Hidden Unsafe Interaction: `DEC-B04` Clause (c) + `OBJ-A02` (`wc1.compare` blindness):**
   - `DEC-B04` relies on `wc1.compare` returning `IDENTICAL` as the final completeness backstop for raw literal-byte cross-object branches. Combined with `OBJ-A02` (`compare.py` ignoring LE object flags and fixup `src_type`), an OMF/linker mistake altering loader attributes or relocation types would pass `DEC-B04` silently unless `compare.py` is hardened first (`DEC-C15`).
3. **Hidden Unsafe Interaction: `DEC-B06` (Group B in S1) + Legacy `wc1.match` (before S2):**
   - Promoting a multi-function TU (`Group B`) while `match.py` still runs the legacy single-function/one-directional matcher opens the door to multi-function `src =` files before `RegionMatch` exists in production. Sequencing `DEC-B02` (Stage 0) before `DEC-B06` (Stage 1) eliminates this window cleanly.
4. **Hidden Dependency: `DEC-B07` Input Symmetry vs Output Coverage & Python-Closure Stubs:**
   - Restoring all writable RAM before the C run fixes *input* asymmetry (unlocking `0x231cc`, `0x23668`, `0x23ae0`), **assuming** custom `T4Stub(fn=...)` callbacks hold zero mutable state in Python closures (if a stub uses a Python `count = [0]` closure instead of emulator RAM `S+0x10`, full-RAM restore STILL leaves the C run seeing `count = [3]`!). Furthermore, as R1-Probe 2 showed on `test_intro_play`, unwatched globals (`0x52c69`, `0x55438`, `0x5ab96`) are still mutated without output comparison—input symmetry must not be mistaken for full-memory output equivalence.
5. **Hidden Dependency: `DEC-A05` / `DEC-B04` + Cross-Piece Fallthrough (`EndCheckSurvive` `0x2f73a` -> `MissionDefeat` `0x2f73c`, `NetSerialPushBytes` `0x20258`):**
   - Both A and B frame B2 exclusively around *relative branch instructions*. Neither states the hidden assumption that an ASM piece ending in a non-unconditional instruction (fallthrough) requires exact physical adjacency with the next piece—valid in `in_place` mode, **silently broken in `--legacy`**.
6. **Hidden Dependency: `DEC-A02` / `DEC-B02` + E2 Cause B (`FunctionMatch` bounds) + Watcom 10.0a `CONST` Padding (V4):**
   - Combining E0 (`DEC-A02`/`DEC-B02`) with multi-function TUs (`DEC-B06`) or B3 (`DEC-A06`/`DEC-B08`) triggers two silent failure cliffs unless fixed upfront: (a) E0 `FunctionMatch` falsely rejects non-contiguous multi-function TUs (`E2 Cause B`, 9 losses), and (b) E0/E5 `CONST` byte checks fail non-deterministically on multi-string `-ot` CUs with 1..3B alignment padding (`Probes 3 & 7`).
7. **Hidden Dependency: `DEC-B12` + `src/playflic/player_reference.c` & Stage-3 Multi-Function T4 Consolidation:**
   - `player_reference.c` ALREADY contains multiple T4 functions calling each other (e.g., `IntroOpStartCredits` calling unstubbed `IntroLoadCreditLines`). Narrowing E6 adoption strictly to "when a T4 needed for M2 requires Group mode" (`DEC-B12`) leaves Stage-3 multi-function T4 consolidation unguarded unless E6 is explicitly gated before *any* new multi-function T4 migration.
8. **Hidden Operational Dependency: Watcom 10.0a ~129-Char Path Limit (`oldcc.py` D9):**
   - Every Architect's verification, `test_t4spec`, and automated `wc1.overnight` wave assumes `wc1.oldcc` compiles reliably from any worktree/pytest tmp path—yet EV-3 (`17733f9`) hit `rc=5` at ~130 chars in `test_t4spec` and our R1 probe hit `rc=-11` when `oldcc.py` resolved a 115-char path under `/mnt/data/projects/warcraft-1-decompile-consilium/...`.

---

## 5. Counterexamples and Probe Results

Four targeted read-only probes were executed in Round 1 (full log in §11):

1. **R1-Probe 1 — Complete Game-Range Cross-Function `rel32-interior` Census (Counterexample to `DEC-B04`'s blanket literal-byte rule):**
   - Found **9** cross-function `rel32` instructions targeting function interiors in `0x104b0..0x3024e`: `0x20301`/`0x2030b` (`NetSerialIsr -> NetSerialIsrFifo+0x4c`), `0x20719`/`0x2072f`/`0x2073c`/`0x207a9` (`NetModemWaitResponse_tail -> NetModemWaitResponse+0x1e/+0x1c`), `0x23310`/`0x23321` (`IntroOpWaitAnim -> IntroOpPlayFrames+0x6e`), and `0x2f6df` (`EndCheckSurvive -> MissionDefeat+0xa`). All 9 can be relocated **symbolically** in OMF32 without raw literal-byte debt.
2. **R1-Probe 2 — Decisive Resolution of `Q-B01` Across ALL 5 Xfailed T4 Functions (Counterexample to `DEC-B16` and my Round 0 §8):**
   - Ran stock `cemu.run_pair` vs full writable-RAM snapshot/restore (`0x50000..0x6ffff`, `0x800000..0xffffff`, `0xef00000..0xeffffff`) on all 5 xfailed functions (`test_playflic_t4.py`, `test_mod_2efd0_t4.py`, byte-identical between `a21772b` and `17733f9`):
     - `test_intro_op_wait_sound` (`0x231cc`): STOCK FAIL (`0x801130: 30 != 0c`, unwatched `0x800010: 3 -> 0`) -> **FULL-RESTORE PASS**.
     - `test_intro_run_script` (`0x23668`): STOCK FAIL (`0x801130: 68 != 50`, unwatched `0x800020: 0 -> 1`) -> **FULL-RESTORE PASS**.
     - `test_intro_play` (`0x23ae0`): STOCK FAIL (`0x801130: 74 != 68`, unwatched `0x800020` + globals `0x52c69`, `0x55438`, `0x5ab96`) -> **FULL-RESTORE PASS**.
     - `test_intro_op_start_credits` (`0x23530`): STOCK FAIL -> **FULL-RESTORE FAIL** (`0x59eb9: original 01 != C 00`) — confirmed real ref-C divergence.
     - `test_end_screen` (`0x2fcfc`): STOCK FAIL -> **FULL-RESTORE FAIL** (`0x80054c: original 70 != C 50`) — confirmed real ref-C divergence.
3. **R1-Probe 3 — Direct Confirmation of Architect A's `OBJ-A02` & `OBJ-A03` on `main@17733f9`:**
   - Confirmed `tools/wc1/compare.py@17733f9` never compares `oa.flags == ob.flags` (`war.exe` objects: `(1, 0x10000, 0x3212b, flags=0x2045)`, `(2, 0x50000, 0x155f0, flags=0x2043)`) and omits `f.src_type` (all `8,770` unique fixups in `war.exe` have `src_type=7`).
   - Confirmed `tools/wc1/omf.py@17733f9` has `0` checksum checks and drops explicit `FRAME` encodings (`fmethod`/`fidx` discarded unless `tmethod` uses frame).
4. **R1-Probe 4 — EV-3 (`main@17733f9`) Diff Verification & Live `oldcc.py` Path Crash:**
   - Confirmed `git diff a21772b 17733f9` is empty for `oldcc.py`, `build.py`, `emit.py`, `match.py`, `cemu.py`, `compare.py`, `omf.py`, `test_playflic_t4.py`, `test_mod_2efd0_t4.py`.
   - Confirmed EV-3 resolved `t3_audit.py`'s R3 provenance defects, while `oldcc.py` still lacks D9 short-path protection—and hit `compile failed (Watcom 10.0a, rc=-11)` live during our attempt to run `test_playflic_t4.py` from the long path `/mnt/data/projects/warcraft-1-decompile-consilium/...`.

---

## 6. Alternative Designs (Synthesis Where Positions Diverge)

### 6.1 Unified Stage-0 Verification Core (Synthesizing `DEC-A02` + `DEC-B02` + `DEC-C02`/`C03`/`C15`)
Reimplement E0 cleanly in `tools/wc1/match.py` (never importing `experiments/`, `DEC-B15`) with five non-negotiable properties:
1. **Strict raw-OMF admission (`OBJ-A03`):** Validate OMF record bounds, nonzero checksums, single `MODEND`, persistent cross-record `THREAD`, and preserve explicit `FRAME` encodings (`DGROUP`/`FLAT`/`Target`/`EXTDEF`) before running verification.
2. **Two scopes, one bidirectional obligation engine:** `FunctionMatch` evaluates branch closure strictly against `[orig_fn.start, orig_fn.start + fn_len)` (fixing E2 Cause B / `OBJ-C05`); `RegionMatch` verifies the full closed contribution (leading bytes, internal padding, trailing filler with `trimmed_branch_target` preserved, local data segments) and is the **sole** minter of immutable `VerifiedRegion` (no separate `CandidateRegion` runtime type in M2, accepting `DEC-B14`).
3. **Invariant V4 (`DEC-C03`):** Strict 5-condition exemption for 1..3B unreachable 4B-alignment gaps after NUL-terminated verified `CONST` literals, forcing Build A `physical_provider = ASM`.
4. **Hardened `wc1.compare` (`DEC-C15`):** Check LE object flags (`0x2045`/`0x2043`), entry/stack object+offset, and fixup `src_type` (`7`) alongside existing loaded-image and fixup comparisons (validated against baseline Build A).
5. **Short-path staging in `wc1.oldcc` (V6 / D9):** Stage compiler inputs/outputs under `<= 48` chars and fail fast before Watcom 10.0a's ~129-char crash threshold.

### 6.2 Unified Single Planner + B1 + Hybrid Symbolic/Piece-Local B2 (Synthesizing `DEC-A03`/`A04`/`A05` + `DEC-B03`/`B04`/`B05` + `DEC-C05`)
Expose one derived `plan(p, verified_regions, mode)` consumed identically by `check_t3_buildable`, `wc1.build`, `wc1.emit`, `batch_driver`, `wave4a`, and `m2_inventory`:
- **B1 (leading tables):** Set `base = first_entry_addr - first_entry_off` iff `VerifiedRegion` proved `[0, k)` bytes/obligations, no foreign entry/reference enters `[0, k)`, and no overlap occurs with the previous cut.
- **Unified cross-object transfer rule (all 4 cases):**
  1. Cross-object `rel32` to exported entry -> `extern` symbolic (existing).
  2. Cross-object `rel32` to cut interior (e.g., `0x2f6df -> 0x2f746`) -> **symbolic** via `omfpatch`-synthesized internal `PUBDEF` `_loc_<addr>` at exact offset inside the `VerifiedRegion` (zero literal-byte debt!).
  3. Cross-object `rel8` (all 3 classes: B2-interior, B2-entry like `0x2f718 -> 0x2f73c`, B2-span like `0x231d7 -> 0x2316c`) -> **strictly `in_place` only** (refused under `--legacy`), emitted as **NASM piece-local label expression** (`<mnem> short loc_<piece_edge> + <signed_delta>`) after proving every intervening byte has a fixed-VA provider and `-128 <= disp <= 127`, logged explicitly as Build A placement debt.
  4. Cross-piece fallthrough (`0x2f73a -> 0x2f73c`, `0x20258 -> 0x202c0`) -> allowed strictly in `in_place` mode with verified adjacency, **refused under `--legacy`**.
- **Joint TUs (`DEC-B06` / `DEC-C06`):** Preferred over B2 debt whenever all members pass `RegionMatch` (Group B promoted in Stage 1 *immediately after* Stage 0 E0 matcher lands).

### 6.3 Hardened T4 Paired-Execution State Symmetry (`DEC-C16`, Extending `DEC-B07`)
In `tools/wc1/cemu.py::run_pair` (subject to owner approval for strengthening test harness behavior):
1. Snapshot and restore **all writable emulator RAM** (LE `_DATA`/`_BSS`, heap `0x800000..alloc_hi`, stack, excluding code/traps) between the original run and C run—or track dirty pages via a Unicorn `UC_HOOK_MEM_WRITE` hook and restore every dirty page.
2. Require `T4Stub(fn=...)` callbacks to store mutable counter state inside emulator RAM (automatically restored) or provide an explicit per-run `reset()` hook; disallow unreset Python-closure mutation.
3. Record unwatched global write ranges (outside stack & `watch`) in the `WC1_T4_AUDIT_LOG` so analysts see any side effects not currently compared.
4. Immediately re-evaluate all 5 xfailed tests -> promotes **+2 DONE** (`IntroRunScript 0x23668`, `IntroPlay 0x23ae0`) in addition to Group B (`0x2315c`/`0x23170`/`0x231cc`), leaving only **2** genuine ref-C bugs (`IntroOpStartCredits 0x23530`, `EndScreen 0x2fcfc`)!

### 6.4 Post-M2 Stage-3 Track: Unified Strict OMF32 Codec -> B3+V4 -> E6 Multi-Function T4 -> Conditional E3/E4
Defer cleanly until after M2 (or an explicit M2 blocker). First unify OMF32 parsing/emission into `tools/wc1/omf.py` (strict checksums, preserved `FRAME`, persistent cross-record `THREAD`, 64-fixup chunking), then build B3+V4 (`DEC-C10`), gate any multi-function T4 consolidation on E6+audit parity (`DEC-A08`/`DEC-C11`), and keep E3/E4 (`DEC-B09`/`DEC-C08`) gated on owner Gate-2 approval + Probe-5/F1–F4 fixes.

---

## 7. Decisions Requiring Further Evidence

| Probe ID | Cheapest Decisive Experiment | Falsification Criterion | Decisions Changed |
|---|---|---|---|
| **EXP-1** (from R0) | Prototype Invariant V4 (5-condition 1..3B unreachable `CONST` gap rule) in E0 + E5 on real `SaveSlotPath` (`0x14740`, 3 strings with non-zero heap residue `8d75e0`/`0800e8`/`a5`) + 6 negative controls (mutated literal byte, 4B gap, `_DATA` gap, pointer into gap). | Fails if `SaveSlotPath` fails `RegionMatch` or Build A `IDENTICAL` with natural literals, OR if any negative control returns `MATCH`. | `DEC-A02`, `DEC-A06`, `DEC-B02`, `DEC-B08`, `DEC-C03`, `DEC-C10`. |
| **Q-B05** (from Claude) | Run the full T4 pytest suite once with `DEC-B07`/`DEC-C16` full writable-RAM restoration enabled (under short-path staging). | Fails if any currently passing T4 test regresses (exposing either a harness bug or a broken test depending on dirty cross-run state). | `DEC-B07`, `DEC-C16`. |
| **EXP-3b** (refines R0 EXP-3) | Build A link probe combining (a) NASM piece-local `rel8` expression (`short loc_<edge> + delta`) on standalone `IntroOpSyncSound` (`0x23170`) & `MissionDefeat` (`0x2f73c`), (b) `omfpatch` internal `PUBDEF` `_loc_2f746` for `0x2f6df` `rel32-interior`, and (c) `--legacy` negative rejection on both `rel8` and fallthrough `0x2f73a`. | Fails if NASM rejects or miscomputes any `rel8`, if `wlink` rejects `_loc_2f746`, if hardened `wc1.compare` is not `IDENTICAL`, or if `--legacy` accepts the cut. | `DEC-A05`, `DEC-B03`, `DEC-B04`, `DEC-C05`. |
| **EXP-A03** (from GPT) | Compare `oa.flags`, `entry`/`initial_esp` object+offset, and `f.src_type` on baseline `war.exe` vs a live Build A `war.exe`, plus negative mutants (`OBJ_EXEC` flip, `src_type` flip). | Fails if legitimate Build A differs from original on any enforced loader attribute, OR if a loader-changing mutant still prints `IDENTICAL`. | `DEC-A03`, `DEC-C15`. |
| **EXP-2 / Q-B06** (post-M2) | Sweep `-5r -d1+ -zp1` (for `OpenArchive`) and `-od -5r` on the 51 `only_4r` T3s. | Fails H1 (`-5r` universal) if any `only_4r` T3 has no `-5r` OD/debug match. | `DEC-B11`, `DEC-C13` (M3 consolidation defaults). |
| **EXP-4** (Stage 3 pre-gate) | Extend E6 `mf_cemu` with 1 switch-bearing multi-function TU + 1 `CONST`-string-returning T4 (`LogicalConstDataPtr`) + 4 negative controls + `t4spec` audit parity. | Fails if an inter-function indirect jump or raw integer masquerading as a string pointer passes. | `DEC-A08`, `DEC-B12`, `DEC-C11`. |
| **Q-B08** (post-M2) | Static count of contiguous E2-style CU consolidations that actually require B3 multi-anchor / out-of-order data segments. | Zero real consolidation blockers keeps B3 deferred until Build B. | `DEC-A06`, `DEC-B08`, `DEC-C10`. |

---

## 8. Structured Positions on Decisions

### 8.1 Architect A — GPT (`DEC-A01`–`DEC-A10`)

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: Exact alignment with M2 completion priority, separate tracking of T4-to-T3 conversions, and fixed finish-line governance (owner retains T5 and scope/gate authority).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: CONDITIONAL
Reason: Strongly accept one bidirectional verifier with strict raw-OMF admission (closing OBJ-A03's checksum/FRAME holes) and live cutover audit (539/539 already verified by Claude P1 and my Probe 4). Must also close three concrete verification gaps omitted here.
Conditions: (1) FunctionMatch checks branch closure strictly against [orig_fn.start, orig_fn.start + fn_len) (fixing E2 Cause B / OBJ-C05); (2) preserve trimmed_branch_target across all modes (E3 Nit 3); (3) include Invariant V4 (DEC-C03, validated by EXP-1) for unreachable 1..3B Watcom 10.0a CONST alignment gaps (OBJ-C01/OBJ-C09).
Related objections: OBJ-A03, OBJ-C01, OBJ-C05, OBJ-C09
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: ACCEPT
Reason: Whole-image single-provider partition plan plus hardening wc1.compare for loader-relevant object flags and typed fixups (closing OBJ-A02) directly strengthens Build A soundness. Ensure check_t3_buildable calls this exact planner (DEC-B03) and validate attributes on baseline Build A first (EXP-A03).
Conditions: none
Related objections: OBJ-A02
```

```text
Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: Sound B1 leading-table contract gated on full region bounds, ownership, and bidirectional obligations; ChooseCampaignDialog (0x157e8) is already Build A feasibility-verified (Claude P6).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: CONDITIONAL
Reason: Strongly accept whole-TU shared-tail preference (Group B) and NASM piece-local relative expressions under proved fixed in-place cover (Q2). Must explicitly cover all cross-piece edge classes discovered in Probe 1 and R1-Probe 1.
Conditions: (1) Explicitly cover all three cross-piece rel8 classes—interior, cut-entry (EndCheckSurvive -> MissionDefeat 0x2f73c), and cut-spanning (IntroOpSyncSound 0x23170)—strictly forbidden under --legacy; (2) explicitly guard cross-piece fallthrough (0x2f73a -> 0x2f73c, 0x20258) under --legacy; (3) emit cross-piece rel32-interior (0x2f6df and 8 other game-range cases) symbolically via omfpatch internal PUBDEF _loc_<addr>; (4) verify via EXP-3b.
Related objections: OBJ-C02, OBJ-C10
```

```text
Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: CONDITIONAL
Reason: Accept storage-identity vs provider separation and deferring B3 until justified post-M2. However, restricting B3 to raw whole-segment byte equality fails on almost every real multi-string -ot CONST segment in war.exe due to Watcom 10.0a's non-deterministic 1..3B alignment padding (Probes 3 & 7: 157/293 strings).
Conditions: (1) Incorporate Invariant V4 (DEC-C03, validated by EXP-1 on SaveSlotPath) for unreachable 1..3B CONST alignment gaps while forcing Build A physical_provider = ASM; (2) implement over one unified strict OMF32 codec (DEC-C09) with rev-e5-02 mutability/aliasing guards.
Related objections: OBJ-C01, OBJ-C09
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: CONDITIONAL
Reason: Accept deferring general selective extraction and bounding any future pilot. However, the stated admission criteria omit a blocking governance prerequisite and four newly uncovered prototype bugs.
Conditions: Any future pilot additionally requires (1) explicit owner approval of Gate-2 / match --all semantics for src = files with mismatching siblings (DEC-B09/OBJ-B04); (2) fixing all four Probe-5 bugs in e4/omf_extract.py (cross-record THREAD crash :258/:823, non-_TEXT PUBDEF corruption when lo>0 :798-807, linear jump-table decode :378, missing 64-fixup chunking :766) plus rev-e4-01 F1-F4; (3) implementation over one unified strict OMF32 codec (DEC-C09).
Related objections: OBJ-B04, OBJ-C03, OBJ-C14
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: CONDITIONAL
Reason: Strongly accept per-side execution boundaries, symmetric substitutions, real callback/ABI checks, typed pointers, and production audit parity as mandatory prerequisites before any cited multi-function T4 relies on E6.
Conditions: (1) Add paired-execution writable-state symmetry (DEC-B07/DEC-C16) immediately for M2 (unlocking 0x231cc, 0x23668, 0x23ae0); (2) extend R2 before Stage-3 CONST-owning T4s to LogicalConstDataPtr and allow proven intra-function switch tables under Isolated mode (EXP-4); (3) keep E6 multi-function machinery off the M2 critical path unless an M2 function genuinely requires Group mode.
Related objections: OBJ-B06, OBJ-C12
```

```text
Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Preserves merged additive presets and declared-compiler policy, keeps S(f) context-scoped, and rightly treats heuristic scores and freshness snapshots (now independently confirmed 0/202 fresh in EV-3) as scheduling inputs only.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A10
Revision: 1
Proposition SHA-256: 8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e
Position: ACCEPT
Reason: Exact alignment with analyst-only premise-carrying CU evidence separated from analysis/modules.toml and build inputs, rejecting automatic source consolidation.
Conditions: none
Related objections: none
```

---

### 8.2 Architect B — Claude (`DEC-B01`–`DEC-B17`)

```text
Decision: DEC-B01
Revision: 1
Proposition SHA-256: 2e0072dfeacf3355c35ae8626056819ee56a56b22736ebe3c1b95f1ef350f7bb
Position: CONDITIONAL
Reason: Strongly accept the M2 priority boundary deferring B3, selective extraction, full E6 Group/Integrated, persistent provenance, and CU databases. Three concrete M2 soundness/unblocking items are missing from the admitted list.
Conditions: Also admit under the M2 boundary: (1) wc1.oldcc short-path staging/guard (E7 D9, still causing rc=5/rc=-11 crashes in EV-3 and R1); (2) strict raw-OMF admission and wc1.compare loader-attribute checks (OBJ-A02/OBJ-A03/DEC-C15); (3) lightweight deterministic cross-TOML symbol migration + Wave 3R routing to unblock the 68 fn_* / low-conf functions currently stuck in needs_human (OBJ-C16).
Related objections: OBJ-A02, OBJ-A03, OBJ-C15, OBJ-C16
```

```text
Decision: DEC-B02
Revision: 1
Proposition SHA-256: 52e9b26dfdd3b6954ee162adfb0c71e128aa2aa696965fcd2c09b43b1e7e7a16
Position: CONDITIONAL
Reason: Strongly accept reimplementing E0 cleanly in tools/wc1/match.py with all 55 controls and full live-T3 population audit. Four soundness fixes discovered across R0/R1 must be included in the cutover implementation.
Conditions: (1) Strict raw-OMF admission validating nonzero checksums and preserving FRAME distinctions (OBJ-A03); (2) function-scoped FunctionMatch branch bounds fixing E2 Cause B (OBJ-C05); (3) preserve trimmed_branch_target across all modes (E3 Nit 3); (4) include Invariant V4 (DEC-C03, validated by EXP-1) for Watcom 10.0a's unreachable 1..3B CONST alignment gaps (OBJ-C01/OBJ-C09).
Related objections: OBJ-A03, OBJ-C01, OBJ-C05, OBJ-C09
```

```text
Decision: DEC-B03
Revision: 1
Proposition SHA-256: e4227a079ab271526345bc98d3a54e8b6c12cccf6b476ee37748b7411375e6f3
Position: CONDITIONAL
Reason: Strongly accept the single planner plan(p, regions) shared by check_t3_buildable, batch_driver, wave4a, m2_inventory, and emit. However, the regression test clause ("IntroOpSyncSound standalone is rejected") directly contradicts DEC-B04 once B2 fixed-displacement emission is active in in_place mode.
Conditions: Qualify the regression tests unambiguously: standalone IntroOpSyncSound MUST be rejected under --legacy or when B2 bridge mode is disabled, accepted ONLY with explicit B2-span debt under in_place B2, and accepted with zero debt as Group B joint TU.
Related objections: OBJ-C11
```

```text
Decision: DEC-B04
Revision: 1
Proposition SHA-256: 10f99b1cf2a534df1eb4b3a8f6dd0774a174e1e785dae2222be7ca52b3ce08a1
Position: CONDITIONAL
Reason: Strongly accept the unified Build A in-place cross-object branch rule (covering B2-a/b/c, strictly forbidden under --legacy, explicit debt tracking, Group B preferred). Four technical hardenings are needed over raw literal bytes.
Conditions: (1) Emit cross-object rel8 as NASM piece-local label expressions (short loc_<edge> + delta, GPT Q2 / DEC-A05) rather than raw db bytes so NASM checks offsets and signed-8-bit range at assembly time; (2) emit cross-object rel32 to cut interiors (0x2f6df + 8 game-range cases from R1-Probe 1) symbolically via omfpatch internal PUBDEF _loc_<addr>; (3) explicitly check cross-piece fallthrough (0x2f73a -> 0x2f73c, 0x20258) and reject under --legacy; (4) harden wc1.compare for LE object flags and fixup src_type (DEC-C15) so clause (c) is actually complete.
Related objections: OBJ-A02, OBJ-C10, OBJ-C11
```

```text
Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: Exact alignment with DEC-A04 and DEC-C05 on B1 leading-byte base gated on E0 RegionMatch verification; also verify zero foreign entry/reference into [0, k) and zero split instructions (DEC-A04).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: CONDITIONAL
Reason: Strongly accept proof-gated multi-function TUs, immediate Group B promotion (+3 DONE, Build A IDENTICAL proved in P3), owner confirmation of AGENTS.md wording, and banning heuristic consolidation. Only the roadmap sequencing needs adjustment.
Conditions: Merge Group B into production AFTER DEC-B02 (production E0 RegionMatch in tools/wc1/match.py), not before it, so the first multi-function src = TU is verified by real RegionMatch from day one (OBJ-C13).
Related objections: OBJ-C13
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: CONDITIONAL
Reason: Major soundness discovery! R1-Probe 2 proved this immediately turns 3 of the 5 xfailed T4 functions (0x231cc, 0x23668, 0x23ae0) into PASS on existing reference C. Needs three concrete hardenings and Q-B05 verification before rollout.
Conditions: (1) Restore all writable emulator RAM (or dirty pages via write hook, excluding read-only code/traps) before the C run; (2) prohibit unreset Python-closure mutable state in T4Stub(fn=...) callbacks (require RAM storage or explicit per-run reset hook); (3) log unwatched global writes (outside stack and watch, as seen on test_intro_play) in WC1_T4_AUDIT_LOG; (4) pass Q-B05 (full T4 test suite regression check) and obtain owner approval for the test-harness change.
Related objections: OBJ-C12
```

```text
Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: CONDITIONAL
Reason: Strongly accept deferring Fix B3 to the M3 track (zero M2 DONE impact). Preconditions must include the newly discovered CONST padding constraint and unified OMF codec.
Conditions: Add Invariant V4 (DEC-C03, validated by EXP-1 on SaveSlotPath) for Watcom 10.0a's unreachable 1..3B CONST alignment gaps (OBJ-C01/OBJ-C09) and unified strict OMF32 codec (DEC-C09) alongside RFC §8.2 constraints 1-5.
Related objections: OBJ-C01, OBJ-C09
```

```text
Decision: DEC-B09
Revision: 1
Proposition SHA-256: 00ff7874640d8a9159ec0d393a17aac144a02a9b2126aafedc5883bc4e6135d6
Position: CONDITIONAL
Reason: Strongly accept deferring E3/E4 post-M2 and requiring an explicit owner decision on Gate-2 / match --all semantics before any later adoption (OBJ-B04 is an important governance catch). Must also include the four newly found E4 prototype bugs.
Conditions: In addition to owner Gate-2 approval and rev-e4-01 F1-F4, require fixing all four Probe-5 bugs in e4/omf_extract.py (cross-record THREAD, non-_TEXT PUBDEF corruption when lo>0, linear jump-table decode, 64-fixup chunking) over one unified strict OMF32 codec (DEC-C09).
Related objections: OBJ-C03, OBJ-C14
```

```text
Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: Exact E2 alignment matrix (16/4/1 + PARA _TEXT SEGDEF for -ot; OW2 16B under -4r and -5r) with clean separation between compiler spacing behavior and historical CU flag claims.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: Persuasive correction to overclaiming -5r as the global default: keep -4r as single-file project default with additive E7 presets, keep S(f) context-scoped, and leave H1/H2/H3 open until 5r-OD is tested (Q-B06).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: Accept deferring E6 multi-function machinery during M2 while T4s remain single-function and keeping c_entry_hook as defense in depth. Scope of the trigger is slightly too narrow.
Conditions: Explicitly require E6 (with DEC-A08's production audit parity, per-side isolation, and EXP-4 switch-table/LogicalConstDataPtr support) as a hard gate before ANY post-M2/Stage-3 multi-function T4 consolidation as well, not only if an M2 function requires Group mode.
Related objections: none
```

```text
Decision: DEC-B13
Revision: 1
Proposition SHA-256: 84a9be5c34e2d9d48bff2c233da0fc9779e5ac2f64a01704f120998ce876741c
Position: CONDITIONAL
Reason: Strongly accept analyst-facing constraint graph, rejecting staircases/call-locality/automatic consolidation, and deferring compilation_units.toml to M3. Minor omission of shared_const_string_literal.
Conditions: Retain shared_const_string_literal as a conditional premise-dependent merge constraint (valid iff independent evidence excludes explicit shared externs and linker string pooling, per GPT §7 and Claude §7) rather than omitting it entirely.
Related objections: none
```

```text
Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: Persuasive simplification for M2: immutable matcher-minted VerifiedRegion + single derived PlacementPlan avoid unnecessary CandidateRegion class scaffolding and premature persistent metadata databases while preserving full soundness.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Clean engineering hygiene; production tools/wc1 must never import experimental scaffolding from experiments/.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Factually superseded by R1-Probe 2 (resolving Q-B01 across all 5 xfailed T4 functions). Reclassifying only IntroOpWaitSound as T4 harness state asymmetry misses IntroRunScript (0x23668) and IntroPlay (0x23ae0), which ALSO pass 100% under full writable-memory restoration, leaving only IntroOpStartCredits (0x23530) and EndScreen (0x2fcfc) as real ref-C divergences. Replace with DEC-C16.
Conditions: none
Related objections: OBJ-C12
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: ACCEPT
Reason: Explicitly agreeing with DEC-B17's REJECT position: selective OMF extraction (Approach D) must NOT be adopted as an M2 strategy (aligns with DEC-C08 and DEC-B09). Note: ACCEPT here endorses DEC-B17's rejection of selective extraction for M2.
Conditions: none
Related objections: none
```

---

### 8.3 Status of My Own Round 0 Decisions (`DEC-C01`–`DEC-C14`) — Preview Only (Formal Revisions Held for Round 2)

- **`DEC-C01`, `DEC-C03`, `DEC-C06`, `DEC-C09`, `DEC-C10`, `DEC-C14`:** **`RETAIN`** (note for `DEC-C01`: will align M2 concrete entity representation with `DEC-B14`, omitting a standalone `CandidateRegion` runtime class; note for `DEC-C06`: will add owner ground-rule wording review from `DEC-B06`).
- **`DEC-C02`:** *Will revise in Round 2* to include strict raw-OMF admission (nonzero checksums + `FRAME` preservation, Architect A `OBJ-A03`).
- **`DEC-C04`:** *Will revise in Round 2* to remove the 3 `t3_audit.py` R3 bugs (now fixed on `main@17733f9` per EV-3!), retain `wc1.oldcc` short-path protection (D9, still unfixed and triggered in EV-3 and R1), and fold in `wc1.compare` hardening (`DEC-C15`) + `cemu.run_pair` state symmetry (`DEC-C16`).
- **`DEC-C05`:** *Will revise in Round 2* to adopt `DEC-B14`'s minimal M2 entity set, add `wc1.compare` hardening (`DEC-C15`), and incorporate Claude P5/P6 and GPT Q2 evidence.
- **`DEC-C07`:** *Will revise in Round 2* to replace "5 real ref-C bugs" with R1-Probe 2's verified split (**3 T4 harness state-asymmetry artifacts `0x231cc`/`0x23668`/`0x23ae0` + 2 real ref-C bugs `0x23530`/`0x2fcfc`**) and add `DEC-B07`/`DEC-C16` to Stage 0/Stage 1.
- **`DEC-C08`:** *Will revise in Round 2* to add the owner Gate-2 / `match --all` governance prerequisite (`DEC-B09`/`OBJ-B04`).
- **`DEC-C11`:** *Will revise in Round 2* to incorporate Architect A's `DEC-A08` production `t4spec` audit parity & per-side original-execution guards.
- **`DEC-C12`:** *Will revise in Round 2* to downgrade `shared_const_string_literal` from unconditional Class 1 to premise-dependent Class 2 (per GPT §7 & Claude §7).
- **`DEC-C13`:** *Will revise in Round 2* to align with `DEC-B10` & `DEC-B11` (keep `-4r` single-file project default with additive presets; avoid claiming `-5r` was the unique original project flag).

---

## 9. New Objections

### `OBJ-C09`
- **Severity:** `correctness/verification`
- **Exact proposition challenged:** `DEC-A06` (GPT: *"Admit B3 initially for fully verified whole segments only"*), `DEC-B02` (Claude: adopting E0 matcher semantics as-is), and `DEC-B08` (Claude: RFC §8.2 constraints 1–5 as-is for B3) omitting explicit handling of Watcom 10.0a's non-deterministic uninitialized 1..3-byte `CONST` alignment padding.
- **Source:** `01-architect-gpt-opening.md` (`DEC-A06`, §3 line 111); `02-architect-claude-opening.md` (`DEC-B02`, `DEC-B08`).
- **Evidence & counterexample:** Round 0 Probes 3 & 7 (`157/293` fixup-bounded `war.exe` `CONST` strings carry non-zero 1994 heap residue, e.g., `SaveSlotPath 0x56b1c` `".net\0" + 8d75e0 + ".sav\0" + 0800e8 + "save%d\0" + a5`; live Watcom 10.0a `-ot -5r` emitted `73002f` then `760061` on consecutive compiles of the same C file); `experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`; `experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`.
- **Assumptions:** Multi-string `-ot` CUs with string lengths not divisible by 4 will be compiled under Watcom 10.0a.
- **Practical consequences:** Both E0 `RegionMatch` and whole-segment B3 will reject real multi-string `-ot` CUs with flaky, non-deterministic false mismatches until Invariant V4 (`DEC-C03`) is adopted.

### `OBJ-C10`
- **Severity:** `correctness/verification` + `blocking architectural`
- **Exact proposition challenged:** `DEC-B04` (Claude) emitting cross-object `rel32` to cut interiors and cross-object `rel8` as raw literal bytes (`db`) while relying on unhardened `wc1.compare` as "a complete check", and both `DEC-B04` and `DEC-A05` omitting explicit cross-piece fallthrough guards.
- **Source:** `02-architect-claude-opening.md` (`DEC-B04`, §5 line 317, §8 line 388); `01-architect-gpt-opening.md` (`DEC-A05`).
- **Evidence & counterexample:** R1-Probe 1 found **9** game-range cross-function `rel32-interior` branches (`0x2f6df -> 0x2f746`, plus 8 in `NetSerialIsr`/`NetModemWaitResponse_tail`/`IntroOpWaitAnim`) that NASM+OMF32+`wlink` can relocate symbolically via internal `PUBDEF` `_loc_<addr>`. Round 0 Probe 2 found fallthrough cuts (`0x2f73a jge` -> `0x2f73c`, `0x20258` `pop ebx`). GPT Q3 / R1-Probe 3 proved `wc1.compare` ignores LE object flags and fixup `src_type`.
- **Assumptions:** NASM piece-local expressions (`short loc_<edge> + delta`, GPT Q2) and `omfpatch` internal `PUBDEF` emission are validated in **EXP-3b**.
- **Practical consequences:** Unnecessary literal-byte debt on `rel32-interior`, loss of NASM assembly-time `rel8` bounds verification, unguarded fallthrough cuts in `--legacy`, and overreliance on an incomplete comparator.

### `OBJ-C11`
- **Severity:** `correctness/verification`
- **Exact proposition challenged:** Internal contradiction between `DEC-B03` (*"Regression tests: IntroOpSyncSound standalone is rejected; Group B is accepted"*) and `DEC-B04` (admitting fixed-layout in-place cross-object `rel8` branches spanning a cut).
- **Source:** `02-architect-claude-opening.md` (`DEC-B03` line 500 vs `DEC-B04` line 512).
- **Evidence & counterexample:** Once `DEC-B04` (I-3) is enabled, `IntroOpWaitSound`'s `0x231d7`/`0x231e1 -> 0x2316c` satisfy I-3 clauses (a)–(c), making standalone `IntroOpSyncSound` **accepted** in `in_place` mode—contradicting `DEC-B03`'s stated regression assertion.
- **Assumptions:** Both `DEC-B03` and `DEC-B04` are implemented together in Stage S3 as proposed.
- **Practical consequences:** Broken test specification unless qualified by mode (rejected under `--legacy` or B2-off; accepted only as explicit B2-span debt under `in_place` B2; zero debt as Group B).

### `OBJ-C12`
- **Severity:** `unsupported factual claim`
- **Exact proposition challenged:** `DEC-B16` (Claude) reclassifying only `IntroOpWaitSound` as T4 harness state asymmetry and estimating S4 as `"up to +4"` DONE.
- **Source:** `02-architect-claude-opening.md` (`DEC-B16` line 656, §8 line 389).
- **Evidence & counterexample:** **R1-Probe 2** proved on `main@a21772b` (identical at `17733f9`) that **3/5** xfails (`IntroOpWaitSound 0x231cc`, **`IntroRunScript 0x23668`**, **`IntroPlay 0x23ae0`**) pass 100% under full writable-RAM restore (caused by unwatched `S+0x10`/`S+0x20` mutations in `snd` and `make_op_stub`), whereas **`IntroOpStartCredits 0x23530`** (`0x59eb9: 01 != 00`) and **`EndScreen 0x2fcfc`** (`0x80054c: 70 != 50`) remain genuine ref-C divergences.
- **Assumptions:** None (directly observed across all 5 tests).
- **Practical consequences:** Misclassifying `0x23668` and `0x23ae0` wastes analyst debugging effort on already-correct C; replace with `DEC-C16`.

### `OBJ-C13`
- **Severity:** `correctness/verification`
- **Exact proposition challenged:** Architect B's Stage S1 (`DEC-B06`) merging the first multi-function `src =` TU (Group B) into production **before** Stage S2 (`DEC-B02` production E0 `RegionMatch`).
- **Source:** `02-architect-claude-opening.md` (§8 lines 386–387).
- **Evidence & counterexample:** `tools/wc1/match.py@17733f9` lacks E0 bidirectional/leading/local-data checks, while all 539/539 current T3s already pass E0 (Claude P1, my Probe 4).
- **Assumptions:** E0 matcher integration has no external blockers.
- **Practical consequences:** Establishes a production multi-function `src =` precedent under the unsound legacy matcher when landing E0 first costs zero delay.

### `OBJ-C14`
- **Severity:** `blocking architectural` + `implementation risk`
- **Exact proposition challenged:** `DEC-A07` (GPT) and `DEC-B09` (Claude) specifying E4 pilot prerequisites without including all four Probe-5 defects in `e4/omf_extract.py` (and `DEC-A07` omitting Claude's Gate-2 governance prerequisite).
- **Source:** `01-architect-gpt-opening.md` (`DEC-A07`); `02-architect-claude-opening.md` (`DEC-B09`).
- **Evidence & counterexample:** Round 0 Probe 5 reproduced cross-record `THREAD` crash (`omf_extract.py:258,823`) and identified non-`_TEXT` `PUBDEF`/`LPUBDEF` corruption when `lo > 0` (`:798-807`), linear jump-table misdecode (`:378`), and missing 64-fixup chunking (`:766`); Claude `OBJ-B04` showed `match --all` (`match.py:368-390`) fails any `src =` TU with mismatching siblings.
- **Assumptions:** Any future E4 pilot must preserve Gate-2 governance and handle arbitrary valid OMF32 slices (`lo > 0`, `THREAD`, jump tables, >64 fixups).
- **Practical consequences:** Silent symbol corruption or Gate-2 violations if an E4 pilot is ever launched under incomplete preconditions.

### `OBJ-C15`
- **Severity:** `implementation risk`
- **Exact proposition challenged:** Omission of Watcom 10.0a short-path staging/guard (`tools/wc1/oldcc.py`, E7 Decision D9) from both Architect A's and Architect B's Stage 0 / M2 roadmaps.
- **Source:** `01-architect-gpt-opening.md` (§8, §11); `02-architect-claude-opening.md` (`DEC-B01`, §8); `tools/wc1/oldcc.py@17733f9`.
- **Evidence & counterexample:** EV-3's own post-campaign report (`docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md@17733f9`, "Operational notes") hit a live `wcc386` crash (`rc=5`) in `test_t4spec` at ~130 chars; our R1 probe hit `rc=-11` on `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main/src/playflic/player_reference.c` (115 chars -> ~129+ Windows path chars) because `oldcc.py` resolves symlinks via `realpath` without short-path staging.
- **Assumptions:** CI/worktree/pytest tmp paths can exceed ~90–120 characters.
- **Practical consequences:** Intermittent, baffling `rc=5`/`rc=-11` toolchain failures during `make verify`, `test_t4spec`, and unattended M2 waves.

### `OBJ-C16`
- **Severity:** `blocking architectural`
- **Exact proposition challenged:** `DEC-B01` (Claude) restricting M2 tooling strictly to E0/planner/B1/B2/joint-TUs/T4-state and assigning the remaining 78 functions to `"existing drivers"` (S5).
- **Source:** `02-architect-claude-opening.md` (`DEC-B01`, §8 line 390).
- **Evidence & counterexample:** `candidate_ledger.json@a21772b` and EV-3 `m2_inventory` (`17733f9`: `14 eligible / 76 needs_human / 8 default-skipped`) show **68** remaining not-DONE functions (`61` referenced cross/same-TOML `fn_*` stubs + `7` `low`-conf names) are filtered out of `wc1.overnight` into `needs_human` because existing drivers lack atomic cross-TOML symbol migration and `low`-conf Wave 3R admission.
- **Assumptions:** Automated/supervised batch reconstruction is intended to close M2 reliably rather than manual editing of 68 cross-referenced symbols.
- **Practical consequences:** Leaves the largest M2 bottleneck (68/98 functions) unaddressed despite directly satisfying `DEC-B01`'s own admission criterion (*"directly unblocks not-done in-scope functions"*).

---

## 10. New Decision Proposals

```text
Decision: DEC-C15
Title: Stage-0 Strict Raw-OMF Admission and Hardened wc1.compare Loader Verification
Proposition: In Stage 0 (alongside E0 matcher cutover and wc1.oldcc short-path protection), enforce strict raw-OMF admission before production verification (validating record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, and preserved explicit FRAME encodings) and harden tools/wc1/compare.py to verify loader-relevant LE object flags, entry/stack object+offset, and fixup src_type alongside loaded bytes and fixup targets, after validating attribute parity on baseline Build A (EXP-A03).
Revision: 1
Position: PROPOSE
Reason: Closes both soundness holes exposed by Architect A's Probe Q3 (OBJ-A02: OBJ_EXEC flag flip printed IDENTICAL and src_type omitted; OBJ-A03: bad checksum accepted by E0 and DGROUP vs FLAT FRAME collapsed by wc1.omf) before B1/B2 placement relies on Build A IDENTICAL.
Evidence: Architect A Probe Q3; R1-Probe 3 verifying tools/wc1/compare.py@17733f9 and tools/wc1/omf.py@17733f9 (war.exe objects flags 0x2045/0x2043, 8770 fixups src_type=7, 0 checksum checks in omf.py).
Assumptions: EXP-A03 confirms baseline Build A matches original war.exe on all enforced loader attributes (any genuine wlink difference is adjudicated explicitly, never weakening existing gates).
Dependencies: EXP-A03
```

```text
Decision: DEC-C16
Title: Empirical 3-vs-2 Reclassification of Xfailed T4 Functions and Hardened run_pair State Symmetry
Proposition: Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per R1-Probe 2 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). Harden tools/wc1/cemu.py::run_pair (subject to owner approval and Q-B05 full T4 suite check) to restore all writable emulator RAM (or dirty pages via write hook, excluding read-only code/traps) before the C run, require T4Stub(fn=...) callbacks to store mutable state in emulator RAM or declare an explicit per-run reset hook, and record unwatched global writes in WC1_T4_AUDIT_LOG.
Revision: 1
Position: PROPOSE
Reason: Supersedes DEC-B16 with complete empirical evidence across all 5 xfailed tests (immediately unblocking +2 DONE for 0x23668 and 0x23ae0 in addition to Group B's 0x231cc) while closing both input-asymmetry channels (unwatched RAM mutations and Python-closure stub state) and auditing unwatched global writes.
Evidence: Architect B Probe P4; R1-Probe 2 (probes/r01_probes.py on main@a21772b, identical to 17733f9: 0x231cc/0x23668/0x23ae0 PASS with full writable-RAM restore; 0x23530 and 0x2fcfc still FAIL); tests/test_playflic_t4.py:114-121,406-411,480-556@17733f9; tools/wc1/cemu.py:349-391@17733f9.
Assumptions: Owner approves strengthening cemu.run_pair restoration semantics and Q-B05 confirms zero regressions across all currently passing T4 tests.
Dependencies: Q-B05
```

---

## 11. Probe Log

All Round 1 probes were strictly read-only against the pinned baseline (`e6150b8`), `main@a21772b` (read-only export `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/export-main` with read-only `original` symlink), and `main@17733f9` via `git show`/`git diff`, using the private Wine prefix `/mnt/data/projects/warcraft-1-decompile-wt/cons-c/build/oldcc/wineprefix` and `TMPDIR=/tmp/opencode/cn-gemini`. Zero tracked files or shared assets were modified.

- **R1-Probe 1 — Complete Game-Range Cross-Function `rel32-interior` Census:**
  - *Command:* `nix develop -c python3 /mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/r01_probes.py` (Section 1).
  - *Output:* **9** game-range (`0x104b0..0x3024e`) cross-function `rel32` branches targeting function interiors: `0x20301`/`0x2030b` (`NetSerialIsr -> NetSerialIsrFifo+0x4c`), `0x20719`/`0x2072f`/`0x2073c`/`0x207a9` (`NetModemWaitResponse_tail -> NetModemWaitResponse+0x1e/+0x1c`), `0x23310`/`0x23321` (`IntroOpWaitAnim -> IntroOpPlayFrames+0x6e`), `0x2f6df` (`EndCheckSurvive -> MissionDefeat+0xa`).
  - *Limitation:* Static Capstone decode of direct relative branches; excludes indirect jumps.
- **R1-Probe 2 — Complete `Q-B01` Test Across All 5 Xfailed T4 Functions:**
  - *Command:* `nix develop -c python3 /mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/r01_probes.py` (Section 2, after verifying `git diff a21772b 17733f9 -- tools/wc1/cemu.py tests/test_playflic_t4.py tests/test_mod_2efd0_t4.py` = `0` lines). Snapshotted & restored all writable Unicorn regions (`0x50000..0x6ffff`, `0x800000..0xffffff`, `0xef00000..0xeffffff`) between original and C calls in memory.
  - *Output:*
    - `test_intro_op_wait_sound` (`0x231cc`): STOCK FAIL (`0x801130: 30 != 0c`, unwatched `0x800010: 3 -> 0`) -> **FULL-RESTORE PASS**.
    - `test_intro_op_start_credits` (`0x23530`): STOCK FAIL (`0x59eb9: 01 != 00`) -> **FULL-RESTORE FAIL** (`0x59eb9: 01 != 00`, both `run_spec` calls).
    - `test_intro_run_script` (`0x23668`): STOCK FAIL (`0x801130: 68 != 50`, unwatched `0x800020: 0 -> 1`) -> **FULL-RESTORE PASS**.
    - `test_intro_play` (`0x23ae0`): STOCK FAIL (`0x801130: 74 != 68`, unwatched `0x52c69`, `0x55438`, `0x5ab96`, `0x800020`) -> **FULL-RESTORE PASS**.
    - `test_end_screen` (`0x2fcfc`): STOCK FAIL (`0x80054c: 70 != 50`, unwatched `0x5ab7c..0x5ab84`) -> **FULL-RESTORE FAIL** (`0x80054c: 70 != 50`).
  - *Limitation:* Tested the 5 xfailed functions only; running the entire passing T4 suite under full-RAM restore remains `Q-B05`.
- **R1-Probe 3 — Direct Inspection of `wc1.compare`, `wc1.le`, and `wc1.omf` on `17733f9`:**
  - *Commands:* `git show 17733f9:tools/wc1/compare.py`, Python inspection of `original/install/war.exe` via `wc1.le.LE`, and source inspection of `wc1.omf`.
  - *Output:* `war.exe` objects `[(1, 0x10000, 0x3212b, 0x2045), (2, 0x50000, 0x155f0, 0x2043)]`, `Entry: 0x34584`, `ESP: 0x655f0`, `Fixup src_types: Counter({7: 8770})`. `compare.py:24-27,45-47` never compares `oa.flags == ob.flags` and omits `src_type` from `fa`/`fb`. `omf.py` has `0` checksum checks and drops explicit `FRAME` method/index encodings.
  - *Limitation:* Read-only inspection; baseline Build A attribute match remains **EXP-A03**.
- **R1-Probe 4 — EV-3 Diff Check & Live Watcom 10.0a `rc=-11` Path/Wine Failure:**
  - *Commands:* `git diff a21772b 17733f9 -- tools/wc1/{oldcc,build,emit,match,cemu,compare,omf}.py tests/test_{playflic,mod_2efd0}_t4.py`, plus attempting full-module `test_playflic_t4.py` execution via `oldcc.py`.
  - *Output:* `0` diff lines across all 9 files (EV-3 fixed `t3_audit.py` and `m2_inventory.py`, leaving `oldcc.py` unchanged). Invoking `cemu.load` on `src/playflic/player_reference.c` returned `compile failed (Watcom 10.0a, rc=-11, 0.1s)` both via the 115-char path and via symlink `/tmp/opencode/cn-gemini/m` (which `oldcc` resolves via `realpath`), reinforcing `OBJ-C15` (short-path staging in `oldcc.py` + Wine stability).
  - *Limitation:* Did not isolate whether the third `rc=-11` invocation in `cons-c` (83-char path) was stale wineserver state vs path length; short-path staging + clean worker isolation in `oldcc.py` addresses the ~129-char crash class directly confirmed in E7 and EV-3.

---

## 12. Source Index

- **Round 1 Inbox (verified SHA-256):**
  - `00-PROPOSITION-INDEX.json` (`1ade8e0e1d3c20b924386f67407d808f28ec0f6eb958a92c70bf27ba1d76558`)
  - `01-architect-gpt-opening.md` (`22477c0cf5f8f211d459c5ec72f26cdb7b0c24903bc6dc5e659f696b6b53b7c1`)
  - `02-architect-claude-opening.md` (`9905f1b405acd6e3bef445fd697d255de6aebb0f29d10d2c328035aadc047203`)
- **Consilium Baseline (`research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`):**
  - `docs/research/build-codegen/{E0..E8,summary,decisions}.md@e6150b8`
  - `experiments/build_codegen/{e0/matcher_proto.py,e3/partial_matcher.py,e4/omf_extract.py,e5/omf_b3.py,e6/mf_cemu.py}@e6150b8`
  - `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/{rev-e3-01,rev-e4-01,rev-e5-02,rev-e8-02}.md@e6150b8` (`06235f6`)
- **RFC Under Reconsideration (`architecture/build-codegen-rfc@6f319ac8ff780bb45ff028d006216016fc932a13`):**
  - `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (blob `e81b117a1ece4f90e8b5cf17c0085b9cfb441b19`)
- **Production Mainline (`EV-1: main@a21772b8140b4b07012cde8da7da18ad3f6d56b6`; `EV-3: main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`):**
  - `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/{report.md,e7_snapshot_revalidation.json}@17733f9`
  - `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json}@a21772b`
  - `tools/wc1/{compare.py,omf.py,omfpatch.py,cemu.py,t4spec.py,match.py,build.py,emit.py,oldcc.py,t3_audit.py,m2_inventory.py}@17733f9`
  - `tests/{test_playflic_t4.py,test_mod_2efd0_t4.py}@17733f9`
- **Private Probe Artifacts (Architect C runtime directory):**
  - `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/probes/{run_probes.py,run_probes2.py,run_probe7b.py,r01_probes.py}`
  - Round 0 position: [CONSILIUM-R00-POSITION.md](file:///mnt/data/projects/warcraft-1-decompile-wt/cons-c/CONSILIUM-R00-POSITION.md)
  - Round 1 durable copy: [CONSILIUM-R01-CROSSREVIEW.md](file:///mnt/data/projects/warcraft-1-decompile-wt/cons-c/CONSILIUM-R01-CROSSREVIEW.md)
