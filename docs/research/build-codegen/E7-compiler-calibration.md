# E7 — Original compiler calibration (Watcom 10.0a)

Date: 2026-11-25. Branch: `research/build-codegen/e7`. Baseline: `7c23d2371e95d8de93f0ba1652c8d44b858da273`.

## Result

The tested configurations recover **19 T4 function matches, 14 whole-object matches, 14 E0 RegionMatches, and 13 buildable T3 opportunities**. All 13 buildable objects link together with the existing T3 population to an **IDENTICAL** Build A: 532 functions from 527 C files, with no legacy layout. Three additional individual `-5r` Build A checks are IDENTICAL. These are measured opportunities; the experiment changes no production source, symbol tier, or build gate.

The original eight Watcom presets recover 3 function matches, 1 whole-object/region match, and 0 buildable objects on the same cohort. The expanded grid therefore adds **16 function matches, 13 whole-object/region matches, and 13 buildable opportunities** beyond those eight presets. It strictly improves mismatch scores for **218** unique dependency-clean T4 functions (199 still have no matching configuration), versus 151 for the legacy eight: **67 additional improved functions**. Comparing with the fixed default instead of each file’s declared flags gives 239 improved functions.

An evidence correction matters: switching only `-4r` to `-5r` in the fixed default loses **zero** existing T3 FunctionMatches (417 match under each; the matched sets are identical). The architecture-wide bins below have unequal secondary-flag coverage and must not be mistaken for that paired control.

## Inputs, method, and scope

- Discovery uses `analysis.run`, `symbols.load`, and the unchanged `progress.classify` in-scope rules: **519 T3 functions / 514 C files** and **385 T4 functions / 329 C files**.
- On the declared-flag 10.0a baseline, **373 T4 functions / 317 files are dependency-clean**. **12 functions / 12 files** have **63 unresolved external relocation sites**; their baseline cells are retained and the other configurations are explicitly untested. No baseline compile failed. Dependency checks include every runtime segment, including data, and ignore non-loadable debug metadata.
- The grid has 22 requested core configurations plus 4 distinct declared configurations. Reordered independent header tokens are deduplicated without changing the actual invocation order. All 26 configurations use capability-verified options. All T3 and all dependency-clean T4 files are swept exhaustively: **21,618 10.0a calibration compiles**, with six worker processes. The baseline compile is reused only for its identical grid cell.
- All exact FunctionMatch and RegionMatch evidence comes from the unmodified [E0 prototype](../../../experiments/build_codegen/e0/matcher_proto.py). Every available requested public also receives `wc1.match.diff_function` scoring. No search stops after a match. A process-local memo reuses E0/scoring only for identical indexed runtime segments, bytes, relocations, publics, statics, externals and communal definitions within the same TU. Every configuration is still compiled.
- `whole_object_match` requires every E0 function body and the complete E0 RegionMatch, including leading bytes and local data pointer fields. This is intentionally stronger than the old matcher’s all-rows check; whole-object and region totals happen to coincide here. `buildable` additionally requires the unchanged `check_t3_buildable` called with the actual unpatched object. All 60 newly matching T4 object/configuration pairs receive that placement check, including files with mismatching siblings.
- Scores use the production lexicographic tuple `(opcode/structure, immediate, register, instruction-count, byte-length)`. An improvement compares against the same file’s declared 10.0a baseline, unless explicitly labelled “fixed default”. A zero score does not establish a match. Unsupported/missing-public comparisons are never promoted.
- `S(f)` is the full observed set of compatible configurations in the function’s current reconstructed compilation context, not a universal compiler flag set. The matrix retains every one of **23,504 function/configuration cells**. It explicitly lists **9,694 untested combinations** in a separate finite 9,720-combination hypothesis universe, plus capability-only axes outside that universe. It does not claim Cartesian coverage.
- The experiment uses no LLM calls. Temporary objects, complete E0 findings/obligations, and linked executables stay in `build/e7/`; generated game data is not committed. The committed compact JSON retains all cells, scores, unresolved operands, verdicts, finding counts/histograms/first findings and complete-finding hashes. Full E0 diagnostic arrays are reproducible scratch evidence, rather than silently truncated arrays.

## Compiler capability database

The NT launcher’s actual no-argument usage output, return codes, compiler executable hashes, diagnostics, synthetic-source hash and per-option effects are in [capability_db.json](results/e7/capability_db.json). The synthetic TU covers loops, narrow comparisons/returns, structure packing, bitfields, a switch, multiply/divide, string/memory intrinsics, tail calls, stack arrays, floating-point operations, aliasing, inlining, identical functions, null checks and string placement.

**29 of 31 probed options are accepted**, including the added baseline control `-s` (28 of the 30 specifically requested options). `-6r` is rejected with E1073 and `-ob` with E1074. **21 options change runtime bytes/relocations** on this suite. The accepted options with no runtime delta against this probe baseline are `-4r`, `-ot`, `-oa`, `-oi`, `-om`, `-zp2`, `-d1`, and `-s`. Four are already baseline settings; debug metadata is excluded from the runtime comparison. These observations do not establish universal no-op flags.

Concrete synthetic effects: `_TEXT` is 739 bytes at the probe baseline, 559 with `-3r`, 603 with `-5r`, 755 with `-or`, 787 with `-ol+`, and 871 with `-d1+`. `-zp1` first changes a byte at offset `0x83` without changing text size. `-ri` first changes offset `0x252`. `-zc` moves the controlled literal from CONST into code. The database records byte windows, exact offsets, segment hashes and relocation changes for each effect. These lengths describe the synthetic suite, not Warcraft functions.

## Complete configuration results

All counts in this table are unique dependency-clean T4 functions per configuration. “Whole/region” uses the strong E0 definition. “Improved” compares with the file’s declared flags. The full S(f), individual scores, unsupported reasons and per-cell proof summaries are in [calibration_matrix.json](results/e7/calibration_matrix.json).

| ID | Flags after `-q -zl -bt=dos` | Function | Whole/region | Buildable | Improved |
|---|---|---:|---:|---:|---:|
| c01 | `-s -ot -ol -4r -zp2` | 0 | 0 | 0 | 10 |
| c02 | `-s -ot -oa -ol -4r -zp2` | 1 | 0 | 0 | 60 |
| c03 | `-s -ot -4r -zp2` | 1 | 0 | 0 | 64 |
| c04 | `-s -ot -oa -4r -zp2` | 2 | 0 | 0 | 75 |
| c05 | `-s -os -ol -4r -zp2` | 1 | 1 | 0 | 36 |
| c06 | `-s -ot -ol -5r -zp2` | 13 | 11 | 11 | 94 |
| c07 | `-s -ot -oa -ol -5r -zp2` | 14 | 11 | 11 | 122 |
| c08 | `-s -ot -5r -zp2` | 13 | 11 | 11 | 111 |
| c09 | `-s -os -ol -5r -zp2` | 1 | 1 | 0 | 36 |
| c10 | `-s -ot -ol -3r -zp2` | 0 | 0 | 0 | 46 |
| c11 | `-s -ot -ol -or -4r -zp2` | 0 | 0 | 0 | 10 |
| c12 | `-s -ot -ol -oi -4r -zp2` | 0 | 0 | 0 | 12 |
| c13 | `-s -ot -ol -om -4r -zp2` | 0 | 0 | 0 | 10 |
| c14 | `-s -ot -ol -oc -4r -zp2` | 0 | 0 | 0 | 13 |
| c15 | `-s -ot -ol+ -4r -zp2` | 0 | 0 | 0 | 10 |
| c16 | `-s -ot -ol -4r -zp1` | 0 | 0 | 0 | 10 |
| c17 | `-s -ot -ol -5r -zp1` | 13 | 11 | 11 | 94 |
| c18 | `-s -ot -ol -4r -d1+ -zp2` | 0 | 0 | 0 | 41 |
| c19 | `-s -ot -ol -5r -d1+ -zp2` | 4 | 2 | 2 | 60 |
| c20 | `-s -od -4r -zp2` | 0 | 0 | 0 | 6 |
| c21 | `-s -od -4r -d1+ -zp2` | 0 | 0 | 0 | 12 |
| c22 | `-s -os -4r -zp2` | 1 | 1 | 0 | 39 |
| c23 | `-s -os -ol -4r -d1+ -zp2` | 0 | 0 | 0 | 29 |
| c24 | `-s -ot -ol -4r -d1+ -zp1` | 0 | 0 | 0 | 41 |
| c25 | `-s -ot -ol -4r -of -zp2` | 0 | 0 | 0 | 16 |
| c26 | `-s -ot -ol -4r -of+ -zp2` | 0 | 0 | 0 | 30 |

The cell-state totals are: **compile_error 0**, **matched 6,701**, **matcher_unsupported 4,790**, **mismatched 11,713**, **untested 300**.

`matcher_unsupported` is a fail-closed result, not an established mismatch. For example, mismatching layouts can leave E0 unable to resolve local obligations or produce external short branches. The PathPeekStep entry at `0x2c4e0` names `PathPeekStep_`, but its reference file defines only `_a`, `_b`, `_c` alternatives. Its 26 cells explicitly report the absent requested public and retain all alternative diagnostic scores; the driver never selects the first alternative as if it were the requested function.

## New function matches and integration

[t4_new_matches.csv](results/e7/t4_new_matches.csv) preserves every successful configuration, including repeated matches for the same function. The following table summarizes functions without truncating their compatible sets.

| Address | Function | Complete S(f) | Integration |
|---|---|---|---|
| `0x13c04` | UnitCountAdd | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x13c84` | UnitCountRemove | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x13dd0` | SetCursorShape | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x15314` | SetGameMode | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x1a800` | OptionsDialog | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x1aca8` | SaveErrorDialog | c05, c09, c22 | RegionMatch; data-anchor order blocks placement |
| `0x1af20` | FogDrawCell | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x21df0` | WorkerReturnToMine | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x22a4c` | PlaceBoxRoad | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x22a98` | PlaceBoxWall | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x22eac` | IntroFadeStep | c03, c04, c06, c07, c08, c17 | FunctionMatch only; mismatching siblings/context |
| `0x22f48` | IntroBeginFlic | c06, c07, c08, c17 | FunctionMatch only; mismatching siblings/context |
| `0x28254` | FarmPanelChanged | c02, c04, c07 | FunctionMatch only; mismatching siblings/context |
| `0x29f40` | AiGuardStartArea | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x2ab54` | AiIdleUnitTick | c06, c07, c08, c17 | Build A IDENTICAL |
| `0x31fc0` | BitmapClear | c19 | FunctionMatch only; mismatching siblings/context |
| `0x34060` | DpmiGetFreeMemoryKB | c19 | Build A IDENTICAL |
| `0x34480` | OpenArchive | c19 | FunctionMatch only; mismatching siblings/context |
| `0x348c0` | RectOutline | c19 | Build A IDENTICAL |

The five function-only cases are IntroFadeStep, IntroBeginFlic, FarmPanelChanged, BitmapClear and OpenArchive. Their current multi-function files do not pass whole-region verification. SaveErrorDialog passes E0 region verification but fails the existing data-anchor ordering rule. No splitting, symbolic rewriting or build-system fix is performed in E7.

The three individual Build A controls are `UnitCountAdd 0x13c04`, `UnitCountRemove 0x13c84`, and `SetCursorShape 0x13dd0`, each under c06 and each failing to match c01. Their links contain 520 functions / 515 C files. The fourth link includes all 13 new buildable objects together: 532 functions / 527 files. Each production `wc1.compare` returns `IDENTICAL (loaded image, entry, stack, fixups)`. The driver wires candidates only in memory, copies unpatched objects before production patching, and redirects Build A outputs into `build/e7/links/`.

## R6 preservation and the role of -5r

All **14 historically named R6 functions** have an observed `-5r` match in this grid. **11 are whole-object/RegionMatch and buildable**, while IntroBeginFlic, BitmapClear and OpenArchive remain function-only. Thirteen match when only the architecture token changes from their declared flags. **OpenArchive is an important qualification:** its observed c19 match uses `-zp2`, while its declared c24 uses `-zp1`; the exact declared-context `-5r -d1+ -zp1` combination is untested. Its observed match must not be attributed solely to architecture from this grid. The complete historical address list, actual matching configurations, and fixed-default/declared-context comparisons are all retained under `summary.r6`.

Using c06 alone finds 13 current functions, 11 whole/region/buildable matches and 94 score improvements against declared baselines (95 against c01). Three historical R6 functions—BitmapClear, DpmiGetFreeMemoryKB and OpenArchive—need the debug context c19, so a c06-only tally must not be called a reproduction of all R6. The declared-context architecture-only configuration is covered for **352 eligible functions** (including the unsupported missing-public case) and improves **93** scores; the other 21 eligible functions require 5r combinations outside this grid and are explicitly untested. The historical “76 improvements” is not reused as a current measurement.

`AiGuardStartArea 0x29f40` reproduces the important R6 change from score `[27, 8, 13, 12, 11]` to `[0, 0, 0, 0, 0]`, with E0 RegionMatch and a successful link in the combined Build A. `SetCursorShape 0x13dd0` improves `[1, 1, 0, 0, 4]` to zero: c01 emits `lea eax, [eax*4]` at object offset `0x1b`, whereas c06 emits the original `shl eax, 2`. The four-byte reduction also changes its conditional-branch displacement from `0x2c` to `0x28`; the earlier `lea eax, [edx*4]` remains under both flags. The expanded current corpus also yields buildable OptionsDialog and RectOutline matches. These results justify additive original-compiler search presets, not a claim that every original CU used Pentium options.

## Existing T3 compatibility and regressions

| Observed architecture compatibility | Functions |
|---|---:|
| both_4r_5r | 467 |
| neither_4r_nor_5r | 1 |
| only_3r | 0 |
| only_4r | 51 |
| only_5r | 0 |

These bins are disjoint and sum to 519. “only_4r” means only among the tested configurations: the grid contains 4r OD/frame variants without corresponding 5r OD variants. “both” does not identify an original architecture flag.

| Paired toggle from c01 | Baseline matches | Variant matches | Lost matches | Gained matches |
|---|---:|---:|---:|---:|
| 4r_to_5r (c06) | 417 | 417 | 0 | 0 |
| add_oa (c02) | 417 | 429 | 3 | 15 |
| add_oi (c12) | 417 | 411 | 6 | 0 |
| add_or (c11) | 417 | 191 | 226 | 0 |
| remove_ol (c03) | 417 | 395 | 22 | 0 |
| zp2_to_zp1 (c16) | 417 | 417 | 0 | 0 |

All **518 declared 10.0a T3 functions** match with their declared configurations. The remaining T3, `InitNewCampaign 0x1e100`, is declared OW2 and has an empty S under this 10.0a grid: its zero-score 10.0a object references unresolved `_STOSB_`. E0 correctly reports unsupported rather than accepting the numerical zero. Its separately recorded native OW2 control passes FunctionMatch and RegionMatch, and every linked Build A retains its native compiler. No production symbol alias is invented.

## Module/CU consistency

[cu_hypotheses.json](results/e7/cu_hypotheses.json) audits **125 module ranges**: **41** have non-empty intersections of observed S(f), and **84** are empty. For modules containing T3 functions, the T3-only subset has **90 non-empty** and **4 empty** intersections. Each empty module retains a concrete contradiction witness, functions with empty S, configuration support counts, missing coverage and current-source pragma evidence.

The four T3-only conflicts illustrate competing explanations:

- `mod_1e100`: InitNewCampaign is a native OW2 control with an unresolved 10.0a intrinsic spelling, so no 10.0a intersection is available.
- `mod_20c30`: UiIssueTownSquareOrder `0x21428` matches only c04, while UiActivateSpell `0x21238` matches c02/c07. This is a source/loop-context conflict in reconstructed separate files.
- `mod_269f0`: AilInit `0x269f0` matches c21 (OD/debug); SndSetMusicVolume `0x27460` matches c20 (OD without debug).
- `mod_2b8e0`: TerrainFlagTest `0x2bf30` needs alias-relaxed c02/c04/c07, whereas TerrainTablesInit `0x2b91c` matches a disjoint set of non-alias-relaxed configurations.

Every empty intersection is classified as contradictory evidence. The database explicitly considers all five RFC §12.2 causes: incomplete flag coverage, a reconstruction error, a local pragma, source-specific compilation behavior, and a hidden none16 boundary requiring independent evidence. The conflicts above do not distinguish all those causes. Most mixed-module emptiness is dominated by unsolved T4 functions, and current reconstructed TUs differ from original CUs. **No new CU boundary is inferred.** Non-empty intersections support compatibility hypotheses only.

## Proposed production search hierarchy

[proposed_presets.json](results/e7/proposed_presets.json) seeds the current default and greedily covers new events by lexicographic marginal yield: buildable T4, function T4, strict score improvement, then existing-T3 coverage; ties follow configuration order. This is empirical coverage ranking, not a timing model or recovered-original-flag claim. Tier 1 is the first five useful configurations; Tier 2 retains every remaining positive-yield configuration.

| Tier | Config | Concrete flags | Marginal function gain | Marginal buildable gain | Marginal score improvements | Existing-T3 coverage gain |
|---|---|---|---:|---:|---:|---:|
| 1 | c01 | `-s -ot -ol -4r -zp2` | 0 | 0 | 10 | 417 |
| 1 | c07 | `-s -ot -oa -ol -5r -zp2` | 14 | 11 | 113 | 15 |
| 1 | c19 | `-s -ot -ol -5r -d1+ -zp2` | 4 | 2 | 32 | 35 |
| 1 | c22 | `-s -os -4r -zp2` | 1 | 0 | 21 | 0 |
| 1 | c03 | `-s -ot -4r -zp2` | 0 | 0 | 17 | 0 |
| 2 | c10 | `-s -ot -ol -3r -zp2` | 0 | 0 | 7 | 0 |
| 2 | c21 | `-s -od -4r -d1+ -zp2` | 0 | 0 | 6 | 45 |
| 2 | c06 | `-s -ot -ol -5r -zp2` | 0 | 0 | 4 | 0 |
| 2 | c26 | `-s -ot -ol -4r -of+ -zp2` | 0 | 0 | 4 | 0 |
| 2 | c04 | `-s -ot -oa -4r -zp2` | 0 | 0 | 2 | 1 |
| 2 | c11 | `-s -ot -ol -or -4r -zp2` | 0 | 0 | 2 | 0 |
| 2 | c20 | `-s -od -4r -zp2` | 0 | 0 | 0 | 3 |
| 2 | c24 | `-s -ot -ol -4r -d1+ -zp1` | 0 | 0 | 0 | 2 |

Tier 1 covers all 19 new function matches, all 13 buildable opportunities and 193 improved functions. Tier 2 adds 25 improved functions and completes coverage of the 518 native-10.0a T3 functions; it adds no further T4 matches. The first three Tier-1 configurations already recover all 13 buildable opportunities. Preserve the declared-file flags and native OW2 fallback. The paired default architecture control shows no regression here; the evidence supports additive search presets without requiring a global default change.

## Reproduction and validation

Run directly in the supplied Nix shell; do not invoke a nested dev shell or `make verify`:

```sh
python3 -m experiments.build_codegen.e7.run_e7
pytest -q experiments/build_codegen/e7/test_e7.py
git diff 7c23d2371e95d8de93f0ba1652c8d44b858da273 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md
```

The default runner freshly compiles the complete grid with six workers, probes capabilities, checks placement, performs four Build A links, and regenerates all five committed result files. Timing is recorded separately in `build/e7/timing.json`; volatile elapsed times and compiler object timestamps are excluded from committed results. The compact matrix encoding preserves every cell while keeping the machine-readable artifact below 100 MiB.

The pytest suite validates all five states, exhaustive S retention, duplicate-segment-safe memoization, dependency checks in data segments, missing-public handling, exact recomputation of summary/CU/preset/CSV data, complete linked coverage, a repeated real capability probe, and seven fresh real compiler cells including R6, a regression, debug/OD and missing-public cases. Fresh-run timing was `308.97 s` (`jobs=6`, recorded in `build/e7/timing.json`), `pytest -q experiments/build_codegen/e7/test_e7.py` passed `18/18` (`6.51 s`), and harness/dataset commits are `a6798c3` and `3799991`.

## Limits and production follow-up

No source spelling, multi-function grouping, data placement or symbol alias is changed. Mismatching bodies remain mismatches/unsupported and the project’s T3/T4 counts stay at 519/385. The flag grid is deliberately finite; 5r OD, some source-specific 5r combinations, secondary-flag interactions, `-zp4`, `-d1` and `-d2` runtime sweeps are not covered. Capability acceptance alone does not justify a production preset.

Production adoption should add the empirically ranked presets with the same strict matcher and placement/link checks, preserve full compatible-set provenance, and use the five function-only cases plus SaveErrorDialog as inputs to the separate extraction/data-anchor experiments. Changes to production drivers, original-CU boundaries, tier definitions or gates are outside E7.
