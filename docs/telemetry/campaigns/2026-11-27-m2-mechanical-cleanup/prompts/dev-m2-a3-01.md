# Developer Assignment — Campaign A: Task A3 (Migrate 7 Matched `codegen_promo.toml` T3 Functions)

You are the Developer working on branch `feature/m2-mechanical-cleanup` inside `/mnt/data/projects/wc1-wt-on/m2-dev` (HEAD is `59a963c`, `DONE = 905 / 1010`).
All repo commands run inside the Nix dev shell: `nix develop -c <cmd>`.
NEVER modify `original/`, `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, `LOCKED_TOMLS`, or `PROTECTED_TOMLS`.
NEVER remove `codegen_promo.toml` from `LOCKED_TOMLS` or weaken `LOCKED_TOMLS` / `PROTECTED_TOMLS`.
NEVER run full `make verify` (the Manager runs serialized `make verify` globally). Run `wc1.symbols`, `wc1.match --all`, `wc1.match --compile-check`, `wc1.build`, `wc1.progress`, and targeted `pytest`.

---

## Objective

Investigate and safely migrate each of the **7 already-matched T3 functions** currently staged in `analysis/symbols/codegen_promo.toml` into their canonical module TOMLs and per-function `src/<module>/*.c` files (following the exact precedent of `fn_12cd4 -> NetNextRecvSlot` documented in `tests/test_codegen_promo.py` lines 12–15):

1. **`0x1132c`** (`fn_1132c`, `src/codegen/mod_110a0.c`, module `mod_110a0`):
   - `FatalError("attack:1")` handler stub in `0x5159c`.
   - Check owning TOML for `mod_110a0` and naming convention for FatalError stubs (e.g., `DispatchFatal`), pick a unique grounded name (e.g., `AttackFatalStub`), move to `src/mod_110a0/<name>.c`, wire `src =`, verify `wc1.match` (10.0a first; fallback OW2 if needed), `wc1.match --compile-check`, and `wc1.build` (`IDENTICAL`).

2. **`0x123cc`** (`fn_123cc`, `src/codegen/bullet.c`, module `BULLET.C`):
   - `FatalError("bullet:6")` handler stub in `0x51210`.
   - Check owning TOML for `BULLET.C` (create `analysis/symbols/bullet.toml` if none exists, or migrate into existing one), pick unique grounded name (e.g., `BulletFatalStub`), move to `src/bullet/<name>.c`, wire `src =`, verify `wc1.match` + `wc1.build` (`IDENTICAL`).

3. **`0x13e94`** (`fn_13e94`, `src/codegen/mod_13e60.c`, module `mod_13e60`):
   - Sets `dat_51530 = 0x10e` (resets demo idle timer decremented by neighbor `DemoIdleTick` `0x13e60` and also reset by `DemoRun` `0x13f0c`).
   - Migrate to `analysis/symbols/mod_13e60.toml` as `DemoIdleReset` (check uniqueness!), move to `src/mod_13e60/demo_idle_reset.c`, wire `src =`, syntax-aware rename across all referencing `src/` and AST-aware update across `tests/`, verify `wc1.match` + `wc1.build` (`IDENTICAL`).

4. **`0x15170`, `0x15230`, `0x15558`** (`src/codegen/mod_13f60.c`, module `mod_13f60` — **3 functions in one file, MUST be split 1-function-per-file**):
   - **`0x15170`**: `fn_150f0(d, 0)` — `analysis/symbols/mod_13f60.toml` line 456 already proves this is the Forest button in Set Map dialog `0x180`, sibling of `MapChoiceSwamp` (`0x1517c`), `MapChoiceDungeon` (`0x1518c`), `MapChoiceRandom` (`0x1519c`) -> **`MapChoiceForest`**.
   - **`0x15230`**: calls `NetLinkHandshake()`, stores result in `dat_516ae`, returns `1`; passed as callback in `NetGameStart` (`0x160f0`) -> check `mod_13f60.toml` naming convention and pick grounded name (e.g., `NetGameHandshakeCallback`).
   - **`0x15558`**: `strcpy(dat_59230, c->text)` — exact counterpart of `0x15568` in `mod_13f60.toml` line 652! Inspect `0x15568`'s exact name in `mod_13f60.toml` and name `0x15558` consistently.
   - Split `src/codegen/mod_13f60.c` into 3 separate single-function files under `src/mod_13f60/` (`-s -ot -ol -4r -zp2`, try `10.0a` first, fallback OW2 if needed; verify `wc1.match` AND `wc1.build` `IDENTICAL` — note `0x15170` and `0x15230` use extent clamping/matching; confirm `wc1.build` accepts each individual object cleanly in sequence and produces `IDENTICAL`! If any of the 3 fails `wc1.build` in-place placement, do NOT force `src =`; document the exact `wc1.build` error and defer only that candidate!).
   - Migrate each buildable entry into `analysis/symbols/mod_13f60.toml`, syntax-aware rename all referencing `src/` and `tests/`, and verify!

5. **`0x19478`** (`fn_19478`, `src/codegen/mod_19470.c`, module `mod_19470`):
   - Linear congruential RNG (`state = state * 0x15a4e35L + 1; return (state >> 16) & 0x7fff`), exact sibling of `GameSetRandomSeed` (`0x19470` in `analysis/symbols/mod_19470.toml`) -> **`GameRandom`** (verify uniqueness!).
   - Preserve native **OW2** compilation (no `codegen-compiler: 10.0a` header) if 10.0a still mismatches — verify under both `--compile-check` and `wc1.match`!
   - IMPORTANT: Check `wc1.build` carefully! Look at `0x19478..0x194a8`: `0x19494..0x194a4` is a pre-function jump table for `0x194a8` (`GameResolveCustomScenario`)! Confirm whether `wc1.build` places `game_random.c` cleanly (`0x19478..0x19491`) without interfering with `0x19494`! If `wc1.build` accepts it and produces `IDENTICAL`, wire `src =` and migrate! If `wc1.build` rejects it due to `0x19494`, report the exact error and check whether renaming + keeping verified match works or defer cleanly!
   - Syntax-aware rename `fn_19478` -> `GameRandom` across all ~17 referencing `src/` files and all referencing `tests/`!

---

## Important Constraints & Test Hygiene

1. **Keep `analysis/symbols/codegen_promo.toml` alive and `LOCKED_TOMLS` unchanged**:
   - Leave `0x150f0` (`fn_150f0`, no C yet) and the 4 `[[data]]` entries (`dat_50d7c`, `dat_51530`, `dat_516ae`, `dat_59230`) in `analysis/symbols/codegen_promo.toml` (unless a data symbol must stay untouched — do NOT rename those 4 `dat_*` symbols tonight to keep diffs focused and clean!).
   - Because `0x150f0` stays in `codegen_promo.toml`, `codegen_promo.toml` remains non-empty!
   - Update `tests/test_codegen_promo.py` cleanly as entries migrate out of `src/codegen/` into `src/<module>/` (just like `fn_12cd4 -> NetNextRecvSlot` did!):
     - Update `PROMOTED` dict to reflect only remaining `src/codegen/` promo files (if all 5 sample files are migrated and removed, replace/update `test_codegen_promo.py` so it guards the promoted functions in their new `src/<module>/` homes AND keeps the `test_extent_retry_matches_the_flow_end` regression guard for `0x15170`/`0x15230` under their new link names and files — NEVER delete or weaken regression coverage!).
   - Run `pytest tests/test_codegen.py tests/test_codegen_promo.py` to confirm zero regressions.

2. **Atomic Commits**:
   Group into clean logical commits (e.g.):
   - Commit 1: `0x1132c` + `0x123cc` + `0x13e94` (or 1 commit per module: `mod_110a0` / `bullet` / `mod_13e60`)
   - Commit 2: `mod_13f60` (`0x15170`, `0x15230`, `0x15558` split & migrated)
   - Commit 3: `mod_19470` (`0x19478` `GameRandom` migrated)
   Before EVERY commit, verify:
   - `nix develop -c python3 -m wc1.symbols`
   - `nix develop -c python3 -m wc1.match --all`
   - `nix develop -c python3 -m wc1.match --compile-check <all modified/new src/*.c>`
   - `nix develop -c python3 -m wc1.build` (MUST be `IDENTICAL`)
   - `nix develop -c pytest tests/test_codegen.py tests/test_codegen_promo.py tests/test_progress.py <all affected module tests>`
   - `nix develop -c python3 -m wc1.progress`

---

## Final Report Format

Report concisely:
1. Every commit SHA, old -> new name, compiler (`10.0a` or `ow2`), owning TOML migration, and explicit affected-file manifest.
2. `wc1.progress` before vs after (`DONE`, `named`, `T3` incl. `10.0a`/`ow2` breakdown, `T4`).
3. Build A result (`IDENTICAL` + counts).
4. Exact targeted verification commands and pytest pass counts.
5. Any deferred candidates and exact technical blockers.

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:19:02.499789Z` (Unix epoch `1795731542`)
- **Hard wall-clock limit:** `2700 s` (~`45 min`, hard cutoff `2026-11-26T23:04:02Z`)
- **70% wrap-up checkpoint:** `1889 s` (`2026-11-26T22:50:31Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally rather than waiting until the end; begin final wrap-up and final commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
