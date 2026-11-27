# Build & Codegen Infrastructure — Architecture Consilium
## Round 2 — Responses and Position Revision (Architect C — Gemini)

- **Author:** Architect C — Gemini (`Gemini 4 Neon (High)`, harness `agy 1.5.17`)
- **Consilium Baseline (unchanged):** `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`
- **RFC Under Reconsideration:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`
- **Evidence Revisions:** `EV-1` (`main@a21772b8`), `EV-2` (`d5d4d2c6`), `EV-3` (`main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`)
- **Reviewed Round 1 Cross-Reviews (verified SHA-256):**
  - `00-PROPOSITION-INDEX.json` (`62db5e6ae8d2d165ebd617d2f686f62a3bd731022e05881a6923ee1b3e3f23d8`, 48 live decisions)
  - Architect A — GPT (`01-architect-gpt-crossreview.md`, `482cbb192515d260ecdc9e878361b2bd0a6ea0a6ce5feed8370c41f37d109f5d`)
  - Architect B — Claude (`02-architect-claude-crossreview.md`, `ee07dd4bfd85cd8d706da39f262739f3eb7cfb601327ea52cd658d79869806d5`)

---

## 1. Disposition of Every Substantive Objection and Challenge Directed at Architect C

### 1.1 Objections from Architect A (GPT)

1. **`OBJ-A09` (GPT) — Attacks `DEC-C01` / `DEC-C05` (planner acceptance equated with integrated buildability; "SHA-256 IDENTICAL" overclaim):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** `tools/wc1/compare.py@17733f9` checks a loader projection (loaded image, entry, stack, target fixups) rather than a whole-EXE SHA-256 and currently omits LE object flags and fixup `src_type` (`OBJ-A02`). Moreover, a clean `PlacementPlan` is preflight admissibility, whereas actual assembly (NASM), linking (`wlink`), and hardened `wc1.compare` produce the observed `IntegratedResult`.
   - **Resulting change:** `DEC-C01` (rev 2) and `DEC-C05` (rev 2) separate `PlacementPlan` (preflight) from `IntegratedResult` (actual assemble + link + hardened compare) and drop "SHA-256 IDENTICAL".

2. **`OBJ-A10` (GPT) — Attacks `DEC-C02`/V2 (blanket rule forcing `UNSUPPORTED` on every cross-function edge in `FunctionMatch`):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** E1 Group A demonstrates locally matching helper bodies targeting a sibling tail even when the owner mismatches. Fixing E2 Cause B requires bounding *intra-function* branch closure to `[orig_fn.start, orig_fn.start + fn_len)` (not the first public's linear window) while attaching cross-function sibling edges as explicit external context obligations on `FunctionMatch`—without ever minting `RegionMatch` or placement permission.
   - **Resulting change:** `DEC-C02` (rev 2) replaces the blanket `UNSUPPORTED` rule with function-scoped local bounds plus explicit sibling-context obligations (never minting placement permission).

3. **`OBJ-A11` (GPT) — Attacks `DEC-C03` & `DEC-C10` (V4 five predicates insufficient to prove `CONST` gap non-use; should not gate E0):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** GPT's Probe Q2 (`const_gap (5,8)`, relocations only at `0` and `8`, computed read `p[5]` returning `0x8d` vs `0x73`) decisively proves that static relocation-site absence does not rule out computed or overlapping access, and that keeping ASM in Build A only preserves original bytes rather than proving source-data equivalence. Combined with Claude's `OBJ-B20`, V4 must not block Stage-0 E0 admission.
   - **Resulting change:** Withdraw `DEC-C03` (superseded by `DEC-B21` + `DEC-C10` rev 2); decouple `DEC-C02` (rev 2) so Stage-0 E0 fails closed on `CONST` pad mismatches; require independent extent/access evidence ruling out computed/overlapping reads and explicit proof disclosure for any future Stage-3 `CONST` gap exemption in `DEC-C10` (rev 2).

4. **`OBJ-A12` (GPT) — Attacks `DEC-C11` (freezing single-function `cemu` during M2; memory-only restore misses `CF`/host writes; over-broad multi-function gate):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** GPT's Probe Q1 proved a carry-flag-only (`CF`) false pass on watched memory and showed Unicorn guest write hooks miss host `mem_write` calls. Independently, Claude's R1-P4 and my R1-Probe 2 proved 3/5 xfailed PLAYFLIC tests fail solely due to `cemu.run_pair` state asymmetry today. Additionally, `src/playflic/player_reference.c@17733f9` already holds 20 functions tested under single-function `cemu`.
   - **Resulting change:** Adopt `DEC-A11` and revise `DEC-C16` (rev 2) to enforce full paired initial-state equivalence (CPU/flags including `EFLAGS`/`CF`, all mapped writable memory, and host/stub accounting) immediately for all T4s; revise `DEC-C11` (rev 2) to trigger E6 on demand (sibling substitution, callbacks, or R2 pointers) with `EXP-4` optional.

5. **`OBJ-A13` (GPT) — Attacks `DEC-C05` (`t - (ia+2)` hardcoded formula and mandatory `_loc_<addr>` `PUBDEF` synthesis for `rel32-interior`):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** GPT's Probe Q3 (`jcxz` = `67 e3 01`, length 3 -> true next IP is `ia + 3`, `disp = 1` vs erroneous `PC+2 -> 2`) refutes hardcoding `+2`; always use decoded `next_ip = ia + insn.size` and typed instruction encodings. Second, both GPT (`OBJ-A13`) and Claude (`OBJ-B23`, P5 linking `0x2f6df` `IDENTICAL` with zero OMF mutation) show that synthesizing `_loc_<addr>` `PUBDEF`s in C objects puts an unnecessary post-codegen OMF transform onto the M2 critical path.
   - **Resulting change:** `DEC-C05` (rev 2) mandates decoded `next_ip = ia + insn.size` + typed encodings, drops `_loc_<addr>` `PUBDEF` synthesis from M2 (using unified piece-local expression / verified fixed displacement for non-exported-entry cross-object branches), keeps `extern` symbolic for `rel32` to exported entries, and adds `DEC-B19` per-object legacy exclusion.

6. **`OBJ-A14` (GPT) — Attacks `DEC-C08` (omission of owner Gate-2 / `match --all` semantics decision for selective extraction):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** `tools/wc1/match.py:368-390@17733f9` fails any `src =` TU with a mismatching public, making partial-region T3 a Gate-2 semantics change requiring explicit owner approval (`OBJ-B04`, `DEC-B09`).
   - **Resulting change:** `DEC-C08` (rev 2) adds explicit owner Gate-2 disposition as precondition #1 for any future post-M2 extraction pilot.

7. **`OBJ-A15` (GPT) — Attacks `DEC-C07` / `DEC-C06` (serializing routine reconstruction and Group B behind generic B1/B2; calling all 5 xfails C bugs):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** Claude's P3 proved Group B builds `IDENTICAL` under current production tools (and E1 already verified it under E0), `BULLET.C` and routine reconstruction can run in parallel with Stage 0/1 tooling, and both R1-Probe 2 and Claude R1-P4 proved only 2 of the 5 xfailed tests (`0x23530`, `0x2fcfc`) are genuine ref-C divergences.
   - **Resulting change:** `DEC-C06` (rev 2) removes any generic B2 dependency from Group B (also withdrawing my R1 `OBJ-C13`); `DEC-C07` (rev 2) restructures M2 into parallel tracks with verified 3-vs-2 xfail classification.

8. **`OBJ-A16` (GPT) — Attacks `DEC-C12` & `DEC-C13` (shared literals as hard merges; PARA alignment on post-table publics; `-5r` as default family):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** E8 had only 1 synthetic shared-literal positive (does not exclude explicit externs/pooling); `PARA` applies at the segment base (not a public after a leading table like `ChooseCampaignDialog`); E7 records 51 `only_4r` T3s and `-3r` also spaces at 4 bytes.
   - **Resulting change:** `DEC-C12` (rev 2) and `DEC-C13` (rev 2) align fully with `DEC-A10`, `DEC-B10`, `DEC-B11`, and segment-base `PARA` qualification.

9. **`OBJ-A17` (GPT) — Attacks `DEC-C04` (obsolete `t3_audit` fixes after EV-3; arbitrary `<= 48` staging cap doesn't bound `-i=` / `Z:\` paths) & `DEC-C02` (strict raw OMF binding):**
   - **Disposition:** **`UPHOLD`**
   - **Evidence / argument:** EV-3 (`main@17733f9`) fixed all 3 `t3_audit.py` R3 defects (`t3_audit.py:160-162,1197-1206,1786-1790`), while `oldcc.py` still passes unguarded `Z:` paths (`oldcc.py:123-125,201-203`). A short staging dir alone does not bound `-i=` include paths or translated Windows arguments.
   - **Resulting change:** `DEC-C04` (rev 2) drops the delivered `t3_audit` clause and specifies measuring/guarding EVERY compiler-facing Windows path (`src`, `-fo`, `-i=`, `TMPDIR`) with unchanged compile/include semantics; `DEC-C02` (rev 2) incorporates strict raw-OMF admission (`OBJ-A03`).

10. **`OBJ-A18` (GPT) — Attacks `DEC-C08` & `DEC-C09` (64-fixup chunking not an established overflow; broad codec rewrite & exhaustive Wave 4B unnecessary):**
    - **Disposition:** **`UPHOLD`**
    - **Evidence / argument:** GPT's Probe Q3 linked a single `1,280`-byte `FIXUPP32` record with **256** `off32` fixups cleanly on OW2 `wlink` (`256 * 11 = 2,816 < 65,535` OMF record limit), refuting my Round 0 claim that missing 64-fixup chunking is a proven overflow bug. Meanwhile GPT Q4 independently confirmed my Probe 5b (`PUBDEF` corruption: `Member_` rebased `DATA+4 -> DATA+0`, `First_` dropped), and both A and B confirmed Probe 5a (`THREAD` per-record reset). Also agreed: permissive `libsig` readers need not be migrated.
    - **Resulting change:** `DEC-C08` (rev 2) drops the 64-fixup claim and exhaustive Wave 4B gate while keeping Probe 5a, 5b (Q4-confirmed), 5c, `rev-e4-01` F1–F4, and owner Gate-2 approval; `DEC-C09` (rev 2) scopes the shared strict OMF32 codec strictly to verification and admitted post-M2 transforms.

11. **Unlabelled factual corrections in GPT §3 & §4 (E6 callback registers, R0 §15 path typos, R0 §9 scaling claims, R0 §8 Stage 4 depending on all of Stage 3):**
    - **Disposition:** **`UPHOLD` ALL FOUR.**
    - **Evidence:** Direct inspection of `experiments/build_codegen/e6/mf_cemu.py:25@e6150b8` confirms `PRESERVED_REGS = ('ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')` + `esp` (not `ds`/`DF`, corrected in `DEC-C11` rev 2). R0 §15 path typos (`results/e0/summary.json`, `results/e1/build_a.json`, `test_e0_matcher.py`) are corrected to actual pinned paths (`results/e0/{controls.json,t3_reaudit.json}`, `results/e1/results.json`, `test_e0.py`). R0 §9 qualitative scaling/code-size figures are retracted as unmeasured estimates. `DEC-C07` (rev 2) decouples M3 Build B from optional Stage-3 Build A consolidation paths.

---

### 1.2 Objections from Architect B (Claude)

12. **`OBJ-B18` (Claude) — Attacks "5 real ref-C divergences" (`DEC-C07`):**
    - **Disposition:** **`UPHOLD`** (independently confirmed identically by my R1-Probe 2 and Claude R1-P4: `0x231cc`, `0x23668`, `0x23ae0` pass under full state restore; `0x23530`, `0x2fcfc` fail). Formally revised in `DEC-C07` (rev 2) & `DEC-C16` (rev 2).

13. **`OBJ-B20` (Claude) — Attacks `DEC-C02` depending on `DEC-C03`/EXP-1:**
    - **Disposition:** **`UPHOLD`** (decoupled in `DEC-C02` rev 2; Stage-0 E0 fails closed on `CONST` pad bytes).

14. **`OBJ-B21` (Claude) — Attacks `DEC-C11` placing paired-state reset only in multi-function T4:**
    - **Disposition:** **`UPHOLD`** (moved to immediate M2 requirement for all T4s in `DEC-C11` rev 2 & `DEC-C16` rev 2, adopting `DEC-A11`).

15. **`OBJ-B22` (Claude) — Attacks `DEC-C03` / `OBJ-C01` ("non-deterministic across consecutive runs" & Stage-0 timing):**
    - **Disposition:** **`UPHOLD` on Stage-0 timing & terminology, with one empirical clarification (R2-Probe 1).**
    - **Evidence / argument:** R2-Probe 1 compiled the exact same fixed file `/tmp/opencode/cn-gemini/p7/net_sav.c` 4 consecutive times inside one session: all 4 emitted identical `gap[5:8] = 660061` (confirming Claude R1-P2's within-session determinism!). Yet across 3 separate sessions on that **exact same fixed path**, the pad bytes differed (`73002f`, `760061`, `660061` vs `war.exe` `8d75e0`). Thus Claude's term **"environment-dependent"** (`DEC-B21`: path/session/heap-environment dependent, not random per consecutive call) is strictly more accurate, and confirms both cache-digest normalization (`DEC-B21`) and Build A ASM `physical_provider`.
    - **Resulting change:** Withdraw `DEC-C03` in favor of `DEC-B21` (with `OBJ-A11`'s access-proof condition) + `DEC-C10` (rev 2) requiring identical matcher + `build.place()` enforcement (`build.py:94-104@17733f9`).

16. **`OBJ-B23` (Claude) — Attacks `DEC-C05`'s `_loc_<addr>` `PUBDEF` synthesis for `rel32-interior`:**
    - **Disposition:** **`UPHOLD`** (same as `OBJ-A13`; dropped in `DEC-C05` rev 2).

17. **`OBJ-B24` (Claude) — Attacks `DEC-C07` / `OBJ-C04` framing ("68 blocked by symbol migration" and "1,002/1,010"):**
    - **Disposition:** **`UPHOLD`.** All 61 placeholder rows have `c_status = "none"`, `missing = ["name", "C"]`, `requires_llm = True` (40 cross-TOML + 21 same-TOML). Reconstruction (name + C + proof) is the binding constraint; deterministic rename / Wave 3R tooling is a supporting enabler, and `1,002/1,010` is a scope upper bound, not a guaranteed yield. Revised in `DEC-C07` (rev 2).

18. **`OBJ-B25` (Claude) — Attacks `DEC-C11`'s wording ("hard prerequisite before consolidating any T4 function into a multi-function `.c`"):**
    - **Disposition:** **`UPHOLD`** (same as `OBJ-A12`; `player_reference.c` already holds 20 functions tested today; E6 triggers on intra-TU sibling substitution, callbacks, or R2 pointer identity). Revised in `DEC-C11` (rev 2).

19. **`OBJ-B26` (Claude) — Attacks `DEC-C13` ("-5r primary default" / "[FACT] predominantly `-5r`") and `DEC-C12` ("`non_16_aligned_start` 100% precision"):**
    - **Disposition:** **`UPHOLD`** (E8 measured `0.800`/`0.836`/`0.618`; E7 records `51 only_4r`). Revised in `DEC-C12` (rev 2) & `DEC-C13` (rev 2).

20. **`OBJ-B27` (Claude) — Attacks forbidding B2 only under global `--legacy` (missing automatic per-object `Unplaceable` fallback at `build.py:310-314@17733f9`):**
    - **Disposition:** **`UPHOLD`.** Direct inspection of `tools/wc1/build.py:310-314@17733f9` confirmed silent per-object legacy fallback. Incorporated into `DEC-C05` (rev 2) and accepted `DEC-B19`.

---

## 2. Retained Decisions

- **`DEC-C14`** (Revision `1`, SHA-256 `66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf`): *Reject Premature Multi-Backend Framework Abstractions in Warcraft I.* Unchanged (already accepted by both A and B).
- **`DEC-C15`** (Revision `1`, SHA-256 `a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8`): *Stage-0 Strict Raw-OMF Admission and Hardened `wc1.compare` Loader Verification.* Unchanged (already specifies measuring attribute parity on baseline Build A via `EXP-A03` before enforcing, aligning with `DEC-A02`, `DEC-A03`, and `DEC-B20`).

---

## 3. Changed Decisions (Incremented to Revision 2)

1. **`DEC-C01` (Rev 1 `89590ee5...` -> Rev 2 `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de`):**
   - *Old (Rev 1):* Retain 3-level separation (`FunctionMatch`, `RegionMatch -> VerifiedRegion`, `BuildAPlacementPlan`) across all tools.
   - *New (Rev 2):* `Maintain four explicit verification and integration outcomes: FunctionMatch (local body diagnostic with explicit external context obligations), RegionMatch -> immutable matcher-minted VerifiedRegion (closed object/region proof), PlacementPlan (single derived preflight partition plan shared by check_t3_buildable, wc1.build, wc1.emit, batch_driver, wave4a, and m2_inventory), and IntegratedResult (actual assemble, link, and hardened wc1.compare receipt). Do not add a separate CandidateRegion runtime class or persistent proof/CU metadata DB in M2.`
   - *Persuading evidence:* `OBJ-A09` (planner preflight != integration receipt) and `DEC-B14` (minimal M2 entity set). *Dependent impact:* Updates `DEC-C05` rev 2.

2. **`DEC-C02` (Rev 1 `32bdbb10...` -> Rev 2 `8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b`):**
   - *Old (Rev 1):* Replace `match.py` with E0 engine, function-scoped bounds forcing `UNSUPPORTED` on cross-function edges, depending on `DEC-C03`/V4.
   - *New (Rev 2):* `Reimplement E0 bidirectional Normalized Addressing Obligation verification in tools/wc1/match.py (importing nothing from experiments/) with strict raw-OMF admission (record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, preserved explicit FRAME encodings) and all 55 controls as production tests, audited over every live declared T3 at cutover. Evaluate FunctionMatch intra-function branch closure against [orig_fn.start, orig_fn.start + fn_len) while attaching explicit sibling-context obligations (never minting placement permission); preserve trimmed_branch_target across all modes; fail closed on CONST pad mismatches (no Stage-0 V4 dependency).`
   - *Persuading evidence:* `OBJ-A03`, `OBJ-A10`, `OBJ-A11`, `OBJ-B20`, `DEC-B15`. *Dependent impact:* Removes Stage-0 blocker on `EXP-1`/`DEC-C03`.

3. **`DEC-C04` (Rev 1 `6110ad1c...` -> Rev 2 `083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37`):**
   - *Old (Rev 1):* Fixed `<= 48` char staging path in `oldcc.py` plus 3 `t3_audit.py` R3 fixes.
   - *New (Rev 2):* `Implement a measured compiler-facing Windows-path length guard and short-path staging policy in tools/wc1/oldcc.py checking all compiler-facing arguments (source, -fo, -i=, TMPDIR, translated Z: paths), failing fast with [TOOLCHAIN ERROR] before Watcom 10.0a path-buffer crashes while verifying unchanged compile/include semantics across checkout depths. (The three t3_audit.py R3 defects from rev 1 are delivered and closed as of EV-3 main@17733f9.)`
   - *Persuading evidence:* EV-3 `main@17733f9` + `OBJ-A17` + Claude `R1-P5`. *Dependent impact:* Standalone Stage-0 reliability item.

4. **`DEC-C05` (Rev 1 `16a616ad...` -> Rev 2 `0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d`):**
   - *Old (Rev 1):* B1 + B2 with `t-(ia+2)`, `omfpatch` `_loc_` `PUBDEF` for `rel32-interior`, global `--legacy` guard only.
   - *New (Rev 2):* `Implement Fix B1 (leading-byte region base first_entry_addr - first_entry_off gated on E0 RegionMatch of [0,k), zero overlap/foreign entry, branch analysis using physical table_start) and Unified Fix B2 inside the single derived PlacementPlan: keep extern symbolic rel32 for exported entries; emit remaining cross-object ASM relative branches (B2-interior, B2-entry, B2-span, and rel32-interior such as 0x2f6df with zero M2 OMF PUBDEF synthesis) via NASM piece-local label expressions (preferred, using decoded next_ip = ia + insn.size and typed encodings with assembled-byte verification) or verified literal displacement fallback, strictly rejecting any span containing a global --legacy or automatic per-object Unplaceable legacy-placed object (DEC-B19), explicitly checking cross-piece fallthrough adjacency, recording Build A placement debt, and requiring IntegratedResult with hardened wc1.compare (DEC-B20/DEC-C15). Qualify IntroOpSyncSound standalone regression tests by mode: rejected under legacy or B2-disabled, accepted only with explicit B2-span debt under in-place B2, zero debt as Group B.`
   - *Persuading evidence:* `OBJ-A09`, `OBJ-A13` (Q3 `jcxz`), `OBJ-B23` (P5 `0x2f6df`), `OBJ-B27` (`build.py:310-314`), `OBJ-C11`. *Dependent impact:* Eliminates OMF writer changes from M2 critical path.

5. **`DEC-C06` (Rev 1 `3bd8b1d5...` -> Rev 2 `ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23`):**
   - *Old (Rev 1):* Group B tied to Stage 1 / generic B2.
   - *New (Rev 2):* `Admit proof-gated multi-function ReconstructedTUs when the whole compiled object passes RegionMatch and Build A IntegratedResult, preferring whole-TU co-compilation over B2 placement debt for shared-epilogue clusters. Pilot E1 Group B (IntroOpPlaySound 0x2315c, IntroOpSyncSound 0x23170, IntroOpWaitSound 0x231cc) as an independent -5r TU without waiting on generic B2, subject to owner confirmation of AGENTS.md ground-rule wording, dual-compiler checks, full make verify, and owner review of any xfailed PLAYFLIC test adjustment.`
   - *Persuading evidence:* Claude P3, `OBJ-A15`, Claude §4.5 (`test_intro_op_wait_sound` owner test checkpoint). *Dependent impact:* Unblocks +3 DONE immediately on an independent track.

6. **`DEC-C07` (Rev 1 `9be785e0...` -> Rev 2 `f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999`):**
   - *Old (Rev 1):* Serial Stage 1 -> Stage 2; framed 68 as "blocked by symbol migration", 5 as "real ref-C bugs", Stage 4 depending on all of Stage 3.
   - *New (Rev 2):* `Prioritize genuine M2 completion (98 remaining not-DONE on EV-3 main@17733f9) via parallel tracks: (a) Stage 0/1 verification hardening, single planner, B1/B2, Group B pilot, and T4 paired-state symmetry (DEC-A11/DEC-B18/DEC-C16, immediately addressing 3 of 5 xfailed PLAYFLIC tests while 0x23530 and 0x2fcfc remain genuine ref-C bugfixes); (b) routine area reconstruction (BULLET.C and the 61+7 name/C backlog, supported by lightweight deterministic rename/Wave 3R enablers, reporting reconstruction yield as an upper bound rather than a deterministic guarantee); and (c) owner evidence packets for the 8 scope/discovery items. Defer Fix B3, selective extraction (E3/E4), demand-led E6 Group machinery, and CU hypothesis databases to the post-M2/M3 track; decouple M3 Build B from optional Build A consolidation paths.`
   - *Persuading evidence:* `OBJ-A15`, `OBJ-B18`, `OBJ-B24`, GPT §4, R1-Probe 2 / Claude R1-P4. *Dependent impact:* Removes artificial serialization of M2 reconstruction and M3 Build B.

7. **`DEC-C08` (Rev 1 `ee55d250...` -> Rev 2 `6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00`):**
   - *Old (Rev 1):* Deferred E4 requiring all 8 defects (incl. 64-fixup) and exhaustive Wave 4B/`-5r`, omitting owner Gate-2 decision.
   - *New (Rev 2):* `REJECT adopting experiments/build_codegen/e4/omf_extract.py@e6150b8 or selective OMF extraction during M2 or as a default consolidation path. Whole-TU RegionMatch is the primary integration path. Any future narrow post-M2 extraction pilot requires: (1) explicit owner decision on Gate-2 / match --all semantics for src files with mismatching publics (DEC-B09); (2) proven canonical-TU benefit; (3) implementation over the shared strict OMF32 subset (DEC-C09) fixing confirmed Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), Probe 5c (typed table/code model), and rev-e4-01 F1-F4; and (4) post-transform verification and Build A IntegratedResult (without mandating unproved 64-fixup chunking or exhaustive Wave 4B).`
   - *Persuading evidence:* `OBJ-B04`/`OBJ-A14` (Gate-2 governance), `OBJ-A18` (Q3 256-fixup link), GPT Q4 & Claude R1-P6 confirming Probe 5a/5b. *Dependent impact:* Aligns with `DEC-A07` and `DEC-B09`.

8. **`DEC-C09` (Rev 1 `dfab7c56...` -> Rev 2 `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b`):**
   - *Old (Rev 1):* Broad consolidation including 64-fixup chunking into `tools/wc1/omf.py`.
   - *New (Rev 2):* `Before landing Fix B3 or any future selective OMF extraction pilot (post-M2), share one tested strict OMF32 record/fixup codec (record bounds, nonzero checksums, preserved explicit FRAME encodings, persistent cross-record THREAD, format/linker-verified record-length bounds) across verification and admitted OMF transforms, while leaving permissive library-signature readers untouched and avoiding unnecessary omfpatch refactoring during M2.`
   - *Persuading evidence:* `OBJ-A18` & Claude `DEC-C09` condition. *Dependent impact:* Scoped strictly post-M2 for transforms.

9. **`DEC-C10` (Rev 1 `0755146f...` -> Rev 2 `b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f`):**
   - *Old (Rev 1):* Stage 3B Fix B3 strictly conditioned on R0 V4 (`DEC-C03`).
   - *New (Rev 2):* `Keep semantic_owner separate from physical_provider and defer Fix B3 to the post-M2/M3 track (triggered by justified need such as Q-B08). Admit B3 initially for strictly verified whole segments over the shared strict OMF32 subset (DEC-C09) with RFC §8.2 constraints 1-5 and rev-e5-02 mutability/aliasing guards. Any future CONST inter-literal alignment-gap rule (per DEC-B21) must additionally: apply identically in matcher and build.place(), force Build A physical_provider = ASM, be explicitly disclosed in the proof receipt, and require independent extent/access evidence ruling out computed or overlapping reads (OBJ-A11).`
   - *Persuading evidence:* `OBJ-A11` (Q2), `OBJ-B20`, `DEC-B21`, `build.py:94-104`. *Dependent impact:* Replaces withdrawn `DEC-C03` for Stage-3 data verification.

10. **`DEC-C11` (Rev 1 `7a204425...` -> Rev 2 `46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090`):**
    - *Old (Rev 1):* Keep single-function `cemu` unchanged in M2; require full E6 + `EXP-4` before any multi-function `.c` T4; misstated ABI regs as `ds`/`DF`.
    - *New (Rev 2):* `Keep full paired initial-state symmetry (DEC-A11/DEC-B18/DEC-C16) mandatory immediately for ALL T4 tests (single- and multi-function), independent of E6. Adopt E6 multi-function machinery (contiguous VerificationBoundary, symbol_aware_reloc primary + c_entry_hook defense in depth, generator callbacks with pre-restore ABI checks on PRESERVED_REGS ebx/ecx/edx/esi/edi/ebp plus esp, R2 typed pointer identity, and full t4spec production audit parity per DEC-A08) on demand whenever any M2 or post-M2 witness requires substituting an intra-TU sibling, executing real callbacks, or comparing logical pointer identities; treat switch-table relaxation and LogicalConstDataPtr (EXP-4) as optional extensions when needed.`
    - *Persuading evidence:* `OBJ-A12`, `OBJ-B21`, `OBJ-B25`, `mf_cemu.py:25@e6150b8`. *Dependent impact:* Aligns with `DEC-A08`, `DEC-A11`, `DEC-B12`, `DEC-B18`.

11. **`DEC-C12` (Rev 1 `9f75f979...` -> Rev 2 `7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa`):**
    - *Old (Rev 1):* Placed `shared_const_string_literal` in Class 1, claimed `non_16_aligned_start` 100% precision, planned `cu_hypotheses.toml` in Stage 3D.
    - *New (Rev 2):* `Explicitly REJECT _DATA/_BSS staircase splits, call_locality_drop, none16 auto-splits, weighted CU boundary scoring, empty-S(f) auto-splitting, and any automatic mutation of analysis/modules.toml or automatic source consolidation. Maintain original CU recovery strictly as an analyst-facing premise-carrying constraint graph (storage deferred to M3): shared_epilogue as a one-directional merge constraint under verified compiler/linker provenance; non_16_aligned_start evaluated at the actual segment base under a PARA-segment premise (with measured corpus precision 0.800/0.836/0.618, never 100%); shared_const_string_literal as conditional premise-dependent evidence requiring exclusion of explicit shared externs and linker pooling; filenames, zero16, none16, style_transition, and S(f)-disjointness as candidate generators preserving competing hypotheses.`
    - *Persuading evidence:* `OBJ-A16`, `OBJ-B26`, `E8-cu-boundaries.md@e6150b8`. *Dependent impact:* Aligns with `DEC-A10` & `DEC-B13`.

12. **`DEC-C13` (Rev 1 `29bf51db...` -> Rev 2 `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02`):**
    - *Old (Rev 1):* Codified `-5r` as primary default family for contiguous CU reconstruction.
    - *New (Rev 2):* `Replace RFC §2.2.5 alignment premises with E2 empirically measured compiler behavior: Watcom 10.0a function spacing is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot (with PARA 16-byte _TEXT SEGDEF for tested -ot), and 1 byte under -os/-od; OW2 uses 16 bytes under -4r and -5r. Keep -4r as the single-file project default with additive E7 presets (DEC-B11), rank -5r as the first-tried candidate family for multi-function -ot TUs requiring 4-byte spacing without claiming it was the universal 1994 project flag, and keep EXP-2/Q-B06 (5r -d1+ -zp1 and 5r -od) as optional additive probes.`
    - *Persuading evidence:* `OBJ-A16`, `OBJ-B26`, `DEC-B10`, `DEC-B11`. *Dependent impact:* Eliminates historical-flag overclaim.

13. **`DEC-C16` (Rev 1 `d2738595...` -> Rev 2 `06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95`):**
    - *Old (Rev 1):* Restored writable emulator RAM + stub rule without CPU/flags (`EFLAGS`/`CF`) checkpointing.
    - *New (Rev 2):* `Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per identical independent results of R1-Probe 2 and Claude R1-P4 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). Adopt full paired initial-state equivalence in tools/wc1/cemu.py::run_pair (combining DEC-A11 and DEC-B18, subject to Q-B05 full T4 suite verification and owner approval for test-meaning/xfail changes): initialize or restore identical per-side CPU/flags (including EFLAGS/CF), all mapped writable memory, and declared/stateless host-stub state; keep restoration strictly separate from watch output assertions; and record restored regions and unwatched global writes in WC1_T4_AUDIT_LOG.`
    - *Persuading evidence:* GPT `DEC-A11` & Q1 (carry-only false pass + host-write gap), Claude `DEC-B18` & R1-P4, my R1-Probe 2. *Dependent impact:* Unifies `DEC-A11`, `DEC-B18`, and `DEC-C16`.

---

## 4. Withdrawn or Superseded Decisions (and Withdrawn Objections)

- **Withdrawn decision: `DEC-C03`** (Rev 1, `2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896`, *Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule*).
  - *Why withdrawn:* `OBJ-A11` (GPT Q2) proved the 5 relocation-based predicates do not exclude computed/overlapping reads, and `OBJ-B20` (Claude D-2) proved V4 must not block Stage-0 E0 admission.
  - *Replaced by:* **`DEC-B21`** (environment-dependent `CONST` pad cache normalization + Stage-0 fail-closed + two-sided matcher/`place()` requirement) combined with **`DEC-C10` (rev 2)** (adding `OBJ-A11`'s independent extent/access evidence and explicit proof disclosure for any future Stage-3 gap rule).
- **Withdrawn Round 1 objection: `OBJ-C13`** (Group B sequencing before E0 matcher). Withdrawn per Claude P3, E1's prior E0 verification of Group B, and `OBJ-A15`.

---

## 5. Unresolved Objections (Still Substantive Pending Peer Revision)

1. **`OBJ-C09` (narrowed to `DEC-B21`):** `DEC-B21` accurately captures environment-dependent `CONST` pad normalization and two-sided matcher/`place()` enforcement, but still needs `OBJ-A11`'s independent extent/access evidence ruling out computed/overlapping reads before any future V4 exemption is enabled. *Resolution condition:* Add `OBJ-A11`'s access-proof requirement to `DEC-B21`.
2. **`OBJ-C10` (narrowed to `DEC-B04` rev 1):** `DEC-B04` rev 1 still specifies raw literal displacement bytes without decoded `next_ip`/piece-local expressions, omits per-object automatic legacy exclusion (`DEC-B19`), omits cross-piece fallthrough, and relies on unhardened `wc1.compare` (`DEC-B20`). *Resolution condition:* Claude's planned `DEC-B04` rev 2 (R1 line 442) incorporating these four items.
3. **`OBJ-C11` (`DEC-B03` rev 1 vs `DEC-B04`):** `DEC-B03` rev 1's unqualified `"IntroOpSyncSound standalone is rejected"` conflicts with `DEC-B04` once in-place B2 is active. *Resolution condition:* Qualify the regression test by mode (rejected under legacy or B2-disabled; accepted only with explicit B2-span debt under in-place B2; zero debt as Group B).
4. **`OBJ-C12` (`DEC-B16` rev 1):** `DEC-B16` rev 1 reclassifies only `IntroOpWaitSound`, omitting `IntroRunScript` (`0x23668`) and `IntroPlay` (`0x23ae0`) proved by both R1-Probe 2 and Claude R1-P4. *Resolution condition:* Claude's planned `DEC-B16` rev 2 (R1 line 444) or adopting `DEC-C16` rev 2.
5. **`OBJ-C14` (narrowed to `DEC-A07` rev 1 & `DEC-B09` rev 1):** `DEC-A07` rev 1 omits owner Gate-2 disposition (`DEC-B09`); both omit confirmed E4 Probe-5a (`THREAD`), Probe-5b/GPT Q4 (non-`_TEXT` `PUBDEF` corruption), and Probe-5c (typed table model). *Resolution condition:* GPT's planned `DEC-A07` rev 2 (R1 line 394) + listing Probe 5a/5b/5c alongside `rev-e4-01` F1–F4.
6. **`OBJ-C15` (Omission of `wc1.oldcc` Windows-path guard from `DEC-B01`):** `tools/wc1/oldcc.py@17733f9` still lacks path-length protection and crashed live in EV-3 (`rc=5`) and R1 (`rc=-11`). *Resolution condition:* Admit `DEC-C04` (rev 2) under the M2 reliability boundary.
7. **`OBJ-C16` (narrowed to `DEC-B01` rev 1 closed list):** Hard-closing `DEC-B01` against lightweight M2 reliability/reconstruction enablers (`oldcc` path guard, strict OMF admission, `compare` hardening, deterministic rename helper) conflicts with `DEC-B01`'s own admission principle. *Resolution condition:* Keep `DEC-B01`'s admission principle open to verified M2 soundness gaps and reconstruction enablers (matching GPT's R1 condition on `DEC-B01`).

---

## 6. New Objections and Decisions

**None.** Every finding from Round 1 cross-reviews, `EV-3`, and Round 2 probes is cleanly absorbed into our Revision 2 decisions (`§3`) and peer proposals (`DEC-A11`, `DEC-B18`–`DEC-B21`). Introducing further overlapping decision IDs would only fragment the ledger.

---

## 7. Convergence Assessment

After Round 1 cross-review and our Round 2 revisions, **no major architectural rift remains** across the core architecture (verification hierarchy, single planner, B1, unified in-place B2 without M2 OMF transforms, Group B joint TU, full paired initial-state symmetry for all T4s, strict raw-OMF admission, measure-first `wc1.compare` hardening, E3/E4 & B3 deferred post-M2, demand-led E6, corrected alignment matrix with additive presets, and analyst-only premise-carrying CU recovery). Remaining open points separate cleanly:

- **Remaining factual disputes requiring decisive experiments:**
  1. **Comparator attribute parity (`EXP-A03` / `DEC-B20`):** Do LE object flags (`0x2045`/`0x2043`), entry/stack object+offset, and fixup `src_type` (`7`) already agree between current Build A and `original/install/war.exe`? *Cheapest decisive probe:* `wc1.le` dump comparing current Build A vs original + `OBJ_EXEC`/`src_type` mutants (<2 min).
  2. **Full T4 regression check under paired-state symmetry (`Q-B05` / `DEC-A11` / `DEC-B18` / `DEC-C16`):** Does restoring CPU/flags + full mapped writable memory break any currently passing T4 test? *Cheapest decisive probe:* Run the existing T4 pytest suite once under full CPU+memory restoration (under short-path `TMPDIR`).
  3. **NASM piece-local B2 link (`EXP-3b`):** Does GPT Q2's piece-local label expression (using decoded `next_ip = ia + insn.size`) link Build A `IDENTICAL` across all 4 B2 functions + standalone `IntroOpSyncSound` + prefixed `jcxz` / per-object legacy negative controls? *Cheapest decisive probe:* Targeted Build A dry-run + link (<10 min).
  4. **Measured `wc1.oldcc` path-length envelope (`DEC-C04` rev 2):** Exact safe Windows-path length bound across `src`, `-fo`, `-i=`, `TMPDIR` with unchanged compile/include output. *Cheapest decisive probe:* Synthetic path-length sweep in `wc1.oldcc` (<2 min).
  5. **Post-M2 only (deferred, non-blocking):** `Q-B06` (`-5r -od` / `-5r -d1+ -zp1` on the 51 `only_4r` T3s); `Q-B08` (count of contiguous consolidations actually requiring B3); `EXP-1` (if B3/natural multi-literal `CONST` is ever triggered, testing `SaveSlotPath` with `OBJ-A11` access-proof negatives).
- **Remaining architectural / ledger-wording alignments (all expected to converge in peer Round 2 revisions):** Combining `DEC-A11` (CPU/flags + host writes) with `DEC-B18` (full memory restore) and `DEC-C16` rev 2 (3-vs-2 reclassification); aligning `DEC-B03`/`DEC-B04` on `IntroOpSyncSound` mode qualification, decoded `next_ip`, fallthrough, and `DEC-B19`/`DEC-B20`; adding Gate-2 governance + E4 Probe 5a/5b/5c to `DEC-A07`/`DEC-B09`; adding `OBJ-A11` access proof to `DEC-B21`; keeping `DEC-B01`'s M2 boundary principle-driven rather than a hard-closed list.
- **Remaining pure design preferences (non-blocking):** Piece-local NASM expression (preferred by A, B §6, C) vs literal-displacement fallback for cross-object fixed-layout branches (both verified against decoded encodings and assembled bytes).

---

## 8. Structured Positions for Every Live Decision

### 8.1 Architect A — GPT (`DEC-A01`–`DEC-A11`)

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: Exact alignment with M2 completion contract, separate T4-to-T3 tracking, and owner T5/gate authority.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: ACCEPT
Reason: Aligned after decoupling Stage-0 E0 from V4 (DEC-C02 rev 2) and adopting strict raw-OMF admission (OBJ-A03) plus live cutover audit. Preserves function-scoped local bounds with explicit sibling-context obligations (OBJ-A10) and trimmed_branch_target.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: ACCEPT
Reason: Single-provider whole-image partition plan plus actual assemble/link/hardened-compare IntegratedResult receipt (OBJ-A09), paired with measure-first attribute validation (DEC-B20) and per-object legacy exclusion (DEC-B19).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: Sound B1 leading-table contract gated on full region bounds, ownership, and checked relocation obligations; ChooseCampaignDialog (0x157e8) already Build A feasibility-verified (Claude P6).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: ACCEPT
Reason: Aligned after upholding OBJ-A13/OBJ-B23 (dropping M2 _loc_ PUBDEF synthesis) and adopting decoded next_ip = ia + insn.size, piece-local expressions across B2-interior/entry/span/rel32-interior, cross-piece fallthrough adjacency, per-object legacy exclusion (DEC-B19), and Group B preference.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: ACCEPT
Reason: Aligned after upholding OBJ-A11 and OBJ-B20: defer B3 post-M2, admit strictly verified whole segments first, and require DEC-B21 + OBJ-A11 independent extent/access evidence for any future CONST gap exclusion.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: CONDITIONAL
Reason: Deferring general extraction is right; rev 1 still omits owner Gate-2 governance (noted by Architect A for R2) and confirmed E4 defects beyond rev-e4-01 F1-F4.
Conditions: (1) Explicit owner decision on Gate-2 / match --all semantics for src files with mismatching publics (DEC-B09/OBJ-A14); (2) fix confirmed E4 Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), and Probe 5c (typed table/code model) over the shared strict OMF32 subset (DEC-C09 rev 2).
Related objections: OBJ-A14, OBJ-B04, OBJ-C03, OBJ-C14
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: CONDITIONAL
Reason: Sound multi-function T4 boundary/callback/ABI/R2/audit-parity contract; rev 1 just needs Architect A's noted R2 separation from immediate single-function paired-state hardening (DEC-A11).
Conditions: Apply DEC-A11 paired initial-state equivalence immediately to all current T4 tests independently of demand-led E6 multi-function adoption.
Related objections: OBJ-A12, OBJ-B21
```

```text
Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Preserves additive presets and declared-compiler policy, scopes S(f) to measured context, and keeps scores/freshness snapshots strictly as scheduling inputs (confirmed by EV-3 0/202 fresh).
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

```text
Decision: DEC-A11
Revision: 1
Proposition SHA-256: 0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78
Position: ACCEPT
Reason: Essential synthesis closing both memory asymmetry (Claude P4/R1-P4, my R1-Probe 2: 3/5 xfails pass) and CPU/CF + host-write leakage (GPT Q1), while keeping input restoration separate from output assertions and gating xfail/test-meaning changes on owner review + Q-B05.
Conditions: none
Related objections: none
```

---

### 8.2 Architect B — Claude (`DEC-B01`–`DEC-B21`)

```text
Decision: DEC-B01
Revision: 1
Proposition SHA-256: 2e0072dfeacf3355c35ae8626056819ee56a56b22736ebe3c1b95f1ef350f7bb
Position: CONDITIONAL
Reason: Strongly accept the M2 priority principle deferring B3, E3/E4, full E6, persistent provenance, and CU DBs; only the closed enumeration of M2 items omits verified soundness/reliability needs.
Conditions: Keep M2 admission principle-driven so wc1.oldcc path-length guarding (DEC-C04 rev 2), strict raw-OMF admission (DEC-C02 rev 2), measure-first wc1.compare hardening (DEC-B20/DEC-C15), CPU/host-write T4 state parity (DEC-A11), and lightweight deterministic rename/Wave 3R enablers are admitted as needed.
Related objections: OBJ-A15, OBJ-C15, OBJ-C16
```

```text
Decision: DEC-B02
Revision: 1
Proposition SHA-256: 52e9b26dfdd3b6954ee162adfb0c71e128aa2aa696965fcd2c09b43b1e7e7a16
Position: CONDITIONAL
Reason: Strongly accept E0 reimplementation in tools/wc1/match.py with 55 controls and full live audit (decoupled from V4). Needs the minimal strict raw-OMF admission Claude already noted for R2 plus E2 Cause B / E3 Nit 3 fixes.
Conditions: Include strict raw-OMF admission (record bounds, nonzero checksums, MODEND, preserved FRAME, OBJ-A03), function-scoped FunctionMatch bounds with explicit sibling-context obligations (OBJ-A10), and preserved trimmed_branch_target.
Related objections: OBJ-A03, OBJ-A10, OBJ-C05
```

```text
Decision: DEC-B03
Revision: 1
Proposition SHA-256: e4227a079ab271526345bc98d3a54e8b6c12cccf6b476ee37748b7411375e6f3
Position: CONDITIONAL
Reason: Strongly accept the single planner plan(p, regions) shared by preflight and emission. Two precision fixes needed on rev 1 wording.
Conditions: (1) Keep plan admissibility distinct from observed IntegratedResult (actual assemble + link + hardened compare, OBJ-A09); (2) qualify the IntroOpSyncSound standalone regression test by mode (rejected under legacy or B2-disabled, accepted only as explicit B2-span debt under in-place B2, zero debt as Group B, OBJ-C11).
Related objections: OBJ-A09, OBJ-C11
```

```text
Decision: DEC-B04
Revision: 1
Proposition SHA-256: 10f99b1cf2a534df1eb4b3a8f6dd0774a174e1e785dae2222be7ca52b3ce08a1
Position: CONDITIONAL
Reason: Strongly accept unified Build A cross-object branch rule (including dropping M2 _loc_ PUBDEF synthesis per OBJ-B23). Needs the exact R2 updates Claude already previewed plus fallthrough and next_ip precision.
Conditions: (1) Prefer NASM piece-local expressions using decoded next_ip = ia + insn.size and typed encodings with assembled-byte verification (OBJ-A13); (2) exclude automatic per-object legacy fallback as well as --legacy (DEC-B19); (3) explicitly check cross-piece fallthrough adjacency; (4) pair with hardened wc1.compare (DEC-B20) rather than claiming unhardened IDENTICAL is complete.
Related objections: OBJ-A02, OBJ-A13, OBJ-B19, OBJ-B27, OBJ-C10
```

```text
Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: Exact alignment with DEC-A04 and DEC-C05 rev 2 on B1 leading-byte base gated on E0 RegionMatch, with cross-object branch analysis using physical table_start and zero foreign entry/overlap.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: ACCEPT
Reason: Aligned after withdrawing OBJ-C13: Claude P3 proved Group B builds IDENTICAL under current production tools, E1 verified it under E0, and normal owner confirmation of AGENTS.md wording + full make verify + owner review of any PLAYFLIC test adjustment suffice without waiting on generic B2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: CONDITIONAL
Reason: Superseded by DEC-B18 + DEC-A11 (as Claude noted in R1 line 443); rev 1 covers memory only and omits CPU flags/host writes (GPT Q1).
Conditions: Adopt combined DEC-A11 + DEC-B18 + DEC-C16 rev 2 (CPU/flags + full mapped writable memory + declared/stateless stub accounting + Q-B05 + owner approval).
Related objections: OBJ-A12
```

```text
Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: ACCEPT
Reason: Aligned after upholding OBJ-A11 and OBJ-B20: B3 stays deferred post-M2 (whole-segment first, RFC §8.2 constraints 1-5 retained), with any future CONST gap rule governed by DEC-B21 + DEC-C10 rev 2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B09
Revision: 1
Proposition SHA-256: 00ff7874640d8a9159ec0d393a17aac144a02a9b2126aafedc5883bc4e6135d6
Position: CONDITIONAL
Reason: Strongly accept deferring E3/E4 post-M2 and requiring explicit owner Gate-2 disposition + rev-e4-01 F1-F4. Needs the confirmed E4 code defects added to the precondition list.
Conditions: Also require fixing confirmed E4 Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), and Probe 5c (typed table/code model) over the shared strict OMF32 subset (DEC-C09 rev 2).
Related objections: OBJ-C03, OBJ-C14
```

```text
Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: Exact E2 alignment matrix cleanly separated from historical CU flag claims (aligned with DEC-C13 rev 2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: Keep -4r single-file project default with additive E7 presets and context-scoped S(f) (aligned with DEC-A09 and DEC-C13 rev 2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: Aligned after upholding OBJ-B25 (trigger E6 on intra-TU sibling substitution, callbacks, or pointer identity, not multi-function files per se). Minor scope alignment needed for post-M2 witnesses and audit parity.
Conditions: Apply the same demand-led trigger to post-M2 witnesses as well as M2, require DEC-A08 production audit parity, and keep full paired-state symmetry (DEC-A11/DEC-B18) independent of E6.
Related objections: OBJ-A12
```

```text
Decision: DEC-B13
Revision: 1
Proposition SHA-256: 84a9be5c34e2d9d48bff2c233da0fc9779e5ac2f64a01704f120998ce876741c
Position: CONDITIONAL
Reason: Strongly accept analyst-facing constraint graph, rejecting staircases/call-locality/automatic consolidation, and deferring compilation_units.toml to M3. Three small precision qualifications from OBJ-A16 / DEC-C12 rev 2 remain.
Conditions: (1) Require verified compiler/linker provenance for shared_epilogue; (2) evaluate PARA at the actual segment base (not a public after a leading table); (3) retain shared_const_string_literal as conditional premise-dependent evidence (excluding explicit externs/pooling) rather than omitted.
Related objections: OBJ-A16
```

```text
Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: Minimal M2 entity set (immutable matcher-minted VerifiedRegion + single derived PlacementPlan; no separate CandidateRegion class or persistent provenance DB in M2), aligned with DEC-C01 rev 2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Production tools/wc1 must never import from experiments/; aligned with DEC-C02 rev 2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Rev 1 reclassifies only IntroOpWaitSound, omitting IntroRunScript (0x23668) and IntroPlay (0x23ae0), which both R1-Probe 2 and Claude's own R1-P4 proved pass under full state restoration. Superseded by DEC-C16 rev 2 (or Claude's planned rev 2).
Conditions: none
Related objections: OBJ-C12, OBJ-B18
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: Rejecting the exact indexed proposition ("Selective OMF extraction is adopted in production as the mechanism for advancing M2") in full agreement with Architect B's own REJECT position and DEC-C08 rev 2 (correction from R1 sign wording so all three ledger entries align on REJECT).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B18
Revision: 1
Proposition SHA-256: ac26e81cd7b7a4b5425bf06c8bbf108dcaad0a36836455c2f7ed8a7f034a02db
Position: CONDITIONAL
Reason: Strongly accept full mapped memory snapshot/restore for all T4 runs, audit logging, empirical reclassification, and owner approval for xfail removal. One gap proved by GPT Q1 must be closed.
Conditions: Also restore/checkpoint CPU state including EFLAGS/CF and account for host-written memory / stateful Python stub closures per DEC-A11 (and verify with Q-B05).
Related objections: OBJ-A12
```

```text
Decision: DEC-B19
Revision: 1
Proposition SHA-256: 2b1f46b75f348a9e7f6ddf23f2bec3b1cb47e9de6674c5f4d6b534b562b1a78f
Position: ACCEPT
Reason: Essential catch verified at tools/wc1/build.py:310-314@17733f9: fixed-displacement spans must reject both global --legacy and automatic per-object Unplaceable fallback (incorporated in DEC-C05 rev 2).
Conditions: none
Related objections: OBJ-B27
```

```text
Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: ACCEPT
Reason: Exact measure-first comparator hardening before enforcing LE object flags and fixup types (aligned with DEC-A03 and DEC-C15).
Conditions: none
Related objections: OBJ-A02, OBJ-B19
```

```text
Decision: DEC-B21
Revision: 1
Proposition SHA-256: adec6bc4ed881a8a7e8279ce049851261811bf95e2144723b0a91dbe7d3a94cd
Position: CONDITIONAL
Reason: Strongly accept environment-dependent CONST pad cache normalization (corroborated by R2-Probe 1 across sessions), Stage-0 fail-closed matching, and identical two-sided matcher + build.place() application with Build A ASM physical provider.
Conditions: Any future V4 rule must additionally require independent extent/access evidence ruling out computed or overlapping reads (OBJ-A11 / GPT Q2) and explicit proof-receipt disclosure, as specified in DEC-C10 rev 2.
Related objections: OBJ-A11, OBJ-C09
```

---

### 8.3 Architect C — Gemini (`DEC-C01`–`DEC-C16`)

```text
Decision: DEC-C01
Revision: 2
Proposition SHA-256: e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de
Position: ACCEPT
Reason: Revised to four explicit outcomes (separating PlacementPlan preflight from IntegratedResult receipt per OBJ-A09) and minimal M2 entity set (DEC-B14).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 2
Proposition SHA-256: 8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b
Position: ACCEPT
Reason: Revised to include strict raw-OMF admission (OBJ-A03), function-scoped bounds with explicit sibling-context obligations (OBJ-A10), no experiments/ imports (DEC-B15), and decoupled from V4/EXP-1 (OBJ-B20/OBJ-A11).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: WITHDRAWN by author in Round 2 (upholding OBJ-A11 and OBJ-B20/OBJ-B22). Superseded by DEC-B21 (with OBJ-A11 access-proof condition) and DEC-C10 rev 2.
Conditions: none
Related objections: OBJ-A11, OBJ-B20, OBJ-B22
```

```text
Decision: DEC-C04
Revision: 2
Proposition SHA-256: 083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37
Position: ACCEPT
Reason: Revised per EV-3 (t3_audit R3 fixes delivered) and OBJ-A17 (measure and guard all compiler-facing Windows paths with verified unchanged compile/include semantics).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C05
Revision: 2
Proposition SHA-256: 0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d
Position: ACCEPT
Reason: Revised per OBJ-A09, OBJ-A13, OBJ-B23, OBJ-B27/DEC-B19, and OBJ-C11: decoded next_ip, zero M2 OMF PUBDEF synthesis, per-object legacy exclusion, cross-piece fallthrough check, hardened compare, and mode-qualified Sync regression tests.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C06
Revision: 2
Proposition SHA-256: ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23
Position: ACCEPT
Reason: Revised per Claude P3 and OBJ-A15 so Group B pilots independently of generic B2, with owner ground-rule confirmation, dual-compiler checks, full make verify, and owner review of PLAYFLIC test adjustments.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C07
Revision: 2
Proposition SHA-256: f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999
Position: ACCEPT
Reason: Revised per OBJ-A15, OBJ-B18, OBJ-B24, and GPT §4: parallel M2 tracks, verified 3-vs-2 xfail split, reconstruction upper bound vs deterministic guarantee, and M3 Build B decoupled from optional Stage-3 consolidation.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C08
Revision: 2
Proposition SHA-256: 6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00
Position: ACCEPT
Reason: Revised per OBJ-A14/DEC-B09 (owner Gate-2 prerequisite), OBJ-A18 (dropping refuted 64-fixup and exhaustive Wave 4B mandates), and Q4/R1-P6 confirmation of Probe 5a/5b/5c.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C09
Revision: 2
Proposition SHA-256: 802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b
Position: ACCEPT
Reason: Revised per OBJ-A18 and Claude's condition: shared strict OMF32 subset for verification and admitted post-M2 transforms only, leaving permissive libsig readers and M2 omfpatch untouched.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C10
Revision: 2
Proposition SHA-256: b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f
Position: ACCEPT
Reason: Revised per OBJ-A11, OBJ-B20, and DEC-B21: whole-segment strict B3 first (post-M2, need-driven), with any future CONST gap rule requiring two-sided matcher+place(), Build A ASM provider, proof disclosure, and independent extent/access evidence.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C11
Revision: 2
Proposition SHA-256: 46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090
Position: ACCEPT
Reason: Revised per OBJ-A12, OBJ-B21, OBJ-B25, and mf_cemu.py:25: full paired initial-state symmetry immediately for all T4s, demand-led E6 on sibling substitution/callbacks/R2 pointers with accurate ABI register list and audit parity, EXP-4 optional.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C12
Revision: 2
Proposition SHA-256: 7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa
Position: ACCEPT
Reason: Revised per OBJ-A16 and OBJ-B26: measured precision for non_16_aligned_start at true segment base, compiler/linker provenance for shared_epilogue, conditional shared_const_string_literal, M3 storage deferral.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C13
Revision: 2
Proposition SHA-256: eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02
Position: ACCEPT
Reason: Revised per OBJ-A16, OBJ-B26, DEC-B10, and DEC-B11: exact measured matrix, -4r single-file default + additive presets, -5r ranked first for 4B-spaced multi-function -ot TUs with no historical-flag claim.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: Retained unchanged at rev 1 (already accepted by both A and B).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: ACCEPT
Reason: Retained unchanged at rev 1 (aligns with DEC-A02, DEC-A03, and DEC-B20 measure-first attribute verification).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C16
Revision: 2
Proposition SHA-256: 06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95
Position: ACCEPT
Reason: Revised to merge DEC-A11 (CPU/flags including EFLAGS/CF + host-write accounting) with DEC-B18 (full mapped writable memory restore) and our independently corroborated 3-vs-2 empirical xfail split (R1-Probe 2 & Claude R1-P4).
Conditions: none
Related objections: none
```

---

## 9. Probe Log and Source Index (Round 2)

### 9.1 Round 2 Probes (Read-Only)
- **R2-Probe 1 — Fixed-Path `CONST` Pad Stability Check (evaluating `OBJ-B22` / Claude `R1-P2`):**
  - *Command:* `nix develop -c env TMPDIR=/tmp/opencode/cn-gemini WINEPREFIX=/mnt/data/projects/warcraft-1-decompile-wt/cons-c/build/oldcc/wineprefix python3 -c "..."` compiling the exact fixed file `/tmp/opencode/cn-gemini/p7/net_sav.c` (`".net"`, `".sav"`, `-q -zl -bt=dos -s -ot -ol -5r -zp2`) 4 consecutive times via `wc1.match.compile_c(..., cc='10.0a')`.
  - *Output:* All 4 consecutive runs inside the same session produced identical `len=13 hex=2e6e6574006600612e73617600 gap[5:8]=660061`—confirming within-session stability (Claude `R1-P2`), while differing from both earlier sessions on that exact same fixed path (`73002f` and `760061` in R0 Probe 7d) and `war.exe` (`8d75e0`). Establishes environment/session-dependent heap residue (`DEC-B21`).
  - *Limitation:* Single 2-string source; did not isolate which env/Wine heap variable shifted between sessions.
- **R2-Probe 2 — Code Verification of `build.py` and `mf_cemu.py`:**
  - *Command:* `git show 17733f9:tools/wc1/build.py | sed -n "90,115p;295,325p"` and `git show e6150b8:experiments/build_codegen/e6/mf_cemu.py | grep -n -C 8 "PRESERVED_REGS"`.
  - *Output:* Confirmed `build.py:94-104` independently compares `DATA`-class (`CONST`) contents (Claude D-2), `build.py:310-314` silently falls back per-object to legacy layout on `Unplaceable` (Claude `OBJ-B27` / `DEC-B19`), and `mf_cemu.py:25` defines `PRESERVED_REGS = ('ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')` (GPT §3 correction).

### 9.2 Source Index (Additions & Path Corrections Over R0/R1)
- **Round 2 Inbox (verified SHA-256):**
  - `r02-inbox/00-PROPOSITION-INDEX.json` (`62db5e6ae8d2d165ebd617d2f686f62a3bd731022e05881a6923ee1b3e3f23d8`)
  - `r02-inbox/01-architect-gpt-crossreview.md` (`482cbb192515d260ecdc9e878361b2bd0a6ea0a6ce5feed8370c41f37d109f5d`)
  - `r02-inbox/02-architect-claude-crossreview.md` (`ee07dd4bfd85cd8d706da39f262739f3eb7cfb601327ea52cd658d79869806d5`)
- **Corrected Pinned Experiment Paths (`@e6150b856106ae113bb023300b956fff318da7ef`, fixing R0 §15 typos caught by GPT §3):**
  - `docs/research/build-codegen/results/e0/{controls.json,t3_reaudit.json}@e6150b8`; `experiments/build_codegen/e0/test_e0.py@e6150b8`
  - `docs/research/build-codegen/E1-shared-epilogues.md@e6150b8`; `docs/research/build-codegen/results/e1/{results.json,disasm_evidence.txt}@e6150b8`
  - `docs/research/build-codegen/E2-compilation-context.md@e6150b8`; `docs/research/build-codegen/results/e2/{results.json,consolidation_rows.csv}@e6150b8`
  - `docs/research/build-codegen/results/{e3,e4,e5,e6}/results.json@e6150b8`; `experiments/build_codegen/e6/mf_cemu.py:25@e6150b8`
  - `docs/research/build-codegen/E5-data-anchors.md@e6150b8`; `docs/research/build-codegen/results/e7/calibration_matrix.json@e6150b8`; `docs/research/build-codegen/results/e8/{metrics.json,signal_metrics.csv}@e6150b8`
- **Production Mainline (`EV-3: main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`):**
  - `tools/wc1/build.py:90-115,295-325@17733f9`; `tools/wc1/t3_audit.py:160-162,1197-1206,1786-1790@17733f9`; `tools/wc1/oldcc.py:123-125,201-203@17733f9`; `tools/wc1/match.py:368-390@17733f9`
- **Durable Round 2 Copy:** [CONSILIUM-R02-RESPONSE.md](file:///mnt/data/projects/warcraft-1-decompile-wt/cons-c/CONSILIUM-R02-RESPONSE.md)
