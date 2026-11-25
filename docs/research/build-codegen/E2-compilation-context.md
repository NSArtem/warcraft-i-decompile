# E2 — Compilation-context sensitivity and intra-TU alignment

Experiment date: 2026-11-25. Baseline:
`7c23d2371e95d8de93f0ba1652c8d44b858da273`. Branch:
`research/build-codegen/e2`. Harness commit: `96f3593`; CSV serialization
follow-up: `022df03`.

**Finding:** alignment depends on CPU and optimization flags, rather than just
compiler generation. Watcom 10.0a emits 16-byte function alignment with
`-4r -ot`, 4-byte alignment with `-3r -ot` or `-5r -ot`, and byte packing
with `-os` or `-od`. OW2 retains 16-byte alignment with `-5r -ot`.
Under native optimization, consolidation changed **zero instruction bodies
relative to same-flags standalone controls** in the 96-function census.
Strict E0 FunctionMatch nevertheless retained only **83/96** in the forced
whole-area experiment: placement, data anchoring, one incompatible flag, and
E0's bounds on non-contiguous regions matter separately from code generation.

Evidence files:

- [Harness and reproduction instructions](../../../experiments/build_codegen/e2/README.md).
- [All measurements and exhaustive checker diagnostics](results/e2/results.json).
- [Every consolidation function/context observation](results/e2/consolidation_rows.csv).

## Selection and experimental controls

The selection is an exact census at the baseline: every symbol-database
function with `src` beginning `src/gamedlg/`, `src/playflic/`, or `src/status/`.
Each of the **96 entries owns a distinct standalone C file**, including files
whose names still contain `_reference.c` but whose database ownership is `src`.
Filename suffixes were never used to decide T3 eligibility.

| Area | Standalone T3 functions | Declared flags, in addition to `-q -zl -bt=dos` |
|---|---:|---|
| GAMEDLG | 14 | `-s -ot -ol -4r -zp2` |
| PLAYFLIC | 24 | `-s -ot -ol -4r -zp2` |
| STATUS | 57 | `-s -ot -ol -4r -zp2` |
| STATUS / StatusPanelDraw | 1 | `-s -ot -oa -ol -4r -zp2` |

All declare Watcom 10.0a. **96/96 standalone FunctionMatch and RegionMatch
controls passed the approved, unchanged E0 matcher.** There are 769 unique
standalone file/flags compilations, plus 58 STATUS header-overlay controls.
Each variant is compared with a freshly compiled standalone using exactly
the same flags, so a flag effect cannot be counted as a consolidation effect.

The complete exclusions, with owning reference entries and reasons, are in
`results.json.excluded`. They are:

- GAMEDLG: `dim_screen_image_reference.c`, `game_load_dialog_reference.c`,
  `game_menu_dialog_reference.c`, `modal_screen_reference.c`,
  `net_timeout_dialog_reference.c`, `options_dialog_reference.c`,
  `save_error_dialog_reference.c` — database references, without T3 `src` ownership.
- PLAYFLIC: `player_reference.c` — a multi-function reference file;
  `intro_op_play_sound.c` and `intro_op_sync_sound.c` — unwired drafts with no
  exact `src` owner in this area. No non-T3 neighbor was silently promoted
  into the denominator.
- STATUS: `button_draw_reference.c`, `can_build_advanced.c`, `can_build_basic.c`,
  `draw_reference.c`, `input_reference.c`, `panel_lock_adjust.c`,
  `panel_state_reference.c`, `panel_text_reference.c`, `selection_reference.c`,
  `status_panel_show_reference.c`, `status_panel_text_refresh_reference.c`,
  `unit_panel_update_reference.c` — database references rather than T3 providers.

The generator concatenates complete source files in original address order;
it leaves function definitions unchanged. Plain STATUS consolidation first
fails with E1071/E1151: `status.h` declares CanBuildBlacksmith, CanBuildChurch,
CanBuildStable, CanBuildTower, and CanRebuildTownHall with an unused `short`
parameter, while their definitions use `(void)`. An experiment-local header
copy changes just those five declarations to `(void)`. All **58/58** STATUS
standalone instruction bodies and E0 FunctionMatch verdicts remain unchanged
with that copy. Production headers were not edited.

The 28 group definitions comprise three whole areas, two STATUS flag-compatible
groups (57 + 1), 15 maximal original-adjacent runs with compatible flags, and
eight contiguous subsets whose original function starts share a modulo-16
value. Adjacency means consecutive discovered original functions, with no
intervening discovered function. Every group is tested under eight variants;
the one-function STATUS group also gets its exact declared flag spelling.
This gives **225 group/flag contexts and 2,097 function observations**.
The deliberately selected aligned subsets supply positive RegionMatch controls,
rather than an unbiased estimate of how frequently arbitrary runs match.

## A. Synthetic alignment and context matrix

There are 12 Watcom 10.0a configurations and two required OW2 configurations,
with explicit flag strings stored in JSON. Each compiles both alignment and
pooling fixtures: **28 matrix objects**. Exact-body probes emit 4/10/16/22
no-op bytes through `#pragma aux` inside exported C functions, giving
5/11/17/23-byte bodies with the compiler's return. Four natural C controls
accompany them. Aux byte emitters test padding policy; natural C and real T3
controls supply the evidence about ordinary instruction selection.

| Compiler/configuration | Starts of 5/11/17/23-byte probes | Intra-object function alignment | `_TEXT` SEGDEF alignment code |
|---|---|---:|---:|
| 10.0a `-4r -ot -ol` | 0, 16, 32, 64 | 16 | 3 = paragraph / 16 bytes |
| 10.0a `-3r -ot -ol` | 0, 8, 20, 40 | 4 | 3 |
| 10.0a `-5r -ot -ol` | 0, 8, 20, 40 | 4 | 3 |
| 10.0a `-4r -os -ol` | 0, 5, 16, 33 | 1 | 1 = byte |
| 10.0a `-3r` or `-5r`, `-os -ol` | 0, 5, 16, 33 | 1 | 1 |
| 10.0a `-4r -od` | 0, 25, 56, 93 | 1; bodies acquire OD frames | 1 |
| 10.0a `-4r -ot -ol -d1+` | 0, 16, 32, 64 | 16; bodies become 9/15/21/27 bytes | 3 |
| 10.0a native + `-oa` / `-or`, or removing `-ol` | 0, 16, 32, 64 | 16 | 3 |
| OW2 `-4r -ot -ol` | 0, 16, 32, 64 | 16 | 3 |
| OW2 `-5r -ot -ol` | 0, 16, 32, 64 | 16 | 3 |

The SEGDEF attribute describes **placement of the segment**, not spacing of
functions inside it: the 10.0a `-5r` object still requests a paragraph-aligned
segment while spacing functions on four-byte boundaries.

Exact padding after the first four native 10.0a bodies is:

| Body | Filler hex |
|---:|---|
| 5 | `8d8000000000 8d5200 8bdb` |
| 11 | `8d4000 8bc9` |
| 17 | `8d8000000000 8d9200000000 8d4000` |
| 23 | `8d8000000000 8d5200` |

These are LEA/self-MOV sequences. The corresponding `-3r`/`-5r` sequences
are `8d4000`, `90`, `8d4000`, `90`; size optimization inserts none.
The complete raw bytes, start residues mod 4/mod 16, and segment attributes
are preserved, including zero bytes inside LEA displacements. Such operand
zeros are not separately classified as zero-filled padding. No assumption
that filler is always `90` or `00` is made.

The AGENTS.md 16-byte warning is therefore correct for the project's native
`-4r -ot` preset and for both tested OW2 presets, but overbroad if applied to
10.0a `-3r`/`-5r`, `-os`, or `-od`. This experiment does not change that rule.

### Loops

**448 loop TUs / 896 loop-function observations** cover both `for` and `while`
loops, 16 prefix lengths, all 14 compiler configurations, and two independent
controls: change only the preceding function, or additionally insert an exact
prefix inside the loop-containing functions.

In the preceding-function-only control, loop function starts cover residues
0/4/8/12 under 10.0a `-3r`/`-5r`, all 16 residues under byte packing, and only
residue 0 under the paragraph-spaced configurations. For every configuration
and loop shape, the **entire loop function body remains byte-identical**
across preceding-function edits. There is no observed absolute-position-driven
loop padding. In the internal-prefix control, loop targets move with the
inserted bytes rather than snapping to 4- or 16-byte boundaries. For example,
native `LoopFor` has target-relative-offset minus prefix length = 21; native
`LoopWhile` = 8, for every prefix length. The OD `for` has two back-edge targets.

`preceding_filler_hex` is a literal run of decoded no-op instructions before
a loop target. In configurations that place the deliberately injected prefix
there, it includes those explicit no-ops; it is not a claim that the compiler
inserted them. Neighbor-only invariance and prefix-adjusted offsets establish
the alignment finding. These two loop forms do not establish a universal
absence of loop alignment under other source constructs or untested flags.

### Strings, static storage, and call visibility

Identical `"E2-identical"` literals share one segment offset in all tested
configurations. The optimized identical PoolA/PoolB functions can also share
an entry address; the snapshots retain both public names.

| Compiler/flags | CONST offsets of identical / `a` / `bc` / `defg` | CONST bytes | CONST SEGDEF |
|---|---|---:|---:|
| 10.0a native `-ot` | 0 and 0 / 16 / 20 / 24 | 29 | 5 = DWORD / 4 bytes |
| 10.0a `-os` | 0 and 0 / 13 / 15 / 18 | 23 | 5 |
| OW2 native `-ot` | 0 and 0 / 13 / 15 / 18 | 23 | 5 |

Thus 10.0a speed optimization aligns individual literals to four bytes here,
whereas size optimization packs them; segment alignment alone does not reveal
literal spacing. The measured 10.0a CONST padding is not necessarily zero:
the first gap is `47 00 48`, followed by `00 00` and `00`. Raw snapshots retain
these observed bytes without assigning semantics or assuming an ABI guarantee.
The shared initialized static and function-local initialized static occupy
distinct four-byte slots in an eight-byte `_DATA`, SEGDEF code 5. Complete
FIXUPP records and public/static definitions remain available in JSON.

The **42 call-control objects** compare an external declaration, a global
callee definition, and a static callee definition under each of 14 compiler
configurations. Within each configuration, caller instruction fingerprints and
named call obligations are identical across the three cases. No inlining,
visibility-induced register-allocation change, or calling-convention change
was observed for this three-register-argument callee. CPU/optimization flags
do matter: native 10.0a caller length is 42 bytes, `-5r` is 38, and native OW2
is 35. This is a controlled observation about this fixture, not all static calls.

## B. Real consolidation results

`FunctionMatch` below is the **unmodified E0 result**, including `UNSUPPORTED`
as a loss of MATCH. E0 starts with `[fn_off, next_fn_off)` and applies only its
approved filler-tail retry. `RegionMatch` additionally checks the entire
object and local data. No function result is upgraded using diagnostic hashes.

| Primary forced whole-area TU, native flags | Tested | Retained | Lost | Gained | Same-flags context body changes | Flag-induced body changes |
|---|---:|---:|---:|---:|---:|---:|
| GAMEDLG | 14 | 10 | 4 | 0 | 0 | 0 |
| PLAYFLIC | 24 | 18 | 6 | 0 | 0 | 0 |
| STATUS | 58 | 55 | 3 | 0 | 0 | 1 |
| **Total** | **96** | **83** | **13** | **0** | **0** | **1** |

Forced native retention is 86.46%, Wilson 95% interval **78.20–91.91%**.
The compatible grouping retains **81, loses 15, gains 0 of 96**, with zero
context or flag body changes; interval **75.81–90.30%**. Its lower checker
retention is caused by shrinking the global comparison window when the large
StatusPanelDraw body is removed from the 57-function group. It is not evidence
that compatible flags make code generation worse. The one-function `-oa`
group passes under its declared flags.

Body diagnostics preserve all non-address instruction bytes, internal branch
displacements, body sizes, exact fixups, and named intra-TU near-call targets.
Only relocation fields and independently named resolved intra-TU rel32 fields
are neutralized. Reachability stops at an externally relocated tail jump;
its zero displacement is never followed into alignment filler. This diagnostic
distinguishes instructions from address operands and is weaker than E0 proof.
Relative to the actual declared standalone bodies, forced native preserves
95/96 bodies because StatusPanelDraw needs `-oa`; the compatible context
preserves 96/96. A descriptive Wilson interval for 96/96 is **96.15–100%**.
These areas are a census chosen for convenience, functions share source/context,
and repeated contexts are correlated. Wilson intervals do not justify a
population probability for the remaining game functions.

### Every primary loss and its cause

Codes: **B** = E0 non-contiguous-region bound; **C** = a known intra-TU code
definition cannot share the proposed linear original base; **D** = conflicting
data anchor; **F** = wrong forced flags. Causes overlap.

| Function | E0 verdict | Cause | Original-relative layout error in compiled TU |
|---|---|---|---:|
| VictoryDialog | UNSUPPORTED | B, C | -908 |
| DefeatDialog | UNSUPPORTED | B, C, D | -904 |
| QuitDialog | UNSUPPORTED | B | -896 |
| GameSaveDialog | UNSUPPORTED | B, C | -896 |
| IntroShowFirstFrame | MISMATCH | C | +20 |
| IntroNextFrame | MISMATCH | C | +32 |
| IntroOpFirstFrame | MISMATCH | C | -544 |
| IntroOpWaitSoundB | UNSUPPORTED | B | -1300 |
| IntroOpScrollCredits | UNSUPPORTED | B, C | -1708 |
| CreditsSetAnim | UNSUPPORTED | B | -3236 |
| ButtonAvailable | MISMATCH | C | -516 |
| StatusPanelDraw | UNSUPPORTED | B, C, F | -1252 |
| StatusPanelSetUnit | UNSUPPORTED | B | -2456 |

**No loss in this table is a same-flags context instruction change.**

- B occurs in nine functions. E0's `check_branches` uses the first public's
  inferred `_TEXT` base and the complete emitted text length as its region
  bounds, even when checking a later public at that function's original
  address. When omitted non-T3 neighbors make that original address exceed
  the proposed contiguous region, even original *intrafunction* short branches
  can be labeled `external_rel8`. The runner distinguishes targets inside the
  discovered original body from genuine cross-function targets. It retains
  E0's `UNSUPPORTED` verdict. A larger or smaller non-contiguous TU can change
  these conservative results without changing the function's bytes.
- C occurs in nine functions, eight in compatible grouping. Resolved calls or
  function-pointer references to another public in the same TU are constrained
  by its compiled offset. Omitted original functions and 16-byte padding change
  these offsets. For example, IntroShowFirstFrame and IntroNextFrame reference
  IntroShowFrame; their bodies remain unchanged after symbolic address
  normalization, while E0 reports `local_definition_mismatch` and
  `relocation_target_mismatch`. This is real layout incompatibility, not a
  register-allocation regression.
- D occurs in DefeatDialog. The merged `CONST` receives a first inferred base
  `0x51e26`, while DefeatDialog's literal implies `0x56b8c`. Original message
  strings occupy different original data-pool locations, including the
  `0x56c0c` defeat string. Concatenating selected T3s cannot make them one
  contiguous local segment. The instruction body is unchanged; this is a
  data-layout collision. Region findings preserve both anchors and source
  fixup offsets. It overlaps B/C and is not added as a fourteenth loss.
- F occurs only in StatusPanelDraw. It already differs standalone without
  `-oa`. Giving the full STATUS TU `-oa` fixes that flag effect, but cannot fix
  its independent placement constraints.

### Flag sensitivity and actual context-driven changes

Each row tests all 96 whole-area functions. “Context” compares with a standalone
under that same flag set; “Flag” compares that standalone with its declared
baseline. The sets can overlap. Gains against declared T3 controls are zero
throughout; there are no non-T3 functions in this census.

| Variant | Retained / lost / gained vs declared controls | Context body changes | Flag body changes |
|---|---|---:|---:|
| native `-4r -ot -ol` | 83 / 13 / 0 | 0 | 1 |
| `-3r` | 36 / 60 / 0 | 1 | 56 |
| `-5r` | 85 / 11 / 0 | 0 | 1 |
| `-os` replacing `-ot` | 25 / 71 / 0 | 23 | 64 |
| remove `-ol` | 79 / 17 / 0 | 0 | 7 |
| add `-oa` | 82 / 14 / 0 | 0 | 1 |
| add `-or` | 60 / 36 / 0 | 0 | 30 |
| add `-d1+` | 0 / 96 / 0 | 0 | 96 |

Relative to the consolidated native verdicts, `-5r` gains IntroShowFirstFrame
and IntroNextFrame without losing another MATCH. Its four-byte layout resolves
their local call placement. `-3r` gains those same two but loses 49 other native
matches. These gains are separate from “gained vs declared standalone,” which
must remain zero in an all-matching baseline census.

The one `-3r` context body change is IntroFrame: at body offset 24, standalone
`jne` to its own return becomes `je` to an earlier shared return; size stays 31.
All 23 size-optimized context body changes are emitted cross-function shared
tails/epilogues, rather than a newly inferred register-allocation cause:

| Function(s) under `-os` | Standalone → consolidated body bytes |
|---|---|
| TwoPlayerComputerDialog | 72 → 16 |
| HelpScreen | 114 → 107 |
| IntroFrame | 31 → 31; inverted condition / shared return |
| IntroOpLoadPalette | 52 → 51 |
| IntroPlayMovieB | 29 → 8 |
| CanTrainFootman | 15 → 9 |
| CanBuildRoad, CanBuildWall, CanTrainConjurer, CanTrainCleric, CanBuildLumberMill, CanBuildFarm, CanBuildBarracks | 15 → 12 each |
| RangedWeaponIs0 / RangedWeaponIs1 | 39 → 32 / 42 → 35 |
| SpeedIs0 / SpeedIs1 | 39 → 27 / 42 → 27 |
| MeleeWeaponIs0 / ArmourIs0 | 39 → 30 each |
| MeleeWeaponIs1, MeleeWeaponIs2, ArmourIs1, ArmourIs2 | 42 → 30 each |

All other changed/lost observations, including every adjacent-run context,
have an explicit cause list, same-flags standalone verdict, body signatures,
first differing instructions, layout error, and E0 findings in the CSV/JSON.
The JSON coalesces consecutive byte mismatches losslessly, rather than
truncating findings. `summary.whole_area_variants` additionally lists every
gain/loss by name against consolidated native verdicts.

### Contiguous regions

None of the three full selected-area TUs has native RegionMatch: selected T3s
omit original functions, and native inter-function padding differs. Every
group also records original-adjacent-run relative offsets inside that group.
Separate run TUs receive E0's full RegionMatch, including local data.

Among the 23 contiguous run/subset definitions, **nine** have native
RegionMatch. Under `-5r`, **all 23** pass, including the **40-function STATUS
run** at `0x27b98..0x28050` (addresses of first/last entries). These counts
overlap in functions and are not independent trials. They show that matching
instruction bodies can form large exact regions when original spacing and
context are reproduced; per-function success alone does not prove that region.

## C. Neighbor perturbations

Three native TUs first pass **whole-object E0 RegionMatch**:

| Control TU | Functions | Edits | Unedited-neighbor observations | Start shifts | Raw body changes | Instruction changes | Neighbor MATCH retained / lost |
|---|---:|---:|---:|---:|---:|---:|---|
| PLAYFLIC `playflic_run_5` | 4 | 21 | 63 | 25 | 0 | 0 | 63 / 0 |
| STATUS `status_run_0_aligned_4` | 6 | 21 | 105 | 28 | 0 | 0 | 105 / 0 |
| GAMEDLG `gamedlg_run_1_aligned_0` | 3 | 21 | 42 | 17 | 3 | 0 | 41 / 1 |
| **Total** | **13 distinct functions** | **63** | **210** | **70** | **3** | **0** | **209 / 1** |

For each TU, edit the first, middle, and last function with each of seven
perturbations: exact +1/+2/+3/+7 no-op bytes; a used string literal; eight
volatile-derived arguments creating register pressure; and a conditional early
return creating another epilogue path. C89 declarations remain before injected
statements. The +1/+2/+3/+7 body deltas are measured and asserted, rather than
assumed from source length. Other measured body deltas are stored per edit.

Padding can absorb an edit: STATUS +1/+2/+3 changes no neighbor start, whereas
+7 shifts following functions by 16 bytes. PLAYFLIC's first function sits at
a boundary where even +1 advances subsequent starts by 16. Register-pressure
edits produce following shifts of 80 or 96 bytes in these controls.

The concrete data domino occurs when a literal is inserted into
**VersionMismatchDialog** between the existing GAMEDLG literals:
**SaveVersionDialog** loses E0 FunctionMatch with `relocation_target_mismatch`.
Its opcode/register/internal-branch bytes remain identical; its `CONST`
operand's addend changes. Across the three GAMEDLG string edits, three neighbor
raw bodies change through literal addends, while only this middle insertion
breaks their common original anchor. Prepending a new literal can instead
shift both old literals together and leave a consistent base.

Thus neighbor edits do affect region layout and data anchoring without an
instruction-allocation domino in these controls. Every edited region loses
RegionMatch as expected; string/pressure/epilogue probes also introduce
deliberately unknown external symbols, so their region `UNSUPPORTED` verdicts
are not evidence about unchanged neighbors. No claim of zero risk for other
TUs, size-optimized shared epilogues, or other data layouts follows from these
63 controlled edits. The 210 observations are repeated measurements, not 210
independent sampled functions.

## Reproduction, limits, and implications

In the configured dev shell, directly:

```sh
python3 -m experiments.build_codegen.e2.run_e2
pytest -q experiments/build_codegen/e2/test_e2.py
git diff 7c23d2371e95d8de93f0ba1652c8d44b858da273 -- tools/ src/ analysis/ tests/ Makefile flake.nix AGENTS.md
```

The test suite has **21 passing tests**, including fresh compiler alignment,
pooling, tail-jump reachability, isolated loop shifts, real matching multi-function
regions, negative instruction/fixup controls, exact inventory accounting,
per-context summaries, CSV parity, and perturbation lengths. Missing compilers
or original input fail; no environment skips hide acceptance failures.
The runner uses uncached original discovery and freshly compiles every context.
Compiler exceptions abort rather than becoming mismatch observations. Short,
hashed object names avoid the old compiler's path-length failure; generated
source concatenation avoids its quoted-source-include working-directory trap.

A second full invocation reproduced both artifacts byte for byte:

| Artifact | SHA-256 |
|---|---|
| `results.json` | `c0104a943bf661d3bfa5800c2d453e983ae3b00bdb2cb582c69c36defdf60322` |
| `consolidation_rows.csv` | `84929d039d2a36b0f754d281ed9be746036e12693180010b5b1c2f41d6220026` |

No production source, symbols, tests, build rules, goals, or E0 matcher were
changed. `make verify` was not run, as required by this experiment contract;
the targeted suite and empty production diff are the relevant checks. No Build A
integration or runtime behavioral equivalence is asserted.

The initial “10.0a always uses four bytes” hypothesis is rejected. The tested
native optimization contexts show stable function instruction generation, but
strict layout and data obligations prevent unrestricted consolidation. The
large successful `-5r` runs support further selective-region and data-anchor
research. They do not authorize production migration, matcher relaxation,
changing default flags, or changing the project's finish line.
