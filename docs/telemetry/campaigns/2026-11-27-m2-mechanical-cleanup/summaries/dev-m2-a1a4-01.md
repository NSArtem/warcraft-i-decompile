## Final Report

### 1. Commits

**Commit 1 (A1, partial): `c9d8733` — `T4: wire WaitInputOrTimeout (0x1bf94) difftest ref_verified_by`**
- `analysis/symbols/mod_1bf80.toml` — added `ref_verified_by = "difftest: tests/test_mod_1bf80.py::test_wait_input_or_timeout"`; existing `ref`, `t3_blocker`, evidence untouched.
- Runtime audit confirmed: `t4spec.audit_t4_log(... src=wait_input_or_timeout_reference.c, orig_addr=0x1bf94, func_name=WaitInputOrTimeout_)` → `True`, `cases_run=4`.
- **`0x23170` was NOT wired** — see blocker below.

**`0x23170` blocker (evidence):** `wc1.match src/playflic/intro_op_sync_sound.c` = `MATCH`, and `build.check_t3_buildable` (called as `wc1.batch_driver` does) returns `(True, "")`, but a real `python3 -m wc1.build` with `src =` added fails:
```
build/pieces/piece_288.asm:19: error: OBJ format can only handle 16- or 32-byte relocations
build/pieces/piece_288.asm:21: error: OBJ format can only handle 16- or 32-byte relocations
```
Cause: replacing 0x23170 splits the asm at 0x23170, leaving `IntroOpWaitSound` 0x231cc in piece_288 with `je short loc_2316c` into piece_287 (`loc_2316c` is the shared epilogue; nasm cannot emit an 8-bit external relocation). Wiring 0x2315c too is rejected by `build` (`0x231d7 branches into the interior of replaced 0x2315c`). This is the known "shared epilogue" case (`docs/HISTORY.md:350` lists it as not-built) and requires DG-03 cut-boundary branch emission. `check_t3_buildable` is a false positive here.

**Commit 2 (A4): `2456f0c` — `wc1.overnight: remove stale BULLET.C from DEFAULT_SKIP + tests`**
- `tools/wc1/overnight.py` (DEFAULT_SKIP + docstring), `tools/wc1/tui.py` (kill-dialog text), `tools/wc1/m2_inventory.py` (branch/taxonomy/GROUP_META), `tests/test_overnight.py`.

**Commit 3 (follow-up): `e1a4178` — `wc1.m2_inventory: reclassify IntroOpSyncSound under shared-epilogue blocker`**
- `tools/wc1/m2_inventory.py` only (no progress/tier change); stops the inventory from advertising 0x23170 as a zero-LLM win.

### 2. `wc1.progress` before → after
| | before | after |
|---|---|---|
| DONE | 899 (89.0%) | **900 (89.1%)** |
| T3 | 532 | 532 |
| T4 | 372 | **373** |
| ref_unchecked | 6 | **5** |

Expected was +2/+1/+1/−1; the missing T3/+1 DONE is exactly the blocked 0x23170 wiring.

### 3. Build A
`IDENTICAL (loaded image, entry, stack, fixups)` — **532 functions from 527 C files, 527 placed in sequence, 0 legacy layout.**

### 4. `BULLET.C` after removal
`DEFAULT_SKIP = ("STATUS.C", "PLAYFLIC.C")` (STATUS/PLAYFLIC/guards/LOCKED_TOMLS/needs_human untouched). Newly **Wave 3-eligible** (`build_queue_with_needs_human`): `0x119c0, 0x11c50, 0x11fa8, 0x11ff0, 0x12074, 0x120c8, 0x12240, 0x122d0, 0x12338, 0x123e0`.
Still excluded: the 8 `mod_104b0.toml` stubs `0x11a10, 0x11cb0, 0x11cd8, 0x11ddc, 0x11ec0, 0x11e70, 0x11f10, 0x11f78` (`existing cross-TOML entry (… needs supervised rename/upgrade)`), and locked `0x123cc` (`locked TOML (analysis/symbols/codegen_promo.toml)`). `m2_inventory` now reports DG-06 as 18 functions (10 clean Wave 3 + 8 stubs), reconciled against progress.

### 5. Targeted checks/tests run
- `wc1.symbols` — OK (1370 functions, 954 data symbols).
- `wc1.match --all` — **527 files, 0 failed**.
- `wc1.build` — **IDENTICAL** (above).
- `wc1.m2_inventory --summary` — OK, reconciliation assertions pass, 24 groups.
- `pytest tests/test_playflic.py tests/test_mod_1bf80.py tests/test_progress.py -q` — **50 passed**.
- `pytest tests/test_overnight.py tests/test_overnight_wave4.py tests/test_tui.py -q` — **91 passed** (includes new `test_bullet_c_clean_functions_queued_after_default_skip_removal` and updated `test_default_skip_includes_playflic`). There is **no `tests/test_m2_inventory.py`** in the repo; `m2_inventory` was verified via `--summary` only.
- Working tree clean apart from the pre-existing untracked `original/`.