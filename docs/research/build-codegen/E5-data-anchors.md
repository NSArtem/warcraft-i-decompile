# E5 — data-anchor decoupling (Fix B3)

2026-11-25. Baseline: `1abb053c112332ec901a8961dc918bdcc25d73c4`.
Branch: `research/build-codegen/e5`. This is an isolated experiment, not a
production promotion. The authoritative machine evidence is
[results.json](results/e5/results.json); generated executables, objects, ASM,
link maps and detailed comparisons remain in `build/e5/`.

## Result

**Fix B3 works for the tested OMF32 off32/LEDATA32 subset.** Nine complete
Warcraft Build A links are `IDENTICAL`: zero differing loaded bytes and exactly
8,770 matching LE fixup source/target object-offset records in each link.
Every link includes the baseline's 519 T3 functions from 514 C objects, plus
`SaveErrorDialog`. The real multi-segment variant replaces the baseline
`DefeatDialog` object with an object containing the same canonical function
and definitions of its canonical globals. Canonical C and production tools
have zero diffs.

| Generated executable | Experiment | Loaded byte diffs | LE fixups A / B | Only A / B |
| --- | --- | ---: | ---: | ---: |
| `war_s1.exe` | Existing T3s + standalone `SaveErrorDialog -os` | 0 | 8770 / 8770 | 0 / 0 |
| `war_native_ot_data.exe` | Experimental explicit `_DATA` arrays, native `-ot` | 0 | 8770 / 8770 | 0 / 0 |
| `war_s2_real_multi.exe` | Real GAMEDLG code + `_DATA`, `CONST`, `_BSS` | 0 | 8770 / 8770 | 0 / 0 |
| `war_s3_thread.exe` | Cross-record F3/T3 definitions on discarded data | 0 | 8770 / 8770 | 0 / 0 |
| `war_s4_flat.exe` | Explicit `FLAT` frame, with THREAD fixture | 0 | 8770 / 8770 | 0 / 0 |
| `war_s4_dgroup.exe` | Explicit `DGROUP` frame, with THREAD fixture | 0 | 8770 / 8770 | 0 / 0 |
| `war_s4_target.exe` | Frame method 5 (Target), with THREAD fixture | 0 | 8770 / 8770 | 0 / 0 |
| `war_s4_external.exe` | Frame method 2 (EXTDEF), with THREAD fixture | 0 | 8770 / 8770 | 0 / 0 |
| `war_per_symbol.exe` | Two independently bounded CONST literal anchors | 0 | 8770 / 8770 | 0 / 0 |

A separate synthetic Watcom 10.0a object with all three nonempty data segments
also links identically under all five modes (preserved frame, FLAT, DGROUP,
Target, EXTDEF). Its oracle is the untouched C object linked with a small
synthetic runtime. It has three LE fixups; it is deliberately reported
separately from the nine full-game comparisons.

## Mechanism and proof boundary

[omf_b3.py](../../../experiments/build_codegen/e5/omf_b3.py) operates on
compiled objects. Before emitting any replacement, it calls E0's actual
`_Checker.check`, checking every ordinary byte, every forward pointer
relocation and every reverse original LE obligation in every anchored data
range. It also checks every rewritten source's original addressing obligation.
Segment bases come from compiled symbol definitions and relocation constraints;
E0 verifies the resulting mapping against the original. The caller remains
responsible for supplying independently justified symbol identities and object
boundaries; this prototype is not an object-boundary discovery algorithm.

For whole-segment mapping, a segment target becomes an appended external
`wc1_anchor_<address>`. The inline addend, displacement presence/value,
location and addressing mode remain unchanged for segment-target rewrites.
Data `SEGDEF32` lengths become zero; data records and their attached fixups
are omitted. Existing public/local definitions of emptied data are removed.
Local data EXTDEF references are converted to the same anchors, accounting
for the independently declared symbol offset. Removed local declarations are
also removed and all surviving external indices are renumbered: wlink demands
resolution even for an unused `LEXTDEF`. External declarations emitted late by
Watcom are hoisted in their original external-index order before data records.

The parser retains F0–F3 and T0–T3 state across every FIXUPP32 record. It parses
records belonging to discarded data too. Every emitted fixup has explicit
frame/target operands: no output depends on an input THREAD definition.
Expansion preserves the P/displacement bit and both short and two-byte OMF
indices. Sixty parameterized controls cover all four slots, frame methods
0/1/2/4/5, segment/group/external target methods, self-relative and absolute
encodings, and absent/zero/nonzero explicit displacements. Rewriting anchored
self-relative data targets is outside the verified subset and is rejected.

The harness reads `wc1.emit` and `asm/wc1.inc`, emits the original data in one
ASM piece, and adds `GLABEL` aliases at verified anchor addresses. It emits no
data cuts in C code order. Original data symbols remain available for existing
C externs. No mutable data is combined by equal contents. Non-loadable Watcom
`$$SYMBOLS`/`$$TYPES` metadata is excluded using E0's exact class/name predicate;
runtime references to excluded segments are rejected.

## Scenario 1: decreasing anchors and SaveErrorDialog

Calling the existing `wc1.build.check_placed_plan` on the actual compiled
objects reproduces exactly:

```text
C objects' data anchors are not in code order
```

The relevant order is `DefeatDialog 0x1ab28 -> CONST 0x56c0c`, then
`SaveErrorDialog 0x1aca8 -> 0x51ea6`. B3 removes that data-order dependency;
`war_s1.exe` retains every other T3 and links both functions in place.

| SaveErrorDialog compilation | Data placement | Second string offset / stride | E0 outcome |
| --- | --- | ---: | --- |
| Canonical source, `-s -os -ol -4r -zp2` | `CONST`, 69 bytes | `0x22` | Region MATCH, full Build A IDENTICAL |
| Canonical source, `-s -ot -ol -4r -zp2` | `CONST`, 71 bytes | `0x24` | MISMATCH: inconsistent pointer target and data bytes |
| Explicit named char arrays, native `-ot` | `_DATA`, 69 bytes | `0x22` | Full Build A IDENTICAL |
| Same arrays + canonical DefeatDialog in one TU, native `-ot` | `_DATA` plus `CONST` | `0x22` | Data-layout probe; not an in-place multi-function match |

The first string occupies `0x22` bytes including NUL. Native `-ot` puts the
next pooled literal on a four-byte boundary in its standalone CONST context,
so its start is `0x24`. The original starts the second string immediately at `0x51ec8`.
`-os` eliminates the intervening two padding bytes. Explicit initialized
character arrays in `_DATA` reproduce the contiguous `0x22` spacing under
native `-ot`, including the multi-function layout probe.

This establishes a viable `_DATA` representation, **not** a claim that adding
a neighbouring function fixes the canonical literal source under `-ot`.
The successful native link uses a clearly identified experimental source
variant and temporary symbol mappings for its two named arrays. The canonical
reference is unchanged, and its standalone `-ot` mismatch is retained as
machine evidence. The multi-function probe is not linked as matching code:
its function order and compiler alignment differ from the original layout.

## Scenario 2: multiple segments

`fixtures/gamedlg_data.c` includes the unchanged canonical `DefeatDialog`
function and defines its existing `net_play_flag` and `game_mode` globals.
Watcom 10.0a emits:

| Segment | Length | Canonical anchor |
| --- | ---: | ---: |
| `CONST` | 33 | `0x56c0c` (defeat message) |
| `_DATA` | 2 | `0x52586` (`net_play_flag`) |
| `_BSS` | 2 | `0x59616` (`game_mode`) |

All three ranges pass E0. Code stays at `0x1ab28`; ASM remains the physical
provider for the data. This is real code-and-global consolidation with one
function, rather than a claim of arbitrary multi-function code extraction.
The synthetic control independently uses a string, initialized counter, and
uninitialized scratch variable, all referenced by compiled C. Its rewritten
object and unified data provider match the untouched-object link in every
frame mode. A further synthetic test rewrites a fixup in **retained `_DATA`**
targeting emptied `CONST`, after checking both ranges through E0.

## Scenario 3: THREAD

A scan of all 514 compiled baseline objects plus the real three-segment
GAMEDLG object found **zero** Watcom THREAD definitions. The link scenario
therefore uses a controlled OMF fixture applied to the real compiled GAMEDLG
and SaveErrorDialog objects; it does not claim native THREAD emission.

The fixture repeats an already verified CONST LEDATA range before the code,
then defines F3 as FLAT and T3 as that CONST segment in its attached FIXUPP32.
Later code FIXUPPs use those threads without redefining them. Dropping the
first range thus exercises the exact cross-record lifetime hazard. B3 expands
the later references explicitly, the emitted objects have zero THREAD
subrecords or uses, and the complete game still has all 8,770 original fixups.
The F0–F3/T0–T3 unit controls also test absent and explicit displacements.

## Scenario 4: frame mechanics

The original 10.0a objects use frame method 1 with **FLAT**, which is group
index 2 in these C objects; DGROUP is group index 1. Group indices are resolved
by name, not hard-coded. Rewritten targets use EXTDEF method 2. We separately
tested:

| Mode | Frame method / datum | Full-game result |
| --- | --- | --- |
| Preserve / explicit FLAT | `1 / GRPDEF FLAT` | IDENTICAL |
| Explicit DGROUP | `1 / GRPDEF DGROUP` | IDENTICAL |
| Target frame | `5 / no datum` | IDENTICAL |
| External frame | `2 / same EXTDEF as target` | IDENTICAL |

For the tested flat DOS/4GW off32 relocations, all resolve to the same LE
target object and offset. For example, SaveErrorDialog's fields at `0x1acb4`
and `0x1acbb` retain `(object 2, offset 0x1ea6)` and
`(object 2, offset 0x1ec8)`. The consolidated DefeatDialog's fields at
`0x1ab2c`, `0x1ab35`, `0x1ab42` retain target offsets `0x9616`, `0x2586`,
`0x6c0c` in object 2. JSON records these original and linked tuples explicitly,
in addition to comparing the complete 8,770-element set. This does not prove
selector, far-pointer or segmented 16-bit frame equivalence.

## Whole-segment versus per-symbol feasibility

**Whole-segment:** supported with E0 verification of the entire segment and
its pointer fields. This is sufficient for the decreasing-anchor and real
three-segment cases.

**Per-symbol:** feasible under wlink. `war_per_symbol.exe` partitions the
verified 69-byte SaveErrorDialog CONST into the two NUL-terminated literal
objects, binds them independently at `0x51ea6` and `0x51ec8`, and makes both
inline addends zero. The link is IDENTICAL. The prototype requires a complete,
nonoverlapping, independently justified partition, includes every terminator,
and rejects changed aliasing or multiple objects collapsed onto one address.
Named mutable mapping additionally requires an exact canonical definition and
explicit canonical size. It does not infer identity from matching bytes.

This experiment does not establish arbitrary string-pool reordering, pooling
across unknown aliases, or remapping structure/array interiors. Uncovered
padding is rejected; standalone `-ot` is not repaired by dropping its padding.

## Negative controls and limitations

* N1 alters one ordinary data byte: E0 reports `byte_mismatch` before rewrite.
* N2 changes a pointer's external target while retaining its inline value:
  E0 reports `relocation_target_mismatch` before rewrite. The positive control
  checks one forward pointer and one reverse LE obligation; a missing pointer
  FIXUPP also fails.
* N3 attempts mutable content merging and an unverified interior-structure
  mapping: both fail closed. Additional controls reject aliased independent
  literals, incomplete partitions, unsupported locations and bad checksums.
* N4 scans every file under `src/`, `analysis/`, `tests/`: zero occurrences of
  `wc1_anchor_`. Generated anchor definitions exist only under `build/e5/`.

The prototype rejects LIDATA rather than trusting unverified expansion or
relocation semantics. It also rejects 16-bit SEGDEF/LEDATA/FIXUPP records,
COMDAT/COMDEF, unsupported target/frame methods, runtime non-off32 locations,
unknown/index-bearing linker comments, and ambiguous retained-source mappings.
Absolute frame-number targets are outside the supported subset. Recognized
non-loadable debug metadata is removed after THREAD state is consumed.
Fixture-only conversion of NASM's narrow length/offset records to OMF32 changes
record representation, not code or data semantics.

No source promotion, ownership DB update, goal/gate change, production build
change, or `make verify` run is part of E5. Production adoption still requires
the RFC's separate review and verification gates.

## Reproduction

Run in the already configured dev shell:

```sh
pytest -q experiments/build_codegen/e5/test_e5.py
python3 -m experiments.build_codegen.e5.run_e5
```

The test command covers the parser controls, fresh compiler/link scenarios,
negative controls and source leak scan. The runner recompiles every baseline
T3 and writes only generated artifacts to `build/e5/` and deterministic machine
results to the designated JSON path. `wc1.compare` checks layouts, entry,
stack, loaded images and the full LE fixup set for each executable. No copied
game image, generated ASM or object is committed.

Watcom 10.0a's Win32 `wcc386` keeps command-line paths in fixed buffers and
access-violates past them (rev-e5-01: a 149-character checkout killed exactly
the two fixture compiles that include
`../../../../src/gamedlg/defeat_dialog.c`). Every E5 10.0a compile therefore
runs in a helper process (`wcc10a.py`) whose `WC1_ROOT` is a deterministic
short symlink to the checkout (`/tmp/wc1e5-<checkout hash>/repo`), with
`build_e5.compiler_path` bounding each compiler-facing path to 112 characters
(the source, the output and `wc1.oldcc`'s own `src/include` and 10.0a `h/`
`-i=` arguments alike). The compiled objects are byte-identical to a compile
from the short checkout, and the complete runner reproduces this `results.json`
from a 166-character symlinked checkout.

Validation: the required pytest command passed **86 tests** with the final
Watcom 10.0a fixture selection. A subsequent fresh runner invocation reproduced
`results.json` byte for byte, SHA-256
`35483f236760c652cf142e90099a6d048f18b2e5e8ace8675993591fb7aa6b11`.
Compiler identities and flags are recorded in the machine evidence for each
experimental object, rather than inferred from successful linking.
