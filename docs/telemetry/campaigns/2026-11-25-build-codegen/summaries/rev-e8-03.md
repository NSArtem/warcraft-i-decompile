I'll start by inspecting the commit under review and the scope check.
Fresh-checkout plain `pytest` passes: **30 passed, 0 skipped**. Now the determinism refresh.
All checks complete. Here is the independent Round 3 review.

## 1. Commit/scope inspection

`06235f6` ("resolve rev-e8-02 findings") touches only 5 files: the E8 report, the synthetic manifest, `e8/conftest.py`, `synthetic_corpus.py`, `test_e8.py`. The mandated scope check is empty:

```
git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md   # -> no output
```

The whole branch (`c946f38..06235f6`) adds exactly 12 files, all E8: `docs/research/build-codegen/E8-cu-boundaries.md`, the 4 artifacts under `results/e8/`, and `experiments/build_codegen/e8/*.py` (incl. the new `conftest.py`). No production file, tier, symbol or gate is touched, and `make verify` runs `pytest tests`, so the 30-test E8 suite is outside the repo gate.

## 2. Fresh-checkout zero-skip run (F2/F3) — PASS

`build/e8/` did not exist in this worktree. Plain console-entry-point invocation:

```
pytest -q experiments/build_codegen/e8/test_e8.py
..............................                                    [100%]
30 passed in 173.28s (0:02:53)
```

**0 failed, 0 skipped, 0 xfailed, 0 errors.** The new `e8/conftest.py` is what makes this work: `experiments/` and `experiments/build_codegen/` have no `__init__.py` while `e8/` does, so pytest's prepend import path lands on `experiments/build_codegen` and `experiments.build_codegen.e8` is not importable without the `parents[3]` (repo-root) insertion. The autouse session fixture rebuilt Corpus A and paid the libsig sweep once (`libsig10a.json` appeared at 01:12), then all dependent B1/B2 tests ran instead of skipping.

## 3. Cross-worktree determinism (F1) — PASS

`python3 -m experiments.build_codegen.e8.run_e8 --refresh` (forces `synthetic_corpus.build(force=True)`, `sf_table(force=True)`, `libsig_corpus(refresh=True)`, `setup_corpus(refresh=True)`) left the committed artifacts byte-identical:

```
git diff --exit-code -- docs/research/build-codegen/results/e8/   # RESULTS-DIFF-EMPTY
```

Exactly 4 files, LF-only, no tabs, no absolute/build paths, no timestamps, no `.tmp` leftovers, no new files in the repo root (the only `git status` entry is the environment-supplied `original → …/warcraft-1-decompile/original` symlink, created at session start at 01:10, not by any E8 code; `/original/` in `.gitignore` has a trailing slash so it does not match a symlink — pre-existing review-worktree condition). The report's "Artifact hashes" block matches `sha256sum` exactly (incl. `synthetic_manifest.json` `1d9dead1…`).

**Digest audit — the normalization drops only compiler padding, with hard evidence.** Corpus A layout is `CONST [0x00,0x8d) = 141 B` (128 literal bytes + 13 pad bytes in 6 gaps), `_DATA [0x90,0xb0) = 32 B` verbatim, `_BSS [0xb0,0xc4) = 20 B` zero. Every gap sits exactly on the 4-byte fill between two declared literals (`0x12+17→0x23` gap 1, `0x36+16→0x46` gap 2, `0x54+9→0x53` gap 1, `0x54+9→0x5d` gap 3, `0x60+9→0x69` gap 3, `0x6c+9→0x75` gap 3; 128+13 = 141), and `declared_literals()` finds 11 literals, 9 in `CONST`, `e8 incode`/`e8 mutable text` elsewhere (the latter in `_DATA`, which is never zeroed). Three independent forced builds produce **three distinct raw data objects** (`2271d200…` baseline, `0b3db113…` in-tree refresh, `93f7a6dd…` scratch) and one semantic digest `41771043…`. Direct comparison of two builds' raw data images: they differ at **exactly offsets 93 and 95** — inside the declared gap `[93, 3]` between `"e8 g17 b"` and `"e8 g17 t"` (`72 00 72` vs `63 00 75`, heap residue); the other 194 bytes are identical. So no real data byte is silently dropped, and every literal byte *and its offset* is pinned.

## 4. F4 and artifact/report consistency — PASS

* "112 extents / 111 objects" is correct and demonstrable from the live corpus: `libsig_corpus()` returns 112 `cus`, counters give **111 distinct `(lib, module)`** with `clib3r:cstrt386` contributing **two** extents (`segi 3` BEGTEXT `0x10000`, `segi 1` _TEXT `0x34584`); `intxa386` is one extent, so the sensitivity is 111 extents / 110 objects / 186 pairs = 73+113. Doc and `metrics.json` agree everywhere (`admitted_extents 112`, `pairs 447`, `boundaries 75`, `same_cu 372`; sensitivity `186/73/113/111`).
* "non-self-relative library relocation" matches the implementation: `real_corpus.verify_segment` requires `not f.self_rel` relocations to land on a `war.exe` fixup, and `wc1.omf` documents `self_rel = True for call/jmp rel32` — exactly the parenthetical in the report.
* Corpus A: manifest gives 22 CUs (19 C + 3 asm), 65 functions, 64 labels, 21 boundaries, text 1612 B (`0x10000..0x1064c`), data 196 B — all as written.
* I re-parsed the report's Corpus A table (16 rows) and B1 table (13 rows + `intxa386`-free columns) and compared cell-by-cell with `signal_metrics.csv` / `metrics.sensitivity`: **0 mismatches** (TP/FP/TN/FN/precision/recall/F1/n/unavailable/rubric label).
* `game_exploratory.json`: range `[66736,197198]` = `0x104b0..0x3024e`, 890 pairs, 58 chunks, `signal_fires` and `agreement` counts match the exploratory section exactly, the caveat is the first field, and no ground-truth metric block references it (R4 test present and passing).

## Findings

No Must-Fix, Should-Fix or blocking findings.

Informational / optional (non-blocking, no resolution required):

1. **Info — `test_e8.py::test_data_digest_excludes_only_the_compiler_padding_gaps`**: the per-byte "flip ⇒ digest changes" loop is partly tautological for a hash (any byte that passes into the digest changes it); it really proves "the excluded set is exactly `gaps`", not that the excluded bytes are compiler residue. That second claim is currently supported only by the report prose and the historical observations. A cheap regression guard would be: two forced scratch builds whose raw data images may differ only inside the committed `gaps` (I verified exactly this by hand: diffs at 93/95 only).
2. **Info — session fixture cost**: the autouse `e8_caches` fixture pays the full libsig sweep (~170 s here) even for `-k`/single-test selection on a fresh worktree. Acceptable given the zero-skip requirement; worth noting for local iteration.
3. **Info — `semantic_data()` generality**: any unclaimed run ≥ 4 bytes inside a `CONST` segment raises (fail-loud). Correct and safe for this fixed recipe; it is not a general-purpose normalizer.
4. **Info — `conftest.py` scope**: it inserts only the repo root, so `import wc1` still relies on the dev-shell `PYTHONPATH=$WC1_ROOT/tools` (`flake.nix`). Plain `pytest` therefore works in the documented shell but would not in a bare environment — consistent with existing repo convention, not introduced by this change.

## Verification summary

Scope and the F1–F4 repairs all hold under adversarial re-execution in a pristine worktree: plain `pytest` is green with **30 passed / 0 skipped** (F2, F3); a full `--refresh` reproduces all four committed artifacts byte-for-byte with no stray files, and the semantic data digest is genuinely padding-only — three raw images, one digest, differing bytes confined to the declared `CONST` alignment gap (F1); the report's "112 extents / 111 objects" and "non-self-relative relocation" statements are true of the code and artifacts, and every quantitative claim I could mechanically cross-check (Corpus A table, B1 table, sensitivity column, game exploratory counts, artifact hashes) is consistent with `synthetic_manifest.json`, `metrics.json`, `signal_metrics.csv` and `game_exploratory.json` (F4).

VERDICT: APPROVE