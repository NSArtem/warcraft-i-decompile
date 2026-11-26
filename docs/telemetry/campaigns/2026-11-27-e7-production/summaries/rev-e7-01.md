I'll start by orienting in the worktree and reviewing the commit range.
Presets and diffs look structurally sound. Now running the live verification checks.
## Review Scope

- **Reviewed commit SHA:** `59efdd2888d9baf6ae59141d212660d7c0d7ecc8`
- **Range:** `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da..59efdd2888d9baf6ae59141d212660d7c0d7ecc8` (`196153c1`, `2b10939b`, `59efdd28`)
- Working tree was read-only for tracked files; only the pre-existing untracked `original/` tree was present. No reviewer edits or commits were made.

---

## Findings

### HIGH — The committed improved-T4 snapshot is stale in every checkout except the producer’s worktree

**Files:**
- `tools/wc1/wave4_fp.py:110,117,123` — `source_inputs()` hashes a mapping keyed by **absolute** paths (`str(fn)`), then `unit_source_digest()` SHA-256s that mapping.
- `tools/wc1/t3_audit.py:676` — `is_improved_record_fresh()` recomputes the digest under the current checkout root.
- `docs/telemetry/campaigns/2026-11-27-e7-production/t4_improved_audit.json`

**Evidence (live):**

- In the producing worktree `<wt-dev>`:
  - `is_improved_record_fresh` → **202 / 202 fresh**
  - digest for `src/mod_104b0/tile_apply_damage.c` = `ada914a7…`
- In this review worktree `<wt-rev>`:
  - `is_improved_record_fresh` → **0 / 202 fresh, 202 stale**
  - digest for the same file = `04968a2a…`
- The source and include contents are byte-identical between the two worktrees:
  - `diff -q dev/src/mod_104b0/tile_apply_damage.c rev/...` → identical
  - `diff -q dev/src/include/mod_104b0.h rev/src/include/mod_104b0.h` → identical
  - For five sampled records, a normalized repo-relative digest is identical in `dev` and `rev`.
- Therefore the only difference is that the absolute checkout path is part of the hash input.

The artifact’s own `summary.verified_fresh: 202` is consequently false in any fresh clone, worktree, or renamed checkout.

**Impact:** The snapshot is fail-closed, so it cannot inject wrong evidence, but Task C’s central deliverable is unusable outside the original `<wt-dev>` path. A future Wave 4B run in a fresh worktree will reject all 202 records.

**Fix:** Hash repo-relative paths (or store per-file `{relative_path: sha256}` entries in each record and validate those), regenerate `t4_improved_audit.json`, and add a test that copies/moves the fixture repo to a second root and still expects freshness. Keep absolute paths out of the digest.

---

### MEDIUM — `improved_t4_records()` stamps current provenance onto records from an unchecked report

**File:** `tools/wc1/t3_audit.py:613-615, 654`

`improved_t4_records()` reads `meta.toolchain` and `meta.git_commit`, but never validates the input report’s `meta.options.presets`, `meta.options.base_flags`, `meta.git_dirty`, or `meta.completion`. It then unconditionally records:

```python
"base_flags": match.BASE_CFLAGS, "presets": current_presets(),
```

**Reproduction (run in `<wt-dev>`):**

Using a genuine `build/t3_audit/report.json` row, wrapped in a synthetic report whose meta said:

```python
{"git_commit": "old", "git_dirty": True,
 "options": {"presets": ["-s -ot -ol -4r -zp2"], "base_flags": "-q -zl -bt=dos"}}
```

produced a record whose `presets` equal the **current** preset list, and `is_improved_record_fresh(rec)` returned **True**. The recorded `git_commit` was the stale `"old"`.

**Impact:** A stale or foreign report can be laundered into records that pass the freshness gate. This defeats the stated purpose of provenance checking and is exactly the “git_commit / preset mismatch” case the checklist asks about. The committed snapshot itself was generated from a matching report, so it is not affected by this particular hole; the generator API is.

**Fix:** Require `meta.completion.status == "complete"`, `meta.git_dirty is False`, and `meta.options.presets == current_presets()` / `meta.options.base_flags == match.BASE_CFLAGS` before emitting records; alternatively stamp the report’s real provenance and let freshness reject it. Add tests for old-preset and dirty reports.

---

### LOW — Recorded `omf_deps_sha256` and `git_commit` are never validated

**File:** `tools/wc1/t3_audit.py:660-696`

`is_improved_record_fresh()` checks source digest, tool signature, preset/base flags, declared flags, and recorded symbol addresses, but not `omf_deps_sha256` or `git_commit`. Mutating a valid record’s `omf_deps_sha256` to `"0"*64` and `git_commit` to `"deadbeef"` still returns `True`. A newly appearing OMF symbol not present in the record is also explicitly accepted by the test at `tests/test_t3_audit.py:684-685`.

Most real changes are caught indirectly by the source digest, tool signature, or symbol-address map, so impact is limited. Still, two recorded provenance fields are dead weight unless documented as informational. Either validate them or document why they are not part of freshness.

---

### LOW — Three promoted files retain comments saying they are “Reference C (T4)” / “not built”

- `src/mod_13f60/set_game_mode_reference.c:6` — “Reference C (T4)”
- `src/mod_295d0/ai_guard_start_area_reference.c:3` — “REFERENCE C (not built)”
- `src/mod_295d0/ai_idle_unit_tick_reference.c:3` — “REFERENCE C (not built)”

These files are now `src =` T3 entries and are built. The comments are misleading, though not functional. Updating them is a small follow-up (only two pre-existing T3 files share this stale wording).

---

### INFO — Snapshot redundancy and reproducibility

- `t4_improved_audit.json` is 395,252 bytes for 202 records (~1.7 KB/record). Each record repeats the full 14-entry preset list, `base_flags`, compiler, manifest, and tool signature already present at the top level. This is acceptable but could be slimmed with a schema reference.
- There is no committed generator or consumer for the snapshot; `summary.verified_fresh` was produced by an ad-hoc run. Adding a small generator/test would make the artifact reproducible.
- `wave4a.py:319` treats a missing `tool_sig` as fail-open (`rep_tool is not None and tool_sig is not None and ...`). New complete reports always carry one, and legacy reports fail the preset/plan check, so this is low risk. `wave4.load_report` also does not compare tool signatures; that is pre-existing behavior, outside this change’s stated scope.

---

## Checklist Results

### Task A — presets and invalidation

- **Required presets present:** `permuter.FLAG_PRESETS` contains `-s -ot -ol -5r -zp2`, `-s -ot -oa -ol -5r -zp2`, and `-s -ot -ol -5r -d1+ -zp2`.
- **Additional presets supported by E7:** `c22` (`-s -os -4r -zp2`), `c10` (`-s -ot -ol -3r -zp2`), and `c26` (`-s -ot -ol -4r -of+ -zp2`) all appear in `research/build-codegen-experiments:docs/research/build-codegen/results/e7/proposed_presets.json`.
- **No duplicate preset lists:** only `permuter.FLAG_PRESETS` defines the runtime list; `t3_audit.attempt_plan()` and `current_presets()` derive from it.
- **Ordering:** minimal `-s -ot -ol -5r -zp2` precedes `-s -ot -oa -ol -5r -zp2`.
- **Preservation:** all 8 original 10.0a presets and the OW2 fallback remain. `FLAG_PRESETS[0]` is still `-s -ot -ol -4r -zp2`; `match.DEFAULT_CFLAGS` is still `BASE_CFLAGS + " -s -ot -ol -4r -zp2"`; `permuter.set_headers()` still uses the `-4r` default.
- **Invalidation:** `wave4.load_report` rejects changed preset/base flags and pre-E7 `options.plan`-only reports; `wave4a` rejects stale bootstrap reports and stores a per-unit plan independent of `omf_deps`; `wave4_fp` fingerprints include `attempt_plan()`; `resolve_omf_deps()` rejects stale source digest, plan, and tool signature.
- **Tests:** `tests/test_permuter_unit.py`, `tests/test_t3_audit.py`, `tests/test_wave4.py`, `tests/test_wave4_fingerprints.py` all pass.

### Task B — 13 promotions

- Exactly 13 TOML entries changed `ref` → `src`; exactly 13 `confidence = "verified"` and `verified_by = "match: ..."` additions; no `addr` lines changed.
- Exactly these addresses: `0x13c04`, `0x13c84`, `0x13dd0`, `0x15314`, `0x1a800`, `0x1af20`, `0x21df0`, `0x22a4c`, `0x22a98`, `0x29f40`, `0x2ab54`, `0x34060`, `0x348c0`.
- All 13 now have `src`, no `ref`, no `ref_verified_by`, no `t3_blocker`.
- Source changes are flag-only: `-4r` → `-5r` (plus the two existing `-d1+` files); no function-body rewrites.
- No other T3/T4 source or TOML files were touched.
- Targeted test files all pass.

### Task C — snapshot

- 202 records, 193 `dependency_clean` and 9 flagged otherwise.
- All required identity/provenance/score fields are present in every record.
- No absolute host paths (`/mnt/`, `/home/`, `/tmp/`), credentials, or `WATCOM` paths found.
- All record addresses still map to current T4 `ref` entries; none became T3.
- All `declared_cflags` remain `-4r`-based; residual canonical flags were not modified.
- **Freshness in the review worktree: 0 / 202 fresh.** See HIGH finding above.

### Task 6 — gate preservation

- `Makefile`, `flake.nix`, `tools/wc1/progress.py`, `build.py`, `match.py`, `oldcc.py`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, and `AGENTS.md` are unchanged in the range.
- No test deletions or added skips/xfails in the modified test files.
- No occurrences of `SaveErrorDialog`, `IntroFadeStep`, `IntroBeginFlic`, `FarmPanelChanged`, `BitmapClear`, or `OpenArchive` in the source/symbol diff.
- No E0 matcher, CodeRegion, Fix B1/B2/B3, selective OMF extraction, multi-function T4, CU recovery, source consolidation, or research-branch changes were merged.

---

## Commands Run

- `git log`, `git diff --stat`, `git diff`, `git diff --check`, `git status`
- `nix develop -c python3 -m wc1.symbols` → 1370 functions, 954 data symbols
- `nix develop -c python3 -m wc1.match <file>` on all 13 promoted files → all `MATCH`
- `nix develop -c python3 -m wc1.match <file> --compile-only` on all 13 → all compile under 10.0a
- `nix develop -c python3 -m wc1.match <file> --compile-only --cc other` on all 13 → all compile under OW2
- `nix develop -c python3 -m wc1.build` → `532 functions from 527 C files`
- `nix develop -c python3 -m wc1.compare build/war.exe original/install/war.exe` → `IDENTICAL (loaded image, entry, stack, fixups)`
- `nix develop -c python3 -m wc1.progress` → T3 **532**, T4 **372**, DONE **899**
- `nix develop -c pytest -q` on the 16 requested test files → **323 passed in 17.09s**
- Python checks parsing all TOMLs, the snapshot schema/paths, and live freshness in both `<wt-dev>` and `<wt-rev>`

## Left Unchecked

- Full `make verify` and the full repository test suite were **not** run, per the assignment; the Manager owns serialized verification.
- `make goal` and the undefined M3 scenario set were not evaluated.
- A full repository-wide `wc1.match` / `match-all` sweep was not run; only the 13 promoted files were checked.
- No runtime re-audit of all 202 snapshot records was performed; freshness was checked statically against the live repo.
- The branch was not merged into `main`, per read-only review rules.

VERDICT: REQUEST_CHANGES
The background probe was a redundant earlier check; it was terminated by its timeout with no output. That does not affect the review: the same question was already answered directly — `<wt-rev>` has no `build/t3_audit/report.json`, while `<wt-dev>/build/t3_audit/report.json` exists and contains the `ada914…` digest used by the committed snapshot.

The findings and verdict are unchanged:

- **HIGH:** the committed snapshot’s source digest is absolute-path-dependent, so all 202 records fail `is_improved_record_fresh` outside `<wt-dev>`.
- **MEDIUM:** `improved_t4_records()` stamps current presets/base flags without validating the source report’s provenance.
- **LOW:** recorded `omf_deps_sha256` / `git_commit` are not validated; stale “Reference C (T4)” / “not built” comments remain in three promoted files.

Reviewed SHA: `59efdd2888d9baf6ae59141d212660d7c0d7ecc8`

VERDICT: REQUEST_CHANGES