# Consilium R0 — Opening Position of Architect B (Claude, `claude-opus-5-5`)

- Round: 0 (independent; no other position seen)
- Baseline read: `research/build-codegen-experiments@e6150b8` (experiments), `main@a21772b` (production), RFC `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (blob `e81b117a`)
- Evidence revision: EV-1
- All probes ran in disposable copies (`/tmp/opencode/cn-claude/m` = `git archive a21772b`, plus my worktree's private Wine prefix). Nothing shared was modified. See §14.

---

## 1. Position summary

1. **The experimental campaign is mostly sound, and its local results hold up.** I checked E0, E1, E2, E5, E6 and E7 against their implementations or results where it mattered, and found no false experimental fact. I reproduced E0 on production `main@a21772b`: **539/539 T3 functions return MATCH at both function and region level**. That covers the 20 T3s promoted after E0 ran (probe P1).
2. **The campaign's production conclusions are mis-prioritised against the actual M2 finish line.** Of the 98 not-done functions on `main`, only 7 are blocked by build infrastructure (B1: 1, B2: 6) and 5 by "reference-C divergences". About 78 need ordinary reconstruction work (no-C stubs, naming), and 8 need owner-approved scope or discovery fixes. Fix B3 (E5), selective extraction (E3/E4) and multi-function T4 (E6) move **zero** DONE functions today. Every function they were shown on (SaveErrorDialog, ScoreTickIncome, FarmPanelChanged, the DialogHighlight group) is already DONE via T4. These belong to the M3/CU track, not to M2.
3. **The campaign never tested Fix B2, yet B2 is the largest infrastructure blocker for M2.** My probes show:
   - (P3) **Group B** (IntroOpPlaySound, IntroOpSyncSound, IntroOpWaitSound) builds **today**, with unchanged production tools, as one `-5r` TU: Build A IDENTICAL, +3 DONE. The inventory's claim that these need cut-boundary emission is wrong.
   - (P5) The remaining four B2 functions build IDENTICAL with a narrow fixed-displacement branch emission.
   - (P6) B1 (ChooseCampaignDialog) builds IDENTICAL with a leading-bytes base in `place()`.
   - Together that is **DONE 912 → 920 with Build A IDENTICAL**. `make verify` was not run on the probe tree.
4. **The IntroOpSyncSound false positive is a predicate-versus-implementation split.** `check_t3_buildable` models only "ASM into the interior of a C cut". It does not model "ASM rel8 crossing a cut" or "ASM rel8 to a C entry", and I found a live example of the latter (MissionDefeat, P5). The architectural fix is a single placement planner that both the buildability check and the emitter consume, plus one unified **cross-object short-branch rule**.
5. **I found a real verification-architecture defect in T4, outside E6's scope.** `cemu.run_pair` restores only `watch` ranges between the original and C runs. Stubs that mutate unwatched memory therefore give the C a different input (P4). IntroOpWaitSound's "behavioural divergence" is this harness artefact: the existing reference C and the byte-exact C both pass once the stub-mutated counter is restored. In principle this can also produce false passes, so it is a soundness issue.
6. **RFC verdict: retain the epistemic framework and invariants (§5, §6, §13). Revise the entity model and roadmap (§4, §7, §10, §16–§18). Replace §14 with results.** Concretely:
   - Adopt now: the E0 matcher, B1, B2 (unified rule), Group-B-style joint TUs, the alignment correction and the T4 paired-state fix.
   - Defer to the post-M2/M3 track: B3, E3/E4 extraction (blocked as well by a gate-semantics question only the owner can decide), the full E6 Group/Integrated machinery, persistent provenance and `analysis/compilation_units.toml`.
   - Keep CU recovery analyst-facing only.

---

## 2. Experiment-by-experiment interpretation

Conventions: "Fact" = established by the experiment's executed controls. "Interpretation" = inference. "Assumption" = untested premise.

### E0 — Matcher soundness

- **Hypothesis.** A bidirectional normalized-obligation matcher accepts all correct forms and rejects known false matches. It covers leading `_TEXT` bytes, reverse LE obligations and local-data pointer relocations (`contracts/E0-contract.md@e6150b8`).
- **Method actually executed.** `experiments/build_codegen/e0/matcher_proto.py@e6150b8`: 55 controls (`results/e0/controls.json`) and a fresh-compile re-audit of 519 T3 functions in 514 files (`results/e0/t3_reaudit.json`, sha `cd8917e1…`). Test suite: 77 pytest tests (`e0/test_e0.py`).
- **Positive controls.** 16 MATCH. These include the real ChooseCampaignDialog leading table (P1: "All 16 leading bytes and their relocations checked", `E0-matcher-soundness.md:152`), plus real-image-derived local pointer tables.
- **Negative controls.** 39 fail closed (25 MISMATCH, 14 UNSUPPORTED), including legacy-matcher false MATCHes (N1, `B_leading_reverse`, `B_leading_byte`).
- **Facts.**
  - The three legacy gaps are real: the controls show legacy MATCH where E0 says MISMATCH.
  - E0 accepts the full T3 population. **Reproduced by me on `main@a21772b`: 539/539 MATCH** at function and region level, 0 legacy false-match candidates (P1).
- **Limits of the population evidence.** The population exercises **0 leading-byte cases and 0 local-data pointer fixups** (P1: `leading_bytes_len` 0 and `data_fixups_checked` 0 across all 539 rows). It does exercise 3,082 code fixups and 1,941 reverse LE obligations. Confidence in gaps #1 and #3 therefore rests on the controls only.
- **Interpretation (mine).**
  - For code that is *placed* in Build A, gaps #1 (leading bytes) and #2 (reverse LE) are already caught by `wc1.compare`. The C object supplies those bytes and fixups, and the comparison checks the loaded image plus all 8,770 fixups. P6 confirms this for ChooseCampaignDialog.
  - Gap #3 (local data pointers) is the only gap that Build A cannot catch, because ASM supplies the data (`build.py:101-104` masks pointer fields "compared by wc1.match", and production `match.py` only masks them).
  - Gaps #1 and #2 still matter: they make the local verdict agree with Build A, and they protect function-only uses such as T4-to-T3 promotion searches.
- **Assumptions.** E0's anchor inference requires independent DB symbol identities. Debug metadata is excluded by exact class/name.
- **Production limitations.** E0 is a prototype living in `experiments/`. Production `tools/wc1/match.py` is unchanged on `main` (`git diff e14d5c0 a21772b -- tools/wc1/match.py` is empty).
- **RFC decision §5 / §3 item 5.** Stands.
- **More experimentation?** No. The work now is production implementation, plus re-running the audit inside `make verify` (which `match --all` does implicitly once the matcher is replaced).

### E1 — Shared epilogues

- **Hypothesis.** Watcom 10.0a reproduces the original cross-function epilogue branches from pure C in the right compilation context.
- **Method.** 97 variants / 196 observations. Group A (DialogItemHitTest/On/Off) and Group B (PlaySound/SyncSound/WaitSound); standalone, reversed-order and pair-only controls; five flag sets (`E1-shared-epilogues.md@e6150b8`, `results/e1/results.json`).
- **Positive controls.**
  - Group A (`group_a_interleaved.c`, `-s -ot -oa -ol -5r -zp2`): region `[0x16cc8,0x16d59)`, Build A IDENTICAL.
  - Group B (`group_b_current.c`, `-5r`, with or without `-oa`): region `[0x2315c,0x231ea)`, IDENTICAL.
  - Both links go through **production `build.place` / `check_placed_plan` / `emit.Emitter`**.
- **Negative controls.**
  - Reversed order, pair-only, standalone and `-4r` all fail E0.
  - **Four standalone SyncSound insertions "reach NASM but are rejected because remaining original rel8 branches span separate ASM objects"** (E1 report, "Isolated Build A integration"). This is exactly the IntroOpSyncSound false-positive mechanism. It was observed in E1 but never fed back into production `check_t3_buildable`.
- **Facts.**
  - Cross-function epilogue sharing is produced by wcc386 within one object.
  - Exact reproduction needs matching bodies, original order and `-5r`-style 4-byte spacing.
- **Facts confirmed by me on `main`.**
  - Production `wc1.match` reports MATCH for all three publics of the Group B TU with header `-s -ot -ol -5r -zp2` (P3).
  - Wired as `src`, production `wc1.build` gives **542 functions from 535 C files, IDENTICAL**, and `wc1.progress` DONE goes 912 → 915 (P3).
  - The Group B TU also passes the compile check under both compilers (P3).
- **Assumptions.** The reconstructed C ordering equals the original's. This is supported by the exact offsets `0 / 0x14 / 0x70`.
- **Limitations.**
  - Group A needed spelling probes; the readable revision was found by search.
  - Group A moves T3 only: all three functions are already DONE via `ref` in `mod_16390.toml@a21772b`.
- **RFC decision §3 item 7 / §7.2.** "Fix B2 implemented within the region contract" stands as a *Build A bridge*. E1 shows that for groups whose members all match, **joint compilation removes the need for B2**. E1 is not evidence for Fix B2 itself.
- **More experimentation?** No for Group B: it is production-ready (§5). Group A is optional (T3-only).

### E2 — Compilation context and alignment

- **Hypothesis.** Compilation context changes codegen; RFC premise: "10.0a always uses 4-byte alignment".
- **Method.**
  - 28 synthetic objects across 12 10.0a and 2 OW2 configurations.
  - A census of 96 T3 functions over 2,097 observations.
  - 23 contiguous run definitions.
  - 63 neighbour perturbations (`E2-compilation-context.md@e6150b8`, `results/e2/`).
- **Positive controls.**
  - Exact start offsets per configuration (table in E2 §A).
  - 23/23 contiguous runs reach RegionMatch under `-5r`, including the 40-function STATUS run.
- **Negative controls.**
  - Edited regions lose RegionMatch as expected.
  - One CONST data-anchor domino (the SaveVersionDialog addend moves `0x28 → 0x3c`).
- **Facts.**
  - Spacing is 16 B for `-4r -ot`, 4 B for `-3r/-5r -ot`, and 1 B for `-os/-od`. The SEGDEF is PARA (16) for `-ot` even under `-5r`.
  - OW2 uses 16 B for both `-4r` and `-5r`.
  - No neighbour-driven instruction changes were seen in the 63 edits.
  - Loop bodies are position-independent in the tested shapes.
- **Interpretation.** The 4-byte spacing inside objects in `war.exe` is consistent with `-3r` or `-5r`. It does **not** identify the original flags. E7's `only_4r` bin holds 51 functions, and its grid lacks 5r OD variants.
- **Assumptions.**
  - The runs are not independent trials (they overlap).
  - The perturbations cover 13 distinct functions.
- **Limitations.** "No domino" holds for the controls only. Size-optimized shared epilogues and other data layouts are untested (stated in E2 §C).
- **RFC.** The premise in §17 item 1 / §14-E2 is refuted. The alignment model must be corrected (DEC-B10). The AGENTS.md "16-byte warning" is correct only for the `-4r -ot` and OW2 presets.
- **More experimentation?** Not for M2. See Q-B06 for the "-5r as CU flag" question (M3).

### E3 — Partial object matching

- **Hypothesis.** A verified region can be certified inside a TU whose siblings mismatch.
- **Method.** `experiments/build_codegen/e3/partial_matcher.py@e6150b8`, two real cases, synthetic data controls, 24 tests.
- **Positive controls.**
  - FarmPanelChanged `[0x80,0xc4)` and ScoreTickIncome `[0,77)`.
  - A shifted CONST pool via per-symbol boundaries.
- **Negative controls.**
  - Outgoing rel8, unresolved sibling targets, unproven mutable shift, literal corruption, equal-string aliasing.
  - The real refuted case DialogHighlightOff under `-os -4r`.
- **Fact.** Region certification is feasible with fail-closed rules.
- **Assumptions.** Data boundaries and jump-table ownership are caller-supplied inputs ("Proof boundary").
- **Production limitations.**
  1. Both real positives are already DONE via T4 (`status.toml@a21772b` FarmPanelChanged `ref`; `save_score.toml@a21772b` ScoreTickIncome `ref`), so E3 moves T3 only.
  2. **Governance.** `match --all` (`match.py:_match_one@a21772b`, `ok &= status == "MATCH"` over *every public in the file*) fails any `src =` file with a mismatching public. A `src =` pointing to a TU with mismatching siblings fails gate 2. Adopting region-level T3 therefore changes what gate 2 checks, which needs the owner's approval under the AGENTS.md finish-line rule. The campaign's decision register (D5) does not mention this.
- **RFC §7 / D5 "ADOPT (SCOPED)".** I reject immediate production adoption (OBJ-B04, DEC-B09). The capability is sound; the time for it is M3 consolidation.
- **More experimentation?** None needed for the capability. A governance decision is needed before use.

### E4 — Selective OMF extraction

- **Hypothesis.** A `VerifiedRegion` can be extracted into a linkable OMF object under Post-Codegen Symbolic Relocation Equivalence.
- **Method.** `omf_extract.py@e6150b8`, 17 tests, and two real Build A IDENTICAL links (ScoreTickIncome via `c_306.obj`, FarmPanelChanged via `c_400.obj`).
- **Positive controls.** Those two real links, plus controlled `A→C` across a mismatching `B`, an E5 anchor, and a 1,500-byte LEDATA split.
- **Negative controls.** 8/8, all six RFC §6.2 classes.
- **Facts.** Extraction works for **single-function slices** with intra-TU rel32 converted to EXTDEF.
- **Not established** (E4 "Scope and trust boundary"): arbitrary multi-function extraction, segmented or 16-bit frames, object-order/data-order independence, automatic symbol identity.
- **Reviewer prerequisites.** `rev-e4-01` F1–F4 (`decisions.md@e6150b8` §3).
- **Production limitations.** Same as E3: no DONE gain and the gate-semantics dependency.
- **RFC §3 item 11 / D6.** Remains "preferred research direction", not production. Defer to M3 (DEC-B09).
- **More experimentation?** Only when M3 consolidation produces a concrete need: a CU whose siblings cannot be matched and whose verified members must reach Build A.

### E5 — Data-anchor decoupling (Fix B3)

- **Hypothesis.** Data segments of C objects can be rewritten to anchors on a single ASM data provider without semantic change, after full verification.
- **Method.** `omf_b3.py@e6150b8`, 86 tests, nine full Build A IDENTICAL links.
- **Positive controls.** The SaveErrorDialog decreasing anchor, native `-ot` explicit `_DATA`, a real three-segment GAMEDLG, a THREAD fixture, four frame modes, and per-symbol CONST.
- **Negative controls.** N1–N4, and zero `wc1_anchor_` leaks.
- **Facts.**
  - Fix B3 is feasible for the exercised subset (flat `off32`, no LIDATA, no COMDAT).
  - **No native THREAD subrecords exist in the current population** (`decisions.md` §2 item 5).
- **Interpretation.** B3 removes the data-order coupling that blocks *future multi-segment CU consolidation*. Today it unblocks exactly one T3: SaveErrorDialog, and only via an `-os` flag outlier (RFC §2.2.5 itself calls this a coincidence that "masks a data-layout mismatch with the wrong optimisation flag"). That function is already DONE via T4 (`gamedlg.toml@a21772b:298-300`).
- **Assumptions.** The caller supplies the symbol identities and boundaries (stated).
- **Production limitations.** It adds an OMF rewriting stage on the Build A path. Its risk is borne only by future consolidation.
- **RFC §8.2 (`[DECISION]/[HYPOTHESIS]`).** The constraints stand. Production timing moves to the M3 track (DEC-B08; OBJ-B05 against D4's "ADOPT" and roadmap PR3).
- **More experimentation?** Q-B08 (measure the actual B3 need over candidate CU consolidations) before scheduling it.

### E6 — Multi-function T4

- **Hypothesis.** Explicit verification boundaries plus substitution policies make multi-function T4 sound, and intra-TU calls lack FIXUPPs, so code hooks are required.
- **Method.** `mf_cemu.py@e6150b8`, 96 tests, 10 positive scenarios, 14 negative variants.
- **Positive controls.** The GAMEDLG Options family (with callbacks) and the PLAYFLIC pair in Isolated, Group and Integrated modes.
- **Negative controls.** Nine families fail closed: asymmetric stubs, trailing-code entry bypass, callback ABI violations, among others.
- **Facts.**
  - **The zero-FIXUPP premise is refuted.** Watcom emits one self-relative EXTDEF FIXUPP for `IntroFrame→IntroLoadCreditLines`.
  - The real defect is `CModule`'s `local_names` precedence over stubs.
  - `symbol_aware_reloc` fixes it; `c_entry_hook` works on a zero-fixup NASM fixture.
- **Assumptions.** The trusted in-process Python boundary; finite scenarios.
- **Limitations.**
  - Production `cemu.py` is unchanged on `main`.
  - E6 did **not** examine the paired-state restoration rule. My probe P4 shows `run_pair` restores only `watch` ranges (`cemu.py:349-391@a21772b`), so a stub that mutates unwatched memory desynchronises the inputs. This is a separate T4 defect that affects M2 today (§6).
- **RFC §11.3.** The `[HYPOTHESIS]` is resolved: mechanism 1 is primary and mechanism 2 is defence in depth. §11.1/§11.2 stand.
- **More experimentation?** Not for M2. Production adoption should come only when a not-done function needs Group mode with intra-TU calls.

### E7 — Compiler calibration

- **Hypothesis.** An empirically calibrated search over Watcom 10.0a options finds matches the legacy eight presets miss.
- **Method.** 21,618 compiles; 26 configurations; 519 T3 and 373 dependency-clean T4 functions (`E7-compiler-calibration.md@e6150b8`, `results/e7/*`).
- **Positive controls.** 13 buildable T3 functions linked together IDENTICAL (532/527); since merged into production `2b10939`.
- **Negative controls.**
  - The paired `-4r → -5r` toggle loses 0 of 417 matches.
  - InitNewCampaign correctly UNSUPPORTED on `_STOSB_`.
- **Facts.**
  - The additive presets are valuable.
  - `S(f)` is context-scoped.
  - 84 of 125 module intersections are empty, and none is used to infer a boundary.
- **Caveat (mine).** E7's "buildable" column comes from production `check_t3_buildable`, which is incomplete (P2, P5). The 13 survived an actual combined link, so the result stands. As a *metric* the column is unsafe until DEC-B03.
- **Limitations.** The grid is finite: 5r OD, `-zp4` and `-d1`/`-d2` sweeps are untested, and OpenArchive's `-zp1` context is untested.
- **RFC §12.** Stands. §17 item 7 is resolved: presets are additive, with no global default change.
- **More experimentation?** Q-B06 (5r OD axis) at M3 only.

### E8 — CU boundary evidence

- **Hypothesis.** Structural signals predict original CU boundaries.
- **Method.** 16 signals; Corpus A (synthetic, 64 pairs); B1 (`clib3r` objects verified by full-segment masked bytes and relocations, 447 pairs); B2 (`setup.exe`, 25 pairs); the game range kept outside the tables.
- **Positive and negative controls.** Ground-truth corpora, with precision and recall per signal (`results/e8/signal_metrics.csv`).
- **Facts.**
  - `shared_epilogue` has 0 false positives (6/6).
  - The `data_bss_staircase_break` and `call_locality_drop` split signals are refuted.
  - `zero16` recall is low.
- **Assumptions (material).**
  - B1 is **library code**: many hand-assembled objects, different flags, and dominated by the `intxa386` stub table. Its precision does not transfer to game C.
  - Corpus A is designed by the experimenters.
  - The `zero16` premise (no in-object zero fill) is "plausible but not proven" in the game range (E8 table).
- **Interpretation.** `shared_epilogue` is a *one-directional proven merge constraint for compiler-generated code*. Its premise is about wcc386, which emits short branches only to targets inside its own object, and about wlink not tail-merging. It is not about the OMF format.
- **RFC §9.2/§9.3.** Revise (D8 agreed): drop the staircase as a split signal and keep everything except `shared_epilogue` as candidate generators.
- **More experimentation?** Q-B07 (the `zero16` premise in the game range) only when CU recovery becomes a deliverable (M3).

---

## 3. Verification architecture proposal

### 3.1 Necessary abstractions (minimum set)

1. **`FunctionMatch` / `RegionMatch` verdicts** (E0 semantics), implemented in `tools/wc1/match.py`:
   - mutually exclusive `MATCH | MISMATCH | UNSUPPORTED | ERROR`;
   - full, untruncated finding lists in machine output (the human report may truncate);
   - normalized obligations checked in both directions;
   - leading bytes included;
   - local-data pointer targets checked (gap #3).
2. **`VerifiedRegion`**: an immutable value minted **only** by `RegionMatch`, carrying:
   - the original `[start,end)`;
   - the object identity (path plus parsed-module digest);
   - the entries;
   - the leading size;
   - any trimmed filler;
   - the verified obligations;
   - the data anchors.

   Implementation: a frozen dataclass with a private constructor token. **No class hierarchy and no `CandidateRegion` type.** A candidate is just the matcher's input arguments.
3. **`PlacementPlan`**: one function `plan(p, verified_regions) -> Plan | PlanError`. It is used by **both** `check_t3_buildable` and `wc1.build`/`emit` (DEC-B03). The plan holds:
   - the cuts;
   - the entries;
   - the per-branch emission mode for every ASM instruction whose target lies in a different link object;
   - the data anchors;
   - any errors.

   It is derived every time and never stored.

### 3.2 Invariants (fail-closed)

- **I-1 (strengthen-only).** A matcher change may only turn MATCH into non-MATCH. Every change re-runs the matcher over the entire T3 population. `make verify` → `match --all` already does this.
- **I-2 (single source of buildability).** "Buildable" is defined as "`plan()` returns no error **and** `emit` accepts the plan". The predicate and the emitter must call the same code. Regression test: standalone `0x23170` → reject (P2); Group B → accept (P3).
- **I-3 (cross-object branch rule; generalises B2).** Let an ASM instruction at `s` be a relative branch to `t`, where `t` lies in a different link object (a C object, or another ASM piece separated by a cut). Then:
  - If the encoding is rel32 and `t` is an exported entry, emit it symbolically (`extern`), as today.
  - Otherwise, emit it with its **original literal displacement** only if all of the following hold:
    - (a) every byte in `[min(s,t), max(s,t))` is supplied by in-place objects (ASM pieces of original length, or C objects placed in sequence; **never legacy layout**);
    - (b) if `t` lies in a C object, `t` is inside that object's `VerifiedRegion`, which proves the bytes at `t` equal the original;
    - (c) the final `wc1.compare` is IDENTICAL.
  - Otherwise the plan is rejected.

  The plan records each such branch as Build A placement debt (`build_a_mode = fixed_displacement`).
- **I-4 (leading bytes).** A region's base is `first_entry_addr − first_entry_off`, allowed only when `RegionMatch` has verified the leading bytes and their obligations. Fixups from leading bytes into the region's own interior are internal.
- **I-5 (data).** Until Fix B3 exists, the C object's data segments must match the original bytes and pointer obligations (gap #3), and the anchors stay in code order (existing rule).
- **I-6 (Build A).** IDENTICAL stays necessary but is never sufficient on its own: T3 = `RegionMatch` ∧ IDENTICAL (existing GOAL.md semantics).

### 3.3 Whole-object versus partial-region

For M2, **whole-object only**. This is the existing `match --all` semantics, which is a gate. Partial regions (E3/E4) need an owner decision on gate-2 semantics and are deferred (DEC-B09).

### 3.4 Proof provenance

For M2, **no new persistent provenance store**. Provenance is recomputed by `make verify` (fresh compile and match), and the existing `wave4_fp` dependency-scoped caches key on compiler, flags and tool signature. RFC §10.2's 13-field digest is deferred until there is a consumer: partial-region T3, or cached proofs across consolidation in M3. This follows RFC §4.1's own "no second parallel metadata DB" rule.

### 3.5 Verified code ownership

A function's semantic owner is its `analysis/symbols` entry (`src =`). The physical provider is the C object or ASM piece in the derived plan. For M2, the B2 "debt" list (branches emitted with fixed displacement) is **printed** by `wc1.build` and asserted in a test. It is not stored.

### 3.6 Defer

`OriginalCUHypothesis` storage, `SemanticVerificationUnit` as a stored entity, `evidence_digest`, region-level T3, extraction, and B3.

---

## 4. Compilation and placement architecture proposal

### 4.1 Entity model (revised)

| Entity | Status in M2 | Storage | Note |
|---|---|---|---|
| ReconstructedTU | exists | `src/` | One function per object **unless the multi-function object passes RegionMatch as a whole** (E1, P3). Proposed AGENTS.md ground-rule wording (owner to approve; it is a ground rule, not a gate). |
| CompiledObject | exists, derived | `build/` | unchanged |
| VerifiedRegion | new, derived | in memory | minted by the matcher only (§3.1) |
| PlacementPlan | new, derived | in memory | single planner (I-2/I-3/I-4) |
| Semantic owner vs physical provider | concept retained | `analysis/symbols` + derived plan | needs no new file in M2 |
| OriginalCUHypothesis | deferred | none in M2 | M3; analyst-facing constraint graph (§7) |
| SemanticVerificationUnit | concept retained | `tests/` + `ref_verified_by` | no new storage |

### 4.2 Relationships, concept by concept

- **Shared epilogues.** Two remedies, in order of preference:
  - (1) a joint TU when every member matches in the joint context (E1, Group B). This is *historically faithful* and *Build B-compatible*.
  - (2) fixed-displacement emission (I-3) when a neighbour is not yet T3. This is Build A-only debt that **disappears in Build B**, because every in-scope neighbour is then C and compiles its own epilogue.
  - Probe P5 covers the four (2)-cases on `main`: ApplyScenarioTerrainKindRects (neighbour `ref`), UnitFinalizeGone (neighbour `fn_2e9c4`, asm), SelectionClickUnit (neighbour `ref`), MissionDefeat (neighbour `ref`).
- **Leading jump tables.** These belong to the function that dispatches through them; the region includes them (I-4). The discovered function partition puts the table bytes in the previous function's `[end,limit)` gap. The plan must not let the previous cut extend past its `end` (it does not today; P6).
- **Inter-function branches.** Intra-object branches are the compiler's (verified by RegionMatch). Cross-object ASM branches follow I-3. Cross-object branches *from C* rel32 are EXTDEF symbolic (existing). **Rel8 from C out of its object is impossible by construction** (wcc386 does not emit it), and the RegionMatch obligations reject it.
- **Alignment.** Model 16/4/1 by flag class (E2). It matters only for multi-function objects, where RegionMatch checks it implicitly. Placement trims the trailing filler only when RegionMatch has proven it filler.
- **Presets and compilation context.** The E7 presets are already merged (`196153c`). `S(f)` is stored as observations in the context of the current reconstructed TU only, and is never promoted to a CU fact.
- **Whole-TU integration.** It is the default and only mode in M2.
- **Selective extraction.** M3 option (DEC-B09).

---

## 5. B1 / B2 / B3 evaluation

### B1 — leading code/data before the first entry

- **Production failure.** `build.place` (`build.py:64-70@a21772b`) requires `pub_off == addr − base`, so `Unplaceable` is raised. In the not-done set this blocks ChooseCampaignDialog `0x157e8`. The leading table `0x157d8..0x157e8` carries four fixups into `0x157e8`'s interior (P6 listing).
- **Experimental remedy.** E0 verified the leading bytes (control P1). No experiment changed placement.
- **What I proved (P6).** With `base -= first_pub_off` in `place()`, ChooseCampaignDialog wired as `src` builds **547 functions from 540 C files, IDENTICAL**. Production `wc1.match` reports MATCH for it, but that matcher does not check the leading bytes (gap #1). Build A IDENTICAL did check them in this probe, because the C object supplies them.
- **Residual risk.** A locally reported T3 for a not-placed object could have an unverified table; hence E0 is a prerequisite. There is also the risk of overlap with the previous function's `[end,limit)`.
- **Hardening.** Implement I-4 only after the E0 matcher lands. Tests: a corrupted-table negative, plus a positive on ChooseCampaignDialog.
- **Verdict.** **Adopt now**, conditional on DEC-B02.

### B2 — interior targets, shared epilogues, ASM-piece boundaries

- **Production failure.** `emit.replaced_interior_refs` (`emit.py:45-84@a21772b`) rejects ASM branches into the interior of a cut. NASM (`-f obj`) fails on any short branch to a label in another object ("OBJ format can only handle 16- or 32-byte relocations").
- **Three sub-cases** (my probes P2/P5):
  - **B2-a: ASM→ASM rel8 crossing a cut.** IntroOpSyncSound standalone: `0x231d7`, `0x231e1` → `0x2316c`. *Not detected by `check_placed_plan`.* **This is the false positive.**
  - **B2-b: ASM→C interior (rel8/rel32).** `0x1e3c4`, `0x2e9db`, `0x2e9e6`, `0x2f0b9`, `0x2f6df`(rel32), `0x2f6ed`, `0x2f6f7`, `0x2f70a`, `0x2f716`, `0x2f73a`. Detected.
  - **B2-c: ASM rel8→C entry.** MissionDefeat: `0x2f718`, `0x2f722`, `0x2f72e`. *Not detected* (entries are exempt from `replaced_interior_refs`); NASM fails at assembly. This is a **second latent false-positive class**.
- **Experimental remedy.** None tested. RFC §7.2 describes only B2-b. E1 provides the joint-TU alternative.
- **What I proved.**
  - (P3) Group B as a joint TU: IDENTICAL without B2.
  - (P5) Fixed literal-displacement emission for the 13 branches above, with the interior check filtered for exactly those sources: **546 functions from 539 C files, IDENTICAL**.
- **Residual risk.** Literal displacements are correct only under in-place placement. This is guaranteed for "placed in sequence" and forbidden for legacy layout. The final IDENTICAL is a complete check for Build A.
- **Hardening.** I-3, derived automatically by the planner (not a hand list like my probe), plus tests for all three sub-cases and negative tests:
  - a legacy-layout object between `s` and `t` → reject;
  - a target outside a VerifiedRegion → reject.
- **Verdict.** **Adopt now** (DEC-B04), with Group-B-style joint TUs preferred where available (DEC-B06).

### IntroOpSyncSound specifically

- `wc1.match` says MATCH (a local fact).
- `check_t3_buildable` says `(True,"")`. That predicate is incomplete: it does not model B2-a.
- The real build fails in NASM. This is an integration fact (`e1a4178`, `m2-mechanical-cleanup/report.md@a21772b` A1).
- Correct resolution: the joint TU with PlaySound and WaitSound (P3), which needs no B2 at all.

There are three levels here, and they must stay distinct:

- **local match**: the bytes of a function in an object;
- **region match**: the closed object region, including spacing;
- **integrated buildability**: the global plan, the emitter's encodability and IDENTICAL.

Only the last makes T3. Under I-2 the predicate becomes a faithful proxy for the last.

### B3 — data anchors, ownership, physical providers

- **Production failure.** `check_placed_plan` requires data anchors in code order (`build.py:129-131`) and a single address per object (`place():108-109`). This blocks SaveErrorDialog T3.
- **Experimental remedy.** E5 Fix B3. It is feasible.
- **M2 impact.** None (SaveErrorDialog is DONE via T4). There is also a fidelity concern: the `-os` match is a flag outlier.
- **Verdict.** **Defer to the M3 track** (DEC-B08). Keep RFC §8.2's constraints as binding preconditions. Schedule it once Q-B08 shows a consolidation that needs it.

---

## 6. Behavioural verification proposal

1. **Paired-state symmetry (new, required for M2).** `run_pair` must give the original and the C **identical initial state for all memory that either execution, or any stub, may read**. Today only `watch` ranges are restored (`cemu.py:349-391@a21772b`).

   Rule: restore every page written during the original run (by code or stubs) before the C run, or fail closed if a stub writes outside the restored set. Probe P4: with the stub-mutated `S+0x10` restored, `test_intro_op_wait_sound` passes for both `player_reference.c` and the byte-exact `zgb.c`. Without it, both fail (`memory 0x80xxxx: original 30 != C 0c`).

   This changes what tests check (it strengthens them), so it needs the owner's approval. Expect XPASSes among the xfailed tests. The rule should come with an audit that counts writes outside the restored set.
2. **Multi-function T4.** When a reference TU contains caller and callee, adopt E6's `symbol_aware_reloc` for **declared** out-of-boundary dependencies. Keep the existing whole-object `c_stubbed` rule as the default. Introduce `VerificationBoundary` only when the first not-done function needs Group mode. `c_entry_hook` is defence in depth for zero-fixup calls, which are not observed in real Watcom output.
3. **Callbacks and ABI.** E6's generator-based callback execution with preserved-register and stack checks is the right model. Adopt it with the first callback-bearing Group test. It is not an M2 prerequisite.
4. **Stubs.** Must be symmetric, declared, and never inside the boundary (E6 rule, retained). New: a stub that mutates memory must declare it, and the harness must restore that memory (rule 1).
5. **Execution boundaries and pointer identity.** E6 R2 (typed pointer slots, equality matrix) is retained for Group/Integrated. Isolated mode must fail closed when isolation is unprovable (E6).
6. **Isolation versus integration.** Isolated remains the default for M2. Integrated is a supplement, never a replacement for Isolated where isolation is possible.

---

## 7. Compilation-unit recovery interpretation

- **Evidence classes (E8-validated).**
  - **Proven merge constraint:** `shared_epilogue`, compiler-generated code only, one-directional.
  - **Conditional proven constraint:** `non_16_aligned_start`, only if the next object requests PARA. Under 10.0a `-5r -ot` the SEGDEF is still PARA (E2), so the premise is plausible for C objects but fails for asm, `-os` and `-od`.
  - **Candidate generators:** `zero16`, `none16`, `style_transition`, `S(f)`-disjointness.
  - **Refuted as split signals:** `data_bss_staircase_break`, `call_locality_drop`.
- **E1 + E2 + E7 together.** They show that *some* original objects used 4-byte function spacing. This is consistent with `-3r`/`-5r`, and `-5r` is favoured by instruction-selection evidence (`SetCursorShape` `shl` vs `lea`, AiGuardStartArea, in E7). They do not show the flags of any whole CU, and 51 T3 functions match only `-4r` in the tested grid. **Competing hypotheses** to keep open:
  - (H1) the whole project was compiled with `-5r`, and the `-4r`-only matches are OD/debug variants missing from the grid;
  - (H2) the flags were mixed per file;
  - (H3) `-3r` for some files.
- **Shared constants.** One positive in Corpus A only. A literal shared across objects does not occur under 10.0a wlink (`g14_tail`/`g15_a`), so a CONST literal shared by two functions is strong merge evidence for *literal-referencing* functions. It is unvalidated on the game.
- **Rejection.** I reject any automatic source consolidation driven by these signals. Consolidation into a multi-function TU is admitted only on **proof**: the whole object passes RegionMatch and Build A is IDENTICAL (P3 is the template). A historical CU name or boundary is never inferred from a successful joint compile alone; the joint compile proves co-location, not file identity.
- **Storage.** `analysis/compilation_units.toml` is deferred to M3. Until then, CU claims stay in `docs/subsystems/modules.md` and in TOML `evidence` strings.

---

## 8. Production roadmap

All stages commit on branches, keep `make verify` green, and merge `--no-ff`. Counts are on `main@a21772b` (98 not done).

| Stage | Content | Entry | Exit | DONE effect | Regression risk / reversibility |
|---|---|---|---|---|---|
| **S0** | Owner approvals and reclassification. (a) Ground-rule wording for multi-function objects. (b) T4 paired-state rule (tests change). (c) Reclassify IntroOpPlaySound/SyncSound/WaitSound as joint-TU T3 and the remaining B2 as fixed-displacement in `wc1.m2_inventory`. | none | owner decision recorded | 0 | none / trivial |
| **S1** | Group B joint TU (`src/playflic/…` with `-5r` header). Wire `src` for 0x2315c, 0x23170, 0x231cc; drop the duplicate reference definition. | S0(a) | verify green, Build A IDENTICAL | **+3** (P3) | low; revert one commit |
| **S2** | E0 matcher in `tools/wc1/match.py`, reimplemented narrowly with E0's controls as production tests. | none | 100% of E0 controls; 539+/539+ population MATCH; verify green | 0 | low (strengthen-only); revert |
| **S3** | Single planner (I-2) and the cross-object branch rule (I-3), B1 (I-4). `check_t3_buildable` = planner. | S2 for B1 (gap #1); I-3 is independent of S2 | positive tests on the 4 B2 functions + ChooseCampaignDialog; negatives; IntroOpSyncSound-standalone reject test; verify green | **+5** (P5, P6) | medium (touches emit/build); IDENTICAL is a complete check; revert |
| **S4** | T4 paired-state restoration and audit. Re-run the 4 PLAYFLIC divergences and EndScreen. | S0(b) | verify green; xfail inventory updated | up to **+4** (IntroOpStartCredits, IntroRunScript, IntroPlay, EndScreen; IntroOpWaitSound is already T3 via S1) | medium (all T4 tests re-evaluated); revert |
| **S5** | Remaining M2 reconstruction (≈78 functions: BULLET.C, stub areas, low-confidence names) with the E7 presets and existing drivers. Scope/discovery items (8) per owner. | S3 (so `batch_driver`/`wave4a` buildability is trustworthy) | gate 1 | ≈86 | per-function |
| **Post-M2 / M3 track** | E6 contract in `cemu` (when needed); Fix B3 (E5) after Q-B08; extraction (E3/E4) after the gate-semantics decision; CU constraint-graph advisor (E8, analyst-facing); `analysis/compilation_units.toml`; data layout; Build B; T5 definition (owner). | M2 or a concrete need | per RFC §16 (revised) | 0 for M2 | — |

What can be deferred until after M2: everything in the last row. Nothing in it moves gate 1.

---

## 9. Scale and generalization

- **Warcraft-specific:** the concrete cases, the address lists, the `zero16` layout of `war.exe`, PLAYFLIC/GAMEDLG facts, the T4 scenario specs.
- **Watcom/OMF/LE-specific:**
  - NASM `-f obj` cannot emit 8-bit external relocations.
  - The 16/4/1 alignment classes.
  - PARA SEGDEFs.
  - THREAD/LEDATA chunking.
  - `wlink` without tail merging, so shared epilogues prove co-location.
  - `$$SYMBOLS`/`$$TYPES` metadata.
  - Path-length crashes in 10.0a.
- **General principles:**
  1. Verify bidirectionally, using normalized obligations.
  2. Local, region and integrated verdicts are distinct, and **the integrated predicate must be the integrator** (I-2).
  3. A byte-identical in-place hybrid build allows fixed-displacement "debt" that a relocatable build must later remove; track it explicitly.
  4. Paired differential execution must start from identical complete state.
  5. Structural CU signals need ground-truth precision measurement before use, and most are candidate generators.
  6. Experimental prototypes are evidence, not production code.
- **Rejected as premature frameworks:** a typed region-lifecycle hierarchy, a persistent provenance graph, a CU database, and a generic "dependency substitution policy" layer before a consumer exists.

---

## 10. Proposed RFC changes (against `6f319ac`)

| RFC § | Action | Change |
|---|---|---|
| Header / status | **Revise** | Baseline `main@a21772b` (912 DONE / 539 T3); state "E0–E8 complete; production adoption per §18 (revised)". |
| §1 | **Revise** | Keep the central question; add that M2 is dominated by reconstruction, and that infrastructure admitted for M2 is B1, B2, the matcher and the T4 state fix. |
| §2.2.1 | **Retain + note** | Add: gaps #1/#2 are caught by Build A for placed code; gap #3 is not; the population exercises 0 cases of #1/#3 (P1). |
| §2.2.2 | **Retain** | Mark as an M3 concern (B3). |
| §2.2.3 | **Retain** | — |
| §2.2.4 | **Revise** | Replace "OMF does not support 8-bit external relocations" with "NASM `-f obj` cannot emit them; wlink LOBYTE support untested". Add the three B2 sub-cases. |
| §2.2.5 | **Revise** | Add: the Group B DialogHit epilogue shift is caused by 16-byte vs 4-byte spacing (`-4r` vs `-5r`), not by standalone compilation alone. |
| §2.2.6 | **Revise** | Add the `run_pair` watch-only restoration defect. |
| §2.2.7 | **Revise** | The `-5r` presets are merged (`196153c`). |
| §3 items 1–4, 8, 10, 12–16 | **Retain** | — |
| §3 item 5 | **Retain** | Add "the re-audit was done at `e14d5c0` (519) and reproduced at `a21772b` (539)". |
| §3 item 6 | **Revise** | VerifiedRegion is minted only by the matcher, plus a single planner; no separate Candidate type. |
| §3 item 7 | **Revise** | Fix B2 = the unified cross-object branch rule (I-3); joint TU preferred. |
| §3 item 9 | **Revise** | B3 is necessary for M3 consolidation, not for M2. |
| §3 item 11 | **Retain** | Add the gate-semantics dependency. |
| §3 item 17 | **Revise** | The experiments are done; sequencing per the revised §18. |
| §4.1 | **Retain** | — |
| §4.2 | **Revise** | Table per §4.1 of this position (storage deferred for OriginalCUHypothesis/SVU). |
| §4.3 | **Revise** | Add the PlacementPlan → buildability predicate edge. |
| §5 | **Retain** | Add "verdict mutual exclusivity and UNSUPPORTED precedence (E0)". |
| §6.1–6.3 | **Retain** | — |
| §6.4 | **Revise** | Cross-reference I-3. |
| §7.1 | **Revise** | Simplify the lifecycle (no CandidateRegion type); add I-2. |
| §7.2 | **Replace** | I-3/I-4 text, with sub-cases B2-a/b/c and the Build A debt record. |
| §8.1 | **Retain** | — |
| §8.2 | **Revise** | The status becomes "E5-verified, production deferred to M3 track"; constraints 1–5 retained. |
| §8.3 | **Retain** | — |
| §9.1 | **Revise** | `compilation_units.toml` deferred to M3. |
| §9.2 | **Revise** | Re-map the examples to E8 classes: `zero16` → strong-conditional, staircase → unreliable. |
| §9.3 | **Replace** | Per my §7 (signals and premises). |
| §10.1 | **Retain** | — |
| §10.2–10.3 | **Revise** | Defer persistent provenance until there is a consumer; keep the list as the target schema. |
| §11.1–11.2 | **Retain** | — |
| §11.3 | **Replace** | Results: zero-FIXUPP refuted; `symbol_aware_reloc` primary; add the paired-state rule. |
| §12 | **Retain** | Add the E7 outcomes and the "S(f) context-scoped" results. |
| §13 | **Retain + add** | Add 11: the integrated predicate equals the integrator. Add 12: paired T4 runs start from identical complete state. |
| §14 | **Replace** | A results digest (per this §2) and new open questions (§13 here). |
| §15 | **Revise** | Record completion (519 at `e14d5c0`; 539 at `a21772b` by P1). |
| §16 | **Revise** | B3 and extraction rows → M3 track; extraction also requires the owner's gate decision. |
| §17 | **Revise** | Items 1, 2, 3, 4, 7, 8 resolved; 5, 6 deferred to M3. |
| §18.1 | **Replace** | Phases per this §8 (S0–S5, M3 track). |
| §18.2 | **Revise** | Per this §9. |
| §19.1 | **Revise** | Add "predicate/implementation divergence" and "T4 state asymmetry". |
| §19.2 | **Retain** | — |
| §20 | **Revise** | Add experiment and telemetry artifacts, and the M2 campaign reports. |

---

## 11. Structured decision proposals

```text
Decision: DEC-B01
Title: M2 priority boundary for infrastructure work
Proposition: Until gate 1 passes, only infrastructure that directly unblocks not-done in-scope functions, or that closes a known verification soundness gap, is admitted to production. On main@a21772b this is: the E0 matcher (DEC-B02), the single planner (DEC-B03), B2 (DEC-B04), B1 (DEC-B05), joint TUs (DEC-B06) and T4 paired-state symmetry (DEC-B07). Fix B3, selective extraction, the full E6 Group/Integrated machinery, persistent provenance and CU databases are scheduled on a post-M2/M3 track.
Revision: 1
Position: PROPOSE
Reason: 98 not-done functions: 7 build-blocked, 5 "divergences", ~78 reconstruction, 8 owner scope/discovery. B3, E3/E4 and E6 have no DONE effect (their cases are already DONE as T4).
Evidence: probe P1/inv-main (wc1.m2_inventory@a21772b output); gamedlg.toml, status.toml, save_score.toml, mod_16390.toml @a21772b; m2-mechanical-cleanup/report.md@a21772b
Assumptions: the owner keeps the current definition of done (GOAL.md §2).
Dependencies: none
```

```text
Decision: DEC-B02
Title: Production adoption of E0 matcher semantics
Proposition: tools/wc1/match.py adopts E0 semantics (bidirectional normalized obligations, leading bytes, local-data pointer targets, mutually exclusive verdicts with UNSUPPORTED precedence, untruncated machine findings), reimplemented in tools/ with E0's 55 controls as production tests. It is admitted only if the full current T3 population returns MATCH under make verify.
Revision: 1
Position: PROPOSE
Reason: Gap #3 is uncaught even by Build A; gaps #1/#2 must be closed locally before B1. Strengthen-only; 539/539 on main today.
Evidence: E0-matcher-soundness.md@e6150b8; results/e0/*; probe P1 (t3_reaudit.json sha 13eea28b… on a21772b)
Assumptions: no new T3 with unsupported constructs lands before adoption (otherwise the audit exposes it, which is the intent).
Dependencies: none
```

```text
Decision: DEC-B03
Title: Buildability predicate equals the integrator
Proposition: wc1.build exposes one planner, plan(p, regions), that computes cuts, entries, cross-object branch emission modes and data anchors, plus errors. check_t3_buildable, batch_driver, wave4a and the m2 inventory call that planner, and the emitter consumes its output. A function may be reported "buildable" only if the planner returns no error and the emitter accepts the plan. Regression tests: IntroOpSyncSound standalone is rejected; Group B is accepted.
Revision: 1
Position: PROPOSE
Reason: The IntroOpSyncSound false positive (B2-a) and MissionDefeat (B2-c) show that the current predicate models one of three failure classes.
Evidence: build.py:113-146,171-267@a21772b; emit.py:45-84@a21772b; e1a4178; E1 report (standalone SyncSound NASM rejects); probes P2, P5
Assumptions: none
Dependencies: none
```

```text
Decision: DEC-B04
Title: Fix B2 as the unified cross-object branch rule (Build A only)
Proposition: An ASM relative branch whose target lies in a different link object is emitted symbolically when it is rel32 to an exported entry. Otherwise it is emitted with its original literal displacement iff (a) every byte between source and target is supplied in place (ASM pieces of original length or C objects placed in sequence; never legacy layout), (b) a target inside a C object lies within that object's VerifiedRegion, and (c) the final wc1.compare is IDENTICAL. Otherwise the plan is rejected. Each such branch is recorded as Build A placement debt in build output and in a test. Joint TUs (DEC-B06) are preferred when available.
Revision: 1
Position: PROPOSE
Reason: It unblocks ApplyScenarioTerrainKindRects, UnitFinalizeGone, SelectionClickUnit and MissionDefeat; probe P5 builds IDENTICAL. The debt vanishes in Build B, where neighbours are C.
Evidence: probe P5 (546 fns / 539 files IDENTICAL), probe-b1-b2-groupb.patch sha 1cd77e6c…; RFC §7.2@6f319ac
Assumptions: in-place layout (existing Build A design).
Dependencies: DEC-B03
```

```text
Decision: DEC-B05
Title: Fix B1 via leading-byte region base
Proposition: place() accepts an object whose first entry has _TEXT offset k>0 by setting base = first_entry_addr - k, only when RegionMatch (DEC-B02) has verified bytes and obligations of [0,k). Fixups from the leading bytes into the object's own range are internal. The plan must reject overlap with any other cut.
Revision: 1
Position: PROPOSE
Reason: It unblocks ChooseCampaignDialog (P6, IDENTICAL), and the other pre-function-table functions once matched.
Evidence: build.py:64-70@a21772b; E0 control P1; probe P6 (547 fns / 540 files IDENTICAL)
Assumptions: discovery assigns table bytes to the previous function's [end,limit) gap, not its [start,end).
Dependencies: DEC-B02, DEC-B03
```

```text
Decision: DEC-B06
Title: Proof-gated multi-function TUs
Proposition: A ReconstructedTU may contain several functions when the whole compiled object passes production RegionMatch (all publics MATCH, original spacing) and Build A is IDENTICAL. Immediately: Group B (IntroOpPlaySound, IntroOpSyncSound, IntroOpWaitSound) in one -5r TU. AGENTS.md's "one function per C object" ground rule is reworded accordingly, subject to owner approval. No consolidation is performed on the basis of heuristic CU signals.
Revision: 1
Position: PROPOSE
Reason: +3 DONE with no tool change; historically faithful; Build B-compatible.
Evidence: E1 report and fixtures/group_b_current.c@e6150b8; probe P3 (542 fns / 535 files IDENTICAL; compile-check 1x2 OK)
Assumptions: the owner accepts the ground-rule wording; full make verify still to be run at implementation.
Dependencies: none
```

```text
Decision: DEC-B07
Title: T4 paired-execution state symmetry
Proposition: cemu.run_pair (or t4spec) restores, before the C run, all memory written during the original run (by code or stubs), or fails closed when a stub writes outside the restored set. The audit log records the restored set. After adoption, every xfailed "reference-C divergence" is re-evaluated, and its blocker category is changed only by evidence.
Revision: 1
Position: PROPOSE
Reason: Watch-only restoration gives C different inputs. IntroOpWaitSound's divergence is this artefact (both reference and byte-exact C pass once the stub-mutated counter is restored). False-pass risk exists in principle.
Evidence: cemu.py:344-391@a21772b; tests/test_playflic_t4.py:403-420@a21772b; probe P4
Assumptions: changing what existing tests check needs owner approval (AGENTS.md finish-line rule).
Dependencies: none
```

```text
Decision: DEC-B08
Title: Fix B3 deferred to the M3 track
Proposition: E5's Fix B3 is recorded as feasible for the verified subset. Its production implementation is scheduled after M2, or earlier only if a not-done function requires it. RFC §8.2's constraints 1–5 remain binding preconditions.
Revision: 1
Position: PROPOSE
Reason: Zero M2 DONE effect (SaveErrorDialog is DONE as T4; its T3 route relies on an -os flag outlier). Adds OMF rewriting risk to the Build A path.
Evidence: E5-data-anchors.md@e6150b8; gamedlg.toml:293-300@a21772b; RFC §2.2.5
Assumptions: no remaining not-done function needs multi-anchor data (none found in the inventory).
Dependencies: DEC-B01
```

```text
Decision: DEC-B09
Title: Region-level T3 and selective extraction deferred pending a governance decision
Proposition: E3/E4 are not adopted into production during M2. Any later adoption first requires an owner decision on gate-2 semantics for src files containing mismatching publics (match --all currently fails them), then rev-e4-01 F1–F4, then the RFC §16 criteria.
Revision: 1
Position: PROPOSE
Reason: Gate semantics are part of the fixed finish line; no DONE gain.
Evidence: match.py:368-390@a21772b; E3/E4 reports@e6150b8; decisions.md D5/D6
Assumptions: none
Dependencies: DEC-B01
```

```text
Decision: DEC-B10
Title: Corrected Watcom 10.0a alignment model
Proposition: The RFC and docs/subsystems/compiler.md state that 10.0a function spacing inside an object is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot, and 1 byte under -os/-od, with a PARA _TEXT SEGDEF for -ot. OW2 uses 16 bytes under -4r and -5r. This describes compiler behaviour and is not a claim about original CU flags.
Revision: 1
Position: PROPOSE
Reason: The E2 matrix (refutes the RFC premise).
Evidence: E2-compilation-context.md §A@e6150b8; results/e2/results.json
Assumptions: none beyond the tested configurations
Dependencies: none
```

```text
Decision: DEC-B11
Title: Presets remain additive; no global default change
Proposition: The merged E7 presets stay additive to each file's declared flags; the project default stays -4r; S(f) is recorded per reconstructed-TU context and never promoted to a CU flag claim.
Revision: 1
Position: PROPOSE
Reason: E7 shows no regression, but also no evidence of a single original flag.
Evidence: E7-compiler-calibration.md@e6150b8; 196153c, 2b10939 on main
Assumptions: none
Dependencies: none
```

```text
Decision: DEC-B12
Title: E6 adoption on demand
Proposition: Production cemu adopts symbol_aware_reloc for declared out-of-boundary dependencies, and VerificationBoundary/callback execution, only when a T4 needed for M2 requires Group mode with intra-TU calls or callbacks. Until then the existing whole-object c_stubbed rule remains. c_entry_hook is kept as defence in depth.
Revision: 1
Position: PROPOSE
Reason: The real defect is local_names precedence (E6). No current not-done function is shown to need Group mode.
Evidence: E6-multifunction-t4.md@e6150b8; cemu.py@a21772b
Assumptions: Q-B01 does not reveal local_names as a cause of the remaining divergences.
Dependencies: DEC-B07
```

```text
Decision: DEC-B13
Title: CU recovery is a constraint graph, analyst-facing only
Proposition: Only shared_epilogue (compiler-generated code; one-directional) is a proven merge constraint. non_16_aligned_start is conditional on a PARA next object. zero16, none16, style_transition and S(f)-disjointness are candidate generators. Staircase breaks and call-locality drops are not used. No tool creates CU boundaries or consolidates sources automatically. compilation_units.toml is deferred to M3.
Revision: 1
Position: PROPOSE
Reason: E8 ground-truth metrics; corpus-transfer caveats.
Evidence: E8-cu-boundaries.md "Epistemic classification"@e6150b8; results/e8/signal_metrics.csv
Assumptions: none
Dependencies: none
```

```text
Decision: DEC-B14
Title: Minimal entity implementation for M2
Proposition: For M2 the production entity set is: VerifiedRegion (immutable, matcher-minted), the single PlacementPlan (derived), and the existing ReconstructedTU/CompiledObject. CandidateRegion is not a separate type. OriginalCUHypothesis and SemanticVerificationUnit get no new storage. Persistent evidence_digest provenance is deferred until a consumer exists.
Revision: 1
Position: PROPOSE
Reason: Avoids a second metadata DB (RFC §4.1); everything needed is recomputed by make verify.
Evidence: RFC §4.1, §7.1, §10.2@6f319ac; wave4_fp caches@a21772b
Assumptions: none
Dependencies: DEC-B03
```

```text
Decision: DEC-B15
Title: Experimental code is evidence, not production
Proposition: No production module imports from experiments/. Each adopted mechanism is reimplemented in tools/wc1 at the minimum scope required, with the experiment's controls ported as tests, and is gated by make verify.
Revision: 1
Position: PROPOSE
Reason: Maintainability; prototypes carry experiment-specific scaffolding.
Evidence: experiments/build_codegen/*@e6150b8
Assumptions: none
Dependencies: none
```

```text
Decision: DEC-B16
Title: Inventory reclassification from probes
Proposition: wc1.m2_inventory reclassifies 0x2315c/0x23170/0x231cc as "joint-TU T3 available (DEC-B06)", 0x1e380/0x2e96c/0x2efd0/0x2f73c as "fixed-displacement cross-object branches (DEC-B04)", and the IntroOpWaitSound divergence as "T4 harness state asymmetry (DEC-B07)".
Revision: 1
Position: PROPOSE
Reason: The current classes contradict probe evidence.
Evidence: probes P3, P4, P5; m2_inventory.py@a21772b (e1a4178)
Assumptions: none
Dependencies: DEC-B04, DEC-B06, DEC-B07
```

```text
Decision: DEC-B17
Title: Integrated selective extraction (Approach D) as the M2 strategy
Proposition: Selective OMF extraction is adopted in production as the mechanism for advancing M2.
Revision: 1
Position: REJECT
Reason: No DONE gain for M2; gate-semantics dependency; complexity. See DEC-B09.
Evidence: as DEC-B09
Assumptions: none
Dependencies: none
```

---

## 12. Objections

**OBJ-B01**
- **Proposition challenged.** Group B (IntroOpPlaySound/IntroOpSyncSound) requires "cut-boundary relative branch emission in wc1.emit/wc1.build". The m2 inventory (`DG-03`) and `e1a4178` say so, and `summary.md` §18.9 PR2 counts Group A and B under "+5–6 more T3s via E1" without stating that no infrastructure is needed.
- **Evidence.** P3: production tools on `main` give Group B as one TU MATCH and IDENTICAL.
- **Failure mode.** Roadmap effort is misdirected, and 3 DONE are delayed behind B2 work.
- **Severity.** Unsupported factual claim.

**OBJ-B02**
- **Proposition challenged.** The campaign roadmap (`summary.md` §18.9; `decisions.md`) presents E0–E8 as covering the RFC's production mechanisms. Fix B2 (RFC §7.2) was never tested; `grep` finds no B2 implementation or test in `experiments/`.
- **Evidence.** B2 blocks 4 not-done functions after Group B (P2, P5).
- **Failure mode.** Production would adopt B3 and extraction (zero DONE) before B2 (+4 DONE).
- **Severity.** Blocking architectural (roadmap).

**OBJ-B03**
- **Proposition challenged.** RFC §7.2 Fix B2 covers "ASM instruction in `piece_k` branches into a verified interior address `t`".
- **Counterexample.** B2-a (IntroOpSyncSound: ASM→ASM across a cut) and B2-c (MissionDefeat `0x2f718`/`0x2f722`/`0x2f72e`: ASM rel8 → C entry). Neither is detected by `replaced_interior_refs`, and both fail in NASM (P2, P5).
- **Consequence.** The §7.2 design repeats the false-positive class.
- **Severity.** Correctness/verification.

**OBJ-B04**
- **Proposition challenged.** D5 "ADOPT (SCOPED)" and D6 "ADOPT (CONDITIONAL)" (`decisions.md@e6150b8`).
- **Evidence.** A `src =` TU with mismatching siblings fails `match --all` (`_match_one`, `ok &= status == "MATCH"`), and that is part of gate 2. Changing it is a finish-line change that needs owner approval. Neither decision states this.
- **Severity.** Blocking architectural (governance).

**OBJ-B05**
- **Proposition challenged.** D4 "ADOPT" Fix B3, and roadmap PR3 placed before the multi-function T4 and extraction work.
- **Evidence.** Zero M2 DONE effect; its only real case (SaveErrorDialog) is DONE and its T3 route is an `-os` outlier.
- **Failure mode.** OMF rewriting complexity on the Build A path with no M2 benefit.
- **Severity.** Implementation risk / prioritisation.

**OBJ-B06**
- **Proposition challenged.** "5 ref-C behavioural divergences … fix real behavioural bug in reference C" (`m2_inventory` DG-04; AGENTS.md next step 2 calls them "real ref-C divergences").
- **Evidence.** P4: for IntroOpWaitSound the reference C passes once the stub-mutated input is restored; the byte-exact C fails identically without the fix.
- **Consequence.** Effort goes into "fixing" correct C. The asymmetric harness also allows false passes in principle.
- **Severity.** Correctness/verification.

**OBJ-B07**
- **Proposition challenged.** `summary.md` §18.1: "single biggest discovery … unifying root cause … `-5r`".
- **Evidence.** E7's own text says "not a claim that every original CU used Pentium options"; 51 T3 functions are `only_4r`; `-3r` also spaces at 4 bytes. The finding explains spacing, not the original flags.
- **Severity.** Unsupported factual claim (editorial). It matters if used to justify a global `-5r` default.

**OBJ-B08**
- **Proposition challenged.** RFC §2.2.4: "Формат OMF не поддерживает внешние 8-битные релокации".
- **Evidence.** The observed limitation is NASM's OBJ backend ("OBJ format can only handle 16- or 32-byte relocations", P5 log). The OMF FIXUPP location type 0 (low-order byte) exists, and wlink's handling of it is untested.
- **Consequence.** Small; I-3 sidesteps it.
- **Severity.** Editorial / unsupported factual claim.

**OBJ-B09**
- **Proposition challenged.** RFC §16 row "CodeRegion + Fix B1 + Fix B2" requires a "strict type/state separation CandidateRegion → VerifiedRegion → PlacementPlan" before B1/B2.
- **Evidence.** The P5/P6 probes show B1 and B2 need about 30 lines of planner logic. The safety comes from the matcher-minted VerifiedRegion and IDENTICAL, not from a type hierarchy.
- **Severity.** Maintainability (propose DEC-B14).

**OBJ-B10**
- **Proposition challenged.** `summary.md` §18.9 PR1: "Zero T3 regressions guaranteed (519/519)".
- **Evidence.** The population has changed (539); P1 re-establishes it at `a21772b`. It must be re-run at implementation. The population exercises 0 leading or data-pointer cases, so the "guarantee" is about the absence of regressions, not about coverage.
- **Severity.** Unsupported claim (minor).

**OBJ-B11**
- **Proposition challenged.** E7 "13 buildable T3 opportunities" as a production metric. It uses `check_t3_buildable` (E7 "Inputs").
- **Evidence.** The predicate is incomplete (P2, P5). The 13 stand only because of the combined link.
- **Consequence.** Wave4/batch_driver "buildable" filters may promote unbuildable candidates; `make verify` still catches them, but at a cost.
- **Severity.** Correctness/verification (mitigated by DEC-B03).

**OBJ-B12**
- **Proposition challenged.** E8 precision figures used as general classification of game-CU signals (RFC §9.2 re-mapping).
- **Evidence.** B1 is library code dominated by `intxa386` and assembly objects; A is designed by the experimenters; the `zero16` premise is unverified in the game.
- **Consequence.** Only the analyst-facing use is justified.
- **Severity.** Unsupported factual claim (if generalised).

**OBJ-B13**
- **Proposition challenged.** RFC §4.2/§9.1 `analysis/compilation_units.toml` and §10.2's 13-field provenance as near-term deliverables.
- **Evidence.** There is no M2 consumer; they risk the "second metadata DB" that RFC §4.1 forbids.
- **Severity.** Maintainability.

---

## 13. Open questions and required experiments

**Q-B01. Do the other four divergences (IntroOpStartCredits, IntroRunScript, IntroPlay, EndScreen) share the T4 state asymmetry?**
- **Falsification:** they still diverge with complete state restored.
- **Cheapest probe:** instrument `run_pair` to snapshot and restore all pages written during the original run, and re-run the 4+1 xfailed tests. EndScreen's documented `LayerAdd` arg swap may be a genuine bug.
- **Decides:** S4's DONE yield; DEC-B12's need.

**Q-B02. Is I-3 complete over all candidate cuts?**
- **Falsification:** any candidate cut set where the planner accepts and NASM or IDENTICAL fails.
- **Probe:** run the planner over every `verified_by match:` function that has no `src`, and over each Wave candidate, comparing against an emit+nasm dry run.
- **Decides:** whether I-2 needs a NASM dry-run safety net.

**Q-B03. Does wlink 10.0a resolve self-relative LOBYTE fixups?**
- **Falsification:** link error or wrong displacement.
- **Probe:** a hand-written OMF with one such fixup.
- **Decides:** whether symbolic rel8 is possible (improves Build A readability; irrelevant to correctness).

**Q-B04. Group A in production.**
- **Probe:** `group_a_interleaved.c` with `-oa -5r` as `src` on `main`, then build.
- **Decides:** T3 +3 (no DONE change). Low priority.

**Q-B05. Does broadened state restoration change any passing T4 outcome?**
- **Falsification:** a passing test fails.
- **Probe:** run the full T4 test set once with DEC-B07 enabled.
- **Decides:** DEC-B07 rollout.

**Q-B06. Is `-5r` the original project flag (H1 vs H2/H3)?**
- **Falsification:** some `only_4r` function has no 5r OD/debug match after the grid is extended.
- **Probe:** extend the E7 grid with 5r OD variants for the 51 `only_4r` functions.
- **Decides:** M3 consolidation defaults.

**Q-B07. Does the `zero16` premise hold in the game's PARA C range?**
- **Falsification:** an in-object zero fill observed in compiled game-C objects.
- **Probe:** scan the E2/E7 compiled objects for zero runs inside `_TEXT`.
- **Decides:** whether `zero16` can be "strong" for game CUs (M3).

**Q-B08. How many plausible CU consolidations need B3 (multi-segment or out-of-code-order anchors)?**
- **Probe:** static count over the E2-style contiguous runs compiled as TUs.
- **Decides:** B3 scheduling (DEC-B08).

---

## 14. Probe and reproduction log

**Environment for all probes.**
- `/tmp/opencode/cn-claude/m` = `git archive a21772b` (tree `5cba1fd0`), with `original/` symlinked read-only to the shared data.
- `WINEPREFIX=/mnt/data/projects/warcraft-1-decompile-wt/cons-b/build/oldcc/wineprefix`, `TMPDIR=/tmp/opencode/cn-claude/t`, `nix develop -c`.
- Artifacts: `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/probes/`.
- **Limitation for all probes:** `make verify` was not run on the modified probe tree. Tests that pin inventories or counts (for example the overnight `needs_human` lists) were not run. The probes establish match, build, compare and progress facts only.

**P1 — E0 re-audit on `main`.**
- Command: copied `experiments/build_codegen/e0` from `e6150b8` into the export. The `production_diff` git call was replaced by a constant because the export has no git metadata. Then ran `python3 -m experiments.build_codegen.e0.reaudit_t3 --jobs 8 --output …/probes/e0-main`.
- Output: `{"c_files": 534, "functions_discovered": 539, "function_verdicts": {"MATCH": 539, …0}, "region_verdicts": {"MATCH": 539, …0}, "legacy_false_match_candidates": 0, "rfc15_categories": {"unaffected": 539}}`, exit 0. `count_matches_expectation` is false only because 519/514 are hard-coded.
- Metrics: leading bytes 0; data fixups checked 0; code fixups 3,082 (505 rows); reverse LE 1,941 (411 rows).
- The 20 new T3 functions (13 E7 + 7 M2-cleanup) all MATCH.
- `t3_reaudit.json` sha256 `13eea28beec6bca6f29d1ce43596fe3b008a8f65fa035ab3f031976bce4d58e1`.

**P2 — rel8 cross-cut scan** (`probes/scripts/rel8_span.py`, read-only).
- Current 539 cuts: 0 spans.
- `+0x23170`: spans `0x231d7→0x2316c` and `0x231e1→0x2316c`.
- Group B (all three), and each of the other B1/B2 single cuts: 0 spans.

**P2b — interior refs** (`probes/scripts/b2_refs.py`, read-only). Lists per §5 B2-b and the B1 fixups, with the sending function and its status: ApplyScenarioTerrainOwnerRects (`ref`), IntroOpWaitSound (`ref`), `fn_2e9c4` (asm), IssueOrderAt (`ref`), EndCheckSurvive (`ref`); the jump table sits in LoadGameDialog's gap.

**P3 — Group B joint TU on `main`.**
- `src/playflic/zgb.c` = header `/* codegen-flags: -s -ot -ol -5r -zp2 / codegen-compiler: 10.0a */` + `experiments/build_codegen/e1/fixtures/group_b_current.c@e6150b8` verbatim (sha `b60b525b…`).
- `wc1.match`: MATCH ×3.
- TOML: `src` for 0x2315c, 0x23170 and 0x231cc (`ref`, `t3_blocker` and `ref_verified_by` removed for 0x231cc).
- `wc1.symbols` OK.
- `wc1.build`: "542 functions from 535 C files (535 placed in sequence, 0 legacy layout) / IDENTICAL (loaded image, entry, stack, fixups)".
- `wc1.progress`: T3 542, unchecked ref 4, DONE 915 (90.6%).
- `wc1.match --compile-check src/playflic/zgb.c`: "1 files x 2 compilers, 0 failures".

**P4 — T4 state asymmetry.**
- `pytest --runxfail tests/test_playflic_t4.py::test_intro_op_wait_sound` fails with `memory 0x801130: original 30 != C 0c`.
- The same test with `SRC=zgb.c` (byte-exact) fails with `memory 0x800490: original 30 != C 0c`.
- With `run_spec` wrapped to add `(S+0x10, 4)` to `watch`, so the counter the `snd` stub mutates is restored, **both pass** (`probes/scripts/probe_gb.py`, `probe_gb2.py`).
- Code reference: `cemu.run_pair` restores only `watch` ranges (`cemu.py:349-391@a21772b`).

**P5 — Fix B2 feasibility** (on top of P3).
- Wired `src` for 0x1e380, 0x2e96c, 0x2efd0 and 0x2f73c.
- Appended 13 branch addresses to `analysis/raw_insns.txt`. Added probe filters, enabled by `WC1_PROBE_B2`, to drop interior-branch errors for exactly those sources in `build.check_placed_plan` and `emit._check_replaced`, and to keep literal branch bytes in `emit.raw_text`.
- First attempt: NASM errors at `jmp short MissionDefeat_` (the B2-c discovery). `probes/scripts/xobj_rel8.py` then listed all cross-object ASM rel8: `0x1e3c4,0x2e9db,0x2e9e6,0x2f0b9,0x2f6ed,0x2f6f7,0x2f70a,0x2f716,0x2f718,0x2f722,0x2f72e,0x2f73a`; plus the rel32-interior `0x2f6df`.
- Final: "546 functions from 539 C files (539 placed in sequence, 0 legacy layout) / IDENTICAL"; `wc1.progress` T3 546, DONE 919.

**P6 — Fix B1 feasibility** (on top of P5).
- `place()` with `base -= first_pub_off`, enabled by `WC1_PROBE_B1`.
- Wired `src` for 0x157e8. `wc1.match`: MATCH (production matcher; leading bytes unchecked by it).
- `wc1.build`: "547 functions from 540 C files … IDENTICAL"; `wc1.progress` T3 547 (54.2%), DONE 920 (91.1%).
- The combined probe diff is `probes/probe-b1-b2-groupb.patch` (sha `1cd77e6c2251…`).

**P7 — not-done inventory on `main`.**
- `python3 -m wc1.m2_inventory --out-dir …/probes/inv-main --summary` gives 912 DONE / 98 not done.
- Class counts: 40 cross-TOML stub no-C; 21 same-TOML stub no-C; 10 wave3-eligible no DB entry; 7 low-confidence named no-C; 5 shared-epilogue; 5 ref-C divergence; 4 AIL scope; 2 data-in-code; 2 split block; 1 pre-function jump table; 1 shared-epilogue-after-cut.

**Not checked by me:**
- the campaign's telemetry prompts and summaries, and individual reviewer transcripts (relied on `decisions.md` §3 for review findings);
- E2's 96-function census raw rows, E4 and E5 implementations line by line;
- the model-calibration-engineering branch (`cea804e`), which is irrelevant to the architecture decisions above.

---

## 15. Source index

**Governance**
- `AGENTS.md@a21772b` (ground rules, one function per object)
- `docs/GOAL.md@a21772b` §2 (definition of T3/T4/DONE), §4 (gates)

**RFC**
- `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` §§1–20

**Campaign**
- `docs/research/build-codegen/{summary,decisions}.md@e6150b8`
- `E0…E8 *.md@e6150b8`
- `results/e0/t3_reaudit.json` (sha `cd8917e1…`)
- `results/e1/results.json`, `results/e2/results.json`, `results/e7/*.json`, `results/e8/signal_metrics.csv`

**Experiment code**
- `experiments/build_codegen/e0/{matcher_proto,reaudit_t3}.py@e6150b8`
- `e1/fixtures/group_b_current.c`
- `e3/partial_matcher.py`, `e4/omf_extract.py`, `e5/omf_b3.py`, `e6/mf_cemu.py`

**Production code**
- `tools/wc1/build.py@a21772b`: 55–112 `place`, 113–146 `check_placed_plan`, 171–267 `check_t3_buildable`
- `tools/wc1/emit.py@a21772b`: 45–84 `replaced_interior_refs`, 112–121 `_check_replaced`, 312–330 `raw_text`
- `tools/wc1/match.py@a21772b`: 368–412 `_match_one` / `match_all`
- `tools/wc1/cemu.py@a21772b`: 344–391 `run_pair`
- `tools/wc1/m2_inventory.py@a21772b` (`e1a4178`)

**Symbols**
- `analysis/symbols/{playflic,gamedlg,status,save_score,mod_16390,mod_13f60,mod_1e380_f1,game_2c4e0,mod_2efd0}.toml@a21772b`

**Tests**
- `tests/test_playflic_t4.py@a21772b`: 22–24 `_DIVERGES`, 403–420

**Production campaigns**
- `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/report.md@a21772b`
- E7 production commits `196153c`, `2b10939`

**Probes**
- `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/probes/`: `e0-main/`, `inv-main/`, `scripts/{rel8_span,b2_refs,xobj_rel8,probe_gb,probe_gb2}.py`, `zgb.c`, `probe-b1-b2-groupb.patch`, `e0-main.log`