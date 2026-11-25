I'll start by examining the current state of the worktree and the E8 experiment.
Now I understand the issue. Let me implement the full-segment verification in `real_corpus.py`.
Repair complete and committed on `research/build-codegen/e8` as `dc1d028`.

## What changed

**`experiments/build_codegen/e8/real_corpus.py`**
- Added `verify_segment()`: every non-relocation byte of the object's whole CODE segment must match `war.exe` at `[base, base + seglen)`; every non-self-relative library relocation must land on a `war.exe` fixup; no `war.exe` fixup may sit on an unmasked library byte.
- Extents failing that check are rejected and recorded (`rejected_extents`, `rejected_counts`, `extents_rejected`).
- Overlapping verified extents are removed as a contested set (fail closed); labels are never derived by set intersection.
- Removed the `cover`/intersection logic; ownership is now a single `owner[start] -> object` map.

## Corrected Corpus B1

| Metric | Before | After |
|---|---:|---:|
| Admitted extents | 114 | **112** |
| Labelled pairs | 449 | **447** |
| Boundaries / same-CU | 75 / 374 | **75 / 372** |
| Matched functions | 482 | **484** |

- `cstrtx3r:cstrtx32` is **rejected** (455 unmasked bytes differ); `0x34850` remains inside genuine `clib3r:cstrt386`, `0x34860` is outside every admitted extent, so `(0x34850, 0x34860)` is no longer labelled at all — and certainly not `same_cu`.
- `clib3r:vsprintf` is also rejected (its `mem_putc_` prefix matches; 13 body bytes differ).
- **Zero overlapping admitted extents.**
- B1 `zero16` and `style_transition` now have no false positives (their old FPs were the phantom `cstrtx32` pairs). `zero16` is 2 TP / 0 FP with recall 0.027; `style_transition` is 2/2.

## `intxa386`

Verified as a genuine 990-byte object (full masked segment match). It supplies 259 of 372 same-CU pairs (69.6%). `metrics.json` now reports both the full corpus and `sensitivity.libsig_without_intxa386` (186 pairs, 111 extents; 261 excluded pairs: 259 same-CU + 2 edge boundaries). `E8-cu-boundaries.md` includes the full sensitivity table; e.g. `non_16_aligned_start` B1 precision falls 0.836 → 0.618 and `call_locality_drop` rises 0.179 → 0.519 without the stub table.

## Verification

- `pytest -q experiments/build_codegen/e8/test_e8.py`: **28 passed** (4 new regression tests: full-segment verification of every admitted extent, zero overlap, `cstrtx32`/`(0x34850,0x34860)` rejection, `intxa386` sensitivity).
- `python3 -m experiments.build_codegen.e8.run_e8` reruns leave artifacts byte-identical; a full `--refresh` also matched.
- Artifact hashes:
  - `metrics.json` `7d6717e0…4912a9`
  - `signal_metrics.csv` `287abde3…930c7`
  - `game_exploratory.json` `b14067f6…f84`
  - `synthetic_manifest.json` `5034535d…70`
- `git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
- `git status`: only pre-existing untracked `original/`.

Commit: `dc1d028 exp(e8): enforce full-segment byte verification and non-overlap in Corpus B1 libsig ground truth`