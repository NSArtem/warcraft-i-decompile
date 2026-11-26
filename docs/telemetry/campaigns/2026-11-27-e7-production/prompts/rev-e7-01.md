# Independent Reviewer Assignment — E7 Compiler Presets, 13 T3 Promotions, and Wave 4B Audit Snapshot

You are an **independent Reviewer** running in a fresh session inside a detached, pre-warmed worktree at commit `59efdd2888d9baf6ae59141d212660d7c0d7ecc8` (branch `feature/e7-compiler-presets`, 3 commits ahead of `main` `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da`).

Do NOT edit or commit any tracked files. This is a read-only adversarial code and evidence review.
All project commands must run inside the Nix dev shell: `nix develop -c <cmd>` (avoid nested Nix shells).
Do NOT run `make verify` or the full repository test suite (the Manager owns serialized `make verify`). Run targeted checks and targeted pytest suites only.

---

## Commits under review (`e14d5c0a..59efdd28`)

1. `196153c1` — `wc1.permuter/t3_audit/wave4: add E7 10.0a presets and preset-aware audit invalidation + tests`
2. `2b10939b` — `T3: promote 13 verified E7 Watcom 10.0a -5r candidates (519 -> 532 T3, Build A IDENTICAL)`
3. `59efdd28` — `wc1.t3_audit: add provenance-checked improved-T4 audit snapshot for Wave 4B + tests`

---

## Mandatory Review Checklist (verify every item from actual diffs and live checks)

1. **Preset correctness & single source of truth:**
   - Verify `permuter.FLAG_PRESETS` contains `-s -ot -ol -5r -zp2`, `-s -ot -oa -ol -5r -zp2`, `-s -ot -ol -5r -d1+ -zp2`, and that any additional presets (`c22`, `c10`, `c26`) are supported by E7 (`git show research/build-codegen-experiments:docs/research/build-codegen/results/e7/proposed_presets.json`).
   - Verify no duplicate preset lists were introduced.
   - Verify `-s -ot -ol -5r -zp2` precedes `-s -ot -oa -ol -5r -zp2` so minimal-change `-5r` wins when both match.

2. **Preservation of existing configurations:**
   - Verify all 8 original Watcom 10.0a presets and the native Open Watcom 2 fallback remain intact.
   - Verify the default architecture flag (`-4r`) is NOT changed globally (`match.DEFAULT_CFLAGS`, `permuter.FLAG_PRESETS[0]`, `permuter.set_headers`, existing T3/T4 files outside the 13 promotions).

3. **Fingerprint and cache invalidation correctness:**
   - Audit `tools/wc1/t3_audit.py`, `tools/wc1/wave4.py`, `tools/wc1/wave4a.py`, and `tools/wc1/wave4_fp.py` carefully for edge cases:
     - Does changing `FLAG_PRESETS` invalidate stale negative results in `wave4.load_report`, `wave4a.load_audit_report_incremental` (`audit_state.json` AND `report.json` bootstrap), `wave4_fp.wave4b_fingerprint`, `wave4_fp.wave4a_fingerprint`, and `omf_deps`?
     - Are there any subtle bugs (e.g., `omf_deps` plan mismatch vs `meta["plan"]`, `tool_sig` missing/None handling, `source_digest` computation failure/circular import, `is_improved_record_fresh` edge cases, or accidental indiscriminate cache invalidation)?
     - Check whether `audit_state.json` entries without `plan` (legacy entries) are properly invalidated and whether `t3_audit.py`'s `_source_digest` or `_tool_sig` can fail or behave inconsistently under mocked tests or real runs.

4. **Promotion evidence (Task B — all 13 candidates):**
   - Inspect `git show 2b10939b`: confirm ONLY the 13 authorized functions (`0x13c04`, `0x13c84`, `0x13dd0`, `0x15314`, `0x1a800`, `0x1af20`, `0x21df0`, `0x22a4c`, `0x22a98`, `0x29f40`, `0x2ab54`, `0x34060`, `0x348c0`) were promoted, with minimal flag changes (`-4r -> -5r` only), no body rewrites, proper TOML transitions (`ref` -> `src`, `confidence = "verified"`, `verified_by = "match: ..."`, `ref`/`ref_verified_by`/`t3_blocker` dropped, evidence prepended), and preserved differential tests.
   - Independently run targeted checks:
     - `nix develop -c python3 -m wc1.symbols`
     - `nix develop -c python3 -m wc1.match` on all 13 promoted files
     - `nix develop -c python3 -m wc1.match --compile-check` on all 13 promoted files (both 10.0a and OW2)
     - `nix develop -c python3 -m wc1.build` and `nix develop -c python3 -m wc1.compare build/war.exe original/install/war.exe` (confirm `IDENTICAL` and `532 functions from 527 C files`)
     - `nix develop -c python3 -m wc1.progress` (confirm `T3: 532`, `T4: 372`, `DONE: 899`)
     - Run the targeted pytest files for Tasks A, B, and C:
       `nix develop -c pytest -q tests/test_permuter_unit.py tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py tests/test_mod_13b30_f1.py tests/test_mod_13dd0_c.py tests/test_mod_13f60.py tests/test_gamedlg.py tests/test_mod_1af20_c1.py tests/test_mod_20c30.py tests/test_placebox.py tests/test_mod_295d0.py tests/test_mod_34060.py tests/test_mod_348c0_c.py`

5. **Task C audit snapshot & staleness validation:**
   - Inspect `tools/wc1/t3_audit.py` (`improved_t4_records`, `is_improved_record_fresh`) and `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json`.
   - Verify:
     - No absolute host paths (`/mnt/`, `/home/`, `/tmp/`) or credentials leaked into `t4_improved_audit.json`.
     - Every required field is preserved: function identity, best observed flags, mismatch score, compiler identity, source & dependency fingerprint, search configuration.
     - Validate `is_improved_record_fresh` against the live repo on all records in `t4_improved_audit.json` AND inspect whether any stale input (source edit, include edit, preset change, tool_sig change, declared_cflags change, OMF symbol change, or `git_commit` / `omf_deps` mismatch) can slip past validation!
     - Check whether `t4_improved_audit.json` is appropriately concise (or if any bloated/unnecessary data was included).
     - Confirm canonical compiler flags of residual T4 functions were NOT modified.

6. **Absence of weakened verification gates & absence of unrelated changes:**
   - Verify `Makefile`, `flake.nix`, `tools/wc1/progress.py`, `tools/wc1/build.py`, `tools/wc1/match.py`, `tools/wc1/oldcc.py`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `AGENTS.md` were NOT modified.
   - Verify NO existing test assertions were weakened or skipped.
   - Verify NONE of the 6 excluded functions (`SaveErrorDialog`, `IntroFadeStep`, `IntroBeginFlic`, `FarmPanelChanged`, `BitmapClear`, `OpenArchive`) or excluded infrastructure (E0 production matcher, CodeRegion, Fix B1/B2/B3, selective OMF extraction, multi-function T4, CU recovery, source consolidation, research branches) were merged or modified.

---

## Required Output Format

Classify any findings by severity (**CRITICAL / HIGH / MEDIUM / LOW / INFO**) with exact file paths, line numbers, and concrete reproduction or fix guidance.

End your review with an explicit verdict line on its own line:
- `VERDICT: APPROVE` (if there are zero CRITICAL/HIGH/MEDIUM blockers)
- `VERDICT: REQUEST_CHANGES` (if any defect must be fixed before sign-off)

Explicitly state the exact reviewed commit SHA (`59efdd2888d9baf6ae59141d212660d7c0d7ecc8`) and list every check you ran and any item left unchecked.

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-26T20:42:51.175560Z` (Unix epoch `1795725771`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-26T21:12:51Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-26T21:03:51Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized by the Manager. Batch independent shell commands into a single step where safe.
- **Environment:** Run project tools inside the Nix dev shell (`nix develop -c <cmd>`) without nested Nix shells.
