I'll start by orienting myself in the repository and checking the scope integrity of the commits under review.
# Independent Adversarial Review — `feature/m2-mechanical-cleanup` (`b0196b4..229c32b`)

Scope: 128 files, 7 commits. HEAD `229c32b`, base `b0196b4`. Working tree clean except the pre-existing untracked `original/` symlink. No repository files were modified; the 0x23170 build experiment was run in a throw-away copy under `/tmp/wc1-rev-m2-01/opencode/rev-copy`.

## CRITICAL

None. Scope and governance rest untouched (evidence in “Verified clean” below).

## HIGH

### H1. The branch is red: `b4891ff`, `59a963c` and `229c32b` break `tests/test_overnight.py::test_build_queue_with_needs_human_filters_unautomatable`

- File: `tests/test_overnight.py:818-820` (test introduced at `93a83f0`, untouched by this range).
- The test asserts the old staging addresses `0x1132c, 0x13e94, 0x15170` are present in `needs_human` with a `"locked TOML"` reason, and (line 826-828) that `0x26360, 0x2b308` are present in `needs_human`.
- A2/A3 promoted exactly these addresses to named, wired, **done** T3 records. `overnight.build_queue_with_needs_human()` skips done rows entirely (`tools/wc1/overnight.py:716`), so they are absent from both the queue and `needs_human`:

```
$ nix develop -c python3 -m pytest -q tests/test_overnight.py::test_build_queue_with_needs_human_filters_unautomatable
E  AssertionError: assert (70444 in {69792: 'data-in-code ...', ...})
tests/test_overnight.py:820: AssertionError      # 70444 = 0x1132c
```

- Confirmed as a commit-level regression, not a base problem: in a clean tree at `b4891ff`, the same test already fails at the later group:

```
$ (tree at b4891ff) pytest ...::test_build_queue_with_needs_human_filters_unautomatable
E  AssertionError: assert 156512 in {...}      # 156512 = 0x26360
tests/test_overnight.py:828
```

  `0x26360` is made done by `b4891ff` (SND rename); `0x2b308` by `59a963c`; `0x1132c`/`0x13e94`/`0x15170` by `229c32b`.
- Impact: `Makefile:56-57` runs `pytest -q -n auto tests` and `verify:` depends on `test` (`Makefile:63`), so `make verify` cannot be green at HEAD or at `b4891ff`/`59a963c`. This violates the AGENTS rule that every commit leaves `make verify` green.
- Fix direction: keep the “must never be queued” half, drop the “must be in `needs_human`” half for addresses that are now done (assert absent from both), and keep reason checks for the still-blocked addresses (`0x110a0`, `0x11530`, `0x257dc`, `0x2efd0`, `0x2f73c`).

### H2. `229c32b` breaks the test added by `2456f0c` (`0x123cc` is no longer “locked”)

- File: `tests/test_overnight.py:545-547` (added by `2456f0c`, broken by `229c32b`).
- The test asserts `"locked TOML" in nh[0x123cc]`; `229c32b` moves `0x123cc` out of `analysis/symbols/codegen_promo.toml` into `mod_104b0.toml`, names it `BulletFatalStub`, and wires its `src=`, so it is a done T3 and no longer in `needs_human`:

```
$ nix develop -c python3 -m pytest -q tests/test_overnight.py::test_bullet_c_clean_functions_queued_after_default_skip_removal
E  KeyError: 74700          # 0x123cc
tests/test_overnight.py:547
```

- The 10 clean BULLET.C addresses and the 8 gated stubs in the same test still behave correctly; only the `0x123cc` guard is stale. `2456f0c` alone is green (verified in a clean tree: both tests pass).
- Impact: same `make verify` blocker as H1; the two commits are not independently green.

## MEDIUM

### M1. `59a963c` leaves stale, non-existent prototypes in `src/include/mod_2b2f0.h`

- `src/include/mod_2b2f0.h:14`: `unsigned short TargetModeGet(void); /* 0x2b308 */`
- `src/include/mod_2b2f0.h:16`: `void TargetModeLeave(void); /* 0x2b390 */`
- The commit renames 0x2b308 → `TargetModeIsActive` and 0x2b390 → `TargetModeExit`; only `TargetModeEnter` (line 15) happens to match. `TargetModeGet`/`TargetModeLeave` now name no symbol anywhere in the tree (`grep -rn "TargetModeGet\|TargetModeLeave" src tests analysis docs` returns only these two header lines). Any future caller using the header will fail to link. Compile-check passes only because nothing includes/calls them.
- This is an interface-consistency bug at exactly the addresses the commit claims to rename.

### M2. `59a963c` writes a false statement into `docs/subsystems/mod_2b2f0.md`

- `docs/subsystems/mod_2b2f0.md:19`: “The near-miss guard asserts that the two target-mode reference files and `target_mode_clear_reference.c` still do not match.”
- In fact both `target_mode_enter_reference.c` and `target_mode_exit_reference.c` **MATCH** and are recorded `verified` + `match:` T3 (`analysis/symbols/mod_2b2f0.toml:20-47`), and `t4spec.assert_ref_mismatch` requires `src=` records to match (`tools/wc1/t4spec.py:165-172`):

```
$ wc1.match src/mod_2b2f0/target_mode_enter_reference.c  -> MATCH
$ wc1.match src/mod_2b2f0/target_mode_exit_reference.c   -> MATCH
$ wc1.match src/mod_2b2f0/target_mode_clear_reference.c  -> MISMATCH
```

  Only `target_mode_clear_reference.c` is a near-miss. The doc contradicts both the table above it and the TOML.

### M3. `f5cf65d` leaves `fn_214d4` evidence references in other areas

- `analysis/symbols/net_link.toml:104` and `:147`
- `analysis/symbols/save_score.toml:219`
- `analysis/symbols/status.toml:1944`
- These are the only remaining `fn_214d4` references outside history/research artifacts; the symbol no longer exists (renamed `PacketSend` in `packet.toml`). A search by the new name misses four pieces of evidence, against the project rule that names/claims live in the TOMLs with evidence. The `packet.toml`/`mod_20c30.toml`/`packet.md` references were updated; these four were missed.

## LOW

1. `docs/subsystems/snd_f1.md:9` cites `src/snd/UnitStartAnim_reference.c`; the actual file is `src/snd/unit_start_anim_reference.c` (lower-case). `b4891ff`.
2. `docs/subsystems/mod_13f60.md:224` still says `fn phone_load`/`fn phone_save` after `PhoneNumberLoad`/`PhoneNumberSave` were named. `229c32b`.
3. `docs/subsystems/packet.md:241-242` says `TargetModeEnter`/`TargetModeExit` are “placeholders in `packet.toml`”; after `59a963c` they are full verified records in `mod_2b2f0.toml`.
4. `tests/test_codegen_promo.py:9-10,25-26` docstring still lists the deleted `src/codegen/{bullet,mod_110a0,mod_13e60,mod_13f60,mod_19470}.c` files and old `fn_*` names (written in the past tense, but stale).
5. `analysis/symbols/mod_19470.toml:18` proto is `"int GameRandom(int id);"` — stray trailing semicolon; also the `id` parameter is unused (documented in the source comment).
6. `src/mod_13f60/net_game_start_reference.c:27` declares `void NetGameHandshakeCallback(void)` while the new definition/TOML is `int`; harmless because the return value is unused, but the prototypes disagree.
7. `analysis/symbols/mod_2b2f0.toml:19` proto says `int TargetModeIsActive(void)` while `src/mod_2b2f0/target_mode_is_active.c` defines `unsigned short`; pre-existing convention, but the DB prototype does not match the source.
8. Stale generated snapshots: `docs/research/m2-completion/{inventory.csv,inventory.json,dependency-groups.json,blocker-analysis.md,roadmap.md}` still describe the migrated entries as locked/staged. They are not regenerated by `wc1.m2_inventory --summary`; only a problem if they are meant to be current.
9. `src/include/mod_16390.h:264` comment “other areas' unnamed functions this object calls” now sits above the named `DemoIdleTimerReset` (cosmetic).

## Verified clean (concrete evidence)

**Scope / governance**
- `git diff --name-only b0196b4..229c32b` contains **no** `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, `tools/wc1/build.py`, `tools/wc1/emit.py`, `tools/wc1/omfpatch.py`, `tools/wc1/batch_driver.py`, `tools/wc1/wave4_fp.py`, `tools/wc1/wave4a.py`, `tools/wc1/discovery.py`, `analysis/modules.toml`.
- `LOCKED_TOMLS`/`PROTECTED_TOMLS` definitions unchanged (`batch_driver.py:769`, `wave4_fp.py:57`); only `analysis/symbols/codegen_promo.toml` content changed, by design of the A3 migration, and the lock itself remains.
- Discovery/scope artifacts unchanged: `0x110a0`/`0x11530` (`mod_104b0.toml` changes are header comment + appended records only), `0x28090`/`0x28093` (`status.toml` untouched), `0x3fe34..0x400b4` (`mod_3df40` untouched). The A4 diff to `m2_inventory.py` does not touch their branches.

**A1 — `WaitInputOrTimeout` 0x1bf94**
- `tests/test_mod_1bf80.py::test_wait_input_or_timeout` passes live (1 passed, no skip/xfail), with `WC1_T4_AUDIT_LOG` records `observed: true`, 4 cases, `run_pair` diffs 0.
- `t4spec.audit_t4_log(... ref_rel=..., orig_addr=0x1bf94, func_name="WaitInputOrTimeout_")` → `(True, {'cases_run': 4, ...})`.
- `wc1.match src/mod_1bf80/wait_input_or_timeout_reference.c` still MISMATCH (relocation targets differ), so `ref=` remains correct.

**A4 — BULLET.C / DEFAULT_SKIP**
- `tools/wc1/overnight.py:54` is `DEFAULT_SKIP = ("STATUS.C", "PLAYFLIC.C")`; only BULLET.C removed. The needs_human guards (`LOCKED_TOMLS`, untracked TOML, unbuildable T3, name-only) are unchanged.
- The 10 clean addresses are queued; the 8 mod_104b0 stubs stay out with `existing cross-TOML entry`; Playflic/STATUS queue exclusions hold (all checked live, except the stale `0x123cc` assertion in H2).

**0x23170 deferral is legitimate**
- `e1a4178`'s evidence is accurate: `build.check_t3_buildable(...)` returns `(True, "")`, but wiring `src=` in a throw-away copy of the tree makes `wc1.build` fail with:

```
piece_295.asm: error: OBJ format can only handle 16- or 32-byte relocations
  je short loc_2316c / jne short loc_2316c     # loc_2316c is extern
```

  i.e. `IntroOpWaitSound` 0x231cc keeps a rel8 into 0x2315c's epilogue, which becomes a cross-piece (external) relocation. The reclassification to `unbuildable_t3_shared_epilogue_after_cut` is more accurate than the old “unwired_buildable_t3” and does not weaken any test or invariant.

**A2 naming (5 functions)**
- Disassembly/evidence support every name: `PacketSend` 0x214d4 (pacing + sync-id stamp), `UnitStartAnim` 0x26360 (animation-table write), `TargetModeIsActive` 0x2b308 (flag read), `TargetModeEnter` 0x2b31c / `TargetModeExit` 0x2b390 (flag set/clear + handler installs). All still `MATCH`; no duplicate addresses; records moved to `packet.toml`, `snd_f1.toml`, `mod_2b2f0.toml` with no duplicate records left behind.
- No stale old `fn_*` identifiers remain in `src/`; `test_mod_2b2f0.py`/`test_packet.py`/`test_snd_f1.py` guards were renamed/tightened (`PLACEHOLDER` is now empty), not weakened.

**A3 split (7 samples)**
- `0x569d4` image bytes are `61 74 74 61 63 6b 3a 31 00` (`"attack:1"`), `0x569e0` are `62 75 6c 6c 65 74 3a 36 00` (`"bullet:6"`); both tags are relocation targets of the new stubs, which match byte-for-byte.
- `src/mod_19470/game_random.c`: OW2 `MATCH`, 10.0a included in the 2-compiler compile check, placed cleanly before the `0x19494` switch table (Build A identical).
- `tests/test_codegen_promo.py`: `test_extent_retry_matches_the_flow_end` is retained for `MapChoiceForest`/`NetGameHandshakeCallback` with the same `f["limit"] > f["end"]` clamp assertion; the old “no `src=`” guard was intentionally replaced by an exact remaining-entry guard (`PROMO_FUNCS`/`PROMO_DATA`), which is stricter, not weaker. All 7 promoted files are checked to still `MATCH`.

**Mechanical**
- `wc1.symbols`: 1370 functions / 956 data, exit 0.
- `wc1.match --all`: `534 files, 0 failed`.
- `wc1.match --compile-check`: `880 files x 2 compilers, 0 failures`.
- `wc1.build`: `539 functions from 534 C files`, **IDENTICAL** (loaded image, entry, stack, fixups).
- `wc1.progress`: in scope 1010, named 926 (91.7%), T3 539 + T4 373, DONE 912 (90.3%); `wc1.m2_inventory --summary`: `ref_unchecked 5`, `t3_by_compiler {10.0a: 537, ow2: 2}`.
- Targeted pytest: `test_codegen.py`, `test_codegen_promo.py`, `test_progress.py`, `test_mod_1bf80.py`, `test_packet.py`, `test_snd_f1.py`, `test_mod_2b2f0.py`, `test_mod_13e60.py`, `test_mod_13f60_c.py`, `test_mod_2ced0_c.py`, `test_mod_19470.py`, `test_t4spec.py`, `test_batch_driver.py`, `test_mod_104b0.py`, `test_mod_20c30.py`, `test_overnight_wave4.py`, `test_codex_backend.py`, `test_wave4a.py`, `test_symbols_cache.py`, `test_match_relocations.py` all pass — only `tests/test_overnight.py` fails (H1/H2).

**Summary:** the naming migrations and the codegen split are technically sound and fully mechanical-verifiable (match/build/compile-check all green). However, the branch cannot pass its own `make verify` because two `test_overnight.py` tests still encode the pre-migration state; A2 (from `b4891ff`) and A3 (`229c32b`) are not independently green. Plus the stale `mod_2b2f0.h` prototypes and the false near-miss doc statement should be fixed in the same units.

VERDICT: REQUEST_CHANGES