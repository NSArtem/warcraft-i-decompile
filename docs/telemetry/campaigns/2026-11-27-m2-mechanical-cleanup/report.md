# Production Campaign Telemetry — M2 Mechanical Cleanup

- **Campaign ID:** `2026-11-27-m2-mechanical-cleanup`
- **Repository:** `NSArtem/warcraft-i-decompile`
- **Starting `main` commit:** `b0196b409be8c0e304f96712632d8e9ebcbd05fc` (already includes `feature/e7-compiler-presets` `3123a47`)
- **Implementation branch:** `feature/m2-mechanical-cleanup` (not auto-merged into `main`)
- **Verified code commit:** `b8d8fb115f71fb534e8981ab2cb035b6aed90e95`
- **Manager / Analyst:** Gemini 4 Neon (High) via Antigravity (`4dd12c69-e0cf-41e6-a460-8933322921b7`)
- **Developer / Reviewer:** `opencode-go/deepseek-v4.1-flash` via `opencode2 v2.4.1` (fresh isolated sessions)

---

## 1. Outcome Summary

| Metric | Before (`main` `b0196b4`) | After (`b8d8fb1`) | Delta |
|---|---:|---:|---:|
| In-scope functions | 1,010 | 1,010 | 0 (no scope change) |
| Semantic name (`>= medium`) | 914 (90.5%) | **926 (91.7%)** | **+12** |
| T3 matched, built from C | 532 (`531 10.0a`, `1 ow2`) | **539 (`537 10.0a`, `2 ow2`)** | **+7 T3** |
| T4 reference C, difftested | 372 | **373** | **+1 T4** |
| Unchecked `ref` | 6 | **5** | **-1** |
| No C | 100 | **93** | **-7** |
| **DONE (`name + T3`, or `T4 + blocker`)** | **899 (89.0%)** | **912 (90.3%)** | **+13 DONE** |
| Remaining not-DONE backlog | 111 | **98** | **-13** |
| `overnight` default Wave 3 eligible queue | 4 | **14** | **+10** (`BULLET.C`) |
| Build A (`wc1.build` + `wc1.compare`) | `IDENTICAL` (`532` fns / `527` files) | **`IDENTICAL` (`539` fns / `534` files, `0` legacy)** | +7 fns / +7 files |
| Serialized `make verify` | green | **green (`71.516 s`, `2283 passed, 11 skipped, 5 xfailed`)** | PASS |

### Category Breakdown (No Double-Counting)
- **A1 — Immediate wiring (`+1 DONE`, `+1 T4`, `-1 ref_unchecked`):**
  - `0x1bf94` `WaitInputOrTimeout` (`c9d8733`): revalidated `tests/test_mod_1bf80.py::test_wait_input_or_timeout` live with `WC1_T4_AUDIT_LOG` (`cases_run=4`), wired `ref_verified_by`.
  - `0x23170` `IntroOpSyncSound` (**deferred**, reclassified in `e1a4178`): `wc1.match` reports `MATCH` and `build.check_t3_buildable` returned a false positive `(True, "")`, but real `python3 -m wc1.build` fails with NASM OMF32 error (`OBJ format can only handle 16- or 32-byte relocations`) because cutting `0x23170` splits the asm between `0x2316c` (shared epilogue of `IntroOpPlaySound`) and `0x231cc` (`IntroOpWaitSound` `je/jne short loc_2316c`). Genuinely requires B2/E1 shared-epilogue support; deferred cleanly without weakening build gates.
- **A2 — Existing verified C requiring semantic names (`+5 DONE`, `+5 named`):**
  - `0x214d4` `fn_214d4` -> `PacketSend` (`f5cf65d`, T3, moved `mod_20c30.toml` -> `packet.toml`, 27 files)
  - `0x26360` `fn_26360` -> `UnitStartAnim` (`b4891ff`, T4, moved `mod_20c30.toml` -> `snd_f1.toml`, 19 files)
  - `0x2b308`/`0x2b31c`/`0x2b390` -> `TargetModeIsActive`/`TargetModeEnter`/`TargetModeExit` (`59a963c`, 3× T3, moved `mod_2efd0.toml`+`packet.toml` -> `mod_2b2f0.toml`, 25 files)
- **A3 — Existing matched `codegen_promo.toml` candidates (`+7 DONE`, `+7 T3`, `+7 named`):**
  - `229c32b`: migrated all 7 matched samples out of `codegen_promo.toml` (keeping `LOCKED_TOMLS` / `PROTECTED_TOMLS` untouched and retaining `fn_150f0`, `NetLinkHandshake`, and the 4 `dat_*` entries in `codegen_promo.toml`):
    - `0x1132c` -> `AttackFatalStub` (`10.0a`, `src/mod_104b0/attack_fatal_stub.c`, `mod_104b0.toml`)
    - `0x123cc` -> `BulletFatalStub` (`10.0a`, `src/mod_104b0/bullet_fatal_stub.c`, `mod_104b0.toml`)
    - `0x13e94` -> `DemoIdleTimerReset` (`10.0a`, `src/mod_13e60/demo_idle_timer_reset.c`, `mod_13e60.toml`)
    - `0x15170` -> `MapChoiceForest` (`10.0a`, split from `src/codegen/mod_13f60.c` -> `src/mod_13f60/map_choice_forest.c`, `mod_13f60.toml`)
    - `0x15230` -> `NetGameHandshakeCallback` (`10.0a`, split -> `src/mod_13f60/net_game_handshake_callback.c`, `mod_13f60.toml`)
    - `0x15558` -> `PhoneNumberSave` (`10.0a`, split -> `src/mod_13f60/phone_number_save.c`, `mod_13f60.toml`)
    - `0x19478` -> `GameRandom` (native `ow2` preserved, 10.0a compile-check green, `src/mod_19470/game_random.c`, `mod_19470.toml`)
- **A4 — Stale `BULLET.C` exclusion (`+0 DONE`, `+10` newly Wave-3-eligible):**
  - `2456f0c`: removed only `"BULLET.C"` from `overnight.DEFAULT_SKIP` (preserving `"STATUS.C"` and `"PLAYFLIC.C"` and all `needs_human`/`LOCKED_TOMLS` guards), updated `tests/test_overnight.py` with regression tests. Newly eligible addresses: `0x119c0`, `0x11c50`, `0x11fa8`, `0x11ff0`, `0x12074`, `0x120c8`, `0x12240`, `0x122d0`, `0x12338`, `0x123e0`; the 8 `mod_104b0.toml` stubs (`0x11a10`..`0x11f78`) remain properly gated in `needs_human`.
- **A5 — Deferred exclusions (untouched):** B1/B2/B3 (`0x157e8`, `0x1e380`, `0x2315c`, `0x23170`, `0x2e96c`, `0x2efd0`, `0x2f73c`), 5 ref-C behavioral divergences (`0x231cc`, `0x23530`, `0x23668`, `0x23ae0`, `0x2fcfc`), 8 governance/discovery/scope artifacts (`0x110a0`, `0x11530`, `0x28090`, `0x28093`, `0x3fe34..0x400b4`).

---

## 2. Atomic Commits on `feature/m2-mechanical-cleanup`

1. `c9d8733` — `T4: wire WaitInputOrTimeout (0x1bf94) difftest ref_verified_by`
2. `2456f0c` — `wc1.overnight: remove stale BULLET.C from DEFAULT_SKIP + tests`
3. `e1a4178` — `wc1.m2_inventory: reclassify IntroOpSyncSound under shared-epilogue blocker`
4. `f5cf65d` — `PACKET.C: fn_214d4 -> PacketSend (T3, verified) and move its record to packet.toml`
5. `b4891ff` — `SND.C: fn_26360 -> UnitStartAnim and move its record to snd_f1.toml`
6. `59a963c` — `mod_2b2f0: fn_2b308/fn_2b31c/fn_2b390 -> TargetModeIsActive/Enter/Exit, records moved to mod_2b2f0.toml`
7. `229c32b` — `T3: name and rebuild the 7 codegen_promo samples in their areas (safe split from src/codegen)`
8. `b8d8fb1` — `m2-cleanup: resolve rev-m2-01 findings (test_overnight, mod_2b2f0.h, docs, prototypes)`

---

## 3. Independent Review & Session Telemetry

| Session ID | Role | Model (`opencode2 v2.4.1`) | Status / Verdict | Wall (s) | Turns | Tool Calls | Input Tokens (Cached) | Output | Reasoning | Commits |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `dev-m2-a1a4-01` | developer | `opencode-go/deepseek-v4.1-flash` | `COMPLETED` | 365.1 | 52 | 84 | 3,154,891 (97.1%) | 13,661 | 20,022 | `c9d8733`, `2456f0c`, `e1a4178` |
| `dev-m2-a2-01` | developer | `opencode-go/deepseek-v4.1-flash` | `COMPLETED` | 370.1 | 85 | 107 | 5,634,379 (98.4%) | 17,846 | 10,176 | `f5cf65d`, `b4891ff`, `59a963c` |
| `dev-m2-a3-01` | developer | `opencode-go/deepseek-v4.1-flash` | `COMPLETED` | 521.1 | 59 | 94 | 5,456,429 (97.5%) | 24,667 | 30,965 | `229c32b` |
| `rev-m2-01` | reviewer | `opencode-go/deepseek-v4.1-flash` | `REQUEST_CHANGES` | 670.1 | 95 | 144 | 11,982,934 (98.4%) | 20,931 | 34,101 | — |
| `dev-m2-fix-01` | developer | `opencode-go/deepseek-v4.1-flash` | `COMPLETED` | 178.0 | 28 | 59 | 1,289,176 (95.5%) | 8,743 | 5,974 | `b8d8fb1` |
| `rev-m2-02` | reviewer | `opencode-go/deepseek-v4.1-flash` | **`APPROVE`** | 304.1 | 35 | 58 | 2,282,605 (95.4%) | 7,442 | 23,808 | — |
| **Total** | **6 sessions** | **0 timeouts / 0 orphans** | **4 dev / 2 rev** | **2,408.5** | **354** | **546** | **29,800,414 (97.8%)** | **93,290** | **125,046** | **8 code commits** |

*Accounting:* OpenCode2 reports `reasoning_tokens` separately from `output_tokens`; `input_tokens = uncached_input + cache.read`; OpenCode Go subscription quota % and `reasoning_time_s` are `unavailable` locally.

- **Round 1 (`rev-m2-01` on `229c32b`):** `REQUEST_CHANGES` — 0 CRITICAL, 2 HIGH (`test_overnight.py` stale `needs_human` checks for newly DONE A2/A3 addresses), 3 MEDIUM (`mod_2b2f0.h` stale `TargetModeGet`/`TargetModeLeave`, false near-miss statement in `mod_2b2f0.md`, 4 stale `fn_214d4` evidence refs), 9 LOW.
- **Round 2 (`rev-m2-02` on `b8d8fb1`):** **`APPROVE`** — All H1/H2/M1–M3 and LOW 1–7 verified resolved cleanly; 2 non-blocking LOW doc/text notes only.

---

## 4. Serialized Final Verification (`make verify`)

- **Command:** `nix develop -c make verify` (global `flock` lock, isolated `WINEPREFIX` and short `TMPDIR`)
- **Verified commit:** `b8d8fb115f71fb534e8981ab2cb035b6aed90e95`
- **Wall time:** `71.516 s` (`exit_code = 0`)
- **Stages:**
  - `wc1.symbols`: `1370 functions, 956 data symbols` (0 errors)
  - `wc1.roundtrip`: `ROUND-TRIP OK: 366 raw instructions of 64173` (`image_identical=True`)
  - `wc1.match --all`: `534 files, 0 failed`
  - `wc1.match --compile-check`: `880 files x 2 compilers, 0 failures`
  - `wc1.build` + `wc1.compare`: `539 functions from 534 C files (534 placed in sequence, 0 legacy layout)` -> **`IDENTICAL (loaded image, entry, stack, fixups)`**
  - `pytest -n auto`: **`2283 passed, 11 skipped, 5 xfailed in 54.12s`**
