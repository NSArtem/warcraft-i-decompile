# E0 — Matcher soundness and full T3 re-audit

Date: 2026-11-25. Baseline: `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`.
Worktree: `/mnt/data/projects/warcraft-1-decompile-wt/e0`.
Branch: `research/build-codegen/e0`.

## Executive summary

**Scientific verdict: CONFIRMED for the stated E0 control set and baseline.**
The isolated prototype closes all three confirmed matcher gaps in the controls:
leading `_TEXT` bytes, reverse original-to-compiled code obligations, and
relocations in module-local runtime data. After resolving all six findings from
`rev-e0-01` (`REQUEST_CHANGES`), all **55 controls pass**: **16 positive controls
return MATCH**, and **39 negative controls fail closed** (**25 MISMATCH,
14 UNSUPPORTED** at region level). These include all five RFC positives, all
eight original assignment negatives, 23 original boundary controls, and 19
review controls. The pytest suite passes **77/77**, including both entry points'
function-only error exit regressions.

The full dynamic inventory is exactly **519 in-scope T3 functions in 514 C
files**. Every function and every associated closed region returns **MATCH**;
there are **0 MISMATCH, 0 UNSUPPORTED, 0 ERROR**, and no discovered existing T3
false matches. No symbol tier, production implementation, gate, or source file
was changed. Full `make verify` remains the Manager's responsibility under this
experiment contract and was not run here.

This confirms the bounded experiment, not soundness for arbitrary OMF or all
possible compiler output. In particular, the current T3 inventory contains no
leading tables and no module-local pointer fixups. The real leading-table
control and the real-image-derived local pointer controls are essential evidence
for those two gaps; the T3 inventory alone does not exercise them.

## Artifacts and provenance

| Artifact | Contents |
|---|---|
| [matcher_proto.py](../../../experiments/build_codegen/e0/matcher_proto.py) | Importable strengthened matcher; normalized obligations; separate function/region verdicts |
| [controls.py](../../../experiments/build_codegen/e0/controls.py) | Real compiler objects, deliberate mutations, independent synthetic boundaries |
| [test_e0.py](../../../experiments/build_codegen/e0/test_e0.py) | Control outcomes, legacy counterexamples, exhaustive finding checks, saved evidence consistency |
| [reaudit_t3.py](../../../experiments/build_codegen/e0/reaudit_t3.py) | Dynamic discovery, fresh bounded compilation, both matchers, JSON/CSV export |
| [run_e0.py](../../../experiments/build_codegen/e0/run_e0.py) | Complete reproduction entry point |
| [controls.json](results/e0/controls.json) | All 55 outcomes, legacy diagnostics, full E0 findings, fixture provenance |
| [t3_reaudit.json](results/e0/t3_reaudit.json) | All 519 rows, full findings, obligation records, metrics, excluded debug metadata, source/compiler/object provenance |
| [t3_reaudit.csv](results/e0/t3_reaudit.csv) | All 519 rows; findings serialized in full as JSON in each CSV row |

The original executable SHA-256 is
`1e966220bf09ab007c49c5ea5ebc42eb494f5cf2f74f894d3969b6115df8d8a9`.
The prototype SHA-256 used for the saved audit is
`9e2b985a56097bfe526013706072b5a8df1d2516dc58d954914068f75d3233c1`.
The audit records an individual object SHA-256 for every function, together
with its source path, compiler, and exact `match.file_cflags()` string.

The hardened implementation's fresh reproduction produced these result files:

| File | SHA-256 |
|---|---|
| controls.json | `e9330624dd3bb4b4da60665f38efad346f5c68163723e9cadb325368dc33e15b` |
| t3_reaudit.json | `cd8917e15092a5ca5e24f56342de2625114743a5a879b97c0edb17f19fcdd628` |
| t3_reaudit.csv | `b39af1a255831b7fc50c489fa5d981e4d996b6d4acc28b9a7a1d3f4fbb3ac9d6` |

The regenerated CSV is byte-identical to the pre-review CSV: all audit rows and
their findings remain unchanged. The JSON additionally records the new
prototype hash.

No executable or compiled object fixture is committed. Real fixture bytes come
from fresh compilation and the user's original executable at reproduction time.

## Verification contract implemented

The implementation follows [RFC sections 5 and 15](../../architecture/rfc-build-codegen-infrastructure.md)
and the assignment's binding clarifications. Verdicts are mutually exclusive:
`MATCH`, `MISMATCH`, `UNSUPPORTED`, `ERROR`. Findings are unrestricted lists;
each contains `code`, `category`, `offset`, `orig_addr`, `message`, and
`evidence`. Unsupported parsed constructs take precedence over mismatches;
audit execution exceptions are recorded as errors. No diagnostic list is
truncated. Per-function audit findings are the complete union of function and
region findings, with their verification scopes attached.

Every normalized obligation stores `kind`, `src_offset`, `field_size`,
`target`, `addend`, `evaluation_rule`, `requires_static_resolution`, and
`requires_le_fixup`. The JSON also identifies its original/compiled origin and
source segment. Absolute code/data fields require OMF off32 fixups and original
LE off32 fixups at the same field, with equal resolved targets. Relative code
branches use the instruction displacement rule; an external rel32 branch needs
an OMF self-relative fixup, while an exact intra-segment displacement does not.
Internal/external classification uses the final retained `_TEXT` region, so a
branch to a discarded tail byte cannot count as internal. No branch in the
retained region may target the trimmed tail, even with an explicit relocation.
Neither kind of relative branch requires an LE loader fixup. Hardware constants
with neither form of relocation remain ordinary byte comparisons.

`FunctionMatch` covers each public/static function body. `RegionMatch` derives
the original `_TEXT` base from `first_address - first_offset`, requires all
known public/static offsets to agree, and checks the closed contiguous region
including its leading bytes. It also checks all anchored local runtime segments.
Unknown publics, unanchored runtime data, ambiguous overlapping fields,
unsupported relocation locations/targets, self-relative data fixups, unsupported
direct branch encodings, additional nonempty CODE-class segments, and communal
storage fail closed. Every fixup in every non-metadata segment is validated
before extent filtering, including entirely out-of-bounds fields, negative
offsets, and fields starting exactly at the declared segment length.

Anchors are inferred consistently from original addressing obligations in code,
then propagated through data segment references. The `_TEXT` anchor is fixed by
the function addresses. Both external and segment targets are resolved, including
data pointers into `_TEXT` and into another local segment. Ordinary data bytes
and original-to-compiled data fixups are checked as well as forward pointer
targets. External names resolve through module-local PUBDEF/LPUBDEF definitions
before database fallback. A local symbol resolves as `segment_base + offset`;
if a database address exists it must agree, including for unreferenced local
definitions in anchored runtime segments. Local externals propagate anchors
through both code and data. References to definitions in excluded debug
metadata fail closed.

Each compiled function must cover at least its discovered original body in
both function and region verification. A missing final instruction and a cut
inside an instruction produce explicit extent findings.

Extent retry requires `off < hi < end`, with `hi` exactly at the discovered
original flow end. The discarded bytes must be `is_filler`, with no OMF field
overlapping the tail, and no original field belonging before the original end
hidden by the cut. The retry rechecks the retained body. A whole-region check
still includes internal padding; only its final safe alignment tail can be
trimmed. Successful earlier bodies are rechecked against that final region to
catch branches into the last function's discarded tail. Thus a function match
does not silently imply a region match.

Both CLI entry points return nonzero for any function-level or region-level
ERROR, including an expected T3 public missing from a successfully checked
region and exceptions recorded at the audit boundary.

### Non-loadable metadata distinction

Watcom `-d1+` emits `$$SYMBOLS`/`DEBSYM` and `$$TYPES`/`DEBTYP` records.
These are compiler debug metadata rather than local runtime data. The same
distinction is documented by [wc1.cemu._SKIP_CLASSES](../../../tools/wc1/cemu.py).
E0 excludes only these two exact name/class pairs from loaded-image comparison,
records every exclusion in `excluded_metadata`, and rejects any runtime-derived
anchor into them as `UNSUPPORTED`. Unknown nonempty segments still fail closed.
The audit records **144 metadata segments across 48 functions**. These are not
unsupported runtime regions. Boundary controls cover both the metadata exclusion
and rejection of unanchored runtime data.

## Core control matrix

All rows passed their expected verdict and required diagnostic categories.
Legacy means the aggregate result of `wc1.match.match_module` on the same
unpatched module. Function/region distinctions apply to E0 only.

| ID | Control | Legacy | E0 function | E0 region | Required evidence |
|---|---|---|---|---|---|
| P1 | Correct real ChooseCampaignDialog leading table | MATCH | MATCH | MATCH | All 16 leading bytes and their relocations checked |
| N1 | Changed leading table case target | MATCH | MATCH | MISMATCH | `code_reloc_forward`, leading range identified |
| P2 | Real InitPaths absolute relocations | MATCH | MATCH | MATCH | OMF and LE agree on resolved absolute addresses |
| N2 | Exact original code address, OMF fixup removed | MATCH | MISMATCH | MISMATCH | `code_reloc_reverse` |
| P3 | Real IntroOpClearScreen VGA constant | MATCH | MATCH | MATCH | `0xa0000` has neither OMF nor LE fixup; zero findings |
| P4 | Correct local CONST pointer table | MATCH | MATCH | MATCH | Both real-image pointer fields verified |
| N3 | Wrong target in local pointer table | MATCH | MATCH | MISMATCH | `data_reloc_forward` |
| N4 | Exact original local pointer, OMF fixup removed | MATCH | MATCH | MISMATCH | `data_reloc_reverse` |
| N5 | Absolute field marked self-relative | MISMATCH | MISMATCH | MISMATCH | `code_reloc_forward` and `code_reloc_reverse` |
| P5 | Real external call rel32 inside CODE_OBJ | MATCH | MATCH | MATCH | OMF self-relative obligation; no LE loader fixup |
| N6 | Non-filler tail proposed for extent retry | MISMATCH | MISMATCH | MISMATCH | `extent_retry_rejected` plus byte differences |
| N7 | Unsupported OMF loc 11 | MISMATCH | UNSUPPORTED | UNSUPPORTED | `unsupported_location`; never MATCH |
| N8 | Three simultaneous independent defects | MISMATCH | MISMATCH | MISMATCH | All three findings retained |

P1 compiles [choose_campaign_dialog.c](../../../src/mod_13f60/choose_campaign_dialog.c)
with Watcom 10.0a and `-s -ot -oa -ol -4r -zp2`. Its function begins at
`0x157e8`, and its leading table occupies `0x157d8..0x157e8`. N1 changes the
first table addend so the target becomes `0x15820` instead of `0x1581f`.
E0 reports the target difference and inconsistent `_TEXT` anchor without
discarding either finding. The body itself still matches.

P2/P5 compile [init.c](../../../src/init.c), `InitPaths` at `0x1d7cc`.
N2 copies the original absolute address `0x557e4` into the field at
`0x1d7d1` and removes its OMF fixup. Legacy accepts the numerical bytes;
E0 reports `missing_compiled_absolute_fixup`, with original size 4 and no
compiled fixup at offset 5.

P3 compiles [intro_op_clear_screen.c](../../../src/playflic/intro_op_clear_screen.c).
The VGA immediate field is at `0x23061`, compiled offset `0xd`. The fixture
explicitly asserts that neither an OMF field nor an LE field overlaps these
four bytes. Exact byte comparison accepts it with no false positive.

P4/N3/N4 use an InitPaths-derived synthetic OMF module, preserving its real
body, with a local CONST table corresponding to original addresses
`0x5159c..0x515a4`. These two original LE pointer fields target `0x1132c`
and `0x113e0`. A code fixup plus its explicit addend establishes the table
anchor. The fixture is not claimed to be natural compiler output for a local
pointer table. It is a controlled module made from parser dataclasses, using
real executable pointer obligations. N3 changes the first target to the second
symbol (`AttackOrderTarget_`, `0x113e0`); E0 records resolved `0x113e0` versus
original `0x1132c`. N4 preserves the exact loaded pointer bytes but removes the
OMF field; E0 reports the missing reverse obligation at `0x5159c`.

N8 retains the independent data anchor and simultaneously introduces:

1. An ordinary code-byte difference at `0x1d7cc`, compiled `0x52` versus
   original `0x53`.
2. A missing absolute OMF field at `0x1d7d8`, whose original target is
   `0x59920`.
3. The N3 data-pointer target error at `0x5159c`.

The saved result contains **all three findings**, in their three distinct
categories. This directly tests the assignment's R3 correction; no one-finding
limit or mutually exclusive finding-category assumption is used.

## Additional boundary controls

| ID | Purpose | Legacy | E0 region |
|---|---|---|---|
| B_grp | Group relocation target | MISMATCH | UNSUPPORTED |
| B_frame | Frame relocation target | MISMATCH | UNSUPPORTED |
| B_data_self_rel | Self-relative data relocation | MATCH | UNSUPPORTED |
| B_leading_reverse | Missing OMF field in leading table | MATCH | MISMATCH |
| B_intra_rel32 | Exact same-segment call without either fixup | MATCH | MATCH |
| B_intra_rel8 | Exact same-segment short branch | MATCH | MATCH |
| B_external_hardcoded_rel32 | Exact external displacement without OMF fixup | MATCH | MISMATCH |
| B_extent_filler | Safe final filler trimming | MATCH | MATCH |
| B_extent_fixup | Fixup starts in filler tail | MISMATCH | MISMATCH |
| B_extent_overlap | Fixup begins before and overlaps tail | MISMATCH | MISMATCH |
| B_data_to_text | Local pointer targets `_TEXT` segment | MATCH | MATCH |
| B_data_chain | Local pointer anchors another segment | MATCH | MATCH |
| B_debug_metadata | Non-loadable Watcom symbol/type records | MATCH | MATCH |
| B_unanchored_data | Unmapped nonempty runtime data | MATCH | UNSUPPORTED |
| B_data_location | Unsupported location in local data | MATCH | UNSUPPORTED |
| B_data_frame | Unsupported target kind in local data | MATCH | UNSUPPORTED |
| B_unknown_location | Unknown OMF location number | ERROR | UNSUPPORTED |
| B_wrong_addend | Correct external symbol, wrong addend | MISMATCH | MISMATCH |
| B_leading_byte | Ordinary leading-byte corruption plus missing field | MATCH | MISMATCH |
| B_public_disagreement | Inconsistent public address/offset mapping | MISMATCH | MISMATCH |
| B_prefixed_branch | Unmodeled operand-size-prefixed direct rel16 | MATCH | UNSUPPORTED |
| B_data_bytes_match | Correct ordinary local data byte | MATCH | MATCH |
| B_data_byte_corrupt | Wrong ordinary local data byte | MISMATCH | MISMATCH |

Synthetic branch/boundary originals are constructed independently of the
matcher from explicit x86 byte strings and LE/OMF dataclasses. Legacy exceptions
are recorded as `ERROR` rather than hiding them. All control findings and exact
evidence are preserved in [controls.json](results/e0/controls.json).

## Review Round 1 repair evidence

The initial 36-control result did not establish the six obligations below;
the independent review demonstrated false matches. The replacement session
`dev-e0-02` adds 19 controls and six CLI exit tests. Synthetic multi-public
fixtures now describe each public's original function extent separately.

| Finding | New controls | Required result/evidence |
|---|---|---|
| R1: truncated body | `R1_truncated_ret`, `R1_truncated_instruction` | Both scopes reject; `truncated_function`, plus `truncated_instruction` for an interior cut |
| R2: trimmed branch targets | `R2_trimmed_rel8`, `R2_trimmed_rel32`, `R2_trimmed_rel32_fixup`, `R2_sibling_trimmed_rel32` | Region MISMATCH; `trimmed_branch_target`; originating function also fails closed, including the earlier sibling |
| R3: metadata definitions | `R3_metadata_publics`, `R3_metadata_statics` | Both scopes UNSUPPORTED; `runtime_reference_to_debug` |
| R3: contradictory data definitions | `R3_conflicting_publics`, `R3_conflicting_statics`, `R3_unreferenced_publics`, `R3_unreferenced_statics` | Region MISMATCH; `local_definition_mismatch`; referenced cases also reject at function level |
| R3: local anchor propagation | `R3_local_chain_publics`, `R3_local_chain_statics`, `R3_transitive_publics`, `R3_transitive_statics` | MATCH; nonzero symbol offsets and transitive DATA external references are supported |
| R4: extra executable segment | `R4_extra_code` | Region UNSUPPORTED; `additional_code_segment`; independently anchored external call lacks a fixup |
| R5: OOB fixups | `R5_oob_end`, `R5_oob_negative` | Both scopes UNSUPPORTED; bounds, location, and target findings all retained |
| R6: command exit status | `test_entrypoint_exit_on_either_audit_error` (six cases) | Both entry points exit 1 for function-only or region-only ERROR; exit 0 when neither has errors |

The rel8 tail case returns FunctionMatch UNSUPPORTED and RegionMatch MISMATCH:
the function's proposed trim would require an unsupported external rel8 fixup;
the untrimmed region independently differs in its reachable tail byte. Neither
scope accepts the object. For the earlier-sibling case, the sibling containing
the branch rejects while the final sibling's own body still matches.

## Full T3 re-audit

Discovery uses `symbols.load()` and
`progress.classify(analysis.run().functions)` and selects exactly rows with
`scope == "in"` and `c == "T3"`. It does not assume the expected count to
construct the worklist. The expected counts are recorded separately and checked
by the reproduction command and test suite.

Each of 514 unique source files is compiled once per audit invocation under its
declared compiler and flags, into isolated `build/e0/obj/reaudit/` objects.
Four worker threads compile with the production compile helper's 180-second
timeout; matching is serial to avoid sharing Capstone disassemblers across
threads. Both legacy and E0 use that same fresh, unpatched object. No cached
compile is reused. Multi-function object metrics are recorded for each function;
the aggregate obligation counts below deduplicate by source file.

| Verdict | Legacy function | E0 FunctionMatch | E0 RegionMatch |
|---|---:|---:|---:|
| MATCH | 519 | 519 | 519 |
| MISMATCH | 0 | 0 | 0 |
| UNSUPPORTED | 0 | 0 | 0 |
| ERROR | 0 | 0 | 0 |

| RFC section 15 category | Functions |
|---|---:|
| unaffected | 519 |
| code_reloc_defect | 0 |
| data_pointer_defect | 0 |
| boundary_extent_defect | 0 |
| matcher_unsupported | 0 |
| other_mismatch (assignment's additional residual category) | 0 |
| Total | 519 |

Primary categories are mutually exclusive. For mixed failures the implementation
uses unsupported, code relocation, data pointer, boundary, then residual
precedence. All secondary findings remain in the unrestricted list regardless
of that primary category. This precedence affects no baseline row because all
are unaffected.

| Coverage measurement, deduplicated over 514 objects | Count |
|---|---:|
| Watcom 10.0a functions / files | 518 / 513 |
| OW2 functions / files | 1 / 1 |
| Compiled code fixups checked | 2,950 |
| Reverse original LE fixups checked | 1,866 |
| Anchored local runtime data segments checked | 11 |
| Module-local data fixups in baseline T3 objects | 0 |
| Leading `_TEXT` bytes in baseline T3 objects | 0 |

| Normalized kind | Compiled OMF obligations | Original obligations |
|---|---:|---:|
| abs_code | 1,866 | 1,866 |
| rel32_code | 1,084 | 1,136 |
| rel8_code | 0 | 1,000 |
| abs_data | 0 | 0 |

The 52 additional original rel32 obligations are exact intra-segment branches
without OMF fixups. The 1,000 rel8 obligations are also checked through exact
intra-region encodings. These differences are expected under normalized
addressing obligations; demanding literal OMF-to-LE table equality would be
incorrect.

The 11 local runtime-data cases are at `0x1a8e4`, `0x1a914`, `0x1a95c`,
`0x1ab28`, `0x21554`, `0x21844`, `0x21c68`, `0x312f0`, `0x31360`,
`0x31a80`, and `0x32540`. Source paths and flags are present in their JSON/CSV
rows. These provide ordinary-data coverage, not local pointer-fixup coverage.

### Complete non-MATCH function table

There are **no non-MATCH functions or associated regions**. All 519 audit
`findings` lists are empty. Consequently there are no addresses, files,
compiler flags, or finding evidence to enumerate in this exception table.

| Address | File | Compiler | Flags | Function / region verdict | Full findings |
|---|---|---|---|---|---|
| None — 0 rows | — | — | — | — | `[]` for every audited function |

The complete inventory, including exact addresses, names, link names, source
paths, flags, object hashes, metrics and obligations, is available in the
machine-readable files; it is not replaced by a sample or a count-only report.

## Reproduction and acceptance checks

Run in the already configured isolated Nix shell, without nesting `nix develop`:

```sh
cd /mnt/data/projects/warcraft-1-decompile-wt/e0
python3 -m experiments.build_codegen.e0.run_e0 --jobs 4
pytest -q experiments/build_codegen/e0/test_e0.py
git diff 3ee53aa -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md
```

Observed after review hardening: command 1 exits 0, reports `55/55` controls and
a fresh `514`-file, `519`-function audit; command 2 reports `77 passed`; the production diff is
empty. The committed results allow the exact requested pytest command to run
before a new audit as well. Tests validate dynamic inventory coverage,
uniqueness, counts, prototype hash, normalized obligation schema, saved control
reproduction and untruncated CSV/JSON finding equivalence.

To regenerate only the audit, use:

```sh
python3 -m experiments.build_codegen.e0.reaudit_t3 --jobs 4
```

All tracked writes are confined to `experiments/build_codegen/e0/`, this report,
and `docs/research/build-codegen/results/e0/`. The existing user-provided
untracked `original` entry is left untouched. No branch switch, merge, push,
symbol promotion, gate change, or production matcher update is part of E0.

## Limitations and interpretation

- This is an isolated prototype using production analysis and OMF parsers, not
  an independent proof of those parsers. Unknown parsed constructs fail closed;
  constructs silently omitted by an upstream parser remain outside this test.
- Supported runtime OMF fields are loc 9/off32 with external or segment targets.
  Other locations, group/frame targets, data self-relative fields, unknown
  anchors, communal storage, additional nonempty CODE segments and unmodeled
  direct branch forms are unsupported.
  Unsupported controls deliberately return `UNSUPPORTED`, not a false match.
- Original branch obligations rely on discovered instruction boundaries in
  `p.insns`. Leading tables are compared as bytes and relocation fields, not
  incorrectly disassembled as instructions.
- Local pointer-table fixtures are controlled real-image-derived modules, not
  newly compiled C declarations that naturally reproduce that table. Separate
  boundaries cover segment targets and transitive anchors. Arbitrary OMF frame
  semantics, THREAD provenance, LIDATA fidelity and selective extraction are
  not established by this experiment.
- The audit establishes matches at the supplied original layout. It does not
  prove relocatable Build B, physical C ownership of original data, build
  placement, or runtime behavior. P1's valid region does not remove the
  production builder's separate pre-function-table placement restriction.
- There is no observed baseline T3 defect to repair from this run. The legacy
  false-match controls still demonstrate why the strengthened contract is
  necessary. Production adoption remains subject to the RFC's separate global
  verification and Build A IDENTICAL requirements.

## Atomic delivery

1. `b59e34d` — strengthened matcher prototype.
2. `fae4690` — initial positive/negative controls and pytest suite.
3. `df4f5f9` — complete re-audit, machine-readable results, metadata distinction,
   additional boundary and evidence-consistency tests.
4. `54bfd6b` — initial report reviewed by `rev-e0-01` (REQUEST_CHANGES).
5. `6b44c39` — matcher, 19 new controls, six CLI exit tests, and regenerated
   result evidence are delivered together so saved-evidence pytest checks pass.
6. The refreshed report follows in a separate documentation commit.
