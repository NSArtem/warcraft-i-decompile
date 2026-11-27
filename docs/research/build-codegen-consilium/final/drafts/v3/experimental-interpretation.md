# Appendix: interpretation of experiments E0–E8 (EDITOR DRAFT)

## Scope and sources

- **Experimental facts** come from the campaign record at `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`:
  - `docs/research/build-codegen/summary.md`;
  - the per-experiment reports `E0-matcher-soundness.md` … `E8-cu-boundaries.md`;
  - `contracts/` and `results/`.
- **Consilium probes** are cited by the identifier used in the frozen responses (for example "A R4 P1", "B R3-P1"). They are disposable evidence.
- **The manifest warning applies:** the campaign summary and decision register are the campaign's own claims (`02-EVIDENCE-MANIFEST.json`, `experimental_campaign.note`). Where the consilium corrected them, the correction and the decision that carries it are listed.

Each experiment is described in five classes:

- **F (experimental fact):** what was measured, on what population, at which commit.
- **I (architectural interpretation):** what the consilium concluded the fact means, and what it does not mean.
- **D (engineering decision):** the ledger decisions that act on it.
- **U (untested assumption):** what the decisions rely on that no experiment or probe has executed.
- **Q (open question):** cross-referenced to `deferred-questions.md` (DQ-nn).

The campaign summary at `e6150b8` §18.8–18.9 lists several production conclusions:

- "adopt directly: … E5 Fix B3 (D4)";
- "PR 3 — Fix B3";
- "Zero T3 regressions guaranteed";
- "+5–6 more T3s via E1".

**These are superseded by the ledger** as described below. The campaign's D1–D9 register is not normative.

---

## E0 — Matcher soundness

- **F:**
  - The prototype `experiments/build_codegen/e0/matcher_proto.py@e6150b8` closes the three legacy gaps: leading `_TEXT` bytes, reverse LE obligations, and module-local data pointers.
  - 55/55 controls pass: 16 positive; 39 negative, failing closed as 25 MISMATCH and 14 UNSUPPORTED.
  - 519/519 baseline T3 functions (514 files) return MATCH at both scopes.
  - The report states that none of the 514 baseline objects contains a leading jump table or module-local data pointer fixups, so confidence in those two checks rests on the controls.
- **I:**
  - The gaps are real and the bidirectional obligation model works on the tested population.
  - The 519/519 audit is a prototype result at the experiments baseline, not a production cutover, and it guarantees nothing about later T3s. EV-3 has 539.
  - The prototype parses raw OMF through `tools/wc1/omf.py@e6150b8`. That parser keeps THREAD state across FIXUPP records within a module. It has no strict record-length bounds check, so a body slice can truncate before record-specific parsing. It does not verify checksums, returns at the first MODEND without checking for trailing content, ignores unknown records instead of using an allow-list, and discards explicit FRAME encodings when constructing `Fixup` (`parse_module`, lines 99–117 and 236–297). The E4 extractor's per-record THREAD reset is a separate transform defect. E5's rewrite uses its own persistent THREAD decoder, including definitions attached to discarded data (see E4 and E5 below).
  - FunctionMatch must not grant placement authority.
- **D:**
  - DEC-A02 r2 and DEC-C02 r2: production reimplementation; all 55 controls ported; strict raw admission; every live declared T3 at cutover.
  - DEC-B15 r1: no imports from experiments/.
  - DEC-C01 r3: four outcome levels.
- **U:**
  - The strict raw-admission subset covers every object the declared compilers emit for current T3s.
  - The live cutover audit will pass without reclassification. It has not run.
- **Q:** DQ-03 (CONST gap exemptions).

## E1 — Shared epilogues

- **F:**
  - Group A (`DialogItemHitTest`/`DialogHighlightOn`/`DialogHighlightOff`, `-s -ot -oa -ol -5r -zp2`) and Group B (`IntroOpPlaySound`/`IntroOpSyncSound`/`IntroOpWaitSound`, `-s -ot -ol -5r -zp2`) reproduce the original cross-function rel8 epilogue branches in pure C.
  - Both pass E0 RegionMatch. Each links Build A IDENTICAL (8,770/8,770 fixups) as an **isolated** link: one compiled candidate region plus the original symbolic ASM remainder, not a rebuild of the existing T3 inventory (`E1-shared-epilogues.md@e6150b8` §Isolated Build A integration and R1 totals).
  - Of 97 variants, 13 regions pass E0. Three links are IDENTICAL, six standalone placements are rejected for incoming interior references, and **four standalone IntroOpSyncSound insertions pass RegionMatch but are rejected at NASM**, because the remaining original rel8 branches span separate ASM objects (same section).
  - Under `-4r`, 16-byte padding breaks Group B's displacements.
- **I:**
  - Joint compilation is a real path to T3 for shared-tail clusters and is preferred over placement debt.
  - Group B works with current tools. B R0 P3 linked it on a disposable production export.
  - RegionMatch alone does not make an object placeable: the four standalone Sync controls show that a separate placement and link result is required (DEC-A03, DEC-C01).
  - The experiment does not show that every remaining T4 is blocked only by context. The summary's "+5–6 more T3s" estimate is not a DONE forecast (DEC-A01: a T4→T3 conversion does not change DONE).
- **D:**
  - DEC-A13 r1: independent exact Group B path.
  - DEC-C06 r2 and DEC-B06 r1: proof-gated multi-function TUs, with owner checkpoints for AGENTS.md wording and cited T4 checks.
  - DEC-A05 r2: prefer a verified whole-TU shared-tail group.
- **U:** the AGENTS.md ground-rule rewording will be approved by the owner. This is an owner decision, not an assumption the architecture may make.
- **Q:** none beyond the owner checkpoints.

## E2 — Compilation context and alignment

- **F:**
  - Synthetic matrix (28 objects): Watcom 10.0a spaces functions at 16 B under `-4r -ot`, 4 B under `-3r`/`-5r -ot`, and 1 B under `-os`/`-od`.
  - `_TEXT` SEGDEF is PARA for the tested `-ot` modes and BYTE for `-os`/`-od`. OW2 spaces at 16 B under `-4r` and `-5r`.
  - In the 96-T3 census, the **normalized same-flags instruction-body diagnostic** shows 0/96 context-induced body changes. The diagnostic neutralizes relocation fields and named intra-TU rel32 fields and is weaker than E0 proof (`E2-compilation-context.md@e6150b8` §B).
  - Under forced whole-area TUs with native flags, strict E0 FunctionMatch is retained for **83/96** functions; 13 are lost (same section).
  - **None of the three native full selected-area TUs passes RegionMatch.** Among 23 separate contiguous run/subset TUs, 9 pass RegionMatch natively and 23/23 pass under `-5r`, including a 40-function STATUS.C run. These counts overlap and are not independent trials (§B, Contiguous regions).
  - In the neighbour-perturbation controls (63 edits, 210 observations), no neighbour instruction changes. Three neighbour raw bodies change through **CONST literal addends**; only one edit (a literal inserted into VersionMismatchDialog) **breaks the common original anchor**, so that SaveVersionDialog loses FunctionMatch (§C).
- **I:**
  - The baseline RFC premise "10.0a aligns to 4 B" is wrong. The matrix describes compiler behaviour and makes no claim about the original project's flags.
  - `-5r` is a context-specific first candidate for multi-function TUs needing 4-byte spacing.
  - The data-anchor domino shows that a later B3 is useful. It does not show that B3 is needed for M2.
- **D:** DEC-B10 r1 and DEC-C13 r3 (alignment matrix); DEC-B11 r1 and DEC-A09 r1 (additive presets, `-4r` default, S(f) per context).
- **U:** nothing has been measured beyond the 96-T3 census and synthetic matrix, for example on a CU in which no function has been reconstructed yet.
- **Q:** DQ-08 (EXP-2: `-5r -d1+ -zp1`, `-5r -od`).

## E3 — Partial object matching

- **F:**
  - `FarmPanelChanged` (`0x28254`) and `ScoreTickIncome` (`0x24e90`) pass REGION_MATCH inside TUs with mismatching siblings.
  - The matching `ScoreTickIncome` is a **modified fixture**: its sole source change is `sum = delta + score;`. The supplied baseline mismatches by one byte, an LEA SIB byte at `0x24eb9` (`E3-partial-matching.md@e6150b8` §Real Watcom 10.0a objects).
  - Shifted CONST passes through independent literal boundaries.
  - Standalone `DialogHighlightOff` (`0x16d48`) is refuted: the two highlight functions are folded and the outgoing rel8 leaves the slice.
  - 24/24 tests pass.
- **I:**
  - Region-scoped matching is sound on the tested cases. A local region proof is not placement or integration authority.
  - Partial matching does not by itself make a function buildable.
- **D:** DEC-A02 r2 and DEC-C02 r2 (scoped engine); DEC-C01 r3 (outcome levels); DEC-A03 r2 (integration only from an actual link).
- **U:** none adopted beyond the verifier.
- **Q:** DQ-02 (extraction, which consumes partial matches).

## E4 — Selective OMF32 extraction

- **F:**
  - `ScoreTickIncome` and `FarmPanelChanged` extract from whole-TU objects and link Build A IDENTICAL. The `ScoreTickIncome` source is the E3 fixture `experiments/build_codegen/e3/fixtures/score_reference.c` with `sum = delta + score;`, not the supplied baseline (`E4-omf-extraction.md@e6150b8` §Positive case 1).
  - The controlled `A→C` case, a CONST anchor case and a >1024 B LEDATA split pass.
  - 8/8 negative controls fail closed.
  - Review `rev-e4-01` approved with findings F1–F4.
- **I:**
  - Feasible on its two real cases and controls, but the prototype has confirmed faults that the consilium recorded:
    - cross-record THREAD: the extractor's `raw_fixups` constructs a new `Threads` decoder for each FIXUPP record (`experiments/build_codegen/e4/omf_extract.py@e6150b8`, lines 245–262);
    - non-`_TEXT` PUBDEF corruption when lo>0;
    - the typed table/code model;
    - F1–F4.
  - Extraction also changes what the source gate means for files with mismatching publics.
  - It is therefore not an M2 mechanism. The campaign's "go" verdict does not stand as a production adoption.
- **D:**
  - DEC-A07 r2 and DEC-C08 r2: deferred; narrow post-M2 pilot only with owner authorization and strict proof.
  - DEC-C09 r3: shared strict codec first.
  - DEC-B17 r1: extraction as the M2 strategy is rejected.
- **U:** a canonical-TU benefit exists for some post-M2 candidate. Not shown.
- **Q:** DQ-02, DQ-15 (owner decision on gate-2 / `match --all` semantics).

## E5 — Data-anchor decoupling (Fix B3)

- **F:**
  - 9/9 complete Build A links IDENTICAL, covering:
    - the SaveErrorDialog decreasing anchor;
    - native `-ot` `_DATA` arrays;
    - a real 3-segment GAMEDLG object;
    - a controlled cross-record THREAD fixture: the rewriter decodes definitions even on discarded data and expands later references. The baseline object scan found no native THREAD definitions (`E5-data-anchors.md@e6150b8` §Scenario 3; `experiments/build_codegen/e5/omf_b3.py@e6150b8`, lines 280 and 318–326);
    - all four frame modes;
    - per-symbol CONST.
  - 0 `wc1_anchor_*` leaks. 86/86 tests pass.
- **I:**
  - Feasible for the verified subset.
  - It is not "adopt directly" for M2, because no not-done function was shown to require it at EV-3.
  - Initial production use is limited to exact whole segments.
  - Shape-only CONST gap exemptions were refuted by a semantic negative (A1 Q2), so per-literal gap rules need independent extent and access proof.
- **D:**
  - DEC-A06 r1, DEC-B08 r1 and DEC-C10 r3: post-M2, or earlier for a named not-done function; RFC §8.2 constraints 1–5 binding.
  - DEC-C09 r3: strict codec.
  - DEC-C03 r1: rejected gap rule.
  - DEC-A14 r1: raw authority.
- **U:** the strict codec required by DEC-C09 can represent every record E5's transform touches. Not yet built.
- **Q:** DQ-01 (B3 production), DQ-03 (gap exemption), DQ-04 (pad variance cause).

## E6 — Multi-function T4

- **F:**
  - 96/96 tests pass across Isolated, Group and Integrated modes, with logical pointer correspondence and callback ABI verification.
  - 14/14 negative variants fail closed.
  - The RFC's zero-FIXUPP premise is refuted for `IntroFrame → IntroLoadCreditLines`, where Watcom emits one EXTDEF fixup. A NASM fixture shows the entry-hook fallback.
- **I:**
  - The design is feasible for the exercised cases, but no generalised production boundary is certified.
  - Separately, the consilium found a single-function harness defect independent of E6:
    - `cemu.run_pair` restores only watch ranges, and `Emu.call` does not reset EFLAGS (A1 Q1).
    - Under the **tested checkpoints**, 3 of the 5 xfailed witnesses pass: `0x231cc`, `0x23668`, `0x23ae0`.
      - B R3-P1 restored all mapped memory and CPU context (GPRs, EFLAGS, data segment registers) before the C call. It did **not** separately restore the emulator's Python-side allocator pointer (`Emu._heap`).
      - A R3 P1 restored CPU context, mapped contents, allocator state and selected bookkeeping between sides. A second checkpoint variant also initialized a fresh `Emu` for each test case before running the pair (`CONSILIUM-R03-DELIBERATION.md`, A R3 P1).
      - Neither checkpoint certifies arbitrary Python-side state, unwatched effects or production audit parity.
    - The other 2 keep a first difference: `0x23530` at `0x59eb9`, and `0x2fcfc` at `0x80054c` (B R3-P1, A R3 P1).
  - These are **diagnostic observations**. Neither probe attributes a cause or validates every substitution.
- **D:**
  - DEC-A11 r1, DEC-A16 r1 and DEC-C16 r3: complete paired state, audit, Q-B05 suite run, owner review, observations only.
  - DEC-A08 r2 and DEC-C11 r2: E6 machinery on witness demand.
  - Rejected: DEC-B07 r1 (restore only original-run writes) and DEC-B16 r1 (inventory reclassification from probes).
- **U:** the production mechanism will reproduce the probe outcomes. It may not, and any change goes to the owner.
- **Q:** DQ-05 (E6 machinery), DQ-12 (attribution of the two persistent differences).

## E7 — Compiler calibration

- **F:**
  - 21,618 compiles over 26 configurations yielded:
    - 19 new T4 function matches;
    - 14 whole-object RegionMatches;
    - 13 buildable T3s, all linking together IDENTICAL;
    - 218 improved T4s.
  - In the **fixed-default paired control** (`c01` `-s -ot -ol -4r -zp2` versus `c06` `-s -ot -ol -5r -zp2`), FunctionMatch loses zero existing T3s: 417 match under each configuration and the matched sets are identical. The architecture-wide bins have unequal secondary-flag coverage and are not this control (`E7-compiler-calibration.md@e6150b8` §Result and §Existing T3 compatibility and regressions).
  - 84 empty CU intersections are recorded as not inferred.
  - Production merged the presets (`feature/e7-compiler-presets@3123a47`, an ancestor of EV-1 `main@a21772b`).
  - At EV-3, 0 of 202 historical improved-T4 records were fresh for Wave 4B (`12-r04-gpt-response.md` §6).
- **I:**
  - Presets are additive search inputs. A match under a flag is not a claim about the original project's flags.
  - Heuristic scores and freshness snapshots schedule work only.
- **D:** DEC-A09 r1, DEC-B11 r1, DEC-C13 r3.
- **U:** none adopted.
- **Q:** DQ-08.

## E8 — CU boundary evidence

- **F:**
  - 16 signals were evaluated on three corpora: synthetic A; real `clib3r` B1 with 112 verified extents; `war.exe` versus `setup.exe` B2.
  - Refuted: `_DATA`/`_BSS` staircase splits (precision 0.250/0.281) and call-locality drops.
  - `zero16` recall gaps were quantified (0.524 on A, 0.027 on B1).
  - `shared_epilogue` was confirmed as a merge constraint: 6 positives, 0 FP (A 2/2, B1 4/4). This holds only under its stated premises (`E8-cu-boundaries.md@e6150b8` §Result and §Epistemic classification):
    - **producer:** both functions are verified as generated by Watcom 10.0a `wcc386`, which emits these cross-function exit blocks within one object;
    - **block partition:** the branch goes into the neighbouring function's own exit block (sharing a third function's exit is invisible), and the direction is one-way;
    - **linker:** 10.0a `wlink` performs no link-time tail merging.
  - Review `rev-e8-02` (F1) responded to **observed raw-byte variation**. The CONST alignment-gap bytes differed between builds of the same recipe (four different byte triples observed). The fix records a `semantic_data_sha256` with only those gaps zeroed (commit `06235f6`; §Corpus A).
- **I:**
  - The signal precisions hold for these corpora only; game-wide precision is not established.
  - The signals generate hypotheses for analysts and never drive automatic splits, merges or source consolidation.
  - The observed variation is why normalized digests may only group candidates (DEC-A14). The causal determinant of the variation is not established (DQ-04).
- **D:**
  - DEC-A10 r1 and DEC-C12 r2: analyst-facing constraint graph; listed signals rejected as automatic splitters.
  - DEC-B14 r1: no CU storage in M2.
  - DEC-A14 r1: raw authority.
- **U:** none adopted.
- **Q:** DQ-04, DQ-06 (CU storage).

---

## Cross-experiment interpretation

The campaign summary identifies `-5r` 4-byte spacing as a single root cause behind several observations. The consilium accepted the compiler fact (DEC-B10) and its use as a search candidate (DEC-B11, DEC-C13). It did **not** accept it as evidence of the original project's flags.

The consilium's main correction to the campaign's rollout order (§18.9) is that rollout is driven by DONE obligations and named blockers, not by experiment success:

- Infrastructure enters M2 only on demonstrated need (DEC-A15).
- The Group B joint TU may go first, independently (DEC-A13).
- Fix B3 and extraction are post-M2 (DEC-B08, DEC-C08).
