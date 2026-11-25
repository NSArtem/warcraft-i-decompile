# E3 partial-object matching

Evaluated on 2026-11-25 at baseline `1abb053c112332ec901a8961dc918bdcc25d73c4`.
The prototype is commit `ee17095` on `research/build-codegen/e3`.

## Finding

E3 supports region-scoped matching for the exercised cases. Watcom 10.0a
produced matching regions for `FarmPanelChanged` and `ScoreTickIncome` inside
objects whose sibling functions and whole-object E0 checks failed. The shifted
`CONST` fixture also matched through independently verified literal boundaries.
The negative controls rejected unresolved sibling targets, outgoing short
branches, unproven mutable shifts, and corrupted or wrongly aliased literals.
[Machine-readable results](results/e3/results.json)

The requested standalone `DialogHighlightOff` result is refuted by the
specified object and original executable. The original jumps to a shared
return outside its body, and the compiler folds both highlight symbols onto
one entry. E3 measures matching and records the obligations for extraction.
E4 owns the extraction and linked-image verification.
[RFC §§5–7 and §14](../../architecture/rfc-build-codegen-infrastructure.md)

## Real Watcom 10.0a objects

| Case and flags | Result | Evidence |
| --- | --- | --- |
| Dialog `-s -os -ol -4r -zp2` | All three functions mismatch. `DialogHighlightOff` is blocked by a sibling dependency. | Original `je` at `0x16d50` uses displacement `0xdf` and targets the `ret` at `0x16d31` inside `DialogItemHitTest`. The OMF short branch uses displacement `0xf5` and targets object offset `0x5e`, also outside the slice. Both `DialogHighlightOn_` and `DialogHighlightOff_` are defined at object offset `0x5f`, while their original entries are `0x16d34` and `0x16d48`. |
| Farm `-s -ot -oa -ol -4r -zp2` | `FarmPanelChanged` passes `FunctionMatch` and `RegionMatch`. `UnitPanelStateChanged` mismatches. | OMF range `[0x80, 0xc4)` maps to `[0x28254, 0x28298)`. The call at `0x28291` is followed by restoration of `edx` and a return. Its OMF displacement field at offset `0xbe` already has an EXTDEF self-relative FIXUPP for `UnitPanelStateChanged_`. The original call targets that symbol's independent DB address, `0x281f4`. Extracting Farm preserves that relocation and requires the original-address provider for the sibling. |
| Score baseline `-s -ot -ol -4r -zp2` | `ScoreTickIncome` mismatches by one byte. | LEA's SIB byte at `0x24eb9` is `0x02` in the object and `0x10` in the original. These encodings exchange the base and index registers in the same sum. |
| Score fixture `-s -ot -ol -4r -zp2` | `ScoreTickIncome` passes `FunctionMatch` and standalone `RegionMatch`. `RankName` and `ScoreSetPage` both mismatch in the same object. | The sole source change is `sum = delta + score;`. The matcher retains `[0x24e90, 0x24edd)`, trims three verified alignment bytes and records zero outgoing sibling edges. |

Farm is classified as `proven_standalone_region` because the dependency
already has a symbolic relocation. The direct-rel32 synthetic control
exercises `requires_rel32_extraction`. Its object call targets sibling offset
`0x6`, and the original call targets the same named sibling at its independent
address `0x10008`. The result carries an obligation to replace the displacement
with an EXTDEF and self-relative FIXUPP32 during extraction.
[Real fixture runner](../../../experiments/build_codegen/e3/run_e3.py)

## Data and dependency controls

The shifted-pool fixture supplies two independent layouts. The compiled
sibling's prefix grows from `x\0` to `longer\0`. Its reference implies a pool
base of `0x50000`, while the surviving function's references imply `0x4fffb`.
E0's object-wide check records both anchor conflicts. The proposed local base
cannot cover the full pool because its prefix differs. E3 instead verifies
compiled literal offsets `0x7` and `0xb` against independently declared
original starts `0x50002` and `0x50006`. Both are complete read-only `CONST`
literals, their bytes including NUL agree, each original LE operand targets
the exact independently declared start, and identity is preserved in both
directions. The sibling also has an ordinary code-byte mismatch.
[Synthetic fixture declarations](../../../experiments/build_codegen/e3/fixtures/synthetic.py)

| Control | Candidate outcome |
| --- | --- |
| Shifted `CONST` | `REGION_MATCH` with two `per_symbol_const` dependencies |
| N1 mutable shift without canonical boundaries | `UNSUPPORTED`, required boundaries are missing |
| Mutable shift with canonical named boundary evidence | `REGION_MATCH` with `per_symbol_mutable` |
| N2 exact outgoing `rel8` to mismatching sibling | `FunctionMatch` and a `CONDITIONAL` region with `outgoing_rel8_dependency` |
| N3 wrong original target or missing independent sibling entry | `MISMATCH` with `unproven_sibling_target` |
| N4 literal byte corruption | `MISMATCH` with `symbol_data_mismatch` |
| N4 either side wrongly aliases two equal strings at distinct certified starts | `UNSUPPORTED` with `data_identity_mismatch` |

The regression suite also covers leading and truncated bytes, outgoing
fallthrough, interior branch and data targets, incoming edges from
mismatching siblings, out-of-bounds fixups, references to debug metadata,
and whole-segment pointer fixups. Expanding the short-branch fixture to
include the target yields a closed group once the target body also matches.
[Regression tests](../../../experiments/build_codegen/e3/test_e3.py)

## Proof boundary

E3 reuses E0's bidirectional OMF/LE and ordinary-byte checks. Each candidate
has a fresh set of segment bases. Its retained code relocations seed local
data inference, and pointer fixups inside a whole segment can introduce
additional data dependencies. Whole-segment verification compares the
complete storage extent and checks pointer obligations in both directions.
Mutable whole segments require an independently named storage boundary.
Per-symbol support covers exact pointer-free literal and mutable ranges with
independent boundary evidence supplied by the caller.

The region verifier checks the full retained byte range, including leading
bytes and in-range local entries. Filler trimming requires the discovered
original extent and a relocation-free alignment tail. A direct outgoing
`call` or `jmp rel32` is admitted with a rewrite obligation only after
its object target identifies an unambiguous local entry and its original
target agrees with the independent DB address. Outgoing `rel8`, unresolved
jump-table ownership and unproven fallthrough block the region. Incoming
original edges and diagnostically decoded sibling edges are reported for
later placement analysis. Data boundaries, jump-table discovery and the
parsed OMF representation are inputs to the proof. The synthetic data cases
use independently authored OMF and LE records.
[Partial matcher](../../../experiments/build_codegen/e3/partial_matcher.py)

## Reproduction

Run from the worktree root in the configured environment with the supplied
original executable and Watcom 10.0a installation.

```sh
PYTHONDONTWRITEBYTECODE=1 pytest -q experiments/build_codegen/e3/test_e3.py
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.build_codegen.e3.run_e3
sha256sum docs/research/build-codegen/results/e3/results.json
```

All 24 tests passed. Two fresh runner invocations produced identical JSON
with SHA-256 `98af31c8ef711917704e4e59899f4fc08e57a2db717909be4e1dfb411005a6e1`.
The JSON includes the compiler executable and original game hashes, C source
hashes and exact flags, match findings, region extents, verified obligations,
and dependency evidence. The diff from the baseline is confined to the
experiment and its research artifacts.
