# Independent Adversarial Review Round 2 — Campaign A
**Branch:** `feature/m2-mechanical-cleanup` · **Tip:** `b8d8fb11` · **Base:** `b0196b4`
**Mode:** read-only; no repository files modified, no commits. Full `make verify` deliberately not run (Manager-owned).

## 1. Round 1 findings — resolution check

| ID | Finding | Status / evidence |
|---|---|---|
| **H1** | `test_build_queue_with_needs_human_filters_unautomatable` failed on newly DONE `0x1132c`, `0x13e94`, `0x15170`, `0x26360`, `0x2b308` | **Resolved.** `tests/test_overnight.py:816-832` now asserts the five are absent from both queue and `needs_human`; all five are genuinely DONE (verified T3 in `mod_104b0.toml:1252`, `mod_13e60.toml:15`, `mod_13f60.toml:449`; `0x26360` T4+blocker in `snd_f1.toml:26`; `0x2b308` T3 in `mod_2b2f0.toml:16`). No weakening: `0x150f0` still requires `"locked TOML"` (line 824), `0x257dc` still requires `"existing cross-TOML entry"`, and the data-in-code (816) / unbuildable-T3 (826-828) guards remain. Test passes. |
| **H2** | `test_bullet_c_clean_functions_queued_after_default_skip_removal` failed on newly DONE `0x123cc` | **Resolved.** `tests/test_overnight.py:545-547` now asserts absence from queue and `needs_human`; `0x123cc` is verified T3 in `mod_104b0.toml:1267` and `test_codegen_promo.py` proves it is no longer in locked `codegen_promo.toml`. The 8 `mod_104b0` stub guards (`"existing cross-TOML entry"`) and the 10 queued clean functions remain enforced. Test passes. |
| **M1** | Stale `TargetModeGet` / `TargetModeLeave` prototypes | **Resolved.** `src/include/mod_2b2f0.h:14,16` use `TargetModeIsActive` / `TargetModeExit`; repo-wide grep finds no `TargetModeGet`/`TargetModeLeave`. |
| **M2** | `docs/subsystems/mod_2b2f0.md:19` falsely claimed enter/exit references still mismatch | **Resolved.** Lines 17-19 now correctly say enter/exit are T3 and only `target_mode_clear_reference.c` is a near miss. Independently confirmed: `wc1.match` → `TargetModeEnter_` MATCH, `TargetModeExit_` MATCH, `TargetModeClear_` MISMATCH. `test_ref_mismatch` still enforces this via `assert_ref_results` (T3 `src=` must match, T4 `ref=` must not), so the guard is stronger, not weakened. |
| **M3** | 4 stale `fn_214d4` evidence refs | **Resolved.** Updated in `net_link.toml` (×2), `save_score.toml`, `status.toml`; `grep fn_214d4 analysis/symbols/` is empty. (Only the dated `docs/research/m2-completion/*` snapshot at `d46f891` still shows old names; it is explicitly a snapshot, not symbol evidence.) |
| **LOW 1–7** | Doc casing/notes, docstring, semicolon, `int` extern, `unsigned short` proto, header comment | **Resolved.** `SetIrq`/`PhoneNumberLoad`/`PhoneNumberSave` casing matches the area TOMLs; `snd_f1.md` names the existing `src/snd/unit_start_anim_reference.c`; `packet.md` no longer lists TargetMode* as placeholders; `test_codegen_promo.py` docstring matches `PROMO_FUNCS`/`PROMO_DATA` exactly; `mod_19470.toml` proto has no trailing semicolon; `NetGameHandshakeCallback` is `int` in both the extern and function-pointer type (TOML proto is `int`; `test_mod_13f60_c` passes); `mod_2b2f0.toml` proto is `unsigned short` matching the C and header; `mod_16390.h` comment/alignment fixed. |

## 2. Scope / governance

`git diff --stat b0196b4..b8d8fb11` is **empty** for: `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, `tools/wc1/build.py`, `tools/wc1/emit.py`, `tools/wc1/omfpatch.py`, `tools/wc1/batch_driver.py`, `tools/wc1/wave4_fp.py`, `tools/wc1/match.py`, `tools/wc1/t4spec.py`, `tools/wc1/symbols.py`, `tools/wc1/analysis.py`, `analysis/symbols/clib.toml`, `analysis/modules.toml`.

`LOCKED_TOMLS` is still exactly `{"analysis/symbols/codegen_promo.toml"}` (`batch_driver.py:769`); `codegen_promo.toml` now holds only `fn_150f0`, the T4-only `NetLinkHandshake` and the four data symbols, enforced by `test_codegen_promo.py`.

## 3. Required command results (tip `b8d8fb11`)

| Command | Result |
|---|---|
| `python3 -m wc1.symbols` | 1370 functions, 956 data symbols; no errors |
| `python3 -m wc1.match --all` | **534 files, 0 failed** |
| `python3 -m wc1.match --compile-check` | **880 files × 2 compilers, 0 failures** |
| `python3 -m wc1.build` | 539 functions from 534 C files → **IDENTICAL** (loaded image, entry, stack, fixups) |
| `python3 -m wc1.progress` | in scope 1010; named 926 (91.7%); T3 539 (53.4%); T4 373; unchecked ref 5; **DONE 912 (90.3%)** |
| Required pytest subset | **197 passed in 37.95 s** (no skips) |
| Focused overnight guards | 3 passed (`default_skip`, `bullet_c_clean`, `build_queue_with_needs_human`) |

## 4. Remaining findings

**LOW-1 (documentation, non-blocking):** `docs/subsystems/codegen.md:300-302` still says the game samples `bullet.c`, `mod_110a0.c`, `mod_13e60.c`, `mod_13f60.c`, `mod_19470.c` "still need semantic names from the game-logic areas", contradicting the same file's section 5 (lines 215-223) and commit `229c32b`. The sentence should be updated to state that all seven were named/migrated on 2026-11-27 and only the `fn_150f0` body remains unreconstructed.

**LOW-2 (planning metadata, non-blocking):** `tools/wc1/m2_inventory.py` `GROUP_META` was not updated after this branch's reclassifications:
- line 606 (DG-01) still says `IntroOpSyncSound` is a "buildable T3", though `e1a4178` reclassified `0x23170` as `unbuildable_t3_shared_epilogue_after_cut` under DG-03;
- lines 637/639 (DG-05) still say "codegen_promo.toml (8)" and require splitting `src/codegen/mod_13f60.c`, which `229c32b` deleted; only `fn_150f0` (no C) remains.
Neither affects `make verify` or the reconciliation assertion; both are descriptive plan text worth a small follow-up commit.

**Not findings:** the `docs/research/m2-completion/*` inventories are explicitly a verified snapshot at `d46f891`; the historical "used to match" paragraph in `test_codegen_promo.py` is intentionally historical.

## 5. Assessment

All H1/H2/M1/M2/M3 and LOW 1–7 items are resolved cleanly, with the nightly `needs_human` guards intact and strengthened by `test_codegen_promo.py`'s exact `PROMO_FUNCS`/`PROMO_DATA` checks. The full required verification chain is green, the C build is byte-identical, and scope/governance files are untouched. The only new observations are two LOW documentation/planning-text staleness items that do not affect any gate.

VERDICT: APPROVE