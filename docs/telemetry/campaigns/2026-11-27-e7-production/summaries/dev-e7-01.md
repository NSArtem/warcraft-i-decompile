I'll start by getting oriented in the repository.
Now attach source_digest to audit rows and enrich meta:
Now wave4a:
Now wave4 tests:
All three atomic commits are complete on `feature/e7-compiler-presets`. Nothing merged, nothing outside scope touched.

## Commits

| SHA | Task |
|---|---|
| `196153c` | Commit 1 — `wc1.permuter/t3_audit/wave4: add E7 10.0a presets and preset-aware audit invalidation + tests` |
| `2b10939` | Commit 2 — `T3: promote 13 verified E7 Watcom 10.0a -5r candidates (519 -> 532 T3, Build A IDENTICAL)` |
| `59efdd2` | Commit 3 — `wc1.t3_audit: add provenance-checked improved-T4 audit snapshot for Wave 4B + tests` |

## Presets (`permuter.FLAG_PRESETS`, 15 entries, single source of truth)

1. `10.0a -s -ot -ol -4r -zp2` (unchanged default, index 0)
2. `10.0a -s -ot -ol -5r -zp2` (c06, before c07)
3. `10.0a -s -ot -oa -ol -5r -zp2` (c07)
4. `10.0a -s -ot -ol -5r -d1+ -zp2` (c19)
5. `10.0a -s -ot -oa -ol -4r -zp2`
6. `10.0a -s -ot -ol -4r -d1+ -zp2`
7. `10.0a -s -od -4r -zp2`
8. `10.0a -s -od -4r -d1+ -zp2`
9. `10.0a -s -os -ol -4r -zp2`
10. `10.0a -s -os -4r -zp2` (c22)
11. `10.0a -s -ot -4r -zp2`
12. `10.0a -s -ot -oa -4r -zp2`
13. `10.0a -s -ot -ol -3r -zp2` (c10)
14. `10.0a -s -ot -ol -4r -of+ -zp2` (c26)
15. `ow2 -s -ot -ol -4r -zp2` (fallback)

`match.DEFAULT_CFLAGS` unchanged (`… -s -ot -ol -4r -zp2`). `t3_audit.current_presets()` now feeds `meta.options.{presets,base_flags}`, `meta.toolchain.tool_sig`, and per-row `source_digest`; `wave4.load_report` and `wave4a.load_audit_report_incremental` (unit_meta `plan`, bootstrap refusal) reject stale evidence.

## 13 promotions (all `MATCH_BUILDABLE` at the required minimal flags)

| Addr | Function | Flags (10.0a) | t3_audit | E0 Fn/Region | compile-check 10.0a+OW2 | difftests |
|---|---|---|---|---|---|---|
| 0x13c04 | UnitCountAdd | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | 110 pass (pre+post) |
| 0x13c84 | UnitCountRemove | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x13dd0 | SetCursorShape | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x15314 | SetGameMode | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x1a800 | OptionsDialog | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x1af20 | FogDrawCell | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x21df0 | WorkerReturnToMine | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x22a4c | PlaceBoxRoad | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x22a98 | PlaceBoxWall | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x29f40 | AiGuardStartArea | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x2ab54 | AiIdleUnitTick | `-s -ot -ol -5r -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x34060 | DpmiGetFreeMemoryKB | `-s -ot -ol -5r -d1+ -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |
| 0x348c0 | RectOutline | `-s -ot -ol -5r -d1+ -zp2` | MATCH_BUILDABLE | MATCH/MATCH | pass | pass |

- `wc1.match <each file>`: 13/13 `MATCH`; `--compile-check`: `13 files x 2 compilers, 0 failures`.
- `wc1.build` + `wc1.compare`: **`IDENTICAL`** — `532 functions from 527 C files`.
- `wc1.progress`: **T3 532, T4 372, DONE 899**. The 6 excluded functions untouched. `_reference.c` names preserved, bodies unmodified.

## Task C snapshot

`docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json` (no absolute host paths; digests + repo-relative paths only):
- Fresh `wc1.t3_audit --jobs 6`: **372 T4 — 0 MATCH_BUILDABLE, 7 MATCH_UNBUILDABLE, 363 MISMATCH, 2 SKIPPED, 0 COMPILE/TOOLCHAIN errors**.
- **202 improved residual T4 functions** (best score strictly beats declared, flags differ), **193 dependency-clean** (no unresolved relocations); all 202 pass `is_improved_record_fresh` on export.
- New helpers: `improved_t4_records(report, by_link=None)` and `is_improved_record_fresh(...)` (fail-closed on source/include digest, tool_sig, presets/base_flags, declared cflags, OMF symbol move/disappear/appear).

## Targeted verification run

- `pytest tests/test_permuter_unit.py tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py` → **210 passed** (before commit 1).
- Selective 13-candidate difftests → **110 passed** both before and after promotion.
- `pytest tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4_fingerprints.py` → **142 passed**; `python3 -m wc1.symbols` → `1370 functions, 954 data symbols` (clean).

## Status

`git status --porcelain` shows only the pre-existing untracked `original/` (never committed). No `build/` artifacts committed; no research branch merged/cherry-picked (E0 matcher was loaded read-only from `research/build-codegen-experiments` into `$TMPDIR` and is not part of any commit). No edits outside the specified tools/tests/docs scope.