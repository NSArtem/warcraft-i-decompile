I'll start by getting oriented: check the current state, read the promo TOML, and understand the precedent.
Time budget: ~2640s left. Let me examine the source files and target TOMLs in parallel.
Now I'll create the migrated C files.
All seven migrations are complete, verified, and committed as one atomic unit (all changes are interdependent through the shared `codegen_promo.toml`/guard rewrite, so splitting would have produced red intermediate commits).

## 1. Commit

**`229c32b`** — `T3: name and rebuild the 7 codegen_promo samples in their areas (safe split from src/codegen)` (52 files)

| Addr | Old → New | Compiler | Record moved to | C file |
|---|---|---|---|---|
| 0x1132c | `fn_1132c` → `AttackFatalStub` | 10.0a | `mod_104b0.toml` (module `mod_110a0`) | `src/mod_104b0/attack_fatal_stub.c` |
| 0x123cc | `fn_123cc` → `BulletFatalStub` | 10.0a | `mod_104b0.toml` (module `BULLET.C`) | `src/mod_104b0/bullet_fatal_stub.c` |
| 0x13e94 | `fn_13e94` → `DemoIdleTimerReset` | 10.0a | `mod_13e60.toml` | `src/mod_13e60/demo_idle_timer_reset.c` |
| 0x15170 | `fn_15170` → `MapChoiceForest` | 10.0a | `mod_13f60.toml` | `src/mod_13f60/map_choice_forest.c` |
| 0x15230 | `fn_15230` → `NetGameHandshakeCallback` | 10.0a | `mod_13f60.toml` | `src/mod_13f60/net_game_handshake_callback.c` |
| 0x15558 | `fn_15558` → `PhoneNumberSave` | 10.0a | `mod_13f60.toml` | `src/mod_13f60/phone_number_save.c` |
| 0x19478 | `fn_19478` → `GameRandom` | **ow2** (10.0a compiles, mismatches) | `mod_19470.toml` | `src/mod_19470/game_random.c` |

Affected-file manifest beyond the 7 C files: the 6 TOMLs above + `codegen_promo.toml` (6 records removed; `fn_150f0`, `NetLinkHandshake`, 4 `dat_*` kept unchanged), the deleted 5 `src/codegen/*.c` samples + stale `src/mod_13e60/fn_13e94.c`, renames in `mod_16390.toml`/`save_score.toml`/`mod_13f60.toml`/`mod_19470.h`/`mod_295d0.h`/`mod_2efd0.h`/`mod_16390.h` and 20 referencing ref-C files, `tests/test_codegen_promo.py` (rewritten guard), `tests/test_mod_13e60.py`, 7 subsystem docs. `LOCKED_TOMLS`/`PROTECTED_TOMLS`, `Makefile`, `progress.py` untouched.

## 2. `wc1.progress` before → after

| | before | after |
|---|---|---|
| named (≥ medium) | 919 (91.0%) | **926 (91.7%)** |
| T3 built from C | 532 (10.0a 531, ow2 1) | **539 (10.0a 537, ow2 2)** |
| T4 difftested | 373 | 373 |
| reference not checked | 5 | 5 |
| no C | 100 | 93 |
| **DONE** | **905 (89.6%)** | **912 (90.3%)** |

## 3. Build A

`IDENTICAL (loaded image, entry, stack, fixups)` — `539 functions from 534 C files (534 placed in sequence, 0 legacy layout)`. The pre-function jump table at 0x19494 did **not** obstruct `game_random.c`; all three split `mod_13f60` objects place in sequence, including the two extent-clamped ones.

## 4. Verification (all in `nix develop -c …`)

- `python3 -m wc1.symbols` → `1370 functions, 956 data symbols`, no errors.
- `python3 -m wc1.match --all` → `534 files, 0 failed`.
- `python3 -m wc1.match <file>` → `MATCH` for all 7 new files; `--compile-only` clean for every new/modified C file (10.0a, and ow2 for `game_random.c`; `--cc other` also compiles it under 10.0a). Note: the CLI flag is `--compile-only` (there is no `--compile-check`).
- `python3 -m wc1.build` → `IDENTICAL`.
- `pytest -n auto` on `test_codegen.py`, `test_codegen_promo.py`, `test_progress.py` + 27 module test files → **309 passed, 1 xfailed** (plus the 50-test codegen/promo/progress subset run separately). The `test_extent_retry_matches_the_flow_end` guard is retained for `MapChoiceForest_`/`NetGameHandshakeCallback_` on the new single-function files.

## 5. Deferred candidates / technical notes

None deferred — all 7 migrated.

One adjustment worth recording: the two FatalError tags (0x569d4 `"attack:1"`, 0x569e0 `"bullet:6"`) are now named data symbols (`attack_fatal_tag`, `bullet_fatal_tag`) referenced externally, instead of inline literals. Inline literals gave the objects CONST segments at 0x569d4/0x569e0, and `wc1.build` rejected them with exactly `C objects' data anchors are not in code order` (those anchors precede the existing 0x1a8e4→0x51e26 anchor). Extern references keep the same relocation target while adding no data anchor. The 4 `dat_*` staging symbols were left un-renamed; only their evidence text was pointed at the new files.