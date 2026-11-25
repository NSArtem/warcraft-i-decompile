I'll start by orienting in the review worktree and reading the core artifacts.
A real failure appeared. Let me reproduce and diagnose it.
Found the root cause of the failure. Let me confirm it faithfully on a pristine tree.
Verification is complete. I reproduced a real failure, diagnosed it to root cause, and validated the Round‑1 repair independently.

---

## 1. `VERDICT: REQUEST_CHANGES`

The Round‑1 **HIGH** finding (Corpus B1 `libsig` ground truth) is genuinely and correctly resolved. But the committed state fails its own reproducibility test in a fresh worktree: `python3 -m experiments.build_codegen.e8.run_e8` rewrites `synthetic_manifest.json`, and `pytest` reports **1 failed, 27 passed**. The experiment's acceptance criteria ("run_e8 reproduces all results deterministically", "`git diff` empty") are therefore not met as committed.

## 2. Findings

### F1 — HIGH (reproducibility / acceptance criterion): committed `synthetic_manifest.json` is not regenerable
- **Location:** `docs/research/build-codegen/results/e8/synthetic_manifest.json` (`image.data_sha256`); `experiments/build_codegen/e8/synthetic_corpus.py` (`build()` → `sha256_bytes(prog.image[DATA_OBJ])`); `test_e8.py::test_run_e8_regenerates_the_committed_artifacts_byte_identically`.
- **Evidence (reproduced on a pristine tree):**
  - `python3 -m experiments.build_codegen.e8.run_e8` → exit 0, no tracebacks; `git diff` is **not** empty: exactly one line, `data_sha256` `2271d200…caba` → `0b3db113…0a59`. The other three artifacts are byte-identical.
  - `python3 -m pytest -q experiments/build_codegen/e8/test_e8.py` → `1 failed, 27 passed` (the failing assertion is the determinism test; it restores the committed bytes so it does not dirty the tree).
  - **Root cause:** Watcom 10.0 `wcc386` emits *uninitialized* alignment-padding bytes in the `CONST` pool. In `g17_uses.obj` the 3 padding bytes between `"e8 g17 b\0"` and `"e8 g17 t"` are `79 00 73` in the dev build and `72 00 72` here; they are copied verbatim into the linked data image. Minimal repro: compile the identical `build/e8/src/g17_uses.c` with identical flags (`-ot -ol -4r -zq -zp2`) in two different directories → the pad bytes differ (`65 00 6e` vs `50 00 52`). The `_TEXT` image and every metric are stable; only the raw data hash varies with the environment.
  - This predates `dc1d028` (the commit itself changed the hash `5689c6…` → `2271d2…`), so all four reviewed commits carry it.
- **Impact:** Signal metrics, labels and conclusions are unaffected (the hash is metadata unused by evaluation). The failure is the artifact-reproducibility contract and the red test.
- **Required resolution:** make `data_sha256` environment-independent — e.g. hash only symbol-initialized data bytes / normalize compiler alignment padding, or drop the raw data hash and hash the semantic corpus — regenerate the manifest, and confirm `git diff` is empty and the determinism test passes in a fresh worktree.

### F2 — LOW (test/documentation hygiene): the documented `pytest` command cannot collect the suite
- **Location:** `test_e8.py` docstring and `E8-contract.md` §5 (`pytest -q experiments/build_codegen/e8/test_e8.py`).
- **Explanation:** with the provided environment (`PYTHONPATH=$WC1_ROOT/tools`), the `pytest` entry point inserts `experiments/build_codegen` on `sys.path`, so `import experiments.build_codegen.e8` raises `ModuleNotFoundError: No module named 'experiments'` (0 tests collected). `python3 -m pytest …` works (cwd on path) and is what I used. The same applies to E7, so this is a shared convention gap, not unique to E8.
- **Resolution:** document/use `python3 -m pytest`, or add a `pythonpath`/`conftest.py` bootstrap.

### F3 — LOW (evidence quality): Corpus B1 verification tests silently skip in a fresh checkout
- **Location:** `test_e8.py` `needs_libsig_cache` / `build/e8/libsig10a.json` (not committed).
- **Explanation:** a fresh tree yields `20 passed, 7 skipped`; all seven B1 integrity/verification tests (full-segment re-verification, non-overlap, `cstrtx32` rejection, `intxa386` sensitivity, …) skip even though `war.exe` and the 10.0a library are present. They run only after `run_e8`, which the checklist asks for — but a plain `pytest` gives false assurance that B1 was checked.
- **Resolution:** build the libsig cache inside the tests (or gate the skip on the *inputs*, not the cache).

### F4 — NIT (minor labelling/documentation precision)
- B1 groups extents by `(lib, module, segi)`: `clib3r:cstrt386` contributes two admitted CODE segments (`_TEXT` 0x34584, `BEGTEXT` 0x10000), so `cus` contains a duplicate `id` and "112 admitted objects" is really **112 extents / 111 objects**. No label spans the two (BEGTEXT is at 0x10000), so no mislabel occurs; but an object whose segments *were* adjacent would be labelled a boundary by the `segi` split. Consider grouping by object for label decisions.
- Doc phrasing "every library relocation must land on a `war.exe` fixup" is true only for non-self-relative relocations (code correctly exempts `self_rel`).

## 3. Independent verification summary

**Scope:** `git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` — empty. Only `experiments/build_codegen/e8/` and `docs/research/build-codegen/{E8-cu-boundaries.md,results/e8/}` changed. No stray files (`git status`: only pre-existing `?? original`). All four artifacts LF-only; no host paths/timestamps.

**Round-1 HIGH — resolved (verified independently, not just via the tests):**
- `real_corpus.verify_segment()` re-checks **every unmasked byte** of the object's CODE segment at `[base, base+seglen)`, requires non-self-relative relocations on `war.exe` fixups, and forbids `war.exe` fixups on unmasked bytes; admission is gated on it (`_extents`).
- Rebuilt from the cache and re-ran `verify_extent` on all 112 admitted extents: **all pass**, `overlap_conflicts = 0`, and the extents are pairwise non-overlapping. 2 candidates rejected by byte mismatch: `vsprintf` (13 bytes) and `cstrtx32` (455 bytes, offset 0).
- `cstrtx3r:cstrtx32` is absent; `0x34850` lies in `clib3r:cstrt386`, `0x34860` lies in **no** admitted extent, and no `(0x34850,0x34860)` label exists at all — the old `same_cu` mislabel is gone (the old artifact did contain it plus a second phantom FP, exactly as the report states).
- `intxa386` is a genuinely verified 990-byte object; the `libsig_without_intxa386` sensitivity run is present (186 pairs = 73 boundaries + 113 same-CU, 111 extents), and its numbers match the report table exactly.

**Methodology (R4):** Corpus A labels are recipe membership only (and survive scrambling of ranges/`S`/rule/gap fields); map-verified placements; B1 uses object identity only; B2 is boundary-only with `precision_measurable=false` everywhere. I re-derived the report's B2 claims: 25 filtered labels, **8 overlap B1, 8/8 agree**; the pre-fix rule reproduces **76 labels / 35 overlapping / 23 contradicting, all 23 with a side shorter than `MIN_LEN=12`**. Exploratory game output is a separate artifact with its `EXPLORATORY / INFERRED` caveat, is never referenced by any metric block, and the report repeatedly states that module names are `modules.toml` hypotheses, not established filenames.

**Numbers:** every `TP+FP+TN+FN == sample_size`; precision/recall/F1 recomputed for all 16 signals × 3 corpora (the `setup` `precision=None` despite TP+FP>0 is the intended unmeasurable-precision rule); all three markdown tables plus the sensitivity table match `metrics.json` **100%**, and CSV matches JSON for all 48 rows. RFC §9.2 classes (3 proven, 1 strong-conditional, 8 weak/ambiguous, 4 unreliable) are consistent with the stated rubric and assumptions.

**Reproduction:** dev worktree `e8` at `dc1d028` has md5-identical result files (committed bytes agree cross-worktree); the drift appears only when the corpus is rebuilt — see F1.

**Recommendation:** fix F1 (and ideally F2/F3) and re-submit; the Round-1 defect itself is properly fixed and the scientific conclusions are sound.