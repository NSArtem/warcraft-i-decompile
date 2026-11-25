# Warcraft I M2 Completion — Blocker Analysis & Architectural Findings

**Baseline:** commit `d46f891` (`899 / 1010 DONE`, **111** in-scope functions remaining).
**Machine-readable backing data:** [inventory.json](inventory.json), [inventory.csv](inventory.csv), [dependency-groups.json](dependency-groups.json), reproducible via `python3 -m wc1.m2_inventory`.

---

## 1. Executive Synthesis

The exhaustion of the existing Wave 2, Wave 3, and Wave 4A queues at **89.0% DONE (899 / 1010)** does **not** mean the remaining 111 functions are unusually hard to reverse-engineer or semantically opaque. On the contrary, empirical audit proves (**VERIFIED**):

1. **88.3% of the remaining backlog (98 / 111 functions) is blocked by pipeline, ownership, buildability, or stale-exclusion constraints**, not by binary complexity or semantic ambiguity.
2. **Only 78 of the 111 functions actually lack reconstructed C.** The other **33** already have verified/matched C (`19`), existing reference C (`6`), or are not Blizzard C functions at all (`8` binary-discovery/scope artifacts).
3. **One single pipeline bottleneck accounts for 72.1% of the entire remaining backlog (80 / 111 functions):** earlier caller-area reconstructions inserted placeholder `fn_XXXXX` (or `low`-confidence) `[[func]]` entries into caller TOMLs (`mod_104b0.toml` holds 26, `mod_20c30.toml` holds 20), and **100% (73 / 73) of all placeholder not-DONE entries are already referenced by name in existing `src/` files**. Because `wc1.batch_driver` is single-module scoped and cannot atomically migrate a TOML entry and rewrite callers across `src/` and `tests/`, `wc1.overnight` excludes all 80 into `needs_human`.
4. **Zero `OD`-style functions remain in the 111-function backlog** (`OPT`: 104, `DBG`: 4, `LEAVE`: 3). There are **zero** non-trivial strongly connected components (mutual recursion cycles) in the 111-node call graph.
5. **16 functions can be resolved deterministically with zero LLM calls**:
   - **8 immediately actionable** under current gates (`2` unwired already-passing artifacts + `1` pre-function switch table + `5` shared-epilogue T3s via two small `wc1.build`/`wc1.emit` extensions, both empirically verified in isolated `/tmp` probes).
   - **8 governance-gated** discovery/scope artifacts (`2` data-in-code byte tables, `2` split mid-function blocks in `STATUS.C`, and `4` third-party Miles AIL hand-written assembly mixer routines in `mod_3df40` that caused 3 consecutive Wave 3 failures).
6. **Secondary Wave 4B finding (challenging a legacy assumption):** Adding Watcom 10.0a `-5r` (omitted from `permuter.FLAG_PRESETS` based on an October 2026 OW2 20-sample assumption) yields **14 brand-new exact byte-identical T3 matches (11 whole-object) and 76 score improvements in 3.0 seconds with 0 LLM calls** — including **3 of the 19 functions** Wave 4B just failed on (`0x13dd0`, `0x1af20`, `0x34060`). A second Watcom 10.0a idiom (`for`-loop zeroing lowers to `call __STOSB` `0x34390`, whereas `memset()` calls `0x30c50`) yields **2 more exact T3 matches** (`0x224e0`, `0x2b2f0`) from the same 19-function Wave 4B failure batch.

---

## 2. Exact Remaining Backlog & Reconciliation (`d46f891`)

**VERIFIED** via `python3 -m wc1.progress` and `python3 -m wc1.m2_inventory`:

| Kind | Total | Named | T3 | T4 | Unchecked `ref` | No C | DONE | Remaining |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `game` | 882 | 792 | 443 | 339 | 6 | 94 | 777 | **105** |
| `runtime` | 90 | 84 | 46 | 38 | 0 | 6 | 84 | **6** |
| `gfx` | 27 | 27 | 23 | 4 | 0 | 0 | 27 | **0** |
| `resource` | 11 | 11 | 7 | 4 | 0 | 0 | 11 | **0** |
| **Total in-scope** | **1,010** | **914** | **519** | **385** | **6** | **100** | **899** | **111** |

- **By codegen style (111 not-DONE, VERIFIED via `wc1.codegen_survey.feat`)**: `OPT`: 104, `DBG`: 4 (`0x1c300`, `0x2fcfc`, `0x3d040`, `0x3d190`), `LEAVE`: 3 (`0x3fe34`, `0x4002a`, `0x40088`), `OD`: **0**.
- **By C-reconstruction reality (DERIVED from `inventory.json`)**:
  - Already `T3` built from C (only missing semantic name): **4** (`0x214d4`, `0x2b308`, `0x2b31c`, `0x2b390`).
  - Already `T4` difftested (only missing semantic name): **1** (`0x26360`).
  - Already byte-matched T3 C on disk, not wired to `src =`: **14** (7 in `codegen_promo.toml` + 1 already-buildable `0x23170` + 1 pre-fn jump table `0x157e8` + 5 shared-epilogue T3s).
  - Existing reference C (`ref =`) missing `ref_verified_by`: **6** (1 unwired passing test `0x1bf94` + 5 genuine divergences).
  - Not C functions (discovery/scope artifacts): **8** (2 data-in-code + 2 `STATUS.C` split blocks + 4 Miles AIL mixer asm).
  - Genuine C functions needing new C written: **78** (10 `BULLET.C` clean + 61 placeholder stubs + 7 low-conf named).
  - Checksum: `4 + 1 + 14 + 6 + 8 + 78 = 111`.

---

## 3. Blocker Taxonomy (Primary & Overlapping Secondary)

We distinguish the **true underlying root cause** from the surface exclusion rule (`DEFAULT_SKIP` or `needs_human`). Every one of the 111 functions has exactly one mutually-exclusive `primary_blocker` and zero or more overlapping `secondary_blockers`.

### 3.1 Primary Blocker Distribution (Mutually Exclusive, Sum = 111)

| # | Primary Blocker | Count | % | Origin | Det. Unlock? | Representative Addresses & Root Cause |
|---:|---|---:|---:|---|---:|---|
| 1 | `cross_toml_placeholder_stub_no_c` | **40** | 36.0% | Tooling/Pipeline | No (LLM + det. rename) | `0x11a10`..`0x11f78` (`BULLET.C` in `mod_104b0.toml`), `0x13270`..`0x13954` (`mod_13270` in `mod_104b0`/`mod_20c30`), `0x150f0` (`codegen_promo.toml`), `0x2e384`..`0x2eefc`. Caller TOMLs hold `fn_*` stubs; `batch_driver` cannot migrate TOMLs or rename callers across modules. |
| 2 | `same_toml_placeholder_stub_no_c` | **21** | 18.9% | Tooling/Pipeline | No (LLM + det. rename) | `0x20c30`..`0x21168` (7 in `mod_20c30.toml`), `0x12f24` (`net_link.toml`), `0x1da34` (`startup.toml`), `0x2b400`/`0x2b4b8` (`mod_2b400.toml`), `0x1e7b0` (`mod_1e380_f1.toml`). Stub is already in its own module's TOML, yet `overnight.py` lumps it into `"existing cross-TOML entry"` and excludes it. |
| 3 | `stale_default_skip_bullet_c` | **10** | 9.0% | Stale Exclusion | No (LLM via Wave 3) | `0x119c0`, `0x11c50`, `0x11fa8`..`0x123e0`. Zero technical blockers; excluded solely by stale `"BULLET.C"` entry in `overnight.DEFAULT_SKIP` left over from a scrapped manual draft. |
| 4 | `locked_codegen_promo_matched_t3` | **7** | 6.3% | Tooling/Pipeline | No (naming + det. migrate) | `0x1132c`, `0x123cc`, `0x13e94`, `0x15170`, `0x15230`, `0x15558`, `0x19478`. Byte-exact T3 C already exists in `src/codegen/*.c`; trapped by `LOCKED_TOMLS`, placeholder `fn_*` names (referenced in 1–17 `src/` files), and 3-fn `src/codegen/mod_13f60.c`. |
| 5 | `existing_low_conf_named_no_c` | **7** | 6.3% | Tooling/Pipeline | No (LLM via Wave 2/3R) | `0x1b00c` `ViewportLayerCallback`, `0x1b448` `MapReleaseDefault`, `0x1b578` `MapPressDefault`, `0x257dc` `ScoreFreePanels`, `0x2c57c` `PathScan`, `0x3d040` `DrawBevelPanel`, `0x3d190` `DrawBevelPanelThin`. Already semantically named with evidence; excluded solely because `confidence = "low"`. |
| 6 | `unbuildable_t3_shared_epilogue` | **5** | 4.5% | Tooling/Pipeline | **Yes (0 LLM)** | `0x1e380` `ApplyScenarioTerrainKindRects`, `0x2315c` `IntroOpPlaySound`, `0x2e96c` `UnitFinalizeGone`, `0x2efd0` `SelectionClickUnit`, `0x2f73c` `MissionDefeat`. Already `MATCH` T3 C; rejected by `wc1.emit.replaced_interior_refs` due to neighbour asm `rel8`/`rel32` branches into shared `ret`/epilogue. |
| 7 | `name_only_placeholder_with_verified_c` | **5** | 4.5% | Tooling/Pipeline | No (naming + det. rename) | `0x214d4` (T3, 23 `src/` refs), `0x26360` (T4, 9 `src/` refs), `0x2b308` (T3, 8 `src/` refs), `0x2b31c` (T3), `0x2b390` (T3, 6 `src/` refs). C verification is already complete; blocked only on semantic naming + repo-wide rename. |
| 8 | `ref_c_behavioural_divergence` | **5** | 4.5% | Reference-C Bug | No (targeted C fix) | `0x231cc`, `0x23530`, `0x23668`, `0x23ae0` (`PLAYFLIC.C`, `@_DIVERGES` stub-call log length mismatch) and `0x2fcfc` `EndScreen` (`LayerAdd` `id`/`res` args swapped + missing `LayerInvalidate(0xd)`/`PaletteSet`). |
| 9 | `scope_misclassified_ail_asm` | **4** | 3.6% | Binary/Discovery | **Yes (governance)** | `0x3fe34`, `0x4002a`, `0x40088`, `0x400b4` (`mod_3df40`). Proven 100% Miles AIL digital audio mixer hand-written assembly (`push ds; push es; cld`, called exclusively by `ail_dig`), misclassified as `kind = "runtime"`. |
| 10 | `discovery_data_in_code` | **2** | 1.8% | Binary/Discovery | **Yes (governance)** | `0x110a0` (`wander_direction_offsets`, 4B `00 01 ff 00`) and `0x11530` (`train_priority_odd`, 8B `01 09 05 07 00 08 04 06`). Read-only byte tables in `_TEXT` already in `datas_db`; not executable functions. |
| 11 | `discovery_split_function_block` | **2** | 1.8% | Binary/Discovery | **Yes (governance)** | `0x28090` `SelectionIsWorkersFalse` (3B `xor eax,eax; ret`) and `0x28093` `SelectionIsWorkersNext` (15B loop tail jumping back to `0x2807d`). Mid-function blocks of `SelectionHasNoWorkers` (`0x28074..0x280a2`). |
| 12 | `unbuildable_t3_pre_function_jump_table` | **1** | 0.9% | Tooling/Pipeline | **Yes (0 LLM)** | `0x157e8` `ChooseCampaignDialog`. Already `MATCH` T3 C; rejected by `wc1.build.place` because Watcom 10.0a emits the 4-entry switch table at `0x157d8..0x157e8` before the function (`pub[1] == 0x10`). |
| 13 | `unwired_passing_t4_difftest` | **1** | 0.9% | Tooling/Pipeline | **Yes (0 LLM)** | `0x1bf94` `WaitInputOrTimeout`. `tests/test_mod_1bf80.py::test_wait_input_or_timeout` already exists and passes (`3 passed in 1.22s`); `ref_verified_by` was omitted in commit `5fa133b`. |
| 14 | `unwired_buildable_t3` | **1** | 0.9% | Tooling/Pipeline | **Yes (0 LLM)** | `0x23170` `IntroOpSyncSound`. **VERIFIED** `MATCH` + `build.check_t3_buildable == True` today (zero interior refs); `src =` was omitted alongside `0x2315c`. |
| | **Total** | **111** | **100.0%** | | **16 det. / 95 LLM** | |

### 3.2 Blocker Origin Summary (VERIFIED / DERIVED)

| Blocker Origin | Functions | Share | Meaning |
|---|---:|---:|---|
| `tooling_or_pipeline` | **88** | **79.3%** | Existing C/pipeline/buildability/TOML-ownership limits |
| `stale_exclusion` | **10** | **9.0%** | Historical `DEFAULT_SKIP` entry (`BULLET.C`) no longer valid |
| `binary_or_discovery` | **8** | **7.2%** | Non-C / non-function artifacts (data tables, split block, AIL asm) |
| `reference_c_bug` | **5** | **4.5%** | Real semantic divergences in existing reference C files |

### 3.3 Overlapping Secondary Blockers (VERIFIED)

A function may carry multiple secondary constraints that also affect execution ordering or tooling:

| Secondary Blocker Tag | Affected Functions | Significance |
|---|---:|---|
| `referenced_in_existing_src` | **73** | Every single placeholder `fn_*` entry (73/73 = 100%) is already called/declared in existing `src/*.c` or `src/include/*.h`; renaming in TOML without atomic repo-wide rewriting breaks `make verify`. |
| `low_confidence` | **50** | Entry has `confidence = "low"`, failing `progress.NAMED_CONFIDENCE` even when semantically named (7) or already T3 (`0x214d4`). |
| `default_skip_bullet_c` | **19** | All 19 remaining `BULLET.C` functions (10 clean + 8 `mod_104b0` stubs + 1 `codegen_promo`). |
| `locked_toml_codegen_promo` | **8** | All 8 remaining `codegen_promo.toml` functions (7 matched T3 + 1 `0x150f0` no C). |
| `cross_toml_ownership` | **6** | Additional non-placeholder or name-only entries stored outside their canonical module TOML (`0x1b00c`, `0x1b448`, `0x1b578`, `0x214d4`, `0x26360`, `0x2b308`/`0x2b31c`/`0x2b390` — note: 40 cross-TOML placeholder stubs already carry this as their primary blocker). |
| `default_skip_playflic_c` | **6** | All 6 remaining `PLAYFLIC.C` functions (1 buildable T3, 1 shared-epilogue T3, 4 ref divergences). |
| `non_watcom_handwritten_asm` | **4** | `mod_3df40` (`0x3fe34..0x400b4`) MASM/TASM Miles AIL digital mixer routines. |
| `multi_function_c_file_needs_split` | **3** | `0x15170`, `0x15230`, `0x15558` share `src/codegen/mod_13f60.c`; must be split 1-function-per-file for in-place `wc1.build`. |
| `shared_epilogue_caller` | **3** | `0x1b00c` (jumps into `0x1af90`), `0x231cc` (jumps into `0x2315c`), `0x2e9c4` (jumps into `0x2e96c`). |
| `large_stack_frame_dbg` | **2** | `0x1c300` (361 insns, `DBG` frame) and `0x2fcfc` `EndScreen` (319 insns, `DBG` frame). |
| `default_skip_status_c` | **2** | `0x28090`, `0x28093` (`STATUS.C` split blocks). |
| `pre_function_jump_table` | **1** | `0x19c14` (`mod_19b80`, 14-entry switch table at `0x19bdc`, currently `no C` — will hit the same `build.place` constraint as `0x157e8` once reconstructed). |
| `large_function_complexity` | **1** | `0x1c300` (361 insns, 1,720 bytes — largest single unreconstructed function). |
| `ow2_match_only_currently` | **1** | `0x19478` (`src/codegen/mod_19470.c` matches OW2, mismatches 10.0a as currently written). |

---

## 4. Dependency Graph & Structural Hub Analysis

### 4.1 Call Graph Properties (VERIFIED)

Extracting all direct calls, tail jumps, and function-pointer fixups across all 1,710 discovered functions and projecting onto the 111 not-DONE functions reveals:

- **Internal call edges among the 111 not-DONE functions:** **46** edges.
- **Strongly connected components (SCCs, size > 1):** **0**. The remaining backlog is a pure DAG with zero mutual-recursion cycles.
- **Weakly connected components (WCCs):** **71** total — **62 singletons** and only **9 multi-node components**:
  1. **Size 21** (`BULLET.C` 16 + `mod_19470` `0x19478` + `mod_1de60` 2 + `mod_1e380` `0x1e7b0` + `mod_2ced0` `0x2eefc`): projectile combat subsystem calling the RNG `0x19478` and unit/map helpers.
  2. **Size 9** (`mod_20c30` 5 + `mod_2b2f0` 2 + `mod_19b80` `0x19f70` + `mod_25820` `0x25b6c`): unit command UI and target-mode dispatch.
  3. **Size 5** (`PLACEBOX.C` 2 + `mod_13270` `0x13348` + `mod_20c30` `0x20f44` + `mod_2ced0` `0x2eefc`): building placement / footprint queries.
  4. **Size 3** (`mod_1c020`: `0x1c10c`, `0x1c2bc`, `0x1c300`): briefing/credits graphics loader.
  5. **Size 3** (`mod_2ced0` `0x2e384`/`0x2e5c8` + `mod_13270` `0x13928`): unit movement/footprint updates.
  6. **Size 2** × 4: `mod_13f60` (`0x150f0`↔`0x15170`), `mod_1af20`/`mod_2efd0` (`0x1b448`→`0x2efd0`), `mod_1de60` (`0x1de60`→`0x1def0`), `PLAYFLIC.C` (`0x23ae0`→`0x23668`).

### 4.2 Ordinary Call Dependencies vs Actual Reconstruction Blockers

A crucial architectural distinction (**VERIFIED**):
- **Call edges do NOT block C reconstruction.** Over 89% of the binary is already reconstructed; any callee already in `analysis/symbols/*.toml` can be declared `extern` and matched/difftested immediately without reconstructing the callee first.
- **The true cross-function coupling is TOML/identifier ownership, NOT call order:**
  - **2 TOML files own 46 of the 111 remaining functions (41.4%)**: `analysis/symbols/mod_104b0.toml` (26 stubs across 7 modules) and `analysis/symbols/mod_20c30.toml` (20 stubs across 8 modules).
  - **13 TOML files** hold all 80 existing-entry/locked/name-only functions.
  - **73 / 73 placeholder functions** are referenced across existing `src/` files; the top rename fan-out hubs are:

| Address | Placeholder | Module | Status | Callers (DONE / ND) | Referencing `src/` Files | Owning TOML |
|---|---|---|---|---:|---:|---|
| `0x214d4` | `fn_214d4` | `PACKET.C` | **T3** (`name-only`) | 16 (16 / 0) | **23** | `mod_20c30.toml` |
| `0x19f70` | `fn_19f70` | `mod_19b80` | `no C` | 19 (16 / 3) | **20** | `mod_104b0.toml` |
| `0x19478` | `fn_19478` | `mod_19470` | **matched T3** (locked) | 20 (14 / 6) | **17** | `codegen_promo.toml` |
| `0x20d74` | `fn_20d74` | `mod_20c30` | `no C` | 10 (10 / 0) | **12** | `mod_104b0.toml` |
| `0x13348` | `fn_13348` | `mod_13270` | `no C` | 11 (9 / 2) | **11** | `mod_104b0.toml` |
| `0x20f30` | `fn_20f30` | `mod_20c30` | `no C` | 10+ (ptrs) | **10** | `mod_104b0.toml` |
| `0x26360` | `fn_26360` | `SND.C` | **T4** (`name-only`) | 6 (6 / 0) | **9** (+3 tests) | `mod_20c30.toml` |
| `0x13270` | `fn_13270` | `mod_13270` | `no C` | 7 (7 / 0) | **8** | `mod_104b0.toml` |
| `0x13e94` | `fn_13e94` | `mod_13e60` | **matched T3** (locked) | 5 (5 / 0) | **8** (+2 tests) | `codegen_promo.toml` |
| `0x2b308` | `fn_2b308` | `mod_2b2f0` | **T3** (`name-only`) | 5 (5 / 0) | **8** (+1 test) | `mod_2efd0.toml` |

**Implication:** Solving **one** shared mechanism — an atomic cross-module symbol renamer + TOML migrator — decouples ALL 73 placeholder functions and enables parallel, module-by-module reconstruction of the remaining 14 stub areas (`DG-08-stub-area-*`) with zero inter-module ordering constraints.

---

## 5. Limitations of Current Automated Waves & `needs_human` Audit

Reviewing `tools/wc1/overnight.py` (lines 649–758) and `tools/wc1/batch_driver.py` (lines 769–1050) reveals why each exclusion rule exists, what property it protects, and how narrower specialized workflows can safely replace coarse exclusions:

| Current Exclusion Rule (`overnight.py`) | Affected Functions | Original Safety Property Protected | Why It Is Now Overly Coarse | Safe Narrow Replacement |
|---|---:|---|---|---|
| `DEFAULT_SKIP = ("BULLET.C", "STATUS.C", "PLAYFLIC.C")` | **27** (19 + 2 + 6) | Prevented clobbering user's untracked WIP `BULLET.C` draft and spinning on `STATUS.C` split blocks / `PLAYFLIC.C` unbuildable epilogues. | User scrapped `BULLET.C` draft (`AGENTS.md`); `0x23170` in `PLAYFLIC.C` is actually buildable today! | Remove `"BULLET.C"` from `DEFAULT_SKIP`. Keep per-address (not per-module) skips for `0x28090`/`0x28093` pending discovery fix. |
| `e is not None and not r["named"]` (`"existing cross-TOML entry"`) | **67** (59 outside skip + 8 in `BULLET.C`) | `batch_driver.py` (`full`) creates a brand-new `analysis/symbols/<area>.toml` and skips addresses already in `funcs_db`; editing an existing `fn_*` name without rewriting callers breaks `wc1.match --all`. | 25 of 67 are already in their own module's TOML; 7 of 67 already have semantic names (`low` confidence, needing zero caller rename!); and the remaining 60 only need a deterministic atomic renamer. | Add **Wave 3R (`upgrade-existing`)**: reconstruct C/T4 + semantic name in module, atomically migrate/update TOML, run syntax-aware repo-wide C/test renamer, verify via `make verify`. Allow `low`-conf named entries into Wave 2/3R directly. |
| `ef in LOCKED_TOMLS` (`codegen_promo.toml`) | **8** (7 outside skip + 1 `BULLET.C`) | Prevented unattended `batch_driver` from corrupting hand-curated sweep-promo entries and breaking `tests/test_codegen.py`. | 7 of 8 already match byte-for-byte; `codegen_promo.toml` was explicitly a temporary staging table (`codegen_promo.toml` header lines 1–8). | One supervised/scripted migration pass moving all 8 entries to their module TOMLs, splitting `src/codegen/mod_13f60.c`, and retiring `codegen_promo.toml` entries as they promote. |
| `not r["named"] and r["c"] in ("T3", "T4")` (`"name-only"`) | **5** | Wave 2 (`c-only`) assumes already-named; Wave 3 (`full`) assumes `no C` and would overwrite verified C! | These 5 need **zero C generation** — only semantic naming from existing disassembly/evidence + atomic repo-wide rename. | Dedicated lightweight **Rename-Only** workflow (1 LLM naming call or human review + deterministic repo-wide renamer + `make verify`). |
| `r["c"] == "none" and verified_by.startswith("match:")` (`"unbuildable T3"`) | **7** (5 outside skip + 2 `PLAYFLIC.C`) | Prevented `batch_driver` from wiring `src =` on functions that fail `wc1.build.check_t3_buildable` (`IDENTICAL` gate). | `0x23170` actually passes `check_t3_buildable` today! `0x157e8` only fails due to pre-fn jump table; the other 5 only fail due to shared-epilogue `rel8` jumps. Also `batch_driver` leaves unbuildable T3s as `c="none"` instead of T4! | Fix `wc1.build`/`wc1.emit` for pre-function jump tables and verified cut-boundary interior jumps -> all 7 become **buildable T3 DONE** (0 LLM calls). |
| `r["named"] and r["c"] == "ref"` (`"T4 incomplete"`) | **6** (2 outside skip + 4 `PLAYFLIC.C`) | Wave 2 skips `c != "none"` so it won't clobber hand-written reference C; Wave 4 skips `ref` without `difftest:`. | `0x1bf94` already has a passing test (`test_mod_1bf80.py`); the other 5 have explicit xfail diagnostics explaining the exact C bugs. | Wire `0x1bf94` immediately; run targeted difftest-guided C repair on the 5 xfailed functions. |
| `a in datas_db` (`"data-in-code"`) | **2** | Correctly prevented Wave 3 from hallucinating C functions for raw byte arrays (`0x110a0`, `0x11530`). | Safeguard is **100% correct**; the bug is upstream in `wc1.analysis` code discovery. | Keep safeguard; propose user-approved discovery veto for verified `datas_db` tables. |
| *(Missing safeguard)* Non-Watcom AIL assembly in `mod_3df40` | **4** (currently Wave 3 eligible!) | None — `overnight` has no check for `LEAVE`/non-Watcom asm prologues or 100%-AIL callers. | Wasted ~24 LLM calls across 3 failed Wave 3 runs trying to write Watcom C for MASM/TASM Miles AIL mixer asm (`push ds; push es; cld`). | Propose user-approved reclassification of `0x3fe34..0x400e4` to `kind = "ail"` in `analysis/modules.toml`; add a pre-flight `LEAVE`/segment-register asm detector to `overnight`. |

---

## 6. Deep Dive: Matched-but-Unbuildable Functions (Build-System Architecture)

Treating matched-but-unbuildable functions as a unified build-system research problem reveals that **every single matched-but-unbuildable function across the ENTIRE repository** (both the **7** not-DONE `unbuildable_T3` functions and the **5** T4 `MATCH_UNBUILDABLE` functions) falls into just **4** cleanly separable root causes (**VERIFIED**):

### 6.1 Complete Current Inventory (12 Functions Across Repo)

| Address | Name | Module | Current Status | Root Cause Class | Exact Failure Mechanism (VERIFIED) |
|---|---|---|---|---|---|
| `0x23170` | `IntroOpSyncSound` | `PLAYFLIC.C` | **Not-DONE** (`none`) | **Class 0: False Alarm** | `wc1.match` = `MATCH`, `build.check_t3_buildable` = **`True`** today! Zero interior refs. Only missing `src =` in `playflic.toml`. |
| `0x157e8` | `ChooseCampaignDialog` | `mod_13f60` | **Not-DONE** (`none`) | **Class 1: Pre-fn Jump Table** | `build.place`: `ChooseCampaignDialog at +0x10 in _TEXT, +0x0 in the original` (4-entry switch table at `0x157d8..0x157e8`). |
| `0x1e380` | `ApplyScenarioTerrainKindRects` | `mod_1e380` | **Not-DONE** (`none`) | **Class 2: Shared Epilogue** | `0x1e3c4` (`je short`, `74 e6` in `0x1e3b4` T4) branches to `0x1e3ac` (`+0x2c`). |
| `0x2315c` | `IntroOpPlaySound` | `PLAYFLIC.C` | **Not-DONE** (`none`) | **Class 2: Shared Epilogue** | `0x231d7` (`je short`, `74 93`), `0x231e1` (`jne short`, `75 89` in `0x231cc` ref) branch to `0x2316c` (`+0x10`). |
| `0x2e96c` | `UnitFinalizeGone` | `mod_2ced0` | **Not-DONE** (`none`) | **Class 2: Shared Epilogue** | `0x2e9db` (`je short`, `74 e4`), `0x2e9e6` (`jne short`, `75 d9` in `0x2e9c4` not-DONE) branch to `0x2e9c1` (`+0x55`). |
| `0x2efd0` | `SelectionClickUnit` | `mod_2efd0` | **Not-DONE** (`none`) | **Class 2: Shared Epilogue** | `0x2f0b9` (`jne short`, `75 ec` in `0x2f0a8` T4) branches to `0x2f0a7` (`+0xd7`, shared `ret`). |
| `0x2f73c` | `MissionDefeat` | `mod_2efd0` | **Not-DONE** (`none`) | **Class 2: Shared Epilogue** | `0x2f6df` (`jne near`, 6B) and 5× `rel8` jumps (`0x2f6ed..0x2f73a` in `0x2f694` T4) branch to `0x2f746` (`+0xa`, shared `ret`). |
| `0x1aca8` | `SaveErrorDialog` | `GAMEDLG.C` | DONE (`T4`) | **Class 3: Data Anchor Order** | `CONST` strings anchor at `0x51ea6` (`_DATA`), whereas earlier-in-code `defeat_dialog.c` (`0x1ab28`) anchors at `0x56c0c` (`STRINGS`), violating `dseq == sorted(dseq)`. |
| `0x16d48` | `DialogHighlightOff` | `mod_16390` | DONE (`T4`) | **Class 4: Multi-Fn Ref File** | Matches under `-s -os -ol -4r -zp2`, but shares `dialog_hit_test_reference.c` with 2 mismatching siblings (`0x16cc8`, `0x16d34`). |
| `0x22eac` | `IntroFadeStep` | `PLAYFLIC.C` | DONE (`T4`) | **Class 4: Multi-Fn Ref File** | Matches under `-s -ot -4r -zp2`, but shares `player_reference.c` with 19 mismatching siblings. |
| `0x28254` | `FarmPanelChanged` | `STATUS.C` | DONE (`T4`) | **Class 4: Multi-Fn Ref File** | Matches under `-s -ot -oa -ol -4r -zp2`, but shares `panel_state_reference.c` with mismatching `UnitPanelStateChanged` (`0x281f4`). |
| `0x24e90` | `ScoreTickIncome` | `SCORE.C` | DONE (`T4`) | **Class 4: Multi-Fn Ref File** | Matched in 1 Wave 4B LLM call (`sum = delta + score`), rejected as `UNBUILDABLE` only because it shares `score_reference.c` with `RankName`/`ScoreSetPage`. |

*(Note on `MainMenu` `0x15588`: `MainMenu` currently has unresolved `owner_5aa90` relocations and is `MISMATCH` in `audit_state.json`, AND carries a 4-entry pre-function jump table at `0x15578..0x15588` — so fixing Class 1 + `owner_5aa90` unlocks it too. There are **13** total in-scope functions with pre-function jump tables across `war.exe`, 11 of which are currently T4 and 2 not-DONE: `0x157e8` and `0x19c14`.)*

### 6.2 Three Systemic Build-System Fixes (All Preserving 100% Byte-Identical Build A)

#### Fix B1: Pre-Function Switch Jump Tables in `wc1.build.place` (Unlocks `0x157e8` for M2 + 12 T4 functions incl. `MainMenu`)
- **Current defect (`tools/wc1/build.py:64-71`):** `place()` sets `base = min(e["addr"] for e in funcs)` and requires `e["addr"] - base == pub[1]`, which assumes the first public function starts at `_TEXT + 0x0`. Watcom 10.0a emits switch jump tables at the beginning of `_TEXT` before the function prologue (`pub[1] == 4 * n_cases`, e.g., `0x10` for `ChooseCampaignDialog`).
- **Fix:** Compute `base = e["addr"] - pub[1]` from the first function, verify all functions in the object agree on `base`, verify no other discovered function lies in `[base, base + text.length)`, and verify that the leading `_TEXT` bytes `[0, min_pub_off)` match the original binary's `[base, min_addr)` (with fixups targeting the exact same original case addresses). Because the resulting cut `[base, base + text.length)` covers the jump table itself, `in_cut(src)` becomes `True` in `emit.replaced_interior_refs` and the interior-ref errors disappear automatically!
- **Complexity:** ~25 lines in `tools/wc1/build.py` + unit/build regression test.

#### Fix B2: Verified Cut-Boundary Local-Label Relative Jumps in `wc1.emit` / `wc1.build` (Unlocks all 5 Shared-Epilogue T3s for M2 + 6 T4 functions)
- **Negative experimental result (VERIFIED in `/tmp` Probe 2):** Our first hypothesis — injecting an OMF `PUBDEF` for the interior epilogue offset via `omfpatch.py` and emitting `jne short loc_int` in NASM — **FAILED**. NASM `-f obj` rejects 8-bit external relocations (`error: OBJ format can only handle 16- or 32-byte relocations`), and **all 5** shared-epilogue unbuildable T3s are targeted by 2-byte `rel8` conditional jumps (`74 e6`, `74 93`, `75 89`, `74 e4`, `75 d9`, `75 ec`, `75 57`, `75 4d`, `75 3a`, `7d 2e`, `7d 0a`).
- **Validated solution (VERIFIED in `/tmp` Probe 1 — `EXACT BYTE MATCH: True`):** In Build A's in-place sequential layout, `piece_{k+1}` starts immediately after C cut `[cs, ce)` with local label `loc_<ce>`, and `piece_k` ends immediately before `[cs, ce)` with local label `loc_<cs>`. For any external branch at `ia` targeting interior address `t` inside a **T3-verified in-place cut** (never legacy layout!), the target sits at a known constant signed displacement from the piece's own boundary label (`loc_<ce> - (ce - t)` for backward branches, `loc_<cs> + (t - cs)` for forward branches).
  - Tested directly with `nasm -O0 -f obj` + `wlink system dos4g`: `jne short (loc_cut_start + 5)` and `je short (loc_cut_end - 1)` assembled with **0 errors, 0 external relocations**, linked cleanly, and produced **byte-identical** `_TEXT` (`85c07506c3b801000000c385c074fbc3`).
  - **Correctness invariant:** Only permitted when `t` lies inside an in-place cut `[cs, ce)` (and all intervening objects between the piece boundary and `t`, e.g., `0x23170` between `0x2315c` and `0x231cc`, are also fixed-size T3-verified in-place cuts), and `wc1.compare` proves the final linked `build/war.exe` is `IDENTICAL` at every byte and fixup.
  - **M3 / Build B compatibility:** In Build B (all-C), both functions are compiled from C independently and neither jumps into the other's interior at all; this mechanism is strictly for Build A's hybrid asm+C bridge.
- **Complexity:** ~40 lines across `tools/wc1/emit.py` and `tools/wc1/build.py`.

#### Fix B3: Data-Anchor Decoupling via OMF `EXTDEF` Relocation Rewriting (Unlocks `SaveErrorDialog` `0x1aca8` + multi-segment data C objects)
- **Current defect (`tools/wc1/build.py:108-132`, `tools/wc1/omfpatch.py`):** `omfpatch` empties each anchored data segment and relies on `wlink`'s link sequence (`piece0, C1, piece1, C2, ...`) to place the zero-length segment at `anchor_addr`. This forces `C` objects' data anchors to appear in monotonically non-decreasing address order matching code order (`dseq == sorted(dseq)`) and forbids a C object from having two data segments at different addresses (`CONST` vs `_DATA`).
- **Fix (HYPOTHESIS — clean OMF32 design, ready for prototype):** After `place()` verifies each data segment's original address `anchor_addr` and byte-for-byte contents, instead of keeping emptied data segments and splitting `data_pieces` in code order:
  1. Emit a `GLABEL wc1_anchor_<addr>` in the single asm data piece at `anchor_addr`.
  2. In `omfpatch`, append an `EXTDEF` for `wc1_anchor_<addr>`, rewrite `_TEXT` `FIXUPP` subrecords targeting `(target_kind="seg", target=seg_i)` to `(target_kind="ext", target=ext_idx)` preserving the exact inline addend/displacement, and drop the anchored data segment's `LEDATA`/`FIXUPP` (or keep it empty with zero references).
  3. Because no C object depends on its data-segment link position anymore, **code order and data order are completely decoupled**, unlocking `SaveErrorDialog` (`0x1aca8`) and any future multi-segment T3 file while keeping `make build` `IDENTICAL`.

*(Class 4 — multi-function reference files — requires no build-system change, only a deterministic 1-function-per-file extractor for matched functions inside the 21 multi-function reference files covering 81 T4 functions.)*

---

## 7. Deterministic (Zero-LLM) Opportunities Catalogue

| Mechanism | Inputs → Outputs | Correctness Conditions | Failure Mode & Fallback | M2 Unlock | Beyond-M2 (T3) Unlock | Complexity | Required Regression Tests |
|---|---|---|---|---:|---:|---|---|
| **D1. Unwired Verified Artifact Audit** | `symbols.load()`, `wc1.match`, `build.check_t3_buildable`, existing `tests/test_*.py` → TOML `src =` / `ref_verified_by =` wiring | Exact `MATCH` + `check_t3_buildable=True` (for T3); live non-skipped `pytest` pass with `WC1_T4_AUDIT_LOG` (for T4) | Any mismatch/fail → leave untouched | **2** (`0x23170`, `0x1bf94`) | 0 | Trivial (~0 tooling) | Existing `make verify` |
| **D2. Pre-Function Jump Table Placement (Fix B1)** | Compiled OMF `_TEXT` with `pub[1] > 0` → in-place cut `[addr - pub[1], end)` | All publics share `base`; no foreign func in `[base, end)`; leading bytes & fixups match `war.exe` | Raises `Unplaceable` → legacy fallback / rejected | **1** (`0x157e8`) | **+12** T4s (incl. `MainMenu` / `owner_5aa90`) | Low (~25 LOC) | `test_build.py` unit + real `ChooseCampaignDialog` T3 build |
| **D3. Cut-Boundary Local-Label Interior Jumps (Fix B2)** | In-place T3 cuts + neighbour asm `rel8`/`rel32` branches → local-label offset expressions | Target strictly inside verified in-place cut; all bytes between boundary and target are fixed in-place cuts; `wc1.compare` `IDENTICAL` | Rejects if legacy layout or target not in verified cut | **5** (`0x1e380`, `0x2315c`, `0x2e96c`, `0x2efd0`, `0x2f73c`) | **+6** T4s | Medium (~40 LOC) | `test_emit.py` rel8/rel32 cut-boundary + real Build A `IDENTICAL` |
| **D4. Atomic Cross-Module Symbol Renamer & TOML Migrator** | `(addr, old_name, new_name, target_toml, evidence, confidence)` → migrated TOML block + syntax-aware rewrites across `src/**/*.c`, `src/**/*.h`, `tests/**/*.py` | New link name globally unique; C lexer skips comments/strings/macros/member accesses/local shadowing; full `make verify` green + Build A `IDENTICAL` | Rollback all touched files on any shadowing ambiguity, compile error, or `make verify` fail | **Enables 80** (12 name-only/locked + 61 stubs + 7 low-conf) | Improves readability across 73+ files | Medium (~200 LOC, reusing `wave4_deps` C tokenizer) | Unit tests for shadowing, struct members, `t4spec` link strings, TOML migration + E2E dry-run |
| **D5. Multi-Function Ref File Splitter** | Multi-fn `*_reference.c` where ≥1 function is `MATCH_UNBUILDABLE` due to mismatching siblings → standalone single-fn `.c` file | Extracted function compiles standalone with same headers, passes `wc1.match`, `check_t3_buildable`, and original T4 difftest | Abort split if static helper or shared local state cannot be cleanly isolated | **0** (already DONE, plus splits `src/codegen/mod_13f60.c` for **3** locked fns) | **+4** immediate (`0x16d48`, `0x22eac`, `0x28254`, `0x24e90`) + 3 `-5r` matches (`0x22f48`, `0x31fc0`, `0x34480`) | Low-Medium (~120 LOC) | Unit tests + `test_match_all` + difftest preservation |
| **D6. Watcom 10.0a `-5r` Flag Preset Expansion** | Add `-5r` variants to `permuter.FLAG_PRESETS` (and `t3_audit`) | Exact `MATCH` + `check_t3_buildable` + difftest pass | None (pure additive preset) | **0** (all 14 are already T4 DONE) | **+14 VERIFIED** (11 immediate whole-obj + 3 via D5) | Trivial (~6 LOC) | `test_permuter.py` + `t3_audit` |
| **D7. Data-Anchor OMF `EXTDEF` Rewriting (Fix B3)** | Anchored data segments → `EXTDEF wc1_anchor_<addr>` + single data piece | Byte-for-byte content verification in `place()` preserved; `wc1.compare` `IDENTICAL` | Raises `ValueError` on `THREAD` FIXUPP or unsupported loc | **0** | **+1** immediate (`SaveErrorDialog 0x1aca8`) + future multi-seg T3s | Medium (~90 LOC in `omfpatch.py`/`build.py`) | `test_omfpatch.py` + `SaveErrorDialog` T3 build |
| **D8. Discovery & Scope Governance Fixes (User-Approved)** | `wc1.analysis` data-in-code veto & shared-return merge; `modules.toml` AIL mixer range | Explicit user approval under fixed-finish-line rules; disassembly & caller-graph proof | Keep in scope & handle explicitly if user declines | **8** (2 data + 2 split + 4 AIL) | **+1** (`SelectionHasNoWorkers` `0x28074` becomes T3-able) | Low (~30 LOC + TOML) | `test_analysis.py` + `make roundtrip` + `make verify` |

### Historical Failed Archives Audit (`build/failed/`) — VERIFIED Negative Result

A recursive scan of all **61** archived failure directories under `build/failed/` found only **11** not-DONE functions with actual archived C definitions (`@0xADDR`):
- 5 are `codegen_promo.toml` functions (`0x13e94`, `0x150f0`, `0x15170`, `0x15230`, `0x15558`) that already have superior/matched C in `src/codegen/`.
- 4 are already T3/T4 or matched (`0x157e8`, `0x26360`, `0x2b308`, `0x2b31c`, `0x2b390`).
- Only **1** (`0x257dc` `ScoreFreePanels`, `20261121_204343_score_f1`) has a usable archived reference-C draft, and `mod_3df40` (`0x3fe34..0x400b4`) failed 3× with invalid `__asm {}` syntax.
- **Conclusion (VERIFIED):** Salvaging `build/failed/` is **not** a significant source of M2 progress; fresh reconstruction under the current symbol DB and Watcom 10.0a pipeline is cleaner and faster.

---

## 8. Secondary Research Track: Wave 4B Empirical Failure Analysis

*Distinction:* Wave 4B targets **T4 → T3 conversion** (already DONE functions) and is **not** on the critical path to 100% M2 DONE. However, investigating the recent `2026-11-25` Wave 4B run (`gpt-6.2-sol:low`) revealed critical systemic pipeline defects worth fixing before any future Wave 4B campaign.

### 8.1 Empirical Breakdown of the Recent 19-Candidate Wave 4B Run (VERIFIED)

Inspecting `build/wave4/metrics.json` and all 19 outcome files from `2026-11-25` (note: the prompt cited the first 16 candidates / 31 calls; 3 more completed before Ctrl-C, totaling **19 candidates / 37 calls / 0 T3 promotions**: 1 `UNBUILDABLE`, 1 `FAILED`, 17 `NO_IMPROVEMENT`):

| Empirical Root Cause | Count (of 19) | Functions | Verified Evidence |
|---|---:|---|---|
| **Missing `-5r` compiler flag preset** | **3** | `0x34060`, `0x13dd0`, `0x1af20` | **VERIFIED** in `/tmp` Probe 3: all 3 match **byte-for-byte with 0 source edits** when `-4r` is changed to `-5r` (Watcom 10.0a `-5r` emits `shl eax, 2/3` instead of 4-byte SIB `lea`). `0x13dd0` was the sole `FAILED` (Call 2 compile error)! |
| **Unknown Watcom 10.0a idiom (`for`-loop → `__STOSB`)** | **2** | `0x224e0`, `0x2b2f0` | **VERIFIED** in `/tmp` Probe 1: replacing `memset(...)` (calls `0x30c50`) with `for (i = 0; i < N; i++) arr[i] = 0;` causes Watcom 10.0a to emit `call __STOSB` (`0x34390`), yielding **instant exact `MATCH`** for both! |
| **Multi-function reference file (`UNBUILDABLE`)** | **1** | `0x24e90` `ScoreTickIncome` | **VERIFIED**: Call 1 achieved an **exact match** (`sum = delta + score` → `lea ecx, [eax + edx]`), but was discarded as `UNBUILDABLE` solely because `score_reference.c` contains 2 mismatching siblings! |
| **Unmatchable standalone binary artifact** | **3** | `0x116a8`, `0x21cb8`, `0x16d34` | `0x116a8` ends with trailing `nop` (fall-through/epilogue); `0x21cb8` has 2-byte `mov eax, eax` alignment filler before `ret`; `0x16d34` branches (`je 0x16d31`) into sibling `0x16cc8`'s epilogue. No standalone C spelling can match these! |
| **Memoryless Call 2 retry after Call 1 regression** | **6** *(incl. 1 overlap w/ `-5r`)* | `0x20bd4`, `0x330a0`, `0x1af20`, `0x208d4`, `0x24900`, `0x2f788` | **VERIFIED** in `tools/wc1/wave4.py:673-680`: when Call 1 worsens the score (6 of 19 cases!), `wave4.py` reverts `work` to the original text and sends Call 2 `_repair_prompt(cand, text, best_row)` **with zero record of Call 1's patch or resulting diff**. Call 2 repeatedly re-diagnoses the identical first mismatch and fails identically. |
| **Genuine regalloc / structural difficulty** | **5** | `0x13d04`, `0x14e9c`, `0x19f94`, `0x27554`, `0x2ee50` | `0x13d04` (33 reg diffs), `0x14e9c` (9 reg diffs), `0x19f94`/`0x27554`/`0x2ee50` (structural/OD/branch-length diffs) where `gpt-6.2-sol:low` could not find a matching spelling in 2 isolated calls. |

Additional verified Wave 4B systemic observations:
1. **Progress thrown away on `NO_IMPROVEMENT`:** `0x224e0` `PlaceBoxInit` strictly improved from `[0, 1, 3, 0, 0]` to `[0, 1, 0, 0, 0]` on Call 1 (eliminating all 3 register diffs), yet `NO_IMPROVEMENT` discarded the improvement.
2. **Cache bypass storm (`263 / 368` dep-clean units = 71.5%):** All 263 `bypass_uncertain` lookups fail on `missing_omf_deps:<ref>` because `build/wave4/audit_state.json` was bootstrapped from a pre-v2 `build/t3_audit/report.json` before `omf_deps` capture existed. One refresh pass eliminates all 263 bypasses.
3. **Full `-5r` empirical sweep across ALL 362 dep-clean T4 mismatches (VERIFIED, 3.0s):** Adding `-5r` produces **14 exact new T3 matches** (`11 whole_obj=True`: `0x13c04`, `0x13c84`, `0x13dd0`, `0x15314`, `0x1af20`, `0x21df0`, `0x22a4c`, `0x22a98`, `0x29f40` [score `[27,8,13,12,11]` → `0`!], `0x2ab54`, `0x34060`; `3 multi-fn`: `0x22f48`, `0x31fc0`, `0x34480`) and **76 strict score improvements**!

### 8.2 High-Leverage Wave 4B Redesign Recommendations (Secondary Track)

1. **Deterministic pre-LLM stage (0 tokens):** Add `-5r` (and probe `-3r`/`-or`) to `permuter.FLAG_PRESETS`; split single-function matches out of multi-function ref files automatically; filter out unmatchable standalone artifacts (trailing `nop`/`mov eax,eax` filler, cross-function `outgoing_cross` epilogue jumps) before calling an LLM.
2. **Compiler idiom knowledge base in prompt + deterministic rewrite probes:** Encode verified Watcom 10.0a idioms (`for`-loop zeroing → `__STOSB`, bitfields for `test byte`, `volatile`/dword-view reads, `short` loop indices, commutative operand order `a + b` vs `b + a` for `lea`).
3. **Structured iterative feedback across calls:** Pass Call 1's attempted patch, new score, and new `first_diff` into Call 2 so Call 2 never repeats a failed hypothesis.
4. **Separate mismatch workflows:** Route `op=0, imm=0` (pure register allocation, currently only 5 dep-clean functions) to deterministic `wc1.permuter` local-decl/type search first; route `wrong-callee` (`call 0x34390` vs `0x30c50`) to idiom/dependency lookup rather than generic syntax repair.

---

## 9. Generalization to Larger Projects (e.g., Icewind Dale II)

Separating Warcraft I specifics from reusable architectural lessons for substantially larger binaries (10,000+ functions):

| Obstacle Class | Scope | Reusable Architectural Lesson |
|---|---|---|
| OMF32 lack of 8-bit external fixups, Watcom 10.0a `-5r` vs `-4r`, `for`-loop → `__STOSB`, DOS/4GW LE fixups | **Watcom 10.0a / DOS-specific** | Always run an empirical compiler-flag & intrinsic/idiom calibration sweep on the **real** target compiler (never carry forward flag assumptions from a proxy compiler like OW2 onto 10.0a, or GCC onto MSVC6/MSVC7 for IWD2). |
| `DEFAULT_SKIP="BULLET.C"`, `codegen_promo.toml` staging table, 4 misclassified AIL functions in `mod_3df40` | **Warcraft I-specific** | Never hardcode module-level skip lists for temporary WIP; use address-level metadata with expiry checks. Run automated third-party/asm classifier (caller-graph isolation + prologue/segment-register fingerprint) *before* queueing Wave 3. |
| **Pre-function jump tables, shared epilogues, data-in-code false functions, split blocks** | **General binary reconstruction** | Build the binary-to-C bridge from day 1 to handle: (a) leading switch tables inside `_TEXT` cuts (`base = addr - pub_off`), (b) cut-boundary local-label relative jumps for shared epilogues, (c) `datas_db`-informed discovery vetoes. |
| **Cross-module placeholder stub lock-in (`72.1%` of remaining M2 backlog!)** | **General orchestration architecture** | **#1 architectural takeaway for IWD2:** In any incremental bottom-up/module-by-module decompilation, early modules *will* reference unnamed callees in later modules. Never couple a function's stub `[[func]]` ownership to the caller's TOML, and build an **atomic repo-wide symbol renamer + ownership migrator** as a Day-1 core primitive — not an afterthought. |
| **Multi-function reference files blocking individual T3 promotions** | **General orchestration architecture** | Enforce 1-function-per-file for *reference C* as strictly as for T3 C (or maintain a deterministic splitter). |
| **Memoryless LLM retry loops & ungrounded compiler guessing** | **General LLM-assisted RE** | Always feed prior failed patch + compiler diff feedback into retry calls; separate deterministic flag/idiom search from LLM reasoning; persist a versioned target-compiler idiom cookbook distilled from verified matches. |
