# Developer Assignment — E7 Compiler Presets, 13 Verified T3 Promotions, and Wave 4B Audit Preservation

You are the Developer working on branch `feature/e7-compiler-presets` (created from `main` at `e14d5c0`).

This is a small, bounded production implementation campaign. Implement Tasks A, B, and C below as **three clean, atomic commits** on `feature/e7-compiler-presets`. Do NOT merge into `main`, do NOT cherry-pick or merge any research branch, and do NOT modify anything outside the explicit scope below.

All project commands must run inside the Nix dev shell: `nix develop -c <cmd>` (avoid nested Nix shells).
Do NOT run `make verify` or the full repository test suite; run only the targeted verification commands specified below.

---

## Commit 1 — Task A: Add empirical Watcom 10.0a compiler presets + targeted cache invalidation + tests

### Requirements
1. **Single source of truth (`tools/wc1/permuter.py`):**
   - `permuter.FLAG_PRESETS` is the single preset list consumed by `wc1.permuter`, `wc1.t3_audit.attempt_plan`, `wc1.wave4`, `wc1.wave4a`, and `wc1.wave4_fp`. Do NOT introduce duplicate preset lists.
   - Keep `("10.0a", "-s -ot -ol -4r -zp2")` at index 0 and do NOT change `match.DEFAULT_CFLAGS` or globally change `-4r` to `-5r`.
   - Preserve ALL 8 existing `10.0a` presets and the native `("ow2", "-s -ot -ol -4r -zp2")` fallback.
   - Add the E7 empirically validated `10.0a` presets, with `-s -ot -ol -5r -zp2` ordered BEFORE `-s -ot -oa -ol -5r -zp2` so functions matching pure `-5r` choose the minimal flag diff (no unnecessary `-oa`):
     ```python
     FLAG_PRESETS = [
         ("10.0a", "-s -ot -ol -4r -zp2"),       # default OPT (c01)
         ("10.0a", "-s -ot -ol -5r -zp2"),       # E7 c06: Pentium OPT (minimal -4r->-5r diff; 11 buildable)
         ("10.0a", "-s -ot -oa -ol -5r -zp2"),   # E7 c07: Pentium OPT + -oa (Tier 1 #1 marginal)
         ("10.0a", "-s -ot -ol -5r -d1+ -zp2"),  # E7 c19: Pentium DBG (Tier 1 #2 marginal; 2 buildable)
         ("10.0a", "-s -ot -oa -ol -4r -zp2"),   # existing (c02)
         ("10.0a", "-s -ot -ol -4r -d1+ -zp2"),  # existing (c18)
         ("10.0a", "-s -od -4r -zp2"),           # existing (c20)
         ("10.0a", "-s -od -4r -d1+ -zp2"),      # existing (c21)
         ("10.0a", "-s -os -ol -4r -zp2"),       # existing (c05)
         ("10.0a", "-s -os -4r -zp2"),           # E7 c22: completes Tier 1 (+21 marginal improved)
         ("10.0a", "-s -ot -4r -zp2"),           # existing (c03)
         ("10.0a", "-s -ot -oa -4r -zp2"),       # existing (c04)
         ("10.0a", "-s -ot -ol -3r -zp2"),       # E7 c10: Tier 2 (+7 marginal, 46 improved)
         ("10.0a", "-s -ot -ol -4r -of+ -zp2"),  # E7 c26: Tier 2 (+4 marginal, 30 improved)
         ("ow2",   "-s -ot -ol -4r -zp2"),       # native Open Watcom 2 fallback
     ]
     ```

2. **Targeted fingerprint & stale negative audit invalidation (no indiscriminate cache invalidation):**
   - In `tools/wc1/t3_audit.py`:
     - Add a small helper `current_presets()` returning `[ _canon(short) for cc, short in permuter.FLAG_PRESETS if cc == CC ]` (deduplicated preserving order).
     - Record `"presets": current_presets()` and `"base_flags": match.BASE_CFLAGS` inside `meta["options"]` of `report.json`.
     - Record `"tool_sig": wave4_fp.tool_signature()` (computed safely without failing in mocked unit tests if `war.exe` / `oldcc` is absent) inside `meta["toolchain"]` (or keep `None` if unavailable).
     - Attach `"source_digest"` (from `wave4_fp.unit_source_digest(ref, repo_root=path())`, fail-open `None` if headers unreadable/mocked) to each audited result row in `audit_unit` so `report.json` carries source+include fingerprint provenance natively. (Watch out for circular imports between `t3_audit` and `wave4_fp` — import `wave4_fp` lazily inside helper functions in `t3_audit.py`!)
   - In `tools/wc1/wave4.py`:
     - In `load_report()`: if `meta.get("options")` is present and `"presets"` is in `meta["options"]` and `meta["options"]["presets"] != t3_audit.current_presets()`, or if `"base_flags"` is in `meta["options"]` and `meta["options"]["base_flags"] != match.BASE_CFLAGS`, treat the report as `"stale"`. Also if `meta.get("options")` has `"plan"` (real `t3_audit` output) without `"presets"` (pre-E7 legacy `report.json`), treat it as `"stale"`. Preserve existing behavior for minimal synthetic unit test dicts that omit `"options"` entirely (`tests/test_wave4.py::test_load_report_states`).
   - In `tools/wc1/wave4a.py`:
     - In `load_audit_report_incremental()`:
       - Store `"plan": [list(x) for x in cur_plan]` directly on `unit_meta[ref]` (both during refresh and bootstrap), AND check `meta.get("plan") != [list(x) for x in cur_plan]` in the staleness loop (not only inside `omf_deps`), so stale negative audit results (even units lacking `omf_deps`) are invalidated when presets change!
       - During `report.json` bootstrap: if `rep["meta"]` contains `"options"` and (`rep_opts.get("presets") != t3_audit.current_presets()` or (`"base_flags"` in `rep_opts` and `rep_opts["base_flags"] != match.BASE_CFLAGS`)), OR if `rep["meta"]` contains `"toolchain"` with a non-None `"tool_sig"` that differs from current `tool_sig`, skip bootstrapping stale rows from `report.json`! (Keep minimal unit test `tests/test_wave4_fingerprints.py` passing where synthetic `report.json` has no `"options"` key.)
     - Verify `wave4_fp.wave4b_fingerprint` and `wave4_fp.wave4a_fingerprint` already include `plan = t3_audit.attempt_plan(...)` and `resolve_omf_deps` checks `plan`.

3. **Focused regression tests:**
   - Update/add tests in `tests/test_permuter_unit.py`, `tests/test_t3_audit.py`, `tests/test_wave4.py`, and `tests/test_wave4_fingerprints.py` covering:
     - Presence of all 3 required `-5r` presets plus `c22`/`c10`/`c26`, preservation of all 8 original `10.0a` presets and OW2 fallback, default `-4r` preserved at index 0 and in `match.DEFAULT_CFLAGS`, `c06` ordered before `c07`.
     - `t3_audit.report.json` records `meta["options"]["presets"]` and `meta["options"]["base_flags"]`.
     - `wave4.load_report()` marks a report stale when `presets` or `base_flags` change (or pre-E7 `options.plan` without `presets`).
     - `wave4a.load_audit_report_incremental()` invalidates stale negative `audit_state.json` entries (even without `omf_deps`) and refuses to bootstrap from a `report.json` with mismatched `presets` when `FLAG_PRESETS` changes, while preserving unrelated entries.
     - `wave4_fp.wave4b_fingerprint` / `wave4a_fingerprint` change keys when `FLAG_PRESETS` changes.

4. **Targeted verification before Commit 1:**
   ```bash
   nix develop -c pytest -q tests/test_permuter_unit.py tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py
   ```
   Commit Commit 1 atomically with an explicit file list and concise one-line message, e.g.:
   `wc1.permuter/t3_audit/wave4: add E7 10.0a presets and preset-aware audit invalidation + tests`

---

## Commit 2 — Task B: Promote the 13 verified E7 candidates (519 T3 -> 532 T3)

Verify and promote ONLY these 13 functions (all confirmed dependency-clean T4 on `main`):

| Address | Function | Target minimal flags (`10.0a`) |
|---|---|---|
| `0x13c04` | `UnitCountAdd` | `-s -ot -ol -5r -zp2` |
| `0x13c84` | `UnitCountRemove` | `-s -ot -ol -5r -zp2` |
| `0x13dd0` | `SetCursorShape` | `-s -ot -ol -5r -zp2` |
| `0x15314` | `SetGameMode` | `-s -ot -ol -5r -zp2` |
| `0x1a800` | `OptionsDialog` | `-s -ot -ol -5r -zp2` |
| `0x1af20` | `FogDrawCell` | `-s -ot -ol -5r -zp2` |
| `0x21df0` | `WorkerReturnToMine` | `-s -ot -ol -5r -zp2` |
| `0x22a4c` | `PlaceBoxRoad` | `-s -ot -ol -5r -zp2` |
| `0x22a98` | `PlaceBoxWall` | `-s -ot -ol -5r -zp2` |
| `0x29f40` | `AiGuardStartArea` | `-s -ot -ol -5r -zp2` |
| `0x2ab54` | `AiIdleUnitTick` | `-s -ot -ol -5r -zp2` |
| `0x34060` | `DpmiGetFreeMemoryKB` | `-s -ot -ol -5r -d1+ -zp2` |
| `0x348c0` | `RectOutline` | `-s -ot -ol -5r -d1+ -zp2` |

Do NOT touch the 6 excluded functions (`SaveErrorDialog`, `IntroFadeStep`, `IntroBeginFlic`, `FarmPanelChanged`, `BitmapClear`, `OpenArchive`).

### Mandatory per-candidate verification procedure (use a deterministic Python script in `$TMPDIR`, NOT tracked)
1. Confirm each candidate is currently T4 on this branch and its source matches the E7 baseline.
2. Run `wc1.t3_audit.audit_unit` on all 13 candidates using the new presets from Commit 1: confirm every one returns `MATCH_BUILDABLE` with the exact minimal flags listed above (`-s -ot -ol -5r -zp2` for the first 11, `-s -ot -ol -5r -d1+ -zp2` for the last 2).
3. Run the read-only E0 experimental matcher as an additional cross-check (load `git show research/build-codegen-experiments:experiments/build_codegen/e0/matcher_proto.py` into `$TMPDIR` without committing or integrating it into production) on the compiled `.obj` of all 13 candidates: confirm `FunctionMatch` and `RegionMatch` for every promoted candidate!
4. Run all 13 cited T4 differential tests BEFORE and AFTER promotion (keep the `_reference.c` filenames and preserve all existing differential tests; `t4spec` guards automatically verify `MATCH` once promoted).
5. Apply the established production T3 promotion procedure (`wc1.wave4.promote` or exact equivalent):
   - Update each C file's `codegen-compiler` / `codegen-flags` headers via `wc1.wave4.set_flags_header` to `10.0a` and its minimal matching flags. Do NOT rewrite function bodies.
   - Update each TOML block via `wc1.wave4.promote_toml_text` (drop `ref`, `ref_verified_by`, `t3_blocker`; set `confidence = "verified"`, `src = "..."`, `verified_by = "match: python3 -m wc1.match <ref> (code bytes, relocation targets, module data; flags from the codegen-flags header)"`; prepend evidence line noting Watcom 10.0a matching flags, E7 calibration / `wc1.t3_audit` promotion, and preserved T4 difftest).
6. If any candidate fails any check, leave it unpromoted and report the exact blocker; do not start an unrelated repair.
7. Run targeted post-promotion verification:
   - `nix develop -c python3 -m wc1.symbols`
   - `nix develop -c python3 -m wc1.match <each of the 13 files>`
   - `nix develop -c python3 -m wc1.match --compile-check <all 13 files>` (verifies both Watcom 10.0a and OW2 compile cleanly!)
   - `nix develop -c python3 -m wc1.build` and `nix develop -c python3 -m wc1.compare build/war.exe original/install/war.exe` -> MUST report `IDENTICAL` (`532 functions from 527 C files` if all 13 succeed)!
   - `nix develop -c pytest -q tests/test_mod_13b30_f1.py tests/test_mod_13dd0_c.py tests/test_mod_13f60.py tests/test_gamedlg.py tests/test_mod_1af20_c1.py tests/test_mod_20c30.py tests/test_placebox.py tests/test_mod_295d0.py tests/test_mod_34060.py tests/test_mod_348c0_c.py`
   - `nix develop -c python3 -m wc1.progress` -> confirm `T3: 532`, `T4: 372`, `DONE: 899` (T4->T3 promotions, NOT +13 DONE).
8. Commit Commit 2 atomically with explicit staged paths:
   `T3: promote 13 verified E7 Watcom 10.0a -5r candidates (519 -> 532 T3, Build A IDENTICAL)`

---

## Commit 3 — Task C: Preserve improved residual T4 audit results for future Wave 4B with staleness validation

1. Run a fresh read-only production `wc1.t3_audit` across all remaining in-scope T4 functions (372 functions) using the new E7 presets:
   ```bash
   nix develop -c python3 -m wc1.t3_audit --jobs 6
   ```
   (This writes the live git-ignored `build/t3_audit/report.{json,md,csv}` natively consumed by `wc1.wave4.discover()` and `wc1.wave4a.load_audit_report_incremental()`.)
2. Add a small, clean, mechanical helper in `tools/wc1/t3_audit.py` (e.g. `improved_t4_records(report)` and `validate_improved_record(record, ...)` or `is_record_fresh(record, ...)`):
   - `improved_t4_records(report)` extracts minimal machine-readable provenance records ONLY for residual `MISMATCH` T4 functions whose `best["score"]` strictly beats their `"declared"` attempt score (and have `best` flags different from `declared_cflags`, with no unresolved relocations or explicitly recording `unresolved_count`), preserving:
     - Function identity (`addr`, `addr_hex`, `name`, `link_name`, `module`, `ref`, `toml`)
     - Declared flags & declared score
     - Best observed compiler flags & best mismatch score & `first_diff`
     - Compiler identity (`compiler`, `manifest_sha256`, `tool_sig`)
     - Source and dependency fingerprint (`source_digest`, `omf_deps_sha256` / `omf_deps` summary)
     - Search configuration (`base_flags`, `presets`, `git_commit`)
   - `is_improved_record_fresh(rec, *, repo_root=None, tool_sig=None, current_presets=None, by_link=None)` validates that stale records are rejected when:
     - source or any recursive include changes (`source_digest` mismatch or unreadable -> fail-closed `False`),
     - compiler/binary `tool_sig` changes,
     - `presets` or `base_flags` search configuration changes,
     - `declared_cflags` of the ref file changes,
     - any recorded OMF external/`_TEXT` symbol in `by_link` moved/disappeared/appeared.
   - Do NOT blindly modify canonical compiler flags of any residual T4 function.
   - Do NOT launch LLM source-repair sessions.
   - Do NOT commit `build/` or the full experimental dataset.
3. Export the minimal regenerated machine-readable JSON snapshot from the fresh production `wc1.t3_audit` run to:
   `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json`
   (Sanitize any absolute host paths like `<host-root>/...` or `/tmp/...` before writing — store repo-relative paths and digests only!)
4. Add focused regression tests in `tests/test_t3_audit.py` testing `improved_t4_records` and `is_improved_record_fresh` (fresh passes; source edit, include edit, preset change, tool_sig change, declared_cflags change, and symbol address change ALL reject stale records).
5. Run targeted tests:
   ```bash
   nix develop -c pytest -q tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4_fingerprints.py
   nix develop -c python3 -m wc1.symbols
   ```
6. Commit Commit 3 atomically with explicit staged paths:
   `wc1.t3_audit: add provenance-checked improved-T4 audit snapshot for Wave 4B + tests`

---

## Final Developer Report
In your final message, provide:
- Exact commit SHAs produced on `feature/e7-compiler-presets`
- Exact presets added and ordering
- Table of all 13 promoted functions, minimal flags, E0 cross-check verdict, compile-check (10.0a + OW2), difftest status, and Build A `wc1.compare` output
- Count of improved residual T4 functions in `t4_improved_audit.json` (total and dependency-clean) and summary of fresh `wc1.t3_audit` results
- Exact targeted test commands and results
- Confirmation of clean `git status` (no untracked files, no edits outside scope).

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-26T20:32:01.640557Z` (Unix epoch `1795725121`)
- **Hard wall-clock limit:** `2700 s` (~`45 min`, hard cutoff `2026-11-26T21:17:01Z`)
- **70% wrap-up checkpoint:** `1889 s` (`2026-11-26T21:03:30Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally as you go rather than waiting until the end; begin wrapping up and finalizing commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized by the Manager. Batch independent shell commands into a single step where safe.
- **Environment:** Run project tools inside the Nix dev shell (`nix develop -c <cmd>`) without nested Nix shells.
