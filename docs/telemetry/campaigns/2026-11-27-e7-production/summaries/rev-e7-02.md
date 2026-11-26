# Round 2 Review — `feature/e7-compiler-presets` (`e14d5c0a..5667e2f7`)

**Reviewed commit:** `5667e2f76a53090dd2077d0047a967cdf30d08de`
**Branch/range:** `feature/e7-compiler-presets`, 4 commits ahead of `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da` (no merges; worktree clean apart from the expected untracked `original` symlink).
**Mode:** read-only adversarial review; no tracked file was modified (`git status --porcelain` = `?? original` only).

## 1. Round-1 finding verification

### HIGH — checkout portability of `portable_source_digest` / `t4_improved_audit.json` — **RESOLVED**
- `portable_source_digest` (`tools/wc1/t3_audit.py:149-192`) maps every resolved dependency to a logical key before hashing (`sys:<rel to 10.0a h/>`, else `repo:<rel to repo_root>`); `sys:` is classified first, so a real `original/` and a symlinked `original/` both produce identical `sys:` keys.
- Live check in this worktree (`<wt-rev>`), with live `symbols.load()` `by_link`, **live `_tool_sig()`, live presets/base flags and live declared cflags**: **202 / 202 fresh**, 0 bad.
- Repeated in a relocated real checkout (`/tmp/.../copy`, `original` symlinked to the real install): **202 / 202 fresh**.
- Edge probes: missing ref → `None`; `../` escaping ref/include → `None`; absolute include outside both roots → `None`; out-of-tree include (unit test) → `None`; absolute ref *inside* the repo still hashes to a `repo:` key (no absolute path enters the digest); synthetic real-vs-symlink `original/` test passes.
- Host paths: zero strings in the JSON start with `/`; zero `/mnt/`, `/home/`, `/tmp/`, `/root/`, etc.; zero Windows drive paths; all `ref` values are relative and contain no `..`.
- The old absolute-keyed `wave4_fp.unit_source_digest` value differs from the recorded portable digest for the same file, confirming the fix is substantive, not a no-op.
- `wave4_fp.py` is untouched by the branch (`git diff e14d5c0a..HEAD -- tools/wc1/wave4_fp.py` empty); Wave 4 cache/fingerprint tests pass.

### MEDIUM — report provenance enforcement — **RESOLVED**
- `_report_provenance` (`t3_audit.py:669-690`) fails closed unless `completion.status == "complete"`, `git_dirty is False` (strict identity; `0`/`"False"`/missing rejected), and `options.presets` is a non-empty list of non-empty strings with a non-empty string `base_flags`.
- `improved_t4_records` (`695-760`) refuses (returns `[]`) dirty/incomplete/missing-options reports and stamps each record with the **report's own** presets/base flags; `build_improved_audit_snapshot` (`779-811`) raises `ValueError` for the same.
- Adversarial matrix run: dirty (`True`, `0`, `"False"`, missing), missing/running completion, missing options, tuple/empty/non-str presets, non-str base, old presets, old base → **0 records** (and old-preset/old-base records, when minted, fail `is_improved_record_fresh`). No laundering path found.
- The committed snapshot's `presets`/`base_flags`/toolchain match the live environment.

### LOW — `omf_deps_sha256`, `git_commit` docs, stale comments — **RESOLVED**
- `_is_sha256_hex` (`814-816`) requires exactly 64 lowercase hex chars; `is_improved_record_fresh` (`819-861`) rejects missing/malformed/uppercase digests and a mismatched `omf_deps=` kwarg.
- Live mutation of a real record: wrong `source_digest`, preset list, base flags, declared cflags, tool sig, missing/uppercase OMF sha, OMF kwarg mismatch, moved symbol → **all nine return `False`**; unmutated record returns `True`.
- `git_commit` is explicitly documented as informational (`830-833`), consistent with the dependency-scoped checks.
- The three comment-edited promoted files all still `MATCH` and pass `--compile-check` under both compilers:
  - `src/mod_13f60/set_game_mode_reference.c` → `MATCH SetGameMode_`
  - `src/mod_295d0/ai_guard_start_area_reference.c` → `MATCH AiGuardStartArea_`
  - `src/mod_295d0/ai_idle_unit_tick_reference.c` → `MATCH AiIdleUnitTick_`
  - `compile check: 1 files x 2 compilers, 0 failures` for each.

## 2. End-to-end branch criteria (all hold on `5667e2f7`)

| Criterion | Result |
|---|---|
| Presets preserved, default/OW2 intact | 14 unique 10.0a presets: all 8 legacy present, 6 new E7 presets; first is `-s -ot -ol -4r -zp2`; `ow2` entry retained; `match.DEFAULT_CFLAGS` unchanged |
| Fingerprint/audit-cache invalidation | `current_presets()`/`base_flags`/`plan`/`tool_sig` invalidation in `wave4.load_report` and `wave4a` bootstrap; covered by new fingerprint/incremental tests, all green |
| 13 promotions | `wc1.progress`: **532 T3** (10.0a 531, ow2 1), **372 T4**, 6 unchecked ref, **899 DONE (89.0%)**; named 914 (90.5%) |
| Build A | `wc1.build`: **532 functions from 527 C files**, `IDENTICAL`; `wc1.compare`: `IDENTICAL (loaded image, entry, stack, fixups)`, fixups A=B=8770, only-A=0, only-B=0 |
| No weakened gates / unauthorized files | `git diff --name-only e14d5c0a..HEAD -- Makefile flake.nix flake.lock tools/wc1/progress.py tools/wc1/build.py tools/wc1/match.py tools/wc1/oldcc.py docs/GOAL.md docs/METHODOLOGY.md AGENTS.md` = empty; tests diff has **0 removed lines**, no new skip/xfail |
| 6 excluded functions | Not enumerable from the branch (no list is recorded), but the changed `src/` set is exactly the 13 promoted reference files; no other function/TOML entry was touched |
| No research merge | `git log --merges e14d5c0a..HEAD` empty; exactly 4 commits |

All 13 promoted files re-verified individually with `wc1.match` — all `MATCH`.

## 3. Remaining findings (non-blocking)

| Severity | Location | Finding |
|---|---|---|
| LOW | `tools/wc1/t3_audit.py:780-783` vs `790-810` | Docstring says the snapshot builder “refuses … any record whose source digest is not checkout-portable”; it does not. With a synthetic report carrying an old absolute-keyed `wave4_fp` digest, the builder returned a snapshot with the non-portable digest retained and `verified_fresh: 0` instead of raising. Suggest raising when any record’s digest ≠ `portable_source_digest(ref)` (or when `fresh < total`) before writing. No impact on the committed artifact (202/202). |
| LOW | `tools/wc1/t3_audit.py:795` | `verified_fresh` is computed with the **report’s** `tool_sig`, not live `_tool_sig()` (and with `by_link` possibly `None`, so symbols may be `None` while still counted fresh). A snapshot built from a foreign-toolchain report could claim fresh records that are stale now. In this artifact the recorded and live `tool_sig`/manifest are identical, and independent recomputation with live identity gives 202/202, so no impact; consider verifying against live identity or documenting the semantics. |
| INFO | `tools/wc1/t3_audit.py:136-137`, `772-776` | `_assert_no_host_paths` is a prefix allowlist; absolute paths outside the listed roots (e.g. `/data/`, `/scratch/`, bare `/mnt`) and UNC paths are not caught. Defense-in-depth only: the artifact has no absolute strings and digest keys are relative. |
| INFO | `tools/wc1/t3_audit.py:660-667` | `_omf_deps_digest({})` returns a valid digest of all-`None` fields, so a report with an empty `omf_deps: {}` can yield a record that passes the new sha check (observed fresh with `by_link={}`). Real audits never emit `{}`; missing key/`None` and malformed/uppercase digests are correctly rejected. |
| INFO | committed `t4_improved_audit.json` | `git_commit` = `4c549bc2…`, a dangling temp commit (“temp: rev-e7-01 fixes for clean audit run”, parent `59efdd2`). Its scoped tree (`src/analysis/tools/tests`) is byte-identical to `5667e2f` (`git diff 4c549bc 5667e2f -- src analysis tools tests` empty), and `git_commit` is documented informational, so this is only an archival note. |
| INFO | `tools/wc1/t3_audit.py:834-844` | A malformed non-string `ref` raises `TypeError` (pre-existing `unit_source_digest` behavior) rather than returning `False`; not reachable from generated records, but slightly at odds with the “fail closed” wording. |

## 4. Checks run / not run

**Run:** targeted pytest (`test_permuter_unit`, `test_t3_audit`, `test_wave4`, `test_wave4a`, `test_wave4_fingerprints`, `test_overnight_wave4`, `test_mod_13f60`, `test_mod_295d0`) → **276 passed in 7.58 s** (`test_t3_audit.py` alone: 49 passed); `wc1.symbols`, `wc1.build`, `wc1.compare`, `wc1.progress`; `wc1.match` on all 13 promoted files; `wc1.match --compile-check` on the 3 comment-edited files; `wc1.t3_audit --dry-run --limit 3`; live 202-record freshness in this worktree and a relocated copy; adversarial provenance/OMF/digest probes; JSON consistency/host-path scans; full commit-range/unauthorized-file/merge checks.

**Not run (per instructions or unavailable):** `make verify` and the full repository suite (Manager-owned); `make compile-check` over all of `src/` (only the 3 requested files, plus the 10.0a full build); byte-for-byte regeneration of the committed snapshot (the source `report.json` is not retained); enumeration of the 6 excluded function names (no list exists in the branch).

VERDICT: APPROVE