# Independent Reviewer Assignment (Round 2) — Verify `rev-e7-01` Fixes & Full Branch Sign-off

You are an **independent Reviewer** running in a fresh session inside a detached, pre-warmed worktree at commit `5667e2f76a53090dd2077d0047a967cdf30d08de` (branch `feature/e7-compiler-presets`, 4 commits ahead of `main` `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da`).

Do NOT edit or commit any tracked files. This is a read-only adversarial review.
All project commands must run inside the Nix dev shell: `nix develop -c <cmd>` (avoid nested Nix shells).
Do NOT run `make verify` or the full repository test suite (the Manager owns serialized `make verify`).
Always run foreground commands cleanly (never leave background processes or unclosed heredocs running).

---

## Commits under review (`e14d5c0a..5667e2f7`)

1. `196153c1` — `wc1.permuter/t3_audit/wave4: add E7 10.0a presets and preset-aware audit invalidation + tests`
2. `2b10939b` — `T3: promote 13 verified E7 Watcom 10.0a -5r candidates (519 -> 532 T3, Build A IDENTICAL)`
3. `59efdd28` — `wc1.t3_audit: add provenance-checked improved-T4 audit snapshot for Wave 4B + tests`
4. `5667e2f7` — `wc1.t3_audit: make improved-T4 digests checkout-portable and enforce report provenance (rev-e7-01 fixes)`

---

## Focus of Round 2 Review

Round 1 (`rev-e7-01`) verified Tasks A & B (`196153c1`, `2b10939b`) cleanly and flagged 4 findings (1 HIGH, 1 MEDIUM, 2 LOW) in Commit 3 (`59efdd28`). Verify that commit `5667e2f7` resolves EVERY finding cleanly without introducing any new bug or regression, and re-verify the full branch `e14d5c0a..5667e2f7`:

1. **HIGH fix — Cross-checkout portability of `portable_source_digest` & `t4_improved_audit.json`:**
   - Inspect `portable_source_digest()` in `tools/wc1/t3_audit.py`. Check edge cases: `sys:` vs `repo:` ordering, symlinked `original/` vs real `original/`, outside-root fail-closed behavior, unreadable/missing files, and whether any absolute path can enter the digest.
   - Run live check in THIS review worktree (`<wt-rev>`): verify `is_improved_record_fresh()` returns **202/202 fresh** on `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json` (using live `symbols.load()` `by_link`) AND verify zero host paths (`/mnt/`, `/home/`, `/tmp/`, etc.) exist anywhere in the JSON.
   - Verify `wave4_fp.unit_source_digest` and Wave 4 cache behavior were not broken.

2. **MEDIUM fix — Report provenance enforcement (`improved_t4_records` & `build_improved_audit_snapshot`):**
   - Inspect `_report_provenance()`, `improved_t4_records()`, and `build_improved_audit_snapshot()` in `tools/wc1/t3_audit.py`.
   - Verify incomplete reports, dirty reports (`git_dirty=True`), missing `options.presets` / `options.base_flags`, and old-preset reports CANNOT be laundered into passing `is_improved_record_fresh()`.

3. **LOW fixes — `omf_deps_sha256` validation, `git_commit` documentation, and 3 stale C comments:**
   - Verify `is_improved_record_fresh()` fails closed on missing/malformed `omf_deps_sha256` and mismatched `omf_deps` kwarg, and clearly documents `git_commit` as informational provenance.
   - Verify the 3 comment-edited promoted files (`src/mod_13f60/set_game_mode_reference.c`, `src/mod_295d0/ai_guard_start_area_reference.c`, `src/mod_295d0/ai_idle_unit_tick_reference.c`) still pass `wc1.match` and `wc1.match --compile-check` (both 10.0a and OW2).

4. **End-to-end branch sanity check (`e14d5c0a..5667e2f7`):**
   - Confirm all 7 campaign criteria still hold on `5667e2f7`:
     - Preset correctness & preservation of existing 8 + OW2 + `-4r` default.
     - Fingerprint & audit cache invalidation correctness.
     - All 13 promotions (`532 T3 / 372 T4 / 899 DONE`, Build A `IDENTICAL` at `532 functions from 527 C files`).
     - No weakened gates, no unauthorized files (`Makefile`, `flake.nix`, `progress.py`, `build.py`, `match.py`, `oldcc.py`, `GOAL.md`, `METHODOLOGY.md`, `AGENTS.md`), none of the 6 excluded functions touched, no research branch merged.
   - Run targeted tests:
     `nix develop -c pytest -q tests/test_permuter_unit.py tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py tests/test_mod_13f60.py tests/test_mod_295d0.py`
   - Run `nix develop -c python3 -m wc1.symbols`, `nix develop -c python3 -m wc1.build`, `nix develop -c python3 -m wc1.compare build/war.exe original/install/war.exe`, and `nix develop -c python3 -m wc1.progress`.

---

## Required Output Format

Classify any remaining findings by severity (**CRITICAL / HIGH / MEDIUM / LOW / INFO**) with file paths and line numbers.
Explicitly state the reviewed commit SHA (`5667e2f76a53090dd2077d0047a967cdf30d08de`), list all checks run and any items left unchecked, and end with an explicit verdict line on its own line:
- `VERDICT: APPROVE`
- `VERDICT: REQUEST_CHANGES`

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-26T21:14:01.315139Z` (Unix epoch `1795727641`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-26T21:44:01Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-26T21:35:01Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized by the Manager. Batch independent shell commands into a single step where safe.
- **Environment:** Run project tools inside the Nix dev shell (`nix develop -c <cmd>`) without nested Nix shells.
