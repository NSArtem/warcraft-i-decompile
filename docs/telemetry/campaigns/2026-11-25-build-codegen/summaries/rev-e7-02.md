I'll start by inspecting the repository state and the repair commit.
Now let me independently confirm the root cause premise (that the unfixed long path really fails and the mirror works), using a scratch script outside tracked files.
Let me confirm the new regression test is actually *sensitive* — i.e. that the pre-fix code really fails the same scenario. I'll use a detached worktree of the pre-fix commit (outside tracked files).
## Round 2 verification — Experiment E7 (`4194a2f`)

### 1. Diff review (`git diff 2ce107a..4194a2f`) — 8 files, all inside the experiment and its doc

**F1 (Must Fix) — long-checkout path portability: RESOLVED**

- `experiments/build_codegen/e7/common.py` adds the fix: `COMPILER_PATH_LIMIT = 112`, `compiler_root()` (deterministic `<tmp>/wc1e7-<sha1(repo)[:8]>/repo` symlink to the checkout), `_external()` for out-of-checkout paths, `compiler_path()` (maps/bounds every compiler-facing path, raises on overflow), `short_oldcc()` (redirects the two fixed include args `oldcc.compile_c` always adds) and `compile_short()` (single compile entry point).
- Wired in where Round 1 failed: `calibrate.compile_one` + the native-control compile (line 242), and `capability_probe.invoke`/`compile_probe` (exe, cwd, `-fo=`, source), with diagnostics sanitized to `<repo>`/`<probe>`. `link_check` also switched to `compile_short` and sanitizes its log.
- Regression tests added: a unit test asserting every path handed to `compile_c` is under the mirror and ≤112 chars (and that an over-long path raises), plus an end-to-end subprocess test with a symlinked `WC1_ROOT` ≥154 chars that runs the **complete real capability probe** (must equal the committed DB) and a **real `-d1+` cell** (must equal the committed runtime hash).
- Docs (`docs/research/build-codegen/E7-compiler-calibration.md`) document the measured limits (129 `-i=`, 130 source / 132 with `Z:`), the mirror design, and the regression tests.

**F2 (Optional) — LF line endings: RESOLVED**

- `analyze.write_derived` now uses `csv.DictWriter(..., lineterminator="\n")`; committed `t4_new_matches.csv` has **0 CR bytes** and is byte-identical to `2ce107a` after CRLF→LF normalization (content otherwise unchanged).

### 2. Tests

```
$ python3 -m pytest -q experiments/build_codegen/e7/test_e7.py
....................                                                     [100%]
20 passed in 9.54s
```

### 3. Scope / whitespace gates

- `git diff 7c23d23 -- tools/ src/ analysis/ tests/ Makefile flake.nix AGENTS.md` → **empty**.
- `git diff --check 7c23d23..HEAD` and `git diff --check 2ce107a..HEAD` → **clean**; no CRLF on `t4_new_matches.csv`.
- Commits touch only `experiments/build_codegen/e7/` and `docs/research/build-codegen/`; working tree unchanged (only the pre-existing untracked `original/`).

### Independent sensitivity checks (beyond the checklist)

- Raw 10.0a compile from a 146-char path → `**** Access violation ****`; same file via `compile_short` (44-char mirror path) → succeeds. Root cause confirmed.
- Pre-fix probe (`2ce107a`, isolated detached worktree) at a 186-char root → `RuntimeError: synthetic baseline failed: **** Access violation ****`; the repair's test passes at 154+. The new regression test is genuinely sensitive to the bug.
- The only non-10.0a native control (`src/mod_1e100/init_new_campaign.c`, OW2) compiles from a 183-char root with output identical to a normal-root compile, so the `cc=ow2` branch in `calibrate.calibrate` is covered too.
- Both scratch worktree and temp artifacts removed afterwards; `git status` back to baseline.

---

### 1. VERDICT: **APPROVE**

### 2. Findings

None blocking. Optional, non-blocking observations (no action required for this round):

- **O1** `common.short_oldcc()` permanently rebinds `wc1.oldcc.root`/`oldcc.path` process-wide and never restores them. Harmless for the standalone E7 entry points and for `make verify` (which collects only `tests/`), but a combined `pytest tests experiments/...` session would leak mirror paths into later tests. Consider scoping/restoring if the suites are ever collected together.
- **O2** A `RuntimeError` from `compiler_path()` (mirror path still >112 chars) is not converted into a per-cell `compile_error` in `calibrate.audit_unit`, so a pathologically deep repo-relative scratch/source path would abort the run rather than degrade. Practically unreachable with the current digest-based object layout.
- **O3** `_short_base()` prefers `/tmp` over `TMPDIR` (deliberate, to bound the prefix) and the `wc1e7-*` mirror dirs are never cleaned up — cosmetic only.

### 3. Verification summary

- F1 and F2 are both cleanly and completely resolved in `4194a2f`, with real-compiler regression coverage and matching documentation.
- 20/20 E7 tests pass in this review worktree (9.54 s, matching the doc's 9.56 s); the two findings' tests were shown to fail against the pre-fix code.
- No changes outside the experiment/docs; `git diff --check` clean on both requested ranges; no CRLF on `t4_new_matches.csv`; no tracked files modified by this review.