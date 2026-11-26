# Developer Assignment — Campaign A Review Fixes (`dev-m2-fix-01`, addressing `rev-m2-01`)

You are the Developer working on branch `feature/m2-mechanical-cleanup` inside `/mnt/data/projects/wc1-wt-on/m2-dev` (HEAD is `229c32b`).
Do NOT rewrite git history (no amend/rebase); create one clean atomic fix commit on top of `229c32b`.
All repo commands run inside `nix develop -c <cmd>`.
Do NOT run full `make verify` (the Manager runs serialized `make verify` after fresh `rev-m2-02` review).

---

## Findings from Independent Reviewer (`rev-m2-01`) to Resolve

### HIGH
1. **H1 (`tests/test_overnight.py:818-828`, `test_build_queue_with_needs_human_filters_unautomatable`):**
   - `0x1132c`, `0x13e94`, `0x15170` (migrated by A3) and `0x26360`, `0x2b308` (migrated by A2) are now DONE, so `build_queue_with_needs_human()` properly omits them from BOTH `queue` and `needs_human`.
   - Fix WITHOUT weakening the test:
     - Keep asserting that the newly DONE addresses (`0x1132c`, `0x13e94`, `0x15170`, `0x26360`, `0x2b308`) are NOT in `queued_addrs` AND NOT in `nh` (since they are DONE).
     - Keep/strengthen the `"locked TOML"` check using `0x150f0` (which IS still in `analysis/symbols/codegen_promo.toml`!).
     - Keep all existing `needs_human` reason assertions for every still-blocked address (`0x110a0`, `0x11530`, `0x257dc`, `0x2efd0`, `0x2f73c`, etc.) intact!

2. **H2 (`tests/test_overnight.py:545-547`, `test_bullet_c_clean_functions_queued_after_default_skip_removal`):**
   - `0x123cc` (`BulletFatalStub`) is now migrated out of `codegen_promo.toml` and DONE T3, so it is absent from BOTH `queued_addrs` and `nh`.
   - Update the assertion for `0x123cc` to assert `0x123cc not in queued_addrs and 0x123cc not in nh` (preserving all assertions for the 10 newly eligible `BULLET.C` functions and the 8 `mod_104b0` stubs in `nh`!).

### MEDIUM
3. **M1 (`src/include/mod_2b2f0.h:14,16`):**
   - Replace stale non-existent prototypes `TargetModeGet` -> `TargetModeIsActive` and `TargetModeLeave` -> `TargetModeExit` (matching the exact prototypes in `src/mod_2b2f0/target_mode_*.c` and `analysis/symbols/mod_2b2f0.toml`).
4. **M2 (`docs/subsystems/mod_2b2f0.md:19`):**
   - Fix the false statement claiming `target_mode_enter_reference.c` and `target_mode_exit_reference.c` still do not match; clarify that both now MATCH T3 and only `target_mode_clear_reference.c` remains a near-miss.
5. **M3 (`analysis/symbols/{net_link,save_score,status}.toml`):**
   - Update the 4 stale `fn_214d4` evidence references (`net_link.toml:104,147`, `save_score.toml:219`, `status.toml:1944`) to `PacketSend` (keep address `0x214d4`).

### LOW (clean up cleanly without churn)
6. `docs/subsystems/snd_f1.md:9`: fix `src/snd/UnitStartAnim_reference.c` -> `src/snd/unit_start_anim_reference.c`.
7. `docs/subsystems/mod_13f60.md:224`: update `fn phone_load`/`fn phone_save` to `PhoneNumberLoad`/`PhoneNumberSave`.
8. `docs/subsystems/packet.md:241-242`: update stale note saying `TargetModeEnter`/`TargetModeExit` are placeholders in `packet.toml` (now verified in `mod_2b2f0.toml`).
9. `tests/test_codegen_promo.py` top docstring: update to reflect that the 7 samples migrated to their module areas while `fn_150f0` and the 4 `dat_*` symbols remain in `codegen_promo.toml`.
10. `analysis/symbols/mod_19470.toml:18`: remove stray trailing semicolon in `proto` (`int GameRandom(void)` or match `src/mod_19470/game_random.c` exact prototype — check `game_random.c` carefully so DB `proto` matches C!).
11. `src/mod_13f60/net_game_start_reference.c:27`: align `extern` prototype of `NetGameHandshakeCallback` to `int NetGameHandshakeCallback(void)` (verify `wc1.match --compile-check` and `tests/test_mod_13f60_c.py` stay green!).
12. `analysis/symbols/mod_2b2f0.toml:19` vs `src/mod_2b2f0/target_mode_is_active.c`: align `proto` to `unsigned short TargetModeIsActive(void)` (verify `wc1.symbols`, `wc1.match`, and `tests/test_mod_2b2f0.py` stay green!).
13. `src/include/mod_16390.h:264`: clean up stale comment above `DemoIdleTimerReset`.

---

## Verification Before Committing

Run ALL of:
- `nix develop -c python3 -m wc1.symbols`
- `nix develop -c python3 -m wc1.match --all`
- `nix develop -c python3 -m wc1.match --compile-check`
- `nix develop -c python3 -m wc1.build` (MUST be `IDENTICAL`)
- `nix develop -c pytest tests/test_overnight.py tests/test_overnight_wave4.py tests/test_codegen.py tests/test_codegen_promo.py tests/test_mod_2b2f0.py tests/test_mod_13f60_c.py tests/test_mod_19470.py tests/test_snd_f1.py tests/test_packet.py tests/test_progress.py`
- `nix develop -c python3 -m wc1.progress`

Stage explicit modified files and commit with a concise single-line message:
`m2-cleanup: resolve rev-m2-01 findings (test_overnight, mod_2b2f0.h, docs, prototypes)`

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:40:21.584263Z` (Unix epoch `1795732821`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-26T23:10:21Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-26T23:01:21Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally rather than waiting until the end; begin final wrap-up and final commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
