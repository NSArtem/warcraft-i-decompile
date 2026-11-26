# Developer Fix Assignment — Resolve `rev-e7-01` Review Findings

You are a fresh Developer session on branch `feature/e7-compiler-presets` (currently at `59efdd2888d9baf6ae59141d212660d7c0d7ecc8` in `<wt-dev>`).

Independent Reviewer `rev-e7-01` verified Tasks A and B (all 13 promotions, Build A IDENTICAL, 323/323 targeted tests passing) and returned `REQUEST_CHANGES` with specific, actionable findings in Commit 3 (`59efdd28`) and 3 minor comment cleanups.

Resolve ALL findings below in a clean atomic commit (do NOT rewrite history / do NOT amend earlier commits; add a new commit on top of `59efdd28`). Do NOT run `make verify` (the Manager owns serialized `make verify`). Use `nix develop -c <cmd>` without nested Nix shells.

---

## Findings to Fix

### 1. [HIGH] Portable source digest across checkouts (`tools/wc1/t3_audit.py`, `t4_improved_audit.json`)
- **Problem:** `wave4_fp.unit_source_digest()` calls `source_inputs()` which keys hashes by **absolute** paths (`str(fn)`), making `source_digest` checkout-path-dependent. As a result, `is_improved_record_fresh()` returned `202/202` in `<wt-dev>` and `0/202` in `<wt-rev>` even though all files are byte-identical.
- **Required fix:**
  - Add a clean helper `portable_source_digest(ref, *, repo_root=None, system_headers=None)` in `tools/wc1/t3_audit.py` (using `wave4_fp.source_inputs()` underneath, WITHOUT breaking `wave4_fp.unit_source_digest()`'s existing behavior for Wave 4 local caches).
  - Normalize every resolved file path returned by `source_inputs()` to a portable logical key:
    - If inside `Path(repo_root).resolve()` → `f"repo:{p.relative_to(repo_resolved).as_posix()}"`
    - Else if inside `Path(system_headers).resolve()` → `f"sys:{p.relative_to(sys_resolved).as_posix()}"`
    - Else → fail closed (return `None`, never hash an absolute host path!).
    - Note: remember `original/` in a worktree may be a symlink to the main repo's `original/`, so also resolve `Path(repo_root) / "original"` / `system_headers` consistently (`Path(system_headers).resolve()` matches `fn.resolve()`!). Check `sys_resolved` first or `repo_resolved` first consistently (checking `repo_resolved` first, and if `original/` is a symlink pointing outside `repo_resolved`, `sys_resolved` catches `original/watcom/10.0a/h/...` identically in every worktree and main checkout!). Test that it produces the **exact same digest** whether `original` is a real directory or a symlink!
  - Compute SHA-256 of `json.dumps(portable_hashes, sort_keys=True).encode()`.
  - Use `portable_source_digest` in `t3_audit._source_digest` / `audit_unit` (for `row["source_digest"]`), `improved_t4_records`, and `is_improved_record_fresh`.
  - **Verification:** Regenerate `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json` from a fresh `wc1.t3_audit --jobs 6` (or using the fresh `build/t3_audit/report.json` after re-running `wc1.t3_audit --jobs 6`), AND verify in Python that `is_improved_record_fresh()` returns `202/202` in `<wt-dev>` AND when evaluated against a symlinked/copied second root path!

### 2. [MEDIUM] Prevent laundering stale/dirty/old-preset reports in `improved_t4_records()` (`tools/wc1/t3_audit.py`)
- **Problem:** `improved_t4_records(report)` did not validate `meta.completion.status == "complete"`, `meta.git_dirty is False`, or read `presets`/`base_flags` from `meta["options"]`; instead it unconditionally stamped `current_presets()` and `match.BASE_CFLAGS`, allowing an old-preset or dirty report to be laundered into records that pass `is_improved_record_fresh()`.
- **Required fix:**
  - In `improved_t4_records(report, by_link=None)`:
    - Require `(meta.get("completion") or {}).get("status") == "complete"` and `meta.get("git_dirty") is False` (otherwise return `[]` or raise — returning `[]` is clean and safe, or document clearly; let's return `[]` when the report is incomplete, dirty, or lacks valid `options.presets` / `options.base_flags`!).
    - Read `presets = opts.get("presets")` and `base_flags = opts.get("base_flags")` directly from `meta["options"]` (requiring `isinstance(presets, list)` and `isinstance(base_flags, str)` and non-empty); NEVER fabricate `current_presets()` or `match.BASE_CFLAGS` from the current environment when the report itself has different or missing values!
    - Stamp the report's actual `presets` and `base_flags` onto each emitted record so `is_improved_record_fresh()` naturally rejects any record produced under different presets or base flags!
  - Add helper `build_improved_audit_snapshot(report, *, by_link=None, campaign=None)` in `tools/wc1/t3_audit.py` so `t4_improved_audit.json` is cleanly reproducible (and validate no absolute host paths appear in the output).

### 3. [LOW] Document/tighten `omf_deps_sha256` & `git_commit` provenance + update 3 stale file header comments
- In `is_improved_record_fresh()`:
  - Require `rec.get("omf_deps_sha256")` to be a valid 64-hex-char SHA-256 string (fail-closed if missing/malformed), and accept optional `omf_deps=None` parameter that verifies `_omf_deps_digest(omf_deps) == rec["omf_deps_sha256"]` when provided.
  - Document explicitly in the docstring that `git_commit` is informational provenance (freshness is intentionally dependency-scoped on source/includes, compiler/binary `tool_sig`, search `presets`/`base_flags`, `declared_cflags`, and OMF symbol addresses so unrelated commits do not invalidate valid records).
- Update the 3 stale "Reference C (T4) / not built" comments in the newly promoted files (comments only, zero code changes!):
  - `src/mod_13f60/set_game_mode_reference.c`
  - `src/mod_295d0/ai_guard_start_area_reference.c`
  - `src/mod_295d0/ai_idle_unit_tick_reference.c`
  And re-verify `wc1.match` and `wc1.match --compile-check` on all 3 files!

### 4. Regression Tests (`tests/test_t3_audit.py`)
Add focused tests covering EVERY finding above:
- Cross-checkout portability test: copy the fixture repo into a second directory (`tmp_path / "checkout_b"`) and assert `portable_source_digest` is identical AND `is_improved_record_fresh(rec, repo_root=checkout_b, ...)` returns `True`!
- Symlinked `original/` vs real `original/` system headers portability test.
- Dirty report (`git_dirty=True`), incomplete report (`completion.status != "complete"`), and missing-options report produce `[]` from `improved_t4_records()`.
- Old-preset report (`options.presets != current_presets()`) stamps its actual old presets onto emitted records so `is_improved_record_fresh()` returns `False` (never laundered!).
- Malformed/missing `omf_deps_sha256` fails closed (`False`), and mismatched `omf_deps` kwarg fails closed (`False`).

---

## Targeted Verification (before committing)
1. `nix develop -c python3 -m wc1.match src/mod_13f60/set_game_mode_reference.c src/mod_295d0/ai_guard_start_area_reference.c src/mod_295d0/ai_idle_unit_tick_reference.c` (or loop over the 3) + `--compile-check` on all 3.
2. Re-run `nix develop -c python3 -m wc1.t3_audit --jobs 6` and regenerate `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json` via `build_improved_audit_snapshot`.
3. Verify ALL records in `t4_improved_audit.json` pass `is_improved_record_fresh` in `<wt-dev>` AND when checked via a different symlinked checkout root in `$TMPDIR` (e.g. `$TMPDIR/alt-root`).
4. Verify NO absolute host paths (`/mnt/`, `/home/`, `/tmp/`) appear in `t4_improved_audit.json`.
5. Run targeted pytest:
   `nix develop -c pytest -q tests/test_permuter_unit.py tests/test_t3_audit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py tests/test_mod_13f60.py tests/test_mod_295d0.py`
6. Run `nix develop -c python3 -m wc1.symbols`.
7. Commit all fixes atomically on `feature/e7-compiler-presets`:
   `wc1.t3_audit: make improved-T4 digests checkout-portable and enforce report provenance (rev-e7-01 fixes)`

Report the new commit SHA, all verification results, and clean `git status`.

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-26T21:06:14.819667Z` (Unix epoch `1795727174`)
- **Hard wall-clock limit:** `2700 s` (~`45 min`, hard cutoff `2026-11-26T21:51:14Z`)
- **70% wrap-up checkpoint:** `1889 s` (`2026-11-26T21:37:43Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Commit finished, tested atomic units incrementally as you go rather than waiting until the end; begin wrapping up and finalizing commits by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized by the Manager. Batch independent shell commands into a single step where safe.
- **Environment:** Run project tools inside the Nix dev shell (`nix develop -c <cmd>`) without nested Nix shells.
