# Independent Adversarial Review — Campaign A (`feature/m2-mechanical-cleanup`, `b0196b4..229c32b`)

You are a fresh, independent, read-only Reviewer inspecting branch `feature/m2-mechanical-cleanup` inside `/mnt/data/projects/wc1-wt-on/m2-rev` (detached HEAD at `229c32b`, base `b0196b4`).
Do NOT modify repository files or create commits.
Do NOT run full `make verify` (the Manager runs serialized `make verify` after review approval); you may run targeted checks (`wc1.symbols`, `wc1.match --all`, `wc1.match --compile-check`, `wc1.build`, `wc1.progress`, `wc1.m2_inventory --summary`, `t4spec.audit_t4_log`, and targeted `pytest`).

---

## Commits Under Review (`b0196b4..229c32b`)

1. `c9d8733` — `T4: wire WaitInputOrTimeout (0x1bf94) difftest ref_verified_by` (A1)
2. `2456f0c` — `wc1.overnight: remove stale BULLET.C from DEFAULT_SKIP + tests` (A4)
3. `e1a4178` — `wc1.m2_inventory: reclassify IntroOpSyncSound under shared-epilogue blocker` (A1/A0)
4. `f5cf65d` — `PACKET.C: fn_214d4 -> PacketSend (T3, verified) and move its record to packet.toml` (A2)
5. `b4891ff` — `SND.C: fn_26360 -> UnitStartAnim and move its record to snd_f1.toml` (A2)
6. `59a963c` — `mod_2b2f0: fn_2b308/fn_2b31c/fn_2b390 -> TargetModeIsActive/Enter/Exit, records moved to mod_2b2f0.toml` (A2)
7. `229c32b` — `T3: name and rebuild the 7 codegen_promo samples in their areas (safe split from src/codegen)` (A3)

---

## Mandatory Audit Checklist

Verify EVERY item independently with concrete evidence:

1. **Scope & Governance Integrity (CRITICAL):**
   - Confirm ZERO changes to `Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, `LOCKED_TOMLS`, `PROTECTED_TOMLS`, or any of the 8 discovery/scope artifacts (`0x110a0`, `0x11530`, `0x28090`, `0x28093`, `0x3fe34..0x400b4`).
   - Confirm ZERO B1/B2/B3 changes (`tools/wc1/build.py`, `emit.py`, `omfpatch.py` untouched).
   - Confirm `0x23170` (`IntroOpSyncSound`) was legitimately deferred (verify whether wiring `src =` actually breaks `wc1.build` due to cross-piece `rel8` from `0x231cc -> 0x2316c`, and check `e1a4178`'s `m2_inventory.py` reclassification is accurate and does not weaken any test or invariant).

2. **A1 (`WaitInputOrTimeout` `0x1bf94`) & A4 (`BULLET.C` `DEFAULT_SKIP`):**
   - Verify `tests/test_mod_1bf80.py::test_wait_input_or_timeout` passes live with `WC1_T4_AUDIT_LOG` / `t4spec.audit_t4_log`, no skip/xfail, and `wait_input_or_timeout_reference.c` still mismatches `wc1.match`.
   - Verify ONLY `"BULLET.C"` was removed from `overnight.DEFAULT_SKIP` (`"STATUS.C"` and `"PLAYFLIC.C"` preserved; `LOCKED_TOMLS` and `needs_human` guards intact).
   - Verify `tests/test_overnight.py` tests the 10 newly eligible `BULLET.C` functions and that remaining `BULLET.C` stubs stay gated.

3. **A2 (5 Semantic Naming Migrations) & A3 (7 `codegen_promo` Migrations):**
   - Check EVERY new semantic name against disassembly (`wc1.func` / `wc1.xref`), prototypes, calling conventions, and existing evidence. Flag ANY weakly grounded name, wrong prototype, or lost evidence!
   - Check for ANY leftover stale `fn_214d4`, `fn_26360`, `fn_2b308`, `fn_2b31c`, `fn_2b390`, `fn_1132c`, `fn_123cc`, `fn_13e94`, `fn_15170`, `fn_15230`, `fn_15558`, `fn_19478` references in `src/` or `tests/` (or broken test citations, corrupted comments/strings/locals!).
   - Check `src/mod_104b0/{attack_fatal_stub,bullet_fatal_stub}.c` and the new `attack_fatal_tag` / `bullet_fatal_tag` data symbols (`0x569d4`, `0x569e0`): verify exact image bytes and evidence!
   - Check `tests/test_codegen.py` and `tests/test_codegen_promo.py`: confirm NO regression guard was silently dropped or weakened (especially `test_extent_retry_matches_the_flow_end` for `0x15170`/`0x15230` and `codegen_promo.toml` remaining-entry checks!).
   - Check `src/mod_19470/game_random.c` (`0x19478`): confirm OW2 match, 10.0a compile-check, and clean placement before `0x19494` jump table!

4. **Mechanical Verification:**
   - Run `nix develop -c python3 -m wc1.symbols`
   - Run `nix develop -c python3 -m wc1.match --all`
   - Run `nix develop -c python3 -m wc1.match --compile-check` (all files x 2 compilers!)
   - Run `nix develop -c python3 -m wc1.build` (confirm Build A `IDENTICAL`!)
   - Run `nix develop -c python3 -m wc1.progress` and `nix develop -c python3 -m wc1.m2_inventory --summary`
   - Run targeted `pytest` on `test_codegen.py`, `test_codegen_promo.py`, `test_overnight.py`, `test_progress.py`, `test_mod_1bf80.py`, `test_packet.py`, `test_snd_f1.py`, `test_mod_2b2f0.py`, `test_mod_13e60.py`, `test_mod_13f60_c.py`, `test_mod_19470.py`, `test_t4spec.py`.

---

## Output Format

Report findings grouped by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with exact file/line/commit locations and concrete evidence. Do not invent speculative nitpicks.
End with an explicit standalone line:
`VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` or `VERDICT: REJECT` or `VERDICT: BLOCKED`

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:28:31.996920Z` (Unix epoch `1795732111`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-26T22:58:31Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-26T22:49:31Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
