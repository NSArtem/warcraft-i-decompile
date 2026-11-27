## Campaign A / Task A2 — Final report

### 1. Commits

| SHA | Old → new | TOML migration | Affected files |
|---|---|---|---|
| `f5cf65d` | `fn_214d4` → **`PacketSend`** (PACKET.C) | `mod_20c30.toml` → `packet.toml`; `confidence = verified`, `verified_by = match: src/packet/packet_send.c` | 27 files: both TOMLs, `docs/subsystems/packet.md`, `src/include/{packet,mod_20c30}.h`, `src/packet/packet_send.c` + 16 senders + `packet_generate_id.c`, 4 `src/mod_20c30/*.c`, `tests/test_packet.py` |
| `b4891ff` | `fn_26360` → **`UnitStartAnim`** (SND.C) | `mod_20c30.toml` → `snd_f1.toml` next to `BulletStartAnim`; preserved `ref`, `ref_verified_by`, `t3_blocker`, evidence; proto corrected to `unsigned char anim` | 19 files: 4 TOMLs, 3 subsystem docs, 2 headers, 7 caller C files, `src/snd/fn_26360_reference.c` → `unit_start_anim_reference.c`, `tests/{test_snd_f1,test_mod_2ced0_c,test_batch_driver}.py` |
| `59a963c` | `fn_2b308`/`fn_2b31c`/`fn_2b390` → **`TargetModeIsActive`/`TargetModeEnter`/`TargetModeExit`** (`mod_2b2f0`) | `mod_2efd0.toml` + `packet.toml` → `mod_2b2f0.toml`; preserved `src`, `verified_by`, `confidence = verified`, evidence | 25 files: 7 TOMLs, 3 docs, 2 headers, 7 caller C files, 3 renamed C files, `tests/test_mod_2b2f0.py` |

C files were renamed cleanly; every TOML `ref`, test path/link-name, header prototype and comment was updated. No `fn_*` references remain for the five functions in `src/` or `tests/`.

### 2. `wc1.progress` before → after

Baseline measured from `e1a4178` in a throwaway worktree:

| metric | before | after |
|---|---|---|
| named (≥ medium) | 914 (90.5%) | **919 (91.0%)** |
| T3 | 532 (52.7%) | 532 (52.7%) |
| T4 | 373 (36.9%) | 373 (36.9%) |
| **DONE** | **900 (89.1%)** | **905 (89.6%)** |

All five now classify as named and DONE (4 T3 + 1 T4 with blocker): +5 DONE exactly.

### 3. Build A

`IDENTICAL (loaded image, entry, stack, fixups)` — `532 functions from 527 C files (527 placed in sequence, 0 legacy layout)`.

### 4. Verification commands / results

Run before each commit:

- `nix develop -c python3 -m wc1.symbols` → `1370 functions, 954 data symbols`
- `nix develop -c python3 -m wc1.match --all` → `527 files, 0 failed`
- `nix develop -c python3 -m wc1.match --compile-check <touched .c>` → commit 1: `22 files x 2 compilers, 0 failures`; commit 2: `7 files, 0 failures`; commit 3: `12 files, 0 failures`
- `nix develop -c python3 -m wc1.build` → `IDENTICAL`
- pytest:
  - commit 1: `tests/test_packet.py tests/test_progress.py` → **40 passed**
  - commit 2: `tests/test_snd_f1.py tests/test_mod_2ced0_c.py tests/test_batch_driver.py tests/test_progress.py` → **46 passed**; `tests/test_t4spec.py` (incl. `t4spec.audit_t4_log`) → **5 passed**
  - commit 3: `tests/test_mod_2b2f0.py tests/test_progress.py tests/test_packet.py tests/test_t4spec.py` → **50 passed**; broader caller sweep (`test_mod_2efd0_t4`, `test_mod_1af20`, `test_mod_19b80`, `test_mod_25ba0_c/f1`, `test_mod_2ced0_c`, `test_harvest`, `test_mod_13f60_c`, `test_progress`) → **68 passed, 1 xfailed**
- `nix develop -c python3 -m wc1.progress` → final numbers above

Full `make verify` was not run and no gate/test was weakened.

### 5. Deferred candidates

None. All five were migrated successfully; no name collisions (`symbols.load()` confirmed all five new names unused).