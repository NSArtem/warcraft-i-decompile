# E8 — Original CU boundary evidence validation

Date: 2026-11-25; Corpus B1 repaired 2026-11-26 after independent review
`rev-e8-01`. Branch: `research/build-codegen/e8`. Baseline commit:
`c946f3854c9fa424f4b47e5305655f8d4a9b6d22` (E7 merged). Experiment contract:
[contracts/E8-contract.md](contracts/E8-contract.md). Machine-readable results:
[results/e8/](results/e8/).

Status: experiment complete. The report evaluates **16 signals** (9 split, 7
merge) against three independently labelled corpora, and keeps the exploratory
`war.exe` reading strictly outside every precision/recall number. No production
file, tier, symbol or build gate is changed by this experiment.

## Result

**No proposed signal is simultaneously precise and complete, and the two
heuristics RFC §9.3 treats as the backbone of CU recovery do not survive
independent measurement unchanged.**

* **Only three readings have a logical (proven) direction**, each with a stated
  premise: `shared_epilogue` (6 positives, 0 false positives across Corpora A and
  B1), `shared_const_string_literal` (1 positive, 0 false positives, and no B1
  positive), and `non_16_aligned_start` as a *one-directional* constraint that is
  only valid when the next object requests paragraph alignment.
* **`zero16` is the best split signal but not a boundary proof**: precision
  **0.846** on the synthetic corpus (11/13) and **1.000** on the real library
  corpus (2/2), with recall **0.524** (11/21) and **0.027** (2/75). The B1
  precision rests on only two positives and is therefore not a strong-evidence
  result; it misses every exact-16-multiple boundary. The false positives on A
  are exactly the premise violations the corpus was built to contain
  (hand-written `align 16, db 0` padding inside one NASM object). The two
  earlier B1 false positives came from the phantom `cstrtx32` overlap removed
  by `rev-e8-01`, not from a real zero fill in `war.exe`.
* **The `none16` baseline is unusable as a boundary**: precision **0.800**
  (4/5) on A but **0.174** (4/23) on B1; in the game range there are **66**
  such candidates. It is a candidate generator that needs independent
  confirmation, not evidence. The B1 false positives are overwhelmingly the
  `intxa386` stub table (16 of 19; see the sensitivity table).
* **The private `_DATA`/`_BSS` staircase is refuted as a split signal**: 1 TP
  against 3 FP on A (precision 0.250) and 9 TP against 23 FP on B1 (0.281).
  This meets RFC §14's falsification criterion (“high share of false boundaries
  from the `_DATA`/`_BSS` staircases”). Its continuation direction is only weak
  merge evidence (0.714 on both corpora).
* **Call/reference locality is refuted in both directions as implemented**:
  `call_locality_drop` has recall ≈ 0.95 but precision **0.323** (A) and
  **0.179** (B1); `call_locality_link` has precision 0.912 on B1 but recall
  **0.140** (it cannot separate intra-CU from cross-CU calls; 1 TP/1 FP on A).
  Removing the `intxa386` stub table lifts `call_locality_drop` B1 precision to
  0.519 and `call_locality_link` recall to 0.442, but neither becomes a sound
  boundary rule.
* **Style transition is not an object-level signal**: 3/3 on A and 2/2 on B1
  after corpus repair, but the B1 sample is two positives out of 447 pairs and
  it misses every boundary between CUs compiled in the same style class. A
  style change therefore says something about the function, not reliably about
  the CU. The former B1 false positive was the phantom `cstrtx32` overlap, not
  an observed in-object style change.
* **The zero16 recall gap is quantified**: of 21 labelled A boundaries, 10 are
  missed (4 hidden `none16`, 1 `zero4`, 1 `zero2`, 1 `data16`, 3 unpadded
  non-16-aligned starts); of 75 B1 boundaries, 73 are missed. A partition built
  from `zero16` alone is a subset of the true boundaries by construction.

**Consequence for automation** (within this experiment's evidence): CU recovery
must be a constraint graph in which each edge carries its premise, not a
weighted score over these signals. `zero16`/`zero4`/`zero2` remain candidate
generators with measured precision; `shared_epilogue` is a sound but rare merge
constraint; the staircase, style and call-locality readings may be shown to an
analyst but must not create or remove a boundary automatically.

A corpus-integrity finding matters as much as the signal numbers: the first
version of Corpus B2 produced **23 boundary labels that contradicted Corpus
B1's object identity among 35 overlapping labels**. All 23 involved a function
shorter than the 12-byte identity minimum of `wc1.modules_setup` (which cannot
classify such a function as shared), i.e. they were construction artefacts. The
committed B2 applies that admissibility rule; **8 of 25 labels overlap B1 and all
8 agree**. The episode is reported in full below because it shows why B1, not
B2, is the trustworthy real corpus for precision.

The first version of B1 had the same class of defect in the opposite direction.
It extrapolated one `clib3r`-style function hit to the whole library object
without verifying the rest of the object. `cstrtx3r:cstrtx32`'s lone `__exit_`
hit at 0x34838 actually lies inside `clib3r:cstrt386`'s
`__do_exit_with_msg__`; the extrapolated `cstrtx32` extent
`[0x3464b, 0x348ce)` overlapped the genuine `cstrt386` extent
`[0x34584, 0x3485b)`, and the old set-intersection rule then labelled
0x34850→0x34860 `same_cu` (it is a real object boundary, with 0x34860 outside
every library object). The corrected B1 verifies **every non-relocation byte of
every admitted object's whole CODE segment** against `war.exe`, requires every
*non-self-relative* library relocation (a `call`/`jmp` `rel32` is not one) to
land on a `war.exe` fixup, and removes any overlapping candidate
extent as a contested set. This rejects two objects (`cstrtx32` and `vsprintf`)
and removes the phantom overlap; **112 extents, 447 pairs** remain. The fix
also removed the only B1 false positives of `zero16` and `style_transition`.
The episode is reported in full below because it shows that a single-function
signature hit is not evidence of object identity.

## Corpus construction and R4 independence

Mandatory Correction R4 requires that no signal is scored against boundaries
produced by that signal (or by a sibling heuristic). The three evidence classes
are kept apart by construction, by the code that writes the artifacts, and by
tests that fail if the separation is broken.

### Corpus A — synthetic Watcom 10.0a + `wlink` (recipe ground truth)

* **Toolchain:** the original Watcom C/C++ **10.0a** `wcc386.exe` (through
  `wc1.oldcc`, under Wine) and hand-written **NASM** objects, linked by the
  original **10.0a `wlink system dos4g`** into a real DOS/4GW LE image at
  `build/e8/e8synth.exe` (never committed).
* **Composition:** **22 CUs — 19 C + 3 NASM — 65 functions, 64 adjacent pairs**
  (21 boundaries, 43 same-CU). `_TEXT` is 1,612 bytes (`0x10000..0x1064c`) and
  the data object 196 bytes; the image text hash is
  `365488cc0ee79cf81cc208a7e25924c05466ce50b377efb051106d0f5516172f`
  and a forced rebuild reproduces it byte-identically (pytest).
* **Data digest is padding-normalized (review repair `rev-e8-02` F1).** Watcom
  10.0a `wcc386` leaves the alignment padding it inserts between two `CONST`
  string literals **uninitialized**: the gap bytes are compiler-heap residue
  and differ between builds of the same recipe (`79 00 73`, `20 00 32`,
  `3e 00 26`, `65 00 6e` were all observed between `"e8 g17 b"` and
  `"e8 g17 t"`). The committed manifest therefore does **not** hash the raw
  data object; it records `semantic_data_sha256`, taken over the data image
  with only those gaps zeroed, plus a `data_padding_normalized` census (9
  declared `CONST` literals, 6 gaps / 13 bytes). Every literal byte and every
  literal offset — and every `_DATA` initializer verbatim — is still covered: a
  pytest case perturbs each pad to four different values (same digest) and
  flips every other data byte one at a time (each flips the digest), and a
  rebuild in a second scratch directory reproduces the committed digest.
* **CU membership is a fact of the recipe.** For each CU the builder knows the
  source, flags, object, link order and own segment sizes; `placements()`
  recomputes every object's contribution from its SEGDEF alignment, then
  **verifies every public the linker map lists** against the prediction before
  any corpus record is produced. A mismatch raises and no artifact is written.
* **Designed edge cases actually present** (asserted during the build, counts in
  `synthetic_manifest.json`):

  | Designed case | Actual | Where |
  |---|---:|---|
  | boundaries (all rules) | 21 | 64 pairs |
  | `zero16` boundaries (1..15 zero bytes) | 11 | e.g. 0x10060→0x10080 gap 12, 0x10580→0x105c0 gap 2 |
  | hidden `none16` boundaries (CU `_TEXT` a multiple of 16) | 4 | 0x100f0→0x10100, 0x1010b→0x10110, 0x10484→0x10490, 0x105e0→0x10600 |
  | `zero2` / `zero4` boundaries | 1 / 1 | 0x10436→0x10452 (gap 1), 0x10463→0x10474 (gap 3) |
  | in-code data before a CU's first function (`data16`) | 1 | 0x104b0 (`static const` array in `_TEXT`) |
  | 16-aligned **interior** function start, same CU (`none16` FP) | 1 | 0x10380 inside `g12_epi4` |
  | zero fill **inside** one hand-written object (`zero16`/`zero4` FP) | 2 / 2 | `n3_align16` (0x10490, 0x104a0), `n2_align4` (0x10474, 0x1047c) |
  | codegen styles | 7 | `-ot -ol -4r`, `-ot -ol -5r`, `-ot -ol -3r`, `-os -ol -4r`, `-od -4r`, `-ot -ol -4r -d1+`, `-ot -oa -ol -4r` |
  | adjacent `-4r` and `-5r` OPT CUs | 1 pair | `g8_5r` → `g9_4r` |
  | cross-function shared epilogues | 2 pairs | `g12_epi4`, `g13_epi5` |
  | private strings, intra-CU literal pooling, cross-CU duplicate literal | present | `g14_strings`, `g15_strings2` |
  | cross-CU `CONST`/`_DATA`/`_BSS` pollution | present | `g16_globals`, `g17_uses`, `g18_uses2` |
  | NASM `align=2/4/16` objects beside C objects | 3 | `n1_align2`, `n2_align4`, `n3_align16` |

* **S(f) is measured, not assumed:** each C CU is recompiled under E7's 22 core
  configurations (`c01..c22`); a configuration enters `S(f)` only when the
  object's masked function bytes equal the linked function bytes. Every C
  function contains its own configuration (tested), and the three NASM CUs have
  an empty set (the flag signal does not apply to assembly).
* **Bias statement:** A is deliberately adversarial. Its precision is a
  **lower bound** for natural C code and its false positives are designed
  premise violations, not a population sample.

### Corpus B1 — real `clib3r.lib` / `cstrtx3r.obj` object identity (447 pairs)

* **Source of truth:** `wc1.clib_sig` matches whole library functions from the
  original `original/watcom/10.0a/lib386/dos/clib3r.lib` and the 10.0a startup
  object `cstrtx3r.obj` into `war.exe` at byte or instruction level. A match
  yields the owning library **object** and the function's offset in it; because
  `wlink` lays one object's `_TEXT` down contiguously, `address − offset` is the
  object base and `base + object text size` its end. Two adjacent functions in
  one extent are one CU; two in different extents are different CUs. **No
  padding, style or data-staircase evidence enters the label.**
* **Full-segment admission (review repair `rev-e8-01`).** A single matched
  function is only a candidate. Before an object is admitted, **every
  non-relocation byte of its whole CODE segment** is compared with `war.exe` at
  `[base, base + seglen)`; every non-self-relative library relocation must land
  on a `war.exe` fixup, and no `war.exe` fixup may sit on an unmasked library
  byte. Any candidate failing this check is recorded and rejected, and any two
  admitted extents that overlap are *both* removed as contested (fail closed);
  a pair is never labelled by intersecting overlapping extents. The corpus
  records the rejected candidates in `metrics.json` (`rejected_extents`,
  `rejected_counts`, `extents_rejected`) and has **zero overlapping admitted
  extents** (`overlap_conflicts: 0`).
* **Rejected candidates (2).**
  - `clib3r:vsprintf`, base 0x31bcf: its `mem_putc_` prefix matches, but its
    `vsprintf_` body at +19 differs from `war.exe` in 13 unmasked bytes. The
    object is not in this link in that form; the 67-byte `clib3r:sprintf`
    object at the same base is fully verified and is the admitted owner of that
    address range.
  - `cstrtx3r:cstrtx32`, base 0x3464b: 455 unmasked bytes differ from `war.exe`.
    Its lone `__exit_` hit at 0x34838 lies inside `clib3r:cstrt386`'s
    `__do_exit_with_msg__`, so the extrapolated extent no longer exists in the
    corpus (the phantom overlap with `cstrt386` was the source of the old
    `zero16`/`style_transition` false positives and of the spurious
    0x34850→0x34860 `same_cu` label).
* **Sample:** 885 candidate library units, 191 accepted, **112 admitted
  extents** — 111 distinct library objects, because one object contributes two
  code segments: `clib3r:cstrt386` is admitted both as its `_TEXT` and as its
  `BEGTEXT` extent, and each segment is an independently verified extent (the
  map keys an extent by library, object and segment index) — **484 matched
  functions** out of the 1,710-function production
  partition, **447 labelled adjacent pairs** (75 boundaries, 372 same-CU).
  1,260 pairs are excluded because one function lies outside every admitted
  extent and 2 because non-padding bytes separate the extents. 3 units are
  ambiguous and 14 weak; they are not used. No 10.0a library is missing, no
  object produced conflicting base addresses, and the admitted extents cover
  23,109 bytes.
* **Provenance digests:** `war.exe`
  `1e966220bf09ab007c49c5ea5ebc42eb494f5cf2f74f894d3969b6115df8d8a9`;
  library set digest
  `f136ac763c1eb2b5787f4773a20f47a0fa255de7fff79c868daaeb8cb6f7f323`
  (a digest over every matched 10.0a library file hash).
* **Limit:** B1 covers runtime/startup code, not the game's own C objects. The
  mechanism (one object's code is contiguous and its object identity is known)
  is the same one the game's link used, but the population is library code,
  which is predominantly byte-packed and contains DBG and hand-written objects.
  One admitted object dominates the same-CU population: `clib3r:intxa386`
  (990 bytes, `__int386x_` + `_DoINTR_` with a 256-entry `int NN; ret` stub
  table) contains 259 of the 372 same-CU pairs (69.6% of same-CU, 57.9% of all
  labelled pairs). It is a genuine, fully verified object, but every aggregate
  B1 number is re-reported without it in the sensitivity subsection below.

### Corpus B2 — real `setup.exe` shared/unshared transitions (25 boundary labels)

* `original/install/setup.exe` **is present** (126,962 bytes, sha256
  `8791a3cbbc2311dbf02d03a29674d99659da9ef1ec7e3fdbd8fd1b6a3dbe6ec8`). It is a
  second 32-bit Watcom/DOS4GW program that statically links the same AIL
  library and Watcom runtime objects (docs/subsystems/modules.md).
* **Premise:** under whole-object linking, a function byte-identical in both
  programs belongs to an object that `setup.exe` links whole; therefore a
  same-CU sibling would also appear in `setup.exe`. An adjacent
  (identical, not identical) pair cannot be one CU.
* **Sample:** 328 of 1,710 `war.exe` functions are identical in `setup.exe`
  (689 functions); 38 shared runs of length ≥ 2. The rule yields **25 boundary
  labels, no same-CU labels** — so this corpus measures detection (recall) and
  **precision is undefined by construction** (`precision_measurable: false` in
  every B2 row).
* **Admissibility rule applied (corpus-integrity fix).** `wc1.modules_setup`
  never reports a function shorter than `MIN_LEN = 12` bytes as shared, so a
  short function's “not identical” status says nothing about its object. Pairs
  with a side shorter than that are excluded: **71** candidate transitions
  (of which 51 would have become labels) and 19 isolated-shared transitions are
  dropped in addition to the run-length rule.
* **Why the rule exists — the cross-check that found it.** The unfiltered rule
  produced 76 labels; 35 overlapped B1 and **23 of those contradicted B1**. All
  23 contained a function shorter than 12 bytes. A concrete case: the 5-byte
  function at `0x401bd` (`jmp 0x402c8`) is a jump thunk **inside
  `clib3r:memalloc`** (B1: object base 0x4011a, object offset 0xa3); B2 marked
  it “not identical” only because of the minimum and called 0x401bd→0x401c2 a
  boundary, while B1 knows both are in one object. With the admissibility rule,
  **8 of the 25 remaining labels overlap B1 and 8/8 agree**
  (0x31be2→0x31c12, 0x33b85→0x33b95, 0x33dc2→0x33de1, 0x3cce5→0x3cda8,
  0x3cefc→0x3cf48, 0x40939→0x40948, 0x41338→0x413c7, 0x413c7→0x413d6).
* **Limit:** B2's labels still depend on the production function partition of
  both executables and on byte identity after masking, not on OMF object
  identity. It is a weaker real corpus than B1 and is reported with that caveat;
  its recall numbers must not be read as signal quality independent of label
  quality.

### How R4 separation is enforced

* **A:** `synthetic_manifest.json` labels are generated from CU membership only
  (`_labels_from_membership`, re-derived in `metrics.json`'s determinism block);
  a test replaces every evaluated feature (`ranges`, `S`, `rule`, `gap_kind`,
  `gap_len`) with nonsense and asserts the truth list is unchanged, and another
  asserts the label list equals the recipe-membership list.
* **B1:** a test re-derives each label from the matched extents and asserts that
  `same_cu` labels share an extent and `boundary` labels do not; the evidence
  strings are object identifiers or object-to-object transitions, never padding.
* **B2:** a test asserts every label says “identical”, that no label's evidence
  mentions zero/padding/staircase/style, and that precision is `null` and
  `precision_measurable` is false for every signal.
* **Exploratory:** the game reading is a separate artifact whose first field is
  the `EXPLORATORY` caveat; a test asserts that no ground-truth metrics block
  references `game_exploratory.json`.
* **Serialization:** JSON is `sort_keys=True`, two-space indent, LF; CSV uses an
  explicit LF terminator; a test rejects checkout/build/temporary paths and
  timestamps in all four artifacts.

## Corpus A results

**64 pairs — 21 boundaries, 43 same-CU.** Gap rules over the pairs:
`none` 41, `zero16` 13, `none16` 5, `zero4` 3, `zero2` 1, `data16` 1.

| Signal | Role | TP | FP | TN | FN | Precision | Recall | F1 | n | n/a | Rubric label |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `zero16` | split | 11 | 2 | 41 | 10 | 0.846 | 0.524 | 0.647 | 64 | 0 | weak_ambiguous |
| `zero4` | split | 1 | 2 | 41 | 20 | 0.333 | 0.048 | 0.083 | 64 | 0 | unreliable_noisy |
| `zero2` | split | 1 | 0 | 43 | 20 | 1.000 | 0.048 | 0.091 | 64 | 0 | weak_ambiguous |
| `none16` | split | 4 | 1 | 42 | 17 | 0.800 | 0.190 | 0.308 | 64 | 0 | weak_ambiguous |
| `style_transition` | split | 3 | 0 | 43 | 18 | 1.000 | 0.143 | 0.250 | 64 | 0 | weak_ambiguous |
| `const_window_break` | split | 0 | 0 | 5 | 2 | — | 0.000 | — | 7 | 57 | unknown |
| `data_bss_staircase_break` | split | 1 | 3 | 5 | 2 | 0.250 | 0.333 | 0.286 | 11 | 53 | unreliable_noisy |
| `flag_set_S_disjoint` | split | 3 | 0 | 37 | 14 | 1.000 | 0.176 | 0.300 | 54 | 10 | weak_ambiguous |
| `call_locality_drop` | split | 20 | 42 | 1 | 1 | 0.323 | 0.952 | 0.482 | 64 | 0 | unreliable_noisy |
| `non_16_aligned_start` | merge | 20 | 5 | 16 | 23 | 0.800 | 0.465 | 0.588 | 64 | 0 | weak_ambiguous |
| `shared_epilogue` | merge | 2 | 0 | 21 | 41 | 1.000 | 0.047 | 0.089 | 64 | 0 | weak_ambiguous |
| `shared_const_string_literal` | merge | 1 | 0 | 21 | 42 | 1.000 | 0.023 | 0.045 | 64 | 0 | weak_ambiguous |
| `exclusive_static_data_sharing` | merge | 1 | 1 | 20 | 42 | 0.500 | 0.023 | 0.044 | 64 | 0 | unreliable_noisy |
| `call_locality_link` | merge | 1 | 1 | 20 | 42 | 0.500 | 0.023 | 0.044 | 64 | 0 | unreliable_noisy |
| `const_window_continues` | merge | 5 | 2 | 0 | 0 | 0.714 | 1.000 | 0.833 | 7 | 57 | weak_ambiguous |
| `data_staircase_continues` | merge | 5 | 2 | 1 | 3 | 0.714 | 0.625 | 0.667 | 11 | 53 | weak_ambiguous |

Definitions: for split signals a positive means “boundary here”; for merge
signals a positive means “same CU”. Precision/recall are suppressed (`—`) when
the truth class needed for the ratio was not sampled (the 25 boundary-only B2
labels cannot measure precision; a signal that never fires cannot measure
precision either). `n` is the number of pairs the signal could speak about;
`n/a` counts pairs where it returned “not evaluable”.

### Split signals on A

* **`zero16` (11 TP, 2 FP, 10 FN).** All 11 hits are real CU boundaries with a
  1..15-byte zero gap. The two false positives are `0x10490→0x104a0` and
  `0x104a0→0x104b0`, both **inside** `n3_align16`: NASM `align 16, db 0` writes
  ten zero bytes between functions of one object, indistinguishable from linker
  padding. The missed boundaries are the four exact-16-multiple CUs
  (`g3_exact16→g4_exact16_os` 0x100f0→0x10100, `g4→g5` 0x1010b→0x10110,
  `n2_align4→n3_align16` 0x10484→0x10490, `g18_uses2→g19_helpers`
  0x105e0→0x10600), the narrower `zero4`/`zero2`/`data16` boundaries, and three
  byte-packed boundaries with no gap at all (`g5_os→g6_od` 0x1011a→0x10125,
  `g13_epi5→g14_strings` 0x103d8→0x103f8, `g14_strings→g15_strings2`
  0x10412→0x10429).
* **`zero4` / `zero2`.** `zero4` hits 0x10463→0x10474 (3-byte gap before the
  `align=4` object) but fires twice inside `n2_align4` where NASM `align 4, db 0`
  leaves two zero bytes (0x10474→0x1047c, 0x1047c→0x10484): precision 0.333.
  `zero2` hits 0x10436→0x10452 (1-byte gap) and has no FP in A; both narrow
  signals fire once in 64 pairs.
* **`none16` (4 TP, 1 FP).** The four hidden boundaries above are detected;
  the false positive is the designed 16-aligned interior start at 0x10380
  inside `g12_epi4`. It also “detects” a boundary at every exact-16-multiple CU,
  which is why its recall (0.19) is better than `zero16`'s but its precision is
  not a boundary estimate.
* **`style_transition` (3 TP, 0 FP).** Hits `g5_os→g6_od` (0x1011a, OPT→OD),
  `g6_od→g7_dbg` (0x10195, OD→DBG) and `g7_dbg→g8_5r` (0x10230, DBG→OPT). It
  misses the many boundaries between CUs compiled with the *same* style class
  (e.g. `g1_basic→g2_basic`, both OPT) — the signal describes function
  appearance, not object ownership.
* **`const_window_break` / `const_window_continues`.** Only 7 of 64 pairs have
  both functions referencing `CONST` (57 not evaluable). The break never fires
  on a boundary (0 TP, 2 boundaries missed) while the continuation direction is
  the informative one: 5 TP and 2 FP. The FPs are real boundaries where the
  same literal text is duplicated in two objects — `g14_tail→g15_a`
  (0x10412→0x10429, both reference “e8 shared literal” at different addresses)
  and `g17_tail→g18_a` (0x10580→0x105c0) — so a continuing window is not proof
  of one CU.
* **`data_bss_staircase_break` (1 TP, 3 FP).** Three designed inversions inside
  one CU (`g17_uses` at 0x10530→0x10550 and 0x10550→0x10580, `g18_uses2` at
  0x105c0→0x105e0 after a `_BSS` reference follows a `_DATA` one) versus one
  true boundary with an inversion (0x10580→0x105c0). The failing pairs are the
  ordinary case where two functions of one CU touch a global first and a string
  later.
* **`flag_set_S_disjoint` (3 TP, 0 FP, 14 FN).** The three disjoint pairs are
  exactly the three style boundaries above; the OD CU's `S` is `{c20}` while
  its neighbours have broad sets. Ten pairs are not evaluable because the NASM
  CUs have empty `S`. This is a diagnostic (RFC §9.3: never proof of a new
  file), and it fires too rarely to partition anything.
* **`call_locality_drop` (20 TP, 42 FP, recall 0.952).** It fires on almost
  every pair that does not contain a direct call — including the 42 same-CU
  pairs in `g1_basic`, `g2_basic`, etc. Its only TN is a pair linked by a call;
  its only FN is `g18_tail→e8_ext` (0x105e0→0x10600), where the *next* CU's
  entry is called. It is a no-boundary detector in disguise.

### Merge signals on A

* **`non_16_aligned_start` (20 TP, 5 FP on merge claims).** It correctly says
  “same CU” for 20 of 43 same-CU pairs whose second function is not 16-aligned;
  it fails on the 23 same-CU pairs where the next function is 16-aligned
  (OPT `-4r` aligns functions, e.g. 0x10000→0x10030, 0x10030→0x10040). The five
  false merge claims are all boundaries whose next object is byte/word packed:
  `g5_os→g6_od` (0x1011a→0x10125), `g13_epi5→g14_strings` (0x103d8→0x103f8),
  `g14_strings→g15_strings2` (0x10412→0x10429), plus the two `-os` starts in
  that sequence. The premise (“a paragraph-aligned object cannot start
  non-16-aligned”) is true; what fails is assuming the next object is
  paragraph-aligned.
* **`shared_epilogue` (2 TP, 0 FP, recall 0.047).** The detector finds the
  cross-function exit blocks in `g12_epi4` and `g13_epi5`: `g12_b` branches
  `je 0x1036c` into `g12_a`'s `xor eax,eax; ret` exit block, and `g13_b`
  branches `je 0x103bc` into `g13_a`'s; the adjacent a→b pair is recognised from
  either direction. Two limitations are visible: `g12_c` and `g13_c` share the
  same exit block but the pair b→c is not adjacent to the block's owner, so it
  is missed; and functions ending in a tail `jmp` have no exit block of their
  own, so they cannot be the merge target. The signal is sound when it fires and
  much too sparse to be the only merge evidence.
* **`shared_const_string_literal` (1 TP, 0 FP).** `g14_a` and `g14_b` both
  reference the pooled literal “e8 shared literal” at one address; every other
  same-CU pair either has no private literal or is not both-referencing. The
  designed cross-CU duplicate (`g14_tail`/`g15_a`, same text, different address)
  does not create a false positive, which is the point: this build does not pool
  identical literals across objects.
* **`exclusive_static_data_sharing` (1 TP, 1 FP).** The TP is `g7_a→g7_b`
  sharing `e8_g7_state` inside `g7_dbg`. The FP is the designed cross-CU pair
  `g17_tail→g18_a`, the only two readers of the global `e8_pair_flag`: a global
  is shared across CUs by definition, so exclusivity is not decisive.
* **`call_locality_link` (1 TP, 1 FP).** The TP is `g17_a→g17_b` (same CU,
  `g17_b` calls `g17_a`); the FP is `g18_tail→e8_ext` (a boundary, `g18_tail`
  calls the next CU's entry). Calls are equally frequent across a boundary.
* **`const_window_continues` / `data_staircase_continues` (5/2 and 5/2/1/3).**
  These are the complementary merge readings of the window/staircase signals.
  Both reach precision 0.714, limited by the duplicated-literal and
  global-inversion cases above.

## Corpus B results

### B1 — real library object identity

**447 pairs — 75 boundaries, 372 same-CU.** Gap rules: `none` 416, `none16` 23,
`zero16` 2, `zero4` 3, `zero2` 3.

| Signal | Role | TP | FP | TN | FN | Precision | Recall | F1 | n | n/a | Rubric label |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `zero16` | split | 2 | 0 | 372 | 73 | 1.000 | 0.027 | 0.052 | 447 | 0 | weak_ambiguous |
| `zero4` | split | 3 | 0 | 372 | 72 | 1.000 | 0.040 | 0.077 | 447 | 0 | weak_ambiguous |
| `zero2` | split | 3 | 0 | 372 | 72 | 1.000 | 0.040 | 0.077 | 447 | 0 | weak_ambiguous |
| `none16` | split | 4 | 19 | 353 | 71 | 0.174 | 0.053 | 0.082 | 447 | 0 | unreliable_noisy |
| `style_transition` | split | 2 | 0 | 372 | 73 | 1.000 | 0.027 | 0.052 | 447 | 0 | weak_ambiguous |
| `const_window_break` | split | 0 | 0 | 0 | 0 | — | — | — | 0 | 447 | unknown |
| `data_bss_staircase_break` | split | 9 | 23 | 10 | 4 | 0.281 | 0.692 | 0.400 | 46 | 401 | unreliable_noisy |
| `flag_set_S_disjoint` | split | 0 | 0 | 0 | 0 | — | — | — | 0 | 447 | unknown |
| `call_locality_drop` | split | 70 | 320 | 52 | 5 | 0.179 | 0.933 | 0.301 | 447 | 0 | unreliable_noisy |
| `non_16_aligned_start` | merge | 353 | 69 | 6 | 19 | 0.836 | 0.949 | 0.889 | 447 | 0 | weak_ambiguous |
| `shared_epilogue` | merge | 4 | 0 | 75 | 368 | 1.000 | 0.011 | 0.021 | 447 | 0 | weak_ambiguous |
| `shared_const_string_literal` | merge | 0 | 0 | 75 | 372 | — | 0.000 | — | 447 | 0 | unknown |
| `exclusive_static_data_sharing` | merge | 10 | 1 | 74 | 362 | 0.909 | 0.027 | 0.052 | 447 | 0 | weak_ambiguous |
| `call_locality_link` | merge | 52 | 5 | 70 | 320 | 0.912 | 0.140 | 0.242 | 447 | 0 | weak_ambiguous |
| `const_window_continues` | merge | 0 | 0 | 0 | 0 | — | — | — | 0 | 447 | unknown |
| `data_staircase_continues` | merge | 10 | 4 | 9 | 23 | 0.714 | 0.303 | 0.426 | 46 | 401 | weak_ambiguous |

Observations and concrete examples:

* **`zero16` transfers badly.** Its two true positives are real object
  transitions with padding: `clib3r:initargv→clib3r:abort` (0x3d82d→0x3d920,
  gap 10) and `clib3r:cmain386→clib3r:inirt386` (0x3def0→0x3df40, gap 1). The
  old two false positives (0x34850→0x34860, 0x34860→0x348c0, both "inside
  `cstrtx3r:cstrtx32`") disappeared with the phantom overlap; the corrected B1
  has no zero16 false positive, but only two positives, so the 1.000 precision
  is not strong evidence. 73 of 75 boundaries have no zero gap at all (`none`),
  so recall is 0.027.
* **`zero4`/`zero2` are precise but nearly inert.** `zero4` hits
  `xmsg→chint386` (0x4181e→0x4183c), `enterdb→fpe387` (0x41a81→0x41aa8) and
  `fpeergo→fpeintel` (0x4200a→0x42024); `zero2` hits `cputs→hrder386`
  (0x3cf48→0x3cf5e), `fpe387→fpeinth` (0x41b05→0x41b62) and
  `fpeintel→chk8087` (0x4207c→0x4207e). All are genuine 1-byte padding
  transitions in the 4/2-aligned runtime area, and no FP occurs — but together
  they catch 6 of 75 boundaries.
* **`none16` is not a boundary signal.** It fires 23 times, of which 19 are
  inside one matched object: `fclose` 0x338d7→0x33940, `intxa386`
  0x3b59d→0x3b5a0, `cstrt386` 0x34815→0x34850, etc. Four are true object
  transitions (`strrchr→fputc`, `tolower→intxa386`, `fprtf→initargv`,
  `d_setvec→d_getvec`) — a 17.4% precision. Sixteen of the 19 false positives
  are the `intxa386` stub table (sensitivity: 0.500 on the other objects); this
  is the quantitative basis for `docs/subsystems/modules.md`'s warning that
  `none16` is only a possibility.
* **`style_transition` has no B1 false positive after repair.** Its two true
  positives are `filelen→write` (0x3b144→0x3b181) and `cmain386→inirt386`
  (0x3def0→0x3df40). The former false positive 0x34850→0x34860 was the phantom
  `cstrtx32` overlap, not an observed in-object style change. The signal still
  misses every boundary between objects compiled in the same style class, so
  2/2 is a small-sample result, not a boundary rule.
* **The staircase is refuted here too.** 23 false split claims versus 9 true
  ones. Examples: `signl` 0x340b1→0x340e5 and 0x340e5→0x3419b (one object,
  inverted `_DATA` references), `hrder386` 0x3cf5e→0x3cf9a. Missed true
  boundaries include `puts→vprintf` (0x3b3f4→0x3b421) and `clock→delay`
  (0x3b8f4→0x3b915). The continuation direction is somewhat better (10 TP/4 FP)
  but only 46 pairs are evaluable.
* **`call_locality_drop` is a no-boundary detector.** 320 of 390 positives are
  same-CU pairs (precision 0.179). For example the three strtol functions
  0x30c98, 0x30dd1, 0x30ddb are all in one object, yet each adjacent pair is
  counted as a boundary; real boundaries whose neighbours call each other
  (`lseek→read`, 0x3ad9d→0x3adde; `fseek→fread`; `fread→fwrite`) are missed.
  `call_locality_link` has the complementary 0.912 precision but catches only 52
  of 372 same-CU pairs (recall 0.140).
* **`non_16_aligned_start` mirrors A.** 353 of 372 same-CU pairs end at a
  non-16-aligned second function (0.836 precision), but 69 of the 75 boundaries
  also start non-16-aligned (all library objects are byte/word packed), so the
  merge claim is wrong at 69 of 75 true boundaries. The failure is not random:
  it is the premise “the next object is paragraph-aligned” failing. The
  precision is inflated by `intxa386`: without that stub table it falls to
  0.618 (110/178), because 243 of the 353 true positives are 3-byte stubs at
  non-16-aligned addresses inside the one `intxa386` object.
* **`shared_epilogue` is sound and rare.** The four positives are
  `clib3r:prtf` 0x3c442→0x3c466, the memalloc thunk 0x401bd→0x401c2,
  0x4052f→0x40602 and 0x41900→0x419bf; no false positive. It finds ~1.1% of
  same-CU pairs.
* **`exclusive_static_data_sharing`** has 10 TP and one FP
  (`nmalloc→nfree`, 0x3ac5c→0x3ad3f: two objects that both touch the heap state),
  so shared private data is not exclusive to a CU when the data is a true global.
* **`shared_const_string_literal` has no positive on B1.** The signal is
  evaluated on all 447 pairs but returns false everywhere: no adjacent matched
  pair has both functions referencing a shared const string inside the
  0x569d0..0x58440 window used as the CONST range. With no positive, its B1
  precision is undefined and recall is 0.0 (`unknown`), which is a coverage
  limit, not evidence that the signal is clean on library code. The
  `const_window_break`/`const_window_continues` rows are stricter: they return
  `None` when either side has no const reference, leaving 0 evaluable samples
  and 447 unavailable. The 401 unavailable staircase pairs are the same
  window/`_DATA` coverage limit: only 46 pairs have both functions referencing
  private data inside the assumed game data object.

#### B1 sensitivity: the `intxa386` stub table

`clib3r:intxa386` is a genuine, fully verified 990-byte object
(`__int386x_` + `_DoINTR_`), but `_DoINTR_` is a table of 256 tiny `int NN; ret`
stubs that the production partition splits into 258 functions. It therefore
contributes 259 of the 372 same-CU pairs. `metrics.json` repeats every metric
with that object removed (`sensitivity.libsig_without_intxa386`: **186 pairs =
73 boundaries + 113 same-CU, 111 extents** = 110 distinct objects, since
`clib3r:cstrt386` still contributes its `_TEXT` and `BEGTEXT` segments; the 259
intxa386 pairs and 2 edge pairs are excluded). Both readings are reported so
the C-runtime pairs are not swamped by one assembly object.

| Signal | Full B1 TP/FP/TN/FN | Full P/R | Without `intxa386` TP/FP/TN/FN | Without P/R |
|---|---|---:|---|---:|
| `zero16` | 2/0/372/73 | 1.000/0.027 | 2/0/113/71 | 1.000/0.027 |
| `zero4` | 3/0/372/72 | 1.000/0.040 | 3/0/113/70 | 1.000/0.041 |
| `zero2` | 3/0/372/72 | 1.000/0.040 | 3/0/113/70 | 1.000/0.041 |
| `none16` | 4/19/353/71 | 0.174/0.053 | 3/3/110/70 | 0.500/0.041 |
| `style_transition` | 2/0/372/73 | 1.000/0.027 | 2/0/113/71 | 1.000/0.027 |
| `data_bss_staircase_break` | 9/23/10/4 | 0.281/0.692 | 9/23/10/4 | 0.281/0.692 |
| `call_locality_drop` | 70/320/52/5 | 0.179/0.933 | 68/63/50/5 | 0.519/0.932 |
| `non_16_aligned_start` | 353/69/6/19 | 0.836/0.949 | 110/68/5/3 | 0.618/0.973 |
| `shared_epilogue` | 4/0/75/368 | 1.000/0.011 | 4/0/73/109 | 1.000/0.035 |
| `shared_const_string_literal` | 0/0/75/372 | —/0.000 | 0/0/73/113 | —/0.000 |
| `exclusive_static_data_sharing` | 10/1/74/362 | 0.909/0.027 | 10/1/72/103 | 0.909/0.088 |
| `call_locality_link` | 52/5/70/320 | 0.912/0.140 | 50/5/68/63 | 0.909/0.442 |
| `data_staircase_continues` | 10/4/9/23 | 0.714/0.303 | 10/4/9/23 | 0.714/0.303 |

The const-window rows (`const_window_break`, `const_window_continues`) and
`flag_set_S_disjoint` remain unevaluable (0 samples) in both runs. The
sensitivity run does not change any qualitative conclusion: `zero16` recall
stays ~0.027, the staircase stays at 0.281 precision, and style_transition still
has only two positives. It does show that the aggregate `non_16_aligned_start`
precision and `call_locality_drop` precision are materially inflated by the
stub table; the report therefore never quotes those aggregate numbers without
the sensitivity qualifier.

### B2 — real `setup.exe` transitions

**25 pairs — 25 boundaries, 0 same-CU.** Gap rules: `none` 15, `none16` 1,
`zero16` 7, `zero4` 1, `zero2` 1.

| Signal | Role | TP | FP | TN | FN | Precision | Recall | F1 | n | n/a | Rubric label |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `zero16` | split | 7 | 0 | 0 | 18 | — | 0.280 | — | 25 | 0 | unknown |
| `zero4` | split | 1 | 0 | 0 | 24 | — | 0.040 | — | 25 | 0 | unknown |
| `zero2` | split | 1 | 0 | 0 | 24 | — | 0.040 | — | 25 | 0 | unknown |
| `none16` | split | 1 | 0 | 0 | 24 | — | 0.040 | — | 25 | 0 | unknown |
| `style_transition` | split | 13 | 0 | 0 | 12 | — | 0.520 | — | 25 | 0 | unknown |
| `const_window_break` | split | 0 | 0 | 0 | 0 | — | — | — | 0 | 25 | unknown |
| `data_bss_staircase_break` | split | 4 | 0 | 0 | 1 | — | 0.800 | — | 5 | 20 | unknown |
| `flag_set_S_disjoint` | split | 0 | 0 | 0 | 0 | — | — | — | 0 | 25 | unknown |
| `call_locality_drop` | split | 24 | 0 | 0 | 1 | — | 0.960 | — | 25 | 0 | unknown |
| `non_16_aligned_start` | merge | 0 | 17 | 8 | 0 | — | — | — | 25 | 0 | unknown |
| `shared_epilogue` | merge | 0 | 0 | 25 | 0 | — | — | — | 25 | 0 | unknown |
| `shared_const_string_literal` | merge | 0 | 0 | 25 | 0 | — | — | — | 25 | 0 | unknown |
| `exclusive_static_data_sharing` | merge | 0 | 0 | 25 | 0 | — | — | — | 25 | 0 | unknown |
| `call_locality_link` | merge | 0 | 1 | 24 | 0 | — | — | — | 25 | 0 | unknown |
| `const_window_continues` | merge | 0 | 0 | 0 | 0 | — | — | — | 0 | 25 | unknown |
| `data_staircase_continues` | merge | 0 | 1 | 4 | 0 | — | — | — | 5 | 20 | unknown |

Precision is not measurable on B2 (no same-CU labels); the table therefore
reports detection only. The `FP` columns are “merge claims at a boundary” and
are shown for completeness, not as precision denominators.

* **`zero16` detects 7 of 25 transitions**, e.g. 0x30b5c→0x30bd0 (end of the
  hand-asm module, gap 7), 0x3419b→0x34260 (gap 3), 0x3b181→0x3b360 (gap 14),
  0x414b1→0x41530 (gap 3). 18 transitions have no zero gap.
* **`style_transition` detects 13 of 25**, but it has only two positives on B1
  (2/2 after the phantom `cstrtx32` overlap was removed); its B2 recall is
  therefore a property of the *transition* set (library → game code often
  changes appearance), not proof that style tracks objects.
* **`non_16_aligned_start` claims “same CU” at 17 of 25 boundaries** (all
  library/shared objects are byte/word aligned), which again shows the premise
  dependence. It is not used for precision anywhere.
* **`shared_epilogue`, `shared_const_string_literal` and
  `exclusive_static_data_sharing` never fire** within these 25 pairs; the
  single `call_locality_link` positive is at a boundary (0x413c7→0x413d6), and
  the single staircase-continuation positive is also at a boundary. Absence of
  a merge signal on a boundary is expected; these are not false negatives of a
  detector when the functions have no such evidence.

## Epistemic classification (RFC §9.2)

The rubric labels in `metrics.json` are a **precision-only summary**
(`strong_evidence` ≥ 0.95 and TP ≥ 5, `weak_ambiguous` 0.60–0.95,
`unreliable_noisy` < 0.60, `unknown` otherwise). They are not the RFC §9.2
status: a proven constraint can have TP < 5 (rare) and a high-precision signal
can still be weak evidence in the RFC sense. The classification below uses the
measured numbers, the stated premise and the corpora's known bias.

| Signal | RFC §9.2 class | Measured support | Stated assumption / basis |
|---|---|---|---|
| `shared_epilogue` | **Proven constraint** | A 2/2, B1 4/4, B2 0/0; 0 FP | Watcom 10.0a `wcc386` emits cross-function exit blocks inside one object and the 10.0a `wlink` performs no link-time tail merging; a branch from one function into the neighbouring function's own exit block therefore places both in one CU. Direction is one-way: same CU does **not** imply a shared epilogue, and the block must belong to the neighbour (b–c sharing a third function's exit is invisible). |
| `shared_const_string_literal` | **Proven constraint (conditional)** | A 1/1, B1 0 positives in 447 evaluable pairs | Identical literals are pooled within one object, while this 10.0a link did **not** coalesce identical literals across objects (`g14_tail`/`g15_a` keep two copies at different addresses). One observed positive pair only; not a practical detector and unverified on the real game's CONST layout. |
| `non_16_aligned_start` | **Proven constraint (one-directional, conditional)** | A 0.800 (20/25), B1 0.836 (353/422), without `intxa386` 0.618 (110/178), B2 17/25 boundaries | A `_TEXT` SEGDEF that requests paragraph (16-byte) alignment cannot place an object start at a non-16-aligned address. The premise fails for byte/word/dword-aligned objects (hand-written asm, `-os`/`-od`, `-5r`/`-3r` CUs, almost all library objects); when applied blindly the measured FP rates above are the premise-failure rate, not a defect of the logical constraint. The B1 precision is materially inflated by the `intxa386` stub table (243 of the 353 true positives); the sensitivity reading is the more representative one for compiler-generated C. |
| `zero16` | **Strong evidence (conditional)** | A 0.846 (11/13), B1 1.000 (2/2, only two positives), B2 recall 0.280 | A 1..15-byte zero gap before a 16-aligned start is linker padding between whole paragraph-aligned objects *provided* no in-object zero fill occurs and the object is not a zero-padded DBG object. The only measured premise violation is NASM `align 16, db 0` on A; the old `cstrtx32` B1 false positives were a corpus artifact (the phantom overlap removed by `rev-e8-01`), not an object in `war.exe`. Within the game's PARA-aligned C range the premise is plausible but not proven. |
| `zero2` | **Weak/Ambiguous heuristic** | A 1 TP/0 FP, B1 3 TP/0 FP; recall 0.048/0.040 | Word-aligned zero gaps are linker padding in the narrow runtime/hand-asm population, but the rule cannot distinguish linker padding from an assembler `align 2` directive; it fires once in 64 pairs and 3 times in 447. |
| `zero4` | **Unreliable/Noisy** | A 1 TP/2 FP (0.333), B1 3 TP/0 FP (recall 0.040) | Same as `zero2` at 4-byte alignment; the A false positives are exactly the NASM `align 4, db 0` pads, so the rule is not sound when an object may contain alignment directives. |
| `none16` | **Unreliable/Noisy** | A 0.800 (4/5), B1 0.174 (4/23), without `intxa386` 0.500 (3/6) | “16-aligned with no gap” is a *possibility*, not evidence: one in six such pairs in B1 is a boundary, and the game range has 66 candidates. Sixteen of B1's 19 false positives are the `intxa386` stub table, so the aggregate number says more about that object than about the rule. It may be used to enumerate candidates, never to assert a boundary. |
| `style_transition` | **Weak/Ambiguous heuristic** | A 1.000 (3/3), B1 1.000 (2/2), B2 recall 0.520 | Codegen style is measured per function by `wc1.codegen_survey.feat`; a change raises the chance of an object change and misses most same-style boundaries. The former B1 false positive (`cstrtx32` OPT→DBG) was the phantom overlap, not an observed in-object change. Useful as a hint or tie-breaker, not as a split proof. |
| `const_window_break` / `const_window_continues` | **Weak/Ambiguous heuristic** | 7 evaluable pairs on A; 0 on B1; break 0 positives; continuation 5 TP/2 FP (0.714) | The string pool is laid out in link order and a window that moves backwards is suspicious, but literal duplication across objects (`g14_tail`/`g15_a`) and non-referencing functions make both directions noisy; the real library objects do not exercise the window at all in B1. |
| `data_bss_staircase_break` | **Unreliable/Noisy** (split) | A 0.250 (1/4), B1 0.281 (9/32) | Private `_DATA`/`_BSS` addresses generally increase within a CU, but globals referenced by several objects invert the chain; the measured false-boundary share meets RFC §14's falsification criterion. Do not split on an inversion. |
| `data_staircase_continues` | **Weak/Ambiguous heuristic** (merge) | A 0.714 (5/7), B1 0.714 (10/14) | A monotone continuation is weak same-CU evidence; it is the better half of this signal family but still misses 37%–70% of same-CU pairs. |
| `flag_set_S_disjoint` | **Weak/Ambiguous heuristic** (diagnostic) | A 1.000 (3/3) but only 3 positives; B1 not evaluable | `S(f)` is E7's observed compatible-configuration set in the *reconstructed TU context*, not the original object's flags. A disjoint pair is at best contradictory evidence requiring one of RFC §12.2's five explanations; the experiment gives no basis for treating it as a boundary proof. |
| `call_locality_drop` | **Unreliable/Noisy** | A 0.323 (recall 0.952), B1 0.179 (recall 0.933), without `intxa386` 0.519 (recall 0.932), B2 recall 0.960 | Most adjacent same-CU functions do not call each other, and cross-CU calls are common; “no call” is the norm, so the signal fires almost everywhere. Removing the stub table improves B1 precision but not to a usable level. It must not be used to split. |
| `call_locality_link` | **Weak/Ambiguous heuristic** (merge) | A 0.500 (1/2), B1 0.912 (52/57), recall 0.140, without `intxa386` 0.909 (50/55), recall 0.442 | A direct call between adjacent functions raises same-CU probability but does not establish it (`g18_tail` calls the next CU's entry; `lseek→read` are separate objects and call each other), and it covers few same-CU pairs. |
| `exclusive_static_data_sharing` | **Weak/Ambiguous heuristic** (merge) | A 0.500 (1/2), B1 0.909 (10/11), recall 0.027, without `intxa386` recall 0.088 | Two functions being the only readers of one data address is suggestive, but a true global is shared across CU boundaries by design (`g17_tail`/`g18_a`; `nmalloc`/`nfree`), and the signal fires on 2.7% of same-CU pairs. |

Summary: **3 proven (2 of them conditional), 1 strong-conditional, 8
weak/ambiguous signal readings (counting the two window directions), 4
unreliable/noisy**. The single most important negative result is that neither of
RFC §9.3's two suggested “strong” structural heuristics (`zero16` and the
`_DATA`/`_BSS` staircase) behaves as a proof: `zero16` is strong only under a
premise the game corpus has not yet verified, and the staircase is refuted at
the measured false-boundary share.

## Exploratory game observations — non-ground truth

**This section is explicitly exploratory.** The game range has no independent
boundary truth; nothing here enters any precision/recall number, and none of it
establishes an original module boundary or source filename. The artifact is
`results/e8/game_exploratory.json` and its first field is the caveat
“EXPLORATORY / INFERRED — no independent ground truth exists for these
addresses; nothing here enters the precision/recall tables.”

* **Range:** `0x104b0..0x3024e` — **891 functions, 890 adjacent pairs, 58
  chunks** from `analysis/modules.toml`. The chunk names are module.toml
  hypotheses (`mod_XXXXX` are placeholders; e.g. the contract's “mod_1f050” is
  named `NETWORK.C` at 0x1f050 in `modules.toml`, a low/medium-confidence
  hypothesis). Named chunks are not established filenames.
* **Signal fires:** `zero16` 56, `none16` 66, `style_transition` 10,
  `const_window_break` 1, `data_bss_staircase_break` 478,
  `flag_set_S_disjoint` 3, `call_locality_drop` 557.
* **Agreement over the 890 pairs:** no signal 714; padding only 118; padding
  and style agree 3; style only 7; merge evidence only 47; **padding vs merge
  conflict 1**. Independent overlays: 731 pairs carry a
  `non_16_aligned_start` merge claim and 3 have disjoint E7 `S(f)` sets.
  The 129 pairs collected in the per-chunk “padding” column are 118 + 3 + 1 + 7
  (the column also lists style-only pairs).
* **Interpretation of the overlays.** 731/890 (82%) adjacent pairs begin at a
  non-16-aligned address; at B1's measured merge precision (0.836) a naive
  application would claim “same CU” for almost every pair and be wrong at
  ~69/75 true boundaries in that corpus. The game C range is PARA-aligned as a
  whole, so the premise is more plausible here than in B1, but E8 provides no
  independent check of the premise inside the game range. Likewise the 3
  disjoint `S(f)` pairs are diagnostics only; `S(f)` is E7's reconstructed-TU
  measurement, not an original-flag property.

### Chunks with the most padding candidates

All 58 chunks are in the JSON; this table shows every chunk with at least three
padding candidates plus the highlighted smaller chunks (129 candidates in
total). `zero16`/`none16`/`data16` are rule counts over the chunk's pairs.

| Chunk (modules.toml) | Start | Funcs | Pairs | zero16 | none16 | data16 | Padding candidates | Functions with S(f) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `mod_104b0` | 0x104b0 | 14 | 13 | 0 | 1 | 0 | 1 | 3 |
| `BULLET.C` | 0x119c0 | 19 | 19 | 1 | 2 | 0 | 3 | 0 |
| `CMD.C` | 0x123f0 | 18 | 18 | 1 | 3 | 0 | 4 | 11 |
| `mod_13270` | 0x13270 | 11 | 11 | 1 | 2 | 0 | 3 | 0 |
| `mod_13f60` | 0x13f60 | 68 | 68 | 1 | 1 | 1 | 2 | 48 |
| `mod_16390` | 0x16390 | 54 | 54 | 1 | 3 | 2 | 6 | 25 |
| `flic_decode` | 0x19020 | 11 | 11 | 1 | 2 | 0 | 3 | 9 |
| `GAMEDLG.C` | 0x1a3c0 | 21 | 21 | 1 | 1 | 1 | 4 | 16 |
| `mod_1c020` | 0x1c020 | 10 | 10 | 1 | 1 | 0 | 3 | 6 |
| `INIT.C` | 0x1d2a0 | 16 | 16 | 1 | 2 | 0 | 3 | 14 |
| `mod_1dca0` | 0x1dca0 | 7 | 7 | 1 | 2 | 0 | 3 | 7 |
| `mod_1e380` | 0x1e380 | 9 | 9 | 1 | 2 | 0 | 3 | 2 |
| `mod_1eba0` | 0x1eba0 | 9 | 9 | 1 | 1 | 0 | 2 | 6 |
| `NETWORK.C` | 0x1f050 | 31 | 31 | 1 | 2 | 0 | 3 | 7 |
| `PLAYFLIC.C` | 0x22c50 | 46 | 46 | 1 | 7 | 0 | 8 | 26 |
| `SCORE.C` | 0x24e50 | 20 | 20 | 1 | 2 | 0 | 3 | 10 |
| `mod_25ba0` | 0x25ba0 | 11 | 11 | 1 | 2 | 0 | 3 | 4 |
| `SND.C` | 0x26320 | 15 | 15 | 1 | 2 | 0 | 3 | 11 |
| `mod_269f0` | 0x269f0 | 23 | 23 | 1 | 1 | 0 | 3 | 18 |
| `SPELL.C` | 0x27670 | 11 | 11 | 1 | 2 | 0 | 3 | 6 |
| `STATUS.C` | 0x27b20 | 81 | 81 | 1 | 6 | 1 | 7 | 59 |
| `mod_295d0` | 0x295d0 | 29 | 29 | 1 | 4 | 0 | 5 | 5 |
| `mod_2b8e0` | 0x2b8e0 | 18 | 18 | 1 | 2 | 1 | 3 | 8 |
| `mod_2efd0` | 0x2efd0 | 26 | 26 | 1 | 1 | 0 | 3 | 8 |

Two structural observations, both exploratory:

1. **Each chunk has exactly one `zero16` at its own start** (the module.toml
   start is itself a zero16 boundary), and almost no `zero16` inside — 56
   `zero16` fires among 890 pairs. This is consistent with the production
   partition: `zero16` defines the chunks, so it cannot also test them. Only the
   interior candidates are informative, and they are `none16`/`data16`.
2. **`none16` candidates are the only interior split evidence** in most chunks.
   There are **66** in the game range. With B1's measured 0.174 precision, a
   naive acceptance would add roughly 54 false boundaries; with A's
   0.800 (adversarial, hand-written exceptions only) it would still add about
   13. Neither justifies an automatic split.

### Candidate splits inside the large chunks

The following are the recorded candidates; “p” = padding rule, “m” = merge
signals present (`non_16_aligned_start`, shared epilogue/literal/private data,
call link), “S” = E7 S(f) disjoint. **None is a finding.**

* **`mod_13f60`** (0x13f60..0x16390, 68 functions, 48 with S(f)): the chunk
  start 0x13f60 is a `zero16` boundary (gap 3). The only interior padding
  candidates are:
  * `0x162b0` (fn_16278→fn_162b0): **`none16`** candidate, no merge evidence,
    staircase+call-locality also fire. That is 4 functions before the end of the
    chunk.
  * `0x14670` (fn_145d0→fn_14670): **`data16`**, 138 bytes of in-code data
    before the function — the documented in-code-table case, not a boundary.
  * Also merge-only at 0x1498c (data gap 46, shared literal + window
    continuation + call link) and 0x14ca8/0x15ee4/0x15f28/0x15f74 (non-16
    starts, private-data sharing, call links). The padding evidence leaves the
    internal structure of this 68-function chunk essentially unresolved.
* **`mod_16390`** (0x16390..0x1f050, 54 functions): `zero16` at the chunk start
  (gap 7); `none16` candidates at **0x16eb0**, **0x18470**, **0x18890**;
  `data16` at 0x16520 (48 bytes) and 0x182e0 (132 bytes). `0x18470` also has
  S(f) disjoint = false (sets overlap) and a staircase continuation. The only
  in-chunk style transitions in the whole game range are here:
  **0x18b64 (OPT→DBG)** and **0x18fb0 (DBG→OPT)**, consistent with a DBG-appearing
  region between them; because style has only two positives on B1, this is a hint, not
  evidence.
* **`STATUS.C`** at 0x27b20 (81 functions): `zero16` at the start (gap 5);
  six `none16` candidates — **0x27be0**, **0x27d20**, **0x28090**, **0x28580**,
  **0x28600**, **0x29410**; `data16` at 0x28c60 (40 bytes); merge-only at
  0x28298. 0x27be0 and 0x27d20 also have disjoint S(f) (false) and staircase
  breaks; 0x27be0 has no merge evidence at all. Note that 0x28090 is already a
  known partition split point in production (the shared return block at
  0x28074/0x28090/0x28093, see AGENTS.md's open work); the candidate's
  coincidence with that known split is interesting but does not validate the
  padding rule, and E8 does not decide that partition question.
* **`NETWORK.C`** at 0x1f050 (31 functions; the contract's “mod_1f050”):
  `zero16` at the chunk start (gap 8); `none16` candidates at **0x1fb60** and
  **0x20900** (the latter also has a call link); merge-only at 0x200e8 (non-16
  start, private-data sharing) and 0x208d4 (non-16 start, shared literal,
  window continuation, call link). No interior `zero16`.
* **`mod_295d0`** (29 functions): `zero16` at the start (gap 5); `none16` at
  **0x298a0** (also private-data sharing and call link), **0x29f40**,
  **0x2a0e0** (call link), **0x2a270** (call link); merge-only at 0x29644.
* **`PLAYFLIC.C`** at 0x22c50 (46 functions): `zero16` at the start (gap 12);
  seven interior `none16` candidates (0x23030, 0x23070, 0x23170, 0x23330,
  0x233c0, 0x234a0, 0x23650), one with a staircase continuation and two with
  disjoint S(f) (false). This chunk is where a false `none16` split would matter
  most for the PLAYFLIC work, which is why the signal is kept as a candidate
  only.
* **`mod_1eba0`** (9 functions): `zero16` at 0x1eba0 (gap 9) and one `none16` at
  0x1ec60; **`mod_104b0`** (14 functions): one candidate at 0x107a0 (first chunk
  of the range, so its start is not a pair).

No filename or module boundary in this section should be quoted as established.
The full candidate list (66 `none16`, 131 alignment candidates, 176 pairs with
any signal, every chunk's `candidate_addrs`) is in `game_exploratory.json`.

## Threats to validity

1. **Corpus A is small and adversarial.** 21 boundaries are enough to expose
   premise violations but not to estimate natural precision; the FPs are
   designed, so A's precision is a lower bound for ordinary C code. The
   contract's requirement (15–20 CUs, 60–80 functions) is met (22/65).
2. **B1 is library code, not game code.** The object-identity mechanism is the
   same, but clib objects are mostly byte-packed and include DBG and
   hand-written objects, so B1's `zero16` and non-16-alignment numbers are
   pessimistic for the game's PARA-aligned C range; conversely B1's staircase
   and call-locality numbers may reflect library code style. One object,
   `clib3r:intxa386` (a 256-entry `int NN; ret` stub table), supplies 259 of
   the 372 same-CU pairs; the sensitivity table reports every metric without
   it, and the aggregate `non_16_aligned_start`, `none16` and
   `call_locality_drop` numbers should be read with that qualifier. E8 does not
   bridge the library/game gap — it shows the premise dependence explicitly.
3. **B1's `ranges` use the game's data windows** (CONST 0x569d0..0x58440,
   `_DATA` below/above it). The library objects' own CONST references may lie
   outside those windows, which is why the const-window and staircase signals
   have 0/447 and 46/447 samples. Those `unknown` rows are a coverage limit,
   not evidence that the signals are clean on library code.
4. **B2's labels are operational, not OMF identity.** They depend on the
   production partition of both executables and on byte identity after masking.
   The 23 pre-filter contradictions with B1 are the measured size of that
   weakness; the committed 25 labels are the subset where the matcher can speak,
   and their 8/8 agreement with B1 is encouraging but covers only a third of
   them. B2 recall must be read with this caveat.
5. **The production function partition is an input.** Labels are pairs of the
   production partition; a missed function boundary removes a pair, and a
   spurious one adds a pair. In A the partition is generated from the recipe and
   independently verified; in B1/B2 it is the production discovery. The
   `0x401bd` thunk is an example of a production partition subtlety.
   Full-segment verification is deliberately conservative: an object that is
   only partly present (such as `clib3r:vsprintf`, whose shared `mem_putc_`
   prefix matches but whose body does not) is excluded rather than admitted
   with a smaller extent, so B1 loses some real library code to avoid a false
   extent.
6. **Style and zero-gap signals are the production implementations**
   (`wc1.codegen_survey.feat`, `wc1.modules_scan.gap_kind/rule_of`), so the
   numbers describe the tools actually used, not an idealized oracle. A
   different implementation could score differently.
7. **No statistical inference is claimed.** The corpora are finite and
   non-random; the tables are measured counts, not population estimates. The
   rubric thresholds are a reporting convention, not a significance test.
8. **The game section inherits discovery and module.toml assumptions** (chunk
   membership, names, `S(f)` from the reconstructed TU context). It is an
   observation list for an analyst, not a recovered CU map.

## Reproduction

Environment: the Nix dev shell for this worktree (already provides `WC1_ROOT`,
`PYTHONPATH`, `WATCOM` = Watcom 10.0a, `WINEPREFIX`, `TMPDIR`), `nasm`, Wine,
and the user-supplied `original/install/war.exe`, `original/install/setup.exe`
and `original/watcom/10.0a/` tree. Do not run `nix develop` a second time.

```sh
cd /mnt/data/projects/warcraft-1-decompile-wt/e8

# Full run, reusing the caches under build/e8/ (about 1 s when cached):
python3 -m experiments.build_codegen.e8.run_e8

# Full rebuild: recompiles 22 CUs × 22 configurations, re-links with 10.0a
# wlink, re-runs the clib3r/cstrtx3r sweep and re-computes setup.exe identity
# (about 4 min on this machine; artifacts are byte-identical):
python3 -m experiments.build_codegen.e8.run_e8 --refresh

# Tests (28; about 5–10 s with caches):
python3 -m pytest -q experiments/build_codegen/e8/test_e8.py

# Inspect the per-signal rows (CSV is LF, sorted by corpus/signal):
column -s, -t docs/research/build-codegen/results/e8/signal_metrics.csv

# Verify the artifacts are canonical and path-free:
python3 - <<'PY'
import json
from pathlib import Path
for name in ("synthetic_manifest.json", "metrics.json", "game_exploratory.json"):
    p = Path("docs/research/build-codegen/results/e8") / name
    t = p.read_text(encoding="utf-8")
    assert t == json.dumps(json.loads(t), sort_keys=True, indent=2) + "\n"
print("canonical JSON/LF/path-free OK")
PY
```

Temporary products (`src/`, `obj/`, `e8synth.exe`, `e8synth.map`, `sf/`,
caches) all live under `build/e8/`, which is git-ignored; `run_e8` writes
nothing to the repository root. The four committed artifacts are byte-identical
after a full `--refresh` (verified with `sha256sum -c`; see the hashes below).

## Artifacts

| File | Contents |
|---|---|
| `results/e8/synthetic_manifest.json` | Recipe-level corpus A: 22 CUs (id, kind, flags, start/end, per-function nops, source hash), 65 functions, 64 labels with rule/gap/truth, designed-case counts, 22 configuration ids/flags, per-function `S(f)`, image hashes. |
| `results/e8/metrics.json` | Three labelled corpora with every signal's confusion matrix, precision/recall/F1, `sample_size`, `unavailable`, the precision-only rubric, concrete FP/FN examples (up to 3 each), the stated `assumption` for proven signals, provenance digests, determinism checks, the B1 `rejected_extents`/verified-extent metadata, and the `sensitivity.libsig_without_intxa386` repeat of every metric. |
| `results/e8/signal_metrics.csv` | 48 data rows (3 corpora × 16 signals), LF, fixed header, same numbers as `metrics.json` rounded to 6 decimals; `precision`/`recall` empty when not measurable. |
| `results/e8/game_exploratory.json` | The exploratory 0x104b0..0x3024e reading: 891 functions, 890 pairs, 58 chunks, signal fires/agreement, 131 alignment candidates, 66 `none16` candidates, 176 pairs with any signal, per-chunk rule counts and `S(f)` support, and the E7 `S(f)` provenance/caveat. |

Artifact hashes (sha256, after the fully refreshed run):

```
b14067f6eb905e919f187f82691340c454435a7d10cc7bab8c0420d5dcc60f84  game_exploratory.json
7d6717e09c13ba8bc2c85b95022b2782d9ccc302dd91657dc7190ace5d4912a9  metrics.json
287abde3ee88385e3f92c929a44a2d57bcb234aa5c159124207b90d3cc3930c7  signal_metrics.csv
1d9dead13f663d6613d1770ca383054bc7d1c45895ba80f14138845cd62a12c2  synthetic_manifest.json
```

The experiment modifies no file under `tools/`, `src/`, `analysis/`, `tests/`,
`asm/`, `Makefile`, `flake.nix` or `AGENTS.md`; `git diff <baseline>` over those
paths is empty.
