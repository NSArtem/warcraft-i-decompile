Resolved all `rev-e7-01` findings in a single new commit.

## Commit

`5667e2f` — `wc1.t3_audit: make improved-T4 digests checkout-portable and enforce report provenance (rev-e7-01 fixes)`

On top of `59efdd2`, no history rewriting.

## Changes

1. **Portable source digest (HIGH)** — `tools/wc1/t3_audit.py`
   - Added `portable_source_digest(ref, *, repo_root=None, system_headers=None)` using `wave4_fp.source_inputs()` underneath (Wave 4's `unit_source_digest` untouched).
   - Every resolved dependency is mapped to `sys:<rel>` (system header tree, classified first) or `repo:<rel>`; anything outside both returns `None` (fail closed, no host path ever hashed).
   - Digest = SHA-256 of `json.dumps(portable_hashes, sort_keys=True)`.
   - Used by `_source_digest`/`audit_unit`, `improved_t4_records`, and `is_improved_record_fresh`.

2. **Report provenance (MEDIUM)** — `improved_t4_records()` now returns `[]` unless the report is `completion.status == "complete"`, `git_dirty is False`, and carries valid `options.presets` (non-empty string list) / `options.base_flags`. Records are stamped with the report's own presets/base flags; `current_presets()`/`match.BASE_CFLAGS` are never fabricated. Added `build_improved_audit_snapshot(report, *, by_link=None, campaign=None)` (raises on an unusable report, refuses absolute host paths).

3. **Provenance tightness + stale comments (LOW)**
   - `is_improved_record_fresh()` requires a valid 64-hex `omf_deps_sha256` and accepts `omf_deps=` to verify it; docstring now documents `git_commit` as informational only.
   - Updated the 3 stale `Reference C (T4)` / `REFERENCE C (not built)` comments (comments only).

4. **Regression tests** — 11 new/updated tests in `tests/test_t3_audit.py`: cross-checkout portability (copy + second root), real-vs-symlinked `original/`, outside-root fail-closed, dirty/incomplete/missing-options reports, old-preset/old-base-flags never laundered, OMF digest malformed/mismatch, and snapshot reproducibility/host-path rejection.

## Verification

- `pytest -q tests/test_t3_audit.py`: **49 passed**
- `pytest -q tests/test_permuter_unit.py tests/test_wave4.py tests/test_wave4a.py tests/test_wave4_fingerprints.py tests/test_overnight_wave4.py tests/test_mod_13f60.py tests/test_mod_295d0.py`: **227 passed**
- `wc1.match` + `wc1.match --compile-check` on all 3 comment-edited files: `MATCH` + `0 failures` each (both compilers).
- `python3 -m wc1.symbols`: 1370 functions, 954 data symbols.
- Regenerated `t4_improved_audit.json` from a fresh `wc1.t3_audit --jobs 6` report (372 T4: 7 unbuildable, 363 mismatch, 2 skipped): **202 records, 193 dependency-clean, `verified_fresh: 202`**.
- Freshness across roots: `dev` **202/202**, `rev` **202/202**, `$TMPDIR` symlinked checkout root **202/202**.
- No `/mnt/`, `/home/`, `/tmp/`, `/root/`, `/Users/` strings in the JSON.
- `git status --short`: only the pre-existing `?? original` symlink; tree otherwise clean.
- `make verify` was not run (Manager-owned).

Note: the snapshot's `git_commit` is `4c549bc` — the clean temporary worktree commit at which the audit actually ran (confirmed with `git_dirty=False`); it cannot record the final commit SHA that adds the JSON itself, and is documented as informational provenance. The temporary worktree was removed.