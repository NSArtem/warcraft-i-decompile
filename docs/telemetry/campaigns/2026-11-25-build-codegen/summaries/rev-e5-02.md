I'll start by orienting in the worktree and reading the contract/docs and the commits under review.
**Scope of this review:** fresh worktree `rev-e5-02` at `54d610ac`, baseline `1abb053c`; all four commits read, contract/design/results inspected, pytest and one full runner invocation executed, plus independent compile/record-level and fail-closed probes. No `nix develop`, no `make verify`, no tracked file changes.

---

## 1. VERDICT: APPROVE

## 2. Findings

### Low — the "compiled objects are byte-identical" claim is not true as written
- **Location:** `docs/research/build-codegen/E5-data-anchors.md:240-242`; same assumption in `experiments/build_codegen/e5/test_e5.py:121-123` ("the objects are the same bytes either way").
- **Explanation:** I compared a direct Watcom 10.0a compile (checkout path, `oldcc.compile_c`) against the mirror compile (`build_e5.compile_source`):
  - `gamedlg_data.c`: 861 B vs 749 B — `THEADR` plus three `COMENT` records embed the source/include paths (`Z:\...\gamedlg_data.c`, `gamedlg.h`, `defeat_dialog.c`).
  - `file_seek.c` (declares `-d1+`): `$$TYPES` segment is 421 B vs 281 B (path-bearing debug type metadata); `$$SYMBOLS` is 79 B in both.
  - **All non-metadata records are identical**: code, `CONST`/`_DATA`/`_BSS` bytes, fixups, publics, statics, externs and groups compare equal for all three probe sources.
  - The long-path regression test compares the long-checkout run with the normal run, but both resolve `realpath(ROOT)` to the same `/tmp/wc1e5-<hash>/repo`, so it proves path-spelling invariance (and that the crash is gone), not independence from the compiler-facing path prefix.
- **Impact:** none on the experiment's conclusions: B3 excludes `$$SYMBOLS`/`$$TYPES` via `e0._metadata`, and the 9 full links are byte- and fixup-identical to `war.exe`. This is a reporting/testing-precision defect, not a semantic one.
- **Required resolution:** reword to "loadable records are identical; `THEADR`/`COMENT`/`$$SYMBOLS`/`$$TYPES` carry the compiler-facing path and differ", and either adjust the test comment or add a non-metadata-record comparison against a direct compile. Non-blocking for E5 acceptance.

### Observations (non-blocking)
- `compiler_root()`/`_external()` create deterministic `/tmp/wc1e5-<hash>/{repo,ext}` symlinks that are intentionally reused and never removed; stale mirrors survive a deleted checkout, and the predictable `/tmp` path is a (low) local symlink-race surface. Per-compile temp objects are cleaned, including on a deliberate failed compile (no `*.err`, no `~pid` leftovers).
- `compile_10a`'s outer `timeout+20` raises `CompileTimeout` without `oldcc.kill_wineserver`; the inner 180 s oldcc timeout does kill it. Only matters if the helper process itself wedges.
- Include/compiler paths are short by construction (mirror root 24 chars; max baseline source path 85 chars) rather than checked by `compiler_path`; `WC1_WATCOM10A` overrides bypass the mirror (unset here). The temporary output name adds ~10 chars beyond the 112 check but stays ≲125, below the measured 130-byte source limit.

## 3. Independent verification summary

**Commands and results**
- `python3 -m pytest -q experiments/build_codegen/e5/test_e5.py` → **86 passed in 25.64 s**; the two long-path tests alone → **2 passed in 2.28 s** (all 9 Build A links, N1–N4, THREAD controls, long-path fixture compile exercised).
- `python3 -m experiments.build_codegen.e5.run_e5` → exit 0, `9 Warcraft links IDENTICAL; synthetic 5/5; negative controls rejected`. `git diff` of `results.json` is empty and its SHA-256 is `35483f23…aa6b11`, exactly the doc's claim. No `/tmp`, `/mnt`, `Z:` or worktree paths in the JSON.
- **Scope:** `git diff 1abb053c -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` empty; changed paths are only `experiments/build_codegen/e5/*` and the E5 doc/results. `wc1_anchor_` count in `src/`, `analysis/`, `tests/` = **0**. `git status` clean except the pre-existing untracked `original/`.

**Long-path fix (`54d610ac`)**
- Recreated a 180-character symlinked checkout: a direct 10.0a compile of `gamedlg_data.c` fails (`rc=1`, access violation), while `build.compile_source` succeeds through `/tmp/wc1e5-419e50d9/repo`.
- The long-checkout object hash equals the normal mirror object hash; record-level comparison confirms code/data/fixups/symbols unchanged. Temp mirror/output cleanup verified, including a deliberate syntax-error compile (no leftovers, no `.err` in the repo root).
- Max compiler-facing source path is 85 chars (limit 112); `compiler_path` maps both the long spelling and the normal spelling to the same mirror.

**Rewriter invariants (`omf_b3.py`)**
- `rewrite()` calls `verify_data()` (`:264`) before building any anchor/output; `verify_data` invokes the real `e0._Checker.check` (`:193`), which is the same routine that checks ordinary bytes (`:333`), forward relocations (`:300-325`) and reverse original LE obligations (`:337-352`). Each rewritten code source is separately checked against its original LE obligation (`:370-375`).
- `Threads` retains F0–F3/T0–T3 across records, parses records attached to dropped data (`:326`), rejects undefined/unsupported/truncated threads, and every emitted fixup encodes explicit frame/target operands. In `s3_thread`, proofs show 2 definitions and 2/4 uses per experimental object, and every emitted `c_*.obj` has **0** THREAD definitions and **0** uses. The fixture's F3/T3 definitions live on a dropped duplicate `CONST` LEDATA, so the cross-record/discarded-definition hazard is genuinely exercised.
- Fail-closed probes all rejected with the expected diagnostics:
  1. Per-symbol partition leaving the first 4 `_DATA` bytes uncovered → `unverified boundary, padding or overlapping symbols`.
  2. Whole-segment base shifted by +4 into the same object → `E0 data check _DATA: MISMATCH` (`missing_original_fixup`, `byte_mismatch`).
  3. Corrupted data-internal pointer addend with an unchanged FIXUPP target → `relocation_target_mismatch`.
  4. Corrupted inline addend of a code pointer into the anchored segment → `anchor reference contradicts original addressing obligation`.
- Real links: each scenario has `byte_diffs=0`, `original_fixups=linked_fixups=8770`, `only_original=only_linked=0`, 515 C objects / 520 functions / 1 data ASM piece, and all `anchor_fixup_records` preserve the original target object/offset (e.g. `0x1ab2c/0x1ab35/0x1ab42 → 0x9616/0x2586/0x6c0c`; `0x1acb4/0x1acbb → 0x1ea6/0x1ec8`). The link map contains 515 `c_*.obj` modules; C code ranges are excluded from the ASM pieces (`build_e5.py:274-281`), so no ASM fallback supplies the C functions. Frame modes really change the emitted fixups (`DGROUP → [1,1]`, Target → `[5,None]`, EXTDEF → `[2,*]`) while the LE result stays identical.
- `SaveErrorDialog` probes reproduce the documented `-os` MATCH (69 B, offset 0x22) vs native `-ot` MISMATCH (71 B, offset 0x24), and the explicit-array `_DATA` variant gives 0x22 and links IDENTICAL. Real three-segment `GAMEDLG` proof covers `CONST`, `_DATA`, `_BSS`; the synthetic three-segment control is identical in all five frame modes. N1–N4 all fail closed.

**Conclusion:** the Round-1 long-path crash is genuinely fixed without changing loadable object semantics or link output, the core B3 claims are independently reproducible, and scope/leak constraints hold. The only issue is the overstrong "byte-identical objects" wording described above.