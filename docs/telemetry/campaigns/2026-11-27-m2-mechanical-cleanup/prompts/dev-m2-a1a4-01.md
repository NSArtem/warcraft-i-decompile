# Developer Assignment — Campaign A: Tasks A1 (Immediate Wiring) & A4 (Stale BULLET.C Exclusion)

You are the Developer working on branch `feature/m2-mechanical-cleanup` inside an isolated worktree.
Base commit: `b0196b409be8c0e304f96712632d8e9ebcbd05fc`.

All repo commands run inside the Nix dev shell: `nix develop -c <cmd>`.
NEVER modify `original/`, `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, or any scope/discovery governance files.
NEVER run full `make verify` (the Manager runs serialized `make verify` globally); run targeted checks (`wc1.symbols`, `wc1.match`, `wc1.build`, `wc1.compare`, `wc1.progress`, `wc1.m2_inventory`, and targeted `pytest`).

---

## Task 1 (Atomic Commit 1): A1 — Immediate Wiring (`0x23170`, `0x1bf94`)

Revalidate and wire two already-verified functions:

1. **`0x23170` `IntroOpSyncSound`** (`analysis/symbols/playflic.toml`, `src/playflic/intro_op_sync_sound.c`):
   - Confirm `python3 -m wc1.match src/playflic/intro_op_sync_sound.c` reports `MATCH`.
   - Confirm `wc1.build.check_t3_buildable` accepts `src/playflic/intro_op_sync_sound.c` (no interior refs, Build A stays IDENTICAL).
   - Add `src = "src/playflic/intro_op_sync_sound.c"` to the `0x23170` `[[func]]` entry in `analysis/symbols/playflic.toml`, preserving existing `verified_by`, `confidence = "verified"`, and `evidence` (append a brief verification note if appropriate).
   - Confirm `tests/test_playflic.py` passes and does not have any stale guard forbidding `src =` on `0x23170` (if it has an outdated guard comment/check, inspect carefully; do NOT weaken any real test).

2. **`0x1bf94` `WaitInputOrTimeout`** (`analysis/symbols/mod_1bf80.toml`, `src/mod_1bf80/wait_input_or_timeout_reference.c`, `tests/test_mod_1bf80.py::test_wait_input_or_timeout`):
   - Confirm `tests/test_mod_1bf80.py` passes cleanly (not skipped/xfailed) AND passes runtime T4 audit (`WC1_T4_AUDIT_LOG` / `wc1.t4spec.audit_t4_log` or `wc1.batch_driver.verify_t4_node`).
   - Confirm `t3_blocker` is already valid and `src/mod_1bf80/wait_input_or_timeout_reference.c` still mismatches `wc1.match` (so it stays T4, not T3).
   - Add `ref_verified_by = "difftest: tests/test_mod_1bf80.py::test_wait_input_or_timeout"` to the `0x1bf94` `[[func]]` entry in `analysis/symbols/mod_1bf80.toml`, preserving all existing evidence and `t3_blocker`.

3. **Verify & Commit 1:**
   - Run `nix develop -c python3 -m wc1.symbols`, `nix develop -c python3 -m wc1.match --all`, `nix develop -c python3 -m wc1.build`, `nix develop -c python3 -m wc1.progress`, and `nix develop -c pytest tests/test_playflic.py tests/test_mod_1bf80.py tests/test_progress.py`.
   - Confirm `DONE` increased by **+2** (`899 -> 901`), `T3` increased by **+1** (`532 -> 533`), `T4` increased by **+1** (`372 -> 373`), `ref_unchecked` decreased by **-1** (`6 -> 5`), and Build A is **IDENTICAL**.
   - Stage explicit modified files only and commit atomically with a concise single-line message (e.g., `T3/T4: wire IntroOpSyncSound (0x23170) and WaitInputOrTimeout (0x1bf94)`).

---

## Task 2 (Atomic Commit 2): A4 — Remove Stale `BULLET.C` Exclusion from `overnight.DEFAULT_SKIP`

Investigate and remove the obsolete `"BULLET.C"` entry from `overnight.DEFAULT_SKIP`:

1. Confirm there is no untracked/WIP `BULLET.C` draft in the repository (already scrapped per `AGENTS.md`).
2. Inspect every reference to `DEFAULT_SKIP` and `BULLET.C` across `tools/wc1/` and `tests/` (including `tools/wc1/overnight.py`, `tools/wc1/tui.py`, `tools/wc1/m2_inventory.py`, `tests/test_overnight.py`, `tests/test_m2_inventory.py`, etc.).
3. Remove **only** `"BULLET.C"` from `overnight.DEFAULT_SKIP` (preserve `"STATUS.C"` and `"PLAYFLIC.C"` and all other guards, `LOCKED_TOMLS`, and `needs_human` filters!).
4. Update stale docstrings/help text in `tools/wc1/overnight.py` and `tools/wc1/tui.py` if they cite `BULLET.C` as an active default skip example.
5. Check `tools/wc1/m2_inventory.py` and `tests/test_m2_inventory.py` — note carefully: `m2_inventory.py` classifies functions dynamically using `overnight.DEFAULT_SKIP`. Ensure `m2_inventory.py` handles `BULLET.C` cleanly when it is no longer in `DEFAULT_SKIP` (do NOT break `m2_inventory` invariants or tests; check what `m2_inventory.py` lines 440-455 do when `BULLET.C` is removed from `DEFAULT_SKIP`!).
6. Update the existing `DEFAULT_SKIP` assertion in `tests/test_overnight.py` and add focused regression test(s) verifying:
   - `"BULLET.C"` is NOT in `overnight.DEFAULT_SKIP`, while `"STATUS.C"` and `"PLAYFLIC.C"` ARE still in `overnight.DEFAULT_SKIP`.
   - `overnight.build_queue_with_needs_human` now puts the 10 clean `BULLET.C` functions (`0x119c0`, `0x11c50`, `0x11fa8`, `0x11ff0`, `0x12074`, `0x120c8`, `0x12240`, `0x122d0`, `0x12338`, `0x123e0`) into the eligible queue while keeping the 8 `mod_104b0.toml` placeholder stubs (`0x11a10`..`0x11f78`) and locked `0x123cc` in `needs_human`.
7. Run targeted tests: `nix develop -c pytest tests/test_overnight.py tests/test_overnight_wave4.py tests/test_tui.py tests/test_m2_inventory.py` (any that exist), plus `nix develop -c python3 -m wc1.m2_inventory --summary` and `nix develop -c python3 -m wc1.progress`.
8. Stage explicit modified files only and commit atomically with a concise single-line message (e.g., `wc1.overnight: remove stale BULLET.C from DEFAULT_SKIP + tests`).

---

## Final Report Format

When both commits are done, report concisely:
1. Exact commit SHAs and touched files for Commit 1 (A1) and Commit 2 (A4).
2. `wc1.progress` before vs after (`DONE`, `T3`, `T4`, `ref_unchecked`).
3. Build A comparison result (`IDENTICAL` + counts).
4. Exact newly eligible `BULLET.C` addresses and remaining `BULLET.C` exclusion reasons from `build_queue_with_needs_human` / `m2_inventory`.
5. Exact targeted test commands run and their pass counts.

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:04:14.726982Z` (Unix epoch `1795730654`)
- **Hard wall-clock limit:** `2700 s` (~`45 min`, hard cutoff `2026-11-26T22:49:14Z`)
- **70% wrap-up checkpoint:** `1889 s` (`2026-11-26T22:35:43Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally rather than waiting until the end; begin final wrap-up and final commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
