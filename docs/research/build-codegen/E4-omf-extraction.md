# E4 — selective OMF32 extraction of a `VerifiedRegion`

2026-11-26. Contract baseline: `ed21ca38feadcadf7e5ba62feed65430d957a6af`;
branch baseline: `654711eb32f5ef7c84c46e108e5a1435c2011a73` (`research/build-codegen/e4`).
This is an isolated experiment, not a production promotion. The authoritative
machine evidence is [results.json](results/e4/results.json); compiled objects,
slices, link maps and rebuilt executables stay under `build/e4/`.

## Result

**Selective extraction is feasible for the tested subset.** Both real game
slices — `ScoreTickIncome` (`0x24e90`) and `FarmPanelChanged` (`0x28254`) — are
cut out of a whole-TU Watcom 10.0a object and linked back into a complete
Warcraft Build A image that is `IDENTICAL`: zero differing loaded bytes and the
same 8,770 LE fixup source/target records. Each link contains the baseline's
519 T3 functions from 514 C objects plus the extracted slice, i.e. 520
functions from 515 objects.

The controlled cases add an `A -> C` intra-TU `call rel32` across a mismatching
neighbour `B` in both compiled forms (`EXTDEF`+`FIXUPP32` and bare `rel32`
displacement), an E5 Fix B3 `wc1_anchor_*` `CONST` literal, and a 1,500-byte
`LEDATA32` split at 1,022 bytes so a 4-byte off32 field never straddles a chunk
boundary. All four positive cases link to an identical oracle image. All eight
negative controls covering the six RFC §6.2 classes fail closed with the
expected machine-readable reason.

`results.json` is deterministic (two separate runs produce the same SHA-256,
`892d3bee8b872411fe0783a3ebc3a1d4f4cc10a17253e208a4c5b6802e3eb043`), contains
no checkout/temp/mirror path or timestamp, and the runner adds no file to the
repository root. Production files have zero diffs against the branch baseline.

| Positive case | Slice (obj / orig) | Chunks | Build A or oracle | Byte diffs | LE fixups |
| --- | --- | --- | --- | ---: | --- |
| `ScoreTickIncome` | `[0,77)` / `0x24e90+77` | 77 | Build A `IDENTICAL` | 0 | 8770 / 8770 |
| `FarmPanelChanged` | `[0x80,0xC4)` / `0x28254+68` | 68 | Build A `IDENTICAL` | 0 | 8770 / 8770 |
| Controlled `A -> C` + CONST anchor | `[0,18)` of 62 | 18 | oracle `IDENTICAL` | 0 | 1 / 1 |
| Bare `call rel32` (NASM) | `[0,10)` of 33 | 10 | oracle `IDENTICAL` | 0 | 0 / 0 |
| >1024 B `LEDATA` | `[0,1500)` | 1022 + 478 | oracle `IDENTICAL` | 0 | 1 / 1 |

## Architecture

[omf_extract.py](../../../experiments/build_codegen/e4/omf_extract.py) maps

```
(compiled whole-TU object, VerifiedRegion, symbol DB, original program)
    -> (extracted OMF32 object, provenance record)
```

and is fail-closed at every step. The pipeline is:

1. **Parser and input gate.** `read_records` validates every OMF checksum and
   requires a `MODEND`; `LIDATA`, multiple `_TEXT` segments and a partially
   stored `_TEXT` are rejected. `raw_fixups` re-reads the raw stream and
   expands every `THREAD` slot, so each `FIXUPP32` is re-based onto its
   `LEDATA` (record-relative `doff` + `LEDATA` base).
2. **E3 `VerifiedRegion` precondition.** No extraction is planned from an
   unverified candidate. A passed `VerifiedRegion` is used as-is; a failed
   evaluation is re-scanned so the rejection names the concrete defect, and
   only then reported as `not_verified_region`.
3. **Independent closure and target scan.** A linear Capstone decode of
   `[obj_lo, obj_hi)` classifies every direct branch. A branch may leave the
   slice only as a named `rel32` target that the symbol DB independently
   identifies and that the original branch at the mapped address agrees with.
   Outgoing `rel8`, interior targets, unknown/ambiguous identities, unanchored
   nonempty local data, shared tables and absolute text pointers all fail here.
4. **Byte-invariant self-check.** `_check_original_bytes` compares every byte
   of the compiled slice against the original image at `orig_start`, masking
   only `off32` fields wholly inside the slice. A changed opcode, length,
   register operand or non-address immediate is therefore rejected even if a
   stale proof is supplied.
5. **Relocation planning and emission.** PUBDEF/LPUBDEF entries inside the
   slice are rebased by `-obj_lo`; entries outside are dropped. `_TEXT`
   `SEGDEF32` length becomes `hi-lo`. Data is re-emitted as `LEDATA32` chunks
   of at most `CHUNK = 1024` bytes (the 10-bit `FIXUPP32` `doff` limit), and
   `_chunks` pulls a cut back to a field's first byte whenever the nominal
   1,024-byte boundary would fall strictly inside its 4 bytes. Each chunk's
   fixups follow it immediately, encoded self-contained (no `THREAD`
   definition is ever emitted). OMF16 `SEGDEF`/`PUBDEF`/`LEDATA`/`FIXUPP`
   records are widened to their 32-bit forms — a representation change only.
6. **Post-emit invariant.** The produced object is reparsed: `_TEXT` must be
   exactly `text[obj_lo:obj_hi]`, and every non-relocated emitted byte must
   equal the compiled source byte. The provenance record carries the digests,
   chunks, transforms, added externs, dropped records and the invariant flags.

This implements RFC §6.1 *Post-Codegen Symbolic Relocation Equivalence*: only
the representation of sections, symbols and address fields changes; every
changed address field has an independently established source, target and
addend, and the original binary is corroboration only. §6.2 cases 1/2
(intra-TU `call`/`jmp rel32` to a DB-confirmed symbol) are supported; cases
3/4/6 (interior target, outgoing `rel8`, shared jump table) are refused; case 5
(`static`/local helper) is accepted only when it is an independently
discovered original function; cases 7/8 (data) are delegated to E5 Fix B3.
No opcode, instruction length, register operand or non-address immediate is
ever modified and `rel8` is never widened.

The two representations of an intra-TU call are handled separately:

* A compiled `EXTDEF` + self-relative `FIXUPP32` (Watcom) is kept as such,
  after checking that the named target's DB address plus addend equals the
  original branch target (`intra_tu_extdef`).
* A bare unfixed `call rel32` (NASM) is resolved from the module symbol table
  to a unique public/local name, checked against the DB and the original
  branch, then rewritten to inline `0` plus an appended `EXTDEF` and a
  self-relative `FIXUPP32` (`direct_rel32_to_extdef`).

Data dependencies integrate with E5's `omf_b3`: `extract` only accepts local
data segments listed in `anchored_segments`, then `apply_data_plan` runs E5's
own E0-based `verify_data` before `rewrite`. Whole-segment `CONST` anchors and
per-symbol literals are therefore reuse, not a second implementation. Mutable
data without a proven base and a mis-anchored plan both fail closed.

### THREAD and record-width scope

FIXUPP `THREAD` definitions (frame and target slots) are expanded during the
raw parse, and the emitted object contains no THREAD subrecord or use;
self-contained re-encoding is round-trip tested for both slots, all frame
methods, explicit/absent displacements and truncated/undefined cases. The
corpus used by the end-to-end cases emits no THREAD (Watcom 10.0a with these
flags and NASM with `-O0 -f obj` both write self-contained FIXUPP), so THREAD
expansion is proven at record level here and end-to-end in E5. OMF16→OMF32
widening is exercised end-to-end by the NASM cases, whose source objects
contain `SEGDEF16`/`PUBDEF16`/`LEDATA16` and whose slices contain only 32-bit
forms.

## Positive case 1 — `ScoreTickIncome` (`0x24e90`)

Source: `experiments/build_codegen/e3/fixtures/score_reference.c`,
`-s -ot -ol -4r -zp2`. The compiled `_TEXT` is 192 bytes and contains the
mismatching `RankName` and `ScoreSetPage` bodies; E3 verifies
`[0,77) <-> 0x24e90..0x24edd` as `REGION_MATCH` (`ScoreTickIncome_` `MATCH`,
evidence `fc0cb3be…`). The 77-byte slice has 53 non-relocated bytes and six
off32 data relocations at object offsets 7, 13, 35, 47, 62, 69
(`_score_rate`, `_game_mode_dword_low`, `_player_score`, `_score_cap`,
`_player_score`, `_score_pool`). `RankName_` and `ScoreSetPage_` publics and
the six out-of-slice fixups are dropped. No data segment is anchored, because
all six targets are canonical externals.

| Digest | Value |
| --- | --- |
| compiled slice SHA-256 | `6e6b8bc683a4cabde6feba4751e6ff7cbf824af6ae7d3dafe26a0ebdd862ef8f` |
| source object loadable SHA-256 | `9bcbedb24fcf762ff6251be860a3e8d6870599295d922d18fa0562e168eeebe6` |
| extracted object loadable SHA-256 | `057b4f56b9dc88caa53d42d1052abed7301c5e84c428a4a7e6fc7477b4774861` |
| extracted object size | 787 bytes |

Linked as `war_score.exe` with the other 514 baseline objects: `IDENTICAL`,
0 byte diffs, 8,770 / 8,770 LE fixups, 0 only-original / 0 only-linked,
520 C functions from 515 objects.

## Positive case 2 — `FarmPanelChanged` (`0x28254`)

Source: `src/status/panel_state_reference.c`, `-s -ot -oa -ol -4r -zp2`.
`FarmPanelChanged` is the second function of a 196-byte `_TEXT`; the sibling
`UnitPanelStateChanged` (`0x281f4`) mismatches in 61 bytes. E3 verifies
`[0x80,0xC4) <-> 0x28254..0x28298` (`REGION_MATCH`, evidence `23e0d0d6…`).
The 68-byte slice has 44 non-relocated bytes, five external data references
(`_player_active_men`, `_player_summoned`, `_status_men_used`,
`_status_men_grown`, `_player_food`) at 6, 14, 24, 41, 48, and one intra-TU
call to the sibling at object offset 62 (`EXTDEF` + self-relative `FIXUPP32`,
DB address `0x281f4`, kept because the named symbol and original branch agree).
The sibling's public and the seven out-of-slice fixups are dropped.

| Digest | Value |
| --- | --- |
| compiled slice SHA-256 | `d39187a5b15dac2e1a559c78fde4f4a8bbc906309c6ee3b89f8ab73be08de00a` |
| source object loadable SHA-256 | `2992d2a839750fe99064c8cad45b9f15df55736190d207e4a404c79af78a1075` |
| extracted object loadable SHA-256 | `5c4d7f4d991d03688039a339ecfdf366ba0e3bcfbe277e7299b5b7bcb883bf0b` |
| extracted object size | 794 bytes |

Linked as `war_farm.exe`: `IDENTICAL`, 0 byte diffs, 8,770 / 8,770 LE fixups,
0 / 0, 520 functions from 515 objects.

## Positive case 3 — controlled `A -> C` across `B` and an E5 anchor

`fixtures/controlled_tu.c` is compiled with the original Watcom 10.0a
(`-s -ot -ol -4r -zp2`) into a real 62-byte `[A, B, C]` TU: `E4_A_ [0,18)`,
`E4_B_ [32,36)`, `E4_C_ [48,62)`, plus a 17-byte anonymous `CONST` literal.
E3 verifies `E4_A_` at `0x10000`; extraction keeps the cross-neighbour call at
slice offset 2 as `EXTDEF E4_C_` + self-relative `FIXUPP32` (target
`0x10030`), and the `CONST` reference at slice offset 10 as a segment target.
`anchored_segments={2}`, `apply_data_plan -> {2: 0x20000}` rewrites the local
data reference into `wc1_anchor_20000` (E5 Fix B3, `whole_segment`), the
`CONST` object is emptied, and the rebuilt executable (extracted `A` + a
remainder object providing `B`, `C` and the anchor + runtime) is `IDENTICAL`
to the untouched-TU oracle. Slice externs are exactly `E4_C_` and
`wc1_anchor_20000`; fixups are `[2, self_rel, ext, E4_C_]` and
`[10, absolute, ext, wc1_anchor_20000]`.

| Digest | Value |
| --- | --- |
| compiled slice SHA-256 | `82e1267c8d45569224230deb19239ae6c0503bd20b75dbd850b1cea824ce1c51` |
| source object loadable SHA-256 | `02f46587168d060a4d02d71d49f27287e2bd956e634cc6f1498b31550bff5bf7` |
| extracted object loadable SHA-256 | `285375251640dd583b4eaa9ffa12ac88fee4cd48ae7a140a3395e8a44ab4430c` |

`fixtures/direct_call.asm` (NASM `-O0 -f obj`) covers the other compiled form:
a 40-byte TU whose `E4_A` call at offset 4 is a bare `rel32` with inline
displacement 24 (`E4_C` is at object offset 32). The extractor adds
`EXTDEF E4_C`, zeroes the field and emits a self-relative `FIXUPP32`; the
10-byte slice `55 89 e5 e8 00 00 00 00 5d c3` links `IDENTICAL` to its oracle.
The same object also exercises OMF16→32 widening.

## Positive case 4 — multi-chunk `LEDATA32`

A 1,500-byte synthetic function has one `off32` field at object offset 1,022 —
exactly the 1,024-byte boundary. The extractor cuts `LEDATA32` at 1,022 so the
field starts the second chunk (`field_offset - chunk offset = 0`, well inside
the 10-bit `doff`), re-attaching the fixup to that chunk. Chunks are
`(0,1022)` and `(1022,478)`; 1,496 bytes are non-relocated. `wlink` links the
slice and its provider into an image `IDENTICAL` to the oracle (1 / 1 LE
fixups). The emitted object's loadable digest is
`04209a7956cc741b4588a6fbd955b99399573755d3b33f32e64069b1e52433ad`.

## Why `DialogHighlightOff` (`0x16d48`) is N1b, not a positive case

E3 already refuted standalone extraction for the folded dialog-highlight pair.
E4 confirms it as a real fail-closed control. Under `-s -os -ol -4r -zp2`
Watcom emits `DialogHighlightOn_` and `DialogHighlightOff_` at the *same*
object offset `0x5F`; `evaluate_module` therefore builds 17-byte candidates
`[0x5F,0x70)` for both, with different claimed originals `0x16d34` and
`0x16d48`. Both fail `RegionMatch` (findings `byte_mismatch`,
`public_layout_mismatch`, `relative_target_mismatch`). The compiled slice
contains `66 83 3d 00 00 00 00 00` (`cmp word [0],0`) followed by `74 f5` at
object offset `0x67` (field `0x68`); its target is object offset `0x5E`, the
single `ret` that is `DialogItemHitTest`'s epilogue, one byte before the slice
start. The original `rel8` at the mapped field similarly jumps to the shared
epilogue `0x16d31`.

OMF has no 8-bit external relocation, widening `rel8` to `rel32` is forbidden
by RFC §6.1, and extending the region to include the target would pull in the
non-matching folded neighbour. E4's independent scan reports
`outgoing_rel8` for both entries before `not_verified_region` could be
returned; the recorded evidence keeps the candidate extents, the E3 verdict
and the raw `rel8` tuple `[104, 94, 93489]`. This is the same limitation RFC
§6.4 separates from Fix B2, not a contradiction of it.

## Negative controls

`run_e4.negatives` exercises the six required classes; N1 is checked for both
folded entries and N4 for an unproven and a deliberately mis-anchored plan.

| Control | RFC §6.2 class | Reason code | Message / evidence |
| --- | --- | --- | --- |
| N1_on | outgoing `rel8` | `outgoing_rel8` | `outgoing rel8 cannot be relocated or widened`; candidate `[0x5f,0x70)` at `0x16d34` |
| **N1_off (`0x16d48`)** | outgoing `rel8` | `outgoing_rel8` | same; `rel8` `[104, 94, 0x16d31]`, E3 `MISMATCH` |
| N2 | interior target | `interior_target` | `unfixed branch target has no module symbol`; original target `0x10011` = neighbour+1 |
| N3 | ambiguous/unknown identity | `ambiguous_symbol` | `local code symbol has no database entry`; `UnitPanelStateChanged_` removed from the DB, never inferred from `war.exe` at `0x281f4` |
| N4 | unproven mutable layout | `data_layout_mismatch` | `nonempty local data segment has no independently proven base` |
| N4b | mis-anchored mutable layout | `data_layout_mismatch` | E5/E0 `_DATA` check: `image_extent` — the 8-byte object at `0x50004` leaves its original image object |
| N5 | incorrect relocation target | `relocation_target_mismatch` | `external relocation disagrees with the original`; declared `_score_pool` (`0x5a0ce`) vs original `_score_rate` (`0x5a0cc`) |
| N6 | incomplete closure | `incomplete_closure` | `absolute or relative text reference leaves the slice`; table at object `0x10`, slice `[0,0x10)`, E3 findings `outgoing_text_pointer` / `unproven_indirect_jump` |

A byte-invariant control additionally mutates a non-address immediate byte in a
synthetic slice while supplying a stale proof: the scan reports
`unsupported_construct` at the exact offset and `extract` refuses, while the
unmutated object extracts with `byte_invariant` true.

## Scope and trust boundary

* The only extraction input is an E3 `VerifiedRegion`. The original program is
  used to *check* mappings (branch targets, loader fixups, image bytes), never
  to name a compiled target. N3 is the executable demonstration.
* Supported: flat DOS/4GW `off32` relocations; intra-slice `seg(_TEXT)`
  references; named intra-TU `rel32` calls; whole-segment/per-symbol data via
  E5 Fix B3; LEDATA32 chunking; THREAD expansion; OMF16 widening.
* Rejected: `LIDATA`; non-`off32` locations; fields crossing the slice or a
  chunk boundary after planning; outgoing `rel8`; interior/unnamed targets;
  code pointers with absolute (non-self-relative) form leaving the slice;
  unanchored or mis-anchored local data; shared tables and unowned statics;
  multiple or partially stored `_TEXT` segments; malformed checksums.
* Not established: arbitrary multi-function TU extraction (the two real cases
  are single-function slices, verified individually), segmented/far-pointer
  or 16-bit frame equivalence, object-order/data-order independence, and
  automatic discovery of symbol identities or data boundaries. The caller must
  supply the DB identities and the E5 anchor plan.
* Everything here is experimental. No production module is imported for
  writing, no `wc1_anchor_*` definition exists outside `build/e4/` and the
  controlled fixture remainder, and no source promotion, ownership DB change,
  goal/gate change or `make verify` run is part of E4. `git diff` against
  `654711eb` over `tools/ src/ analysis/ tests/ asm/ Makefile flake.nix
  AGENTS.md` is empty.

## Reproduction

Run in the already configured dev shell:

```sh
python3 -m experiments.build_codegen.e4.run_e4
pytest -q experiments/build_codegen/e4/test_e4.py
```

The runner takes about 20 s, compiles and verifies the 514-object Build A
baseline once, and writes only `build/e4/` artifacts plus the deterministic
`docs/research/build-codegen/results/e4/results.json`. The suite takes about
30 s, re-extracts and re-links every positive case (comparing each record with
the committed JSON), re-runs all controls, and asserts that the results file is
byte-identical to a fresh collection and free of absolute paths and timestamps.
17 tests pass.

Watcom 10.0a's Win32 `wcc386` access-violates past its fixed command-line
buffer (E5, rev-e5-01), so every E4 10.0a compile (both real cases, the
controlled TU and every baseline object) goes through E5's short mirror:
`build_e5.compile_10a` runs `wcc10a.py` with `WC1_ROOT` set to
`/tmp/wc1e5-<checkout hash>/repo` and bounds each compiler-facing path to
`COMPILER_PATH_LIMIT = 112` characters, independent of checkout depth. The
runner also uses short sequential baseline names (`b000.obj`) rather than E5's
source-derived names, and the suite asserts the bound for every source, object
and output path the experiment hands the compiler. NASM and `wlink` take the
real paths and have no such limit.
