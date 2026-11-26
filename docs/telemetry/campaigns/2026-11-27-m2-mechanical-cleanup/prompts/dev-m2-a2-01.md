# Developer Assignment — Campaign A: Task A2 (Semantic Naming & Atomic Migration of 5 Already-Verified Functions)

You are the Developer working on branch `feature/m2-mechanical-cleanup` inside `/mnt/data/projects/wc1-wt-on/m2-dev`.
All repo commands run inside the Nix dev shell: `nix develop -c <cmd>`.
NEVER modify `original/`, `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, or any scope/discovery governance files.
NEVER run full `make verify` (the Manager runs serialized `make verify` globally). Run `wc1.symbols`, `wc1.match --all`, `wc1.match --compile-check <touched>`, `wc1.build`, `wc1.progress`, and targeted `pytest`.

---

## Objective

Five functions already have verified C (4 T3, 1 T4) and are blocked from `DONE` solely by placeholder `fn_*` names (and in `0x214d4`'s case, `low` confidence + cross-TOML placement):

1. **`0x214d4`** (`fn_214d4`, T3 in `src/packet/packet_send.c`, currently in `analysis/symbols/mod_20c30.toml`, `confidence = "low"`, `PACKET.C` module)
2. **`0x26360`** (`fn_26360`, T4 in `src/snd/fn_26360_reference.c`, currently in `analysis/symbols/mod_20c30.toml`, `confidence = "medium"`, `SND.C` module)
3. **`0x2b308`** (`fn_2b308`, T3 in `src/mod_2b2f0/fn_2b308.c`, currently in `analysis/symbols/mod_2efd0.toml`, `mod_2b2f0` module)
4. **`0x2b31c`** (`fn_2b31c`, T3 in `src/mod_2b2f0/fn_2b31c_reference.c`, currently in `analysis/symbols/packet.toml`, `mod_2b2f0` module)
5. **`0x2b390`** (`fn_2b390`, T3 in `src/mod_2b2f0/fn_2b390_reference.c`, currently in `analysis/symbols/packet.toml`, `mod_2b2f0` module)

---

## Strict Requirements for EVERY Migration

1. **Disassembly-grounded semantic identity**: Inspect `wc1.func`, `wc1.xref`, existing C, and tests for each function. Choose a concise, globally unique PascalCase semantic name consistent with nearby symbols (check `symbols.load()` for uniqueness before editing!). Suggested candidates to verify against the DB:
   - `0x214d4`: `PacketSend` (check `analysis/symbols/packet.toml`; stamps `packet_id` into `msg[1]` when `len >= 3` and `NetPendingMessageCount() < 7`, then calls `NetSendDataMessage`; called by all 16 `NetSend*`/`PacketSendIdle` senders). Note: check its `verified_by` and `confidence` — since it has `src = "src/packet/packet_send.c"` and `wc1.match` reports `MATCH`, `confidence = "verified"` with `verified_by = "match: python3 -m wc1.match src/packet/packet_send.c"` is appropriate.
   - `0x26360`: `UnitStartAnim` (exact sibling of `BulletStartAnim` `0x26390` — check which TOML owns `0x26390` and migrate `0x26360` alongside it if clean; verify prototype param name e.g. `anim_idx` matches actual disassembly, preserve `ref`, `ref_verified_by`, `t3_blocker`, and evidence).
   - `0x2b308` / `0x2b31c` / `0x2b390`: `TargetModeIsActive`, `TargetModeEnter`, `TargetModeExit` (check `analysis/symbols/mod_2b2f0.toml` if it exists; migrate cleanly and preserve all existing `src`, `verified_by`, `confidence = "verified"`, and evidence).
2. **Syntax-aware C identifier replacement**: Use a deterministic Python C tokenizer (you may reuse `wc1.wave4_deps` tokenizer or write a small temporary script in `/tmp/` — never leave scratch scripts in the repo!) to replace ONLY identifier tokens matching the old symbol name across `src/**/*.c` and `src/**/*.h`, strictly preserving comments, string literals, `#include`s, `.field`/`->field` member accesses, and checking for any local/param/typedef/macro shadowing collisions.
3. **AST-aware test updates**: Update all referencing `tests/**/*.py` files (e.g., `"fn_214d4_"`, `"fn_26360_"`, `"fn_2b308_"`, `"fn_2b31c_"`, `"fn_2b390_"` link names, `t4spec.run_spec`, `EXTRA` dicts, etc.) using Python `ast` verification so no unrelated string or comment is corrupted.
4. **Do NOT leave stale `fn_XXXXX` references** in `src/` or `tests/` for migrated functions, and do NOT weaken any test or verification gate.
5. **Preserve existing C filenames if renaming them would risk unrelated test churn**, OR only rename C files if clean and every reference is updated; either way `wc1.symbols`, `wc1.match --all`, `wc1.match --compile-check` on all touched C files, `wc1.build` (`IDENTICAL`), and ALL affected pytest files must pass!
6. **Atomic commits (3 logical commits)**:
   - Commit 1: `0x214d4` (`PACKET.C` -> `PacketSend`, +1 DONE)
   - Commit 2: `0x26360` (`SND.C` -> `UnitStartAnim`, +1 DONE)
   - Commit 3: `0x2b308`, `0x2b31c`, `0x2b390` (`mod_2b2f0` -> `TargetModeIsActive`/`TargetModeEnter`/`TargetModeExit`, +3 DONE)
   Stage explicit paths only for each commit. Before each commit, verify:
   - `nix develop -c python3 -m wc1.symbols`
   - `nix develop -c python3 -m wc1.match --all`
   - `nix develop -c python3 -m wc1.match --compile-check <all modified src/*.c files>`
   - `nix develop -c python3 -m wc1.build` (must be `IDENTICAL`)
   - `nix develop -c pytest <all affected test files> tests/test_progress.py` (including runtime T4 audit check for `0x26360`'s `ref_verified_by`!)
   - `nix develop -c python3 -m wc1.progress`

If any function has an unexpected collision or blocker that cannot be safely migrated within bounded scope, defer it with exact evidence and continue with the others.

---

## Final Report Format

Report concisely:
1. Each commit SHA, old -> new name, owning TOML migration, and explicit affected-file manifest.
2. `wc1.progress` before vs after (`DONE`, `named`, `T3`, `T4`).
3. Build A result (`IDENTICAL` + counts).
4. Exact verification commands and pytest pass counts (including `t4spec.audit_t4_log` for `0x26360`).
5. Any deferred candidates and exact reasons.

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:11:50.979904Z` (Unix epoch `1795731110`)
- **Hard wall-clock limit:** `2700 s` (~`45 min`, hard cutoff `2026-11-26T22:56:50Z`)
- **70% wrap-up checkpoint:** `1889 s` (`2026-11-26T22:43:19Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally rather than waiting until the end; begin final wrap-up and final commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
