I'll start by verifying the repo state and reading the files involved in the findings.
Now I'll apply the fixes, starting with the HIGH-severity test updates and header prototypes.
All verification checks pass. Now staging the exact modified files and committing.
Committed as `b8d8fb1` on `feature/m2-mechanical-cleanup` (parent `229c32b`), one atomic commit, no history rewrite.

## What changed

**HIGH**
- **H1** `tests/test_overnight.py`: the migrated/DONE addresses `0x1132c`, `0x13e94`, `0x15170` now assert absent from **both** `queued_addrs` and `nh`; the `"locked TOML"` guarantee is retained via `0x150f0` (still in `codegen_promo.toml`); `0x26360`/`0x2b308` moved to the DONE pair assertion; `0x257dc` keeps its `needs_human` membership assertion; all data-in-code/unbuildable-T3 reason assertions untouched.
- **H2** `tests/test_overnight.py`: `0x123cc` now asserts absent from both `queued` and `nh` (migrated to `mod_104b0.toml`, DONE T3); all 10 clean BULLET.C and 8 `mod_104b0` stub assertions preserved.

**MEDIUM**
- **M1** `src/include/mod_2b2f0.h`: `TargetModeGet` → `TargetModeIsActive`, `TargetModeLeave` → `TargetModeExit`.
- **M2** `docs/subsystems/mod_2b2f0.md`: enter/exit reference files documented as T3 matches; only `target_mode_clear_reference.c` remains a near-miss.
- **M3** 4 stale `fn_214d4` evidence refs → `PacketSend` in `net_link.toml` (2), `save_score.toml`, `status.toml`.

**LOW**
- `snd_f1.md` path fix, `mod_13f60.md` `PhoneNumberLoad`/`PhoneNumberSave`, `packet.md` target-mode note, `test_codegen_promo.py` docstring, `mod_19470.toml` proto semicolon + exact C signature, `net_game_start_reference.c` callback prototype (and its local pointer, required for OW2 type compatibility), `mod_2b2f0.toml` proto → `unsigned short`, `mod_16390.h` stale comment.

## Verification (all green)
- `wc1.symbols`: 1370 functions / 956 data
- `wc1.match --all`: 534 files, **0 failed**
- `wc1.match --compile-check`: 880 files × 2 compilers, **0 failures**
- `wc1.build`: **IDENTICAL** (539 functions from 534 C files)
- targeted pytest set: **189 passed** in 36.39 s
- `wc1.progress`: runs cleanly (DONE 912, 90.3%)

`make verify` was not run, per instructions. Untracked `original/` was left alone.