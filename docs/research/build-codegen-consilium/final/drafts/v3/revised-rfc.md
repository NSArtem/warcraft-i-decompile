# RFC: Build & Codegen Infrastructure (revised after the 2026 consilium)

- **Document status:** EDITOR DRAFT for Architect review. Not frozen. It carries no approval beyond the ledger it quotes.
- **Editor for draft revision 3:** Architect A (GPT), by owner reassignment. This revision completes the partial draft prepared by Architect B (Claude). See §13 for both Architects’ recorded positions.
- **Supersedes:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13` (blob `e81b117a1ece4f90e8b5cf17c0085b9cfb441b19`, written in Russian). See `editorial-notes.md` for the language change.
- **Normative source:** `decision-ledger.json`, a byte-identical copy of `00-CANONICAL-LEDGER-v2.json`, SHA-256 `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`.
  - It was built from `01-DECISION-LEDGER-FULL-v2.json` (`f5523c8c…`) and `02-OBJECTION-LEDGER-v2.json` (`aaf68de7…`).
- **Evidence baseline:** EV-3.
  - Production `main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`.
  - Experiments `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`.
  - The pinned campaign manifest (`02-EVIDENCE-MANIFEST.json`) is revision EV-1 (`main@a21772b`). The consilium package identifies the supplemental notices as `03-EV-2.json` (`0f546837…`) and `03-EV-3.json` (`3d3dfa43…`), as recorded in §12 item 4. The EV-3 figures below also appear in the frozen r04 responses.
- **Target:** `original/install/war.exe`: Warcraft: Orcs & Humans, DOS CD v1.22h, LE/DOS4GW, Watcom C/C++ 10.0a, OMF32 objects.

## 0. How to read this document

- **Normative content.** This RFC has exactly two kinds of normative content:
  1. **Accepted decision text.** Blocks starting with `DEC-…` reproduce the exact ledger proposition, revision, SHA-256 and status. The propositions marked `UNANIMOUS` bind. Rejected and withdrawn propositions are retained for the record.
  2. **Incorporated baseline provisions.** These are the provisions of the pinned baseline RFC `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13` listed in §8, incorporated by reference at their pinned (Russian) text.
  - Where an accepted decision changes or replaces an incorporated provision, the decision governs, as stated per provision in §8. Translations of baseline text, in `editorial-notes.md` or here, are explanatory only.
- **Editorial text.** All other text is editorial. Headings, connective prose, grouping and the tables that relate decisions are there to navigate the decisions. They do not create, narrow or broaden any obligation. The normative provisions govern any discrepancy with editorial text.
- **Status labels** are the ledger's.
  - **UNANIMOUS:** all three Architects accept the current revision with no conditions.
  - **UNANIMOUS_REJECTED:** all three reject it.
  - **WITHDRAWN_SUPERSEDED:** the author withdrew it in favour of the listed replacements.
  - **State of the ledger:** it contains **no** CONDITIONAL, DISPUTED, NEEDS_EXPERIMENT or DEFERRED *decision*. Deferred *questions* are in `deferred-questions.md`.
- **Every acceptance obligation is three separate questions** (§10):
  - (i) Is the architecture agreed?
  - (ii) What future acceptance test was agreed?
  - (iii) Has that test been executed?
  - **For every new production mechanism under review in this RFC, (iii) is "not executed".** Consilium probes and E0–E8 experiments are evidence for (i), not executions of (ii). The exception is the merged E7 presets, which are already in production and covered by `make verify` at EV-1 and EV-3 (§10).

## 1. Executive summary (editorial)

The baseline RFC proposed a broad architecture: CU recovery, verified regions, OMF transforms, data decoupling, multi-function T4 and calibrated search. It gated that architecture on experiments E0–E8. The experiments ran. The consilium then reconciled the RFC with them and with the production state at EV-3:

- 912 of 1010 in-scope functions DONE.
- 98 not DONE.
- 539 T3.
- `make verify` green: 2505 passed, 11 skipped, 5 xfailed; Build A IDENTICAL.
- Gate 1 fails by 98. Gate 3 is undefined.

The result is a narrower, need-driven architecture:

1. **The finish line is unchanged.** Work is ordered by DONE obligations. Infrastructure enters M2 only for a demonstrated verification or toolchain defect, or for a documented blocker to a named not-DONE function. Reconstruction, owner packets and hardening run as independent tracks (DEC-A01, DEC-A15, DEC-C07).
2. **Verification soundness comes first**, and all of it is still unexecuted in production:
   - a bidirectional, scoped matcher with strict raw-OMF admission and a live cutover audit (DEC-A02, DEC-C02, DEC-B15);
   - integration accepted only from an actual link plus a hardened typed LE comparison (DEC-A03, DEC-C01);
   - raw-artifact authority for any reuse (DEC-A14);
   - complete paired T4 starting state (DEC-A11, DEC-A16, DEC-C16);
   - a measured compiler-path guard (DEC-A12, DEC-C04).
3. **The named M2 build blockers are solved narrowly, inside one placement plan:**
   - B1, leading jump tables (DEC-A04, DEC-B05);
   - B2, cross-object short branches and fallthrough (DEC-A05, DEC-B19, DEC-C05);
   - the exact Group B joint TU, which may proceed independently (DEC-A13, DEC-C06, DEC-B06).
4. **Some mechanisms stay outside M2:**
   - Data-anchor decoupling (Fix B3) is feasible but deferred to after M2, unless a named function needs it earlier (DEC-A06, DEC-B08, DEC-C10, DEC-C09).
   - Selective OMF extraction is not an M2 mechanism (DEC-A07, DEC-C08; DEC-B17 rejected).
   - E6 multi-function machinery is demand-led (DEC-A08, DEC-C11).
   - CU recovery stays analyst-facing, with no automatic consolidation (DEC-A10, DEC-C12).
5. **Compiler facts are corrected and kept separate from historical claims.** The alignment matrix is 16/4/1 bytes. Presets are additive. `-4r` remains the default (DEC-B10, DEC-C13, DEC-B11, DEC-A09).
6. **The entity set is minimal, with no frameworks** (DEC-B14, DEC-B15, DEC-C14).

## 2. Context at EV-3 (editorial, cited)

| Fact | Value | Source |
|---|---|---|
| In-scope / DONE / not DONE | 1010 / 912 / 98 | `12-r04-gpt-response.md` §5 (EV-3 notice, `main@17733f9`) |
| T3 / C files in Build A | 539 / 534 | same |
| `make verify` at EV-3 | 2505 passed, 11 skipped, 5 xfailed; Build A IDENTICAL | `12-r04-gpt-response.md` header; `14-r04-gemini-response.md` header |
| Gate 1 / 2 / 3 | FAIL (98) / PASS / FAIL (T5 undefined) | `02-EVIDENCE-MANIFEST.json` (EV-1 `goal_gates`); unchanged counts at EV-3 |
| Remaining-work composition named by the consilium | BULLET.C and the "61+7" name/C backlog; 8 owner scope/discovery packets | DEC-C07 r3 |
| Named build-infrastructure blockers | B1 ChooseCampaignDialog `0x157e8`; B2 IntroOpSyncSound standalone, MissionDefeat entry/fallthrough; Group B `0x2315c/0x23170/0x231cc` | DEC-A04, DEC-A05, DEC-C05, DEC-A13, DEC-C06 |
| T4 xfails | 5 (four PLAYFLIC tests and EndScreen) | DEC-C16 r3; `12-r04-gpt-response.md` §4 |

The baseline RFC's diagnosis in §2.2 is retained as context, with the corrections recorded in `experimental-interpretation.md`. In particular:

- E0 confirmed the three matcher gaps and closed them in a prototype only.
- The "4-byte intra-object alignment" premise was wrong (E2).

## 3. Applicability classes (editorial)

| Class | Content in this RFC |
|---|---|
| **Warcraft I-specific** | The EV-3 counts and backlog. The named functions (ChooseCampaignDialog, IntroOpPlaySound/SyncSound/WaitSound, MissionDefeat, SaveErrorDialog, StartCredits, EndScreen). The GAMEDLG/PLAYFLIC/STATUS groupings. The 5 xfailed witnesses. |
| **Watcom 10.0a / OMF32 / LE / NASM / wlink-specific** | The alignment matrix (DEC-B10, DEC-C13). The strict OMF subset: THREAD, FRAME, checksums, MODEND (DEC-A02, DEC-C02, DEC-C09). No 8-bit external relocations from NASM `-f obj`, hence piece-local expressions (DEC-A05, DEC-C05). LE fixup semantics versus serialization (DEC-A03). Compiler path limits (DEC-A12, DEC-C04). CONST pad variance (DEC-A14, OBJ-B22). E8 signal precision values (DEC-C12). |
| **General principles** | Order work by finish-line obligations, with need-driven infrastructure (DEC-A01, DEC-A15). Local proof is not placement authority, and a preflight is not integration (DEC-A02, DEC-A03, DEC-C01). Authority binds to raw artifacts (DEC-A14). Equivalent per-side starting state for differential tests (DEC-A11). Storage identity is separate from the physical provider (DEC-A06). Heuristics generate hypotheses and never drive automatic changes (DEC-A10, DEC-C12). Experiments are evidence, not production code (DEC-B15). No speculative frameworks (DEC-C14). These are principles. Their transfer to COFF/ELF/C++ projects is not claimed and was not evaluated. |

## 4. Decision ledger at a glance

| Decision | Rev | Status | Title | Section |
|---|---|---|---|---|
| DEC-A01 | r1 | UNANIMOUS | Keep the M2 completion contract | §5.1 |
| DEC-A02 | r2 | UNANIMOUS | Scoped bidirectional verifier with strict raw-OMF admission [editorial title] | §5.2 |
| DEC-A03 | r2 | UNANIMOUS | Single preflight plan; integration only from actual link and comparison [editorial title] | §5.4 |
| DEC-A04 | r1 | UNANIMOUS | Admit verified leading tables | §5.4 |
| DEC-A05 | r2 | UNANIMOUS | Cross-object transfer and fallthrough rule (B2) [editorial title] | §5.4 |
| DEC-A06 | r1 | UNANIMOUS | Separate storage identity from provider | §5.6 |
| DEC-A07 | r2 | UNANIMOUS | General extraction deferred; narrow pilot conditions [editorial title] | §5.7 |
| DEC-A08 | r2 | UNANIMOUS | Demand-led E6 boundary machinery [editorial title] | §5.8 |
| DEC-A09 | r1 | UNANIMOUS | Keep compiler search evidence scoped | §5.9 |
| DEC-A10 | r1 | UNANIMOUS | Record historical alternatives and premises | §5.10 |
| DEC-A11 | r1 | UNANIMOUS | Certify paired starting state independently of outputs | §5.8 |
| DEC-A12 | r1 | UNANIMOUS | Protect effective Watcom 10.0a paths | §5.9 |
| DEC-A13 | r1 | UNANIMOUS | Admit an independent exact Group B proof | §5.5 |
| DEC-A14 | r1 | UNANIMOUS | Bind verification reuse to raw artifacts | §5.6 |
| DEC-A15 | r1 | UNANIMOUS | Admit M2 infrastructure by demonstrated need [editorial title] | §5.1 |
| DEC-A16 | r1 | UNANIMOUS | Implement and audit paired T4 state before reclassification [editorial title] | §5.8 |
| DEC-B01 | r2 | WITHDRAWN_SUPERSEDED | M2 admission principle for infrastructure work | §7 |
| DEC-B02 | r2 | WITHDRAWN_SUPERSEDED | Production adoption of E0 matcher semantics with strict raw admission | §7 |
| DEC-B03 | r2 | WITHDRAWN_SUPERSEDED | One planner; promotion requires an integration receipt | §7 |
| DEC-B04 | r2 | WITHDRAWN_SUPERSEDED | Unified cross-object transfer rule (Build A only) | §7 |
| DEC-B05 | r1 | UNANIMOUS | Fix B1 via leading-byte region base | §5.4 |
| DEC-B06 | r1 | UNANIMOUS | Proof-gated multi-function TUs | §5.5 |
| DEC-B07 | r1 | UNANIMOUS_REJECTED | T4 paired-execution state symmetry | §6 |
| DEC-B08 | r1 | UNANIMOUS | Fix B3 deferred to the M3 track | §5.6 |
| DEC-B09 | r2 | WITHDRAWN_SUPERSEDED | Region-level T3 and selective extraction deferred pending governance and codec preconditions | §7 |
| DEC-B10 | r1 | UNANIMOUS | Corrected Watcom 10.0a alignment model | §5.9 |
| DEC-B11 | r1 | UNANIMOUS | Presets remain additive; no global default change | §5.9 |
| DEC-B12 | r1 | WITHDRAWN_SUPERSEDED | E6 adoption on demand | §7 |
| DEC-B13 | r2 | WITHDRAWN_SUPERSEDED | CU recovery is a premise-carrying constraint graph, analyst-facing only | §7 |
| DEC-B14 | r1 | UNANIMOUS | Minimal entity implementation for M2 | §5.3 |
| DEC-B15 | r1 | UNANIMOUS | Experimental code is evidence, not production | §5.2 |
| DEC-B16 | r1 | UNANIMOUS_REJECTED | Inventory reclassification from probes | §6 |
| DEC-B17 | r1 | UNANIMOUS_REJECTED | Integrated selective extraction (Approach D) as the M2 strategy | §6 |
| DEC-B18 | r2 | WITHDRAWN_SUPERSEDED | Complete paired starting state for all T4 runs | §7 |
| DEC-B19 | r2 | UNANIMOUS | Plan-level exclusion of legacy-placed objects and fallthrough adjacency | §5.4 |
| DEC-B20 | r1 | WITHDRAWN_SUPERSEDED | Comparator coverage measured, then strengthened | §7 |
| DEC-B21 | r2 | WITHDRAWN_SUPERSEDED | CONST pad bytes are environment-dependent and exempt only on independent access proof | §7 |
| DEC-B22 | r1 | WITHDRAWN_SUPERSEDED | Measured compiler-facing path guard in wc1.oldcc | §7 |
| DEC-C01 | r3 | UNANIMOUS | Four verification and integration outcomes [editorial title] | §5.3 |
| DEC-C02 | r2 | UNANIMOUS | Production E0 verifier with 55 controls and live cutover audit [editorial title] | §5.2 |
| DEC-C03 | r1 | UNANIMOUS_REJECTED | Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (Invariant V4) | §6 |
| DEC-C04 | r2 | UNANIMOUS | Measured compiler-facing path guard in wc1.oldcc [editorial title] | §5.9 |
| DEC-C05 | r4 | UNANIMOUS | Fix B1 and unified Fix B2 inside the single PlacementPlan [editorial title] | §5.4 |
| DEC-C06 | r2 | UNANIMOUS | Proof-gated multi-function TUs; Group B pilot [editorial title] | §5.5 |
| DEC-C07 | r3 | UNANIMOUS | M2 parallel tracks and deferrals (EV-3 instantiation) [editorial title] | §5.1 |
| DEC-C08 | r2 | UNANIMOUS | No selective extraction in M2; post-M2 pilot preconditions [editorial title] | §5.7 |
| DEC-C09 | r3 | UNANIMOUS | Shared strict OMF32 codec before B3 or extraction [editorial title] | §5.6 |
| DEC-C10 | r3 | UNANIMOUS | Data ownership separation, post-M2 B3, raw authority [editorial title] | §5.6 |
| DEC-C11 | r2 | UNANIMOUS | Paired state now; E6 machinery on demand [editorial title] | §5.8 |
| DEC-C12 | r2 | UNANIMOUS | CU recovery as analyst-facing constraint graph [editorial title] | §5.10 |
| DEC-C13 | r3 | UNANIMOUS | E2 alignment matrix replaces RFC alignment premise [editorial title] | §5.9 |
| DEC-C14 | r1 | UNANIMOUS | Reject Premature Multi-Backend Framework Abstractions in Warcraft I | §5.11 |
| DEC-C15 | r2 | WITHDRAWN_SUPERSEDED | Stage-0 strict raw-OMF admission and hardened wc1.compare typed LE verification | §7 |
| DEC-C16 | r3 | UNANIMOUS | T4 witness observations and complete paired-state mechanism [editorial title] | §5.8 |

Counts: {'UNANIMOUS': 38, 'WITHDRAWN_SUPERSEDED': 12, 'UNANIMOUS_REJECTED': 4} (54 decisions). Objections: {'RESOLVED': 64, 'WITHDRAWN': 2} (66).

## 5. Normative contracts

The decisions are grouped by the contract they form. Within a group, the first decision is the general rule; the others are compatible detailed forms. Every decision in a group binds.

### 5.1 M2 completion contract and sequencing

> **DEC-A01 r1** · UNANIMOUS · SHA-256 `cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31`  
> *Keep the M2 completion contract*
>
> Sequence work by remaining DONE obligations under the existing scope, tiers and gates. Count a T4-to-T3 conversion separately. Leave T5 authorization to the owner.

> **DEC-A15 r1** · UNANIMOUS · SHA-256 `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44`  
> *Admit M2 infrastructure by demonstrated need [editorial title]*
>
> Prioritize M2 by newly satisfied DONE obligations under DEC-A01. Run eligible reconstruction, owner evidence packets and verification hardening on independent tracks. Admit M2 production infrastructure for a demonstrated verification or toolchain defect or a documented blocker to a named in-scope function that is not DONE, including a scoped rename or routing helper when reconstruction is otherwise ready. Keep general B3, selective extraction, E6 beyond a named witness, persistent proof stores and CU databases off the M2 critical path, subject to their own adoption boundaries. M3 Build B does not require optional Build A consolidation.

> **DEC-C07 r3** · UNANIMOUS · SHA-256 `4756b13b2fde6f82475c1180e4d5c0102effb4dccda5c6936d8e93b6adf84a9f`  
> *M2 parallel tracks and deferrals (EV-3 instantiation) [editorial title]*
>
> Prioritize genuine M2 completion (98 remaining not-DONE on EV-3 main@17733f9) via parallel tracks: (a) Stage 0/1 verification hardening, single planner, B1/B2, independent Group B pilot (DEC-A13), and complete T4 paired-state symmetry (DEC-A11 / DEC-C16 r3, recording the three passing witnesses and two persistent witness differences under R3 P1 as diagnostic observations with no new DONE credit until production-equivalent verification and owner review pass); (b) routine area reconstruction (BULLET.C and the 61+7 name/C backlog, supported by lightweight deterministic rename/Wave 3R enablers when demonstrably needed, reporting reconstruction yield as an upper bound rather than a deterministic guarantee); and (c) owner evidence packets for the 8 scope/discovery items. Defer Fix B3, selective extraction (E3/E4), and CU hypothesis databases to the post-M2/M3 track; admit E6 boundary machinery earlier only for a named necessary witness; decouple M3 Build B from optional Build A consolidation paths.


*Editorial relation:* DEC-A15 states the admission rule. DEC-C07 instantiates the tracks at EV-3. DEC-B08 keeps its named-function exception for B3, and DEC-C07 and DEC-A08 keep theirs for E6.

### 5.2 Verifier: FunctionMatch and RegionMatch

> **DEC-A02 r2** · UNANIMOUS · SHA-256 `87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca`  
> *Scoped bidirectional verifier with strict raw-OMF admission [editorial title]*
>
> Use one bidirectional obligation engine for FunctionMatch and RegionMatch. Bound local branch checks to the independently verified function extent and carry independently proven external context as explicit obligations. Check trim targets in both scopes. Admit only the strictly decoded raw OMF subset of the actual declared compiler output, and cut over only after the existing file gate and every live declared T3 pass. Defer unproven CONST gap exemptions.

> **DEC-C02 r2** · UNANIMOUS · SHA-256 `8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b`  
> *Production E0 verifier with 55 controls and live cutover audit [editorial title]*
>
> Reimplement E0 bidirectional Normalized Addressing Obligation verification in tools/wc1/match.py (importing nothing from experiments/) with strict raw-OMF admission (record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, preserved explicit FRAME encodings) and all 55 controls as production tests, audited over every live declared T3 at cutover. Evaluate FunctionMatch intra-function branch closure against [orig_fn.start, orig_fn.start + fn_len) while attaching explicit sibling-context obligations (never minting placement permission); preserve trimmed_branch_target across all modes; fail closed on CONST pad mismatches (no Stage-0 V4 dependency).

> **DEC-B15 r1** · UNANIMOUS · SHA-256 `c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387`  
> *Experimental code is evidence, not production*
>
> No production module imports from experiments/. Each adopted mechanism is reimplemented in tools/wc1 at the minimum scope required, with the experiment's controls ported as tests, and is gated by make verify.


### 5.3 Outcome levels and the M2 entity set

> **DEC-C01 r3** · UNANIMOUS · SHA-256 `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de`  
> *Four verification and integration outcomes [editorial title]*
>
> Maintain four explicit verification and integration outcomes: FunctionMatch (local body diagnostic with explicit external context obligations), RegionMatch -> immutable matcher-minted VerifiedRegion (closed object/region proof), PlacementPlan (single derived preflight partition plan shared by check_t3_buildable, wc1.build, wc1.emit, batch_driver, wave4a, and m2_inventory), and IntegratedResult (actual assemble, link, and hardened wc1.compare receipt). Do not add a separate CandidateRegion runtime class or persistent proof/CU metadata DB in M2.

> **DEC-B14 r1** · UNANIMOUS · SHA-256 `18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd`  
> *Minimal entity implementation for M2*
>
> For M2 the production entity set is: VerifiedRegion (immutable, matcher-minted), the single PlacementPlan (derived), and the existing ReconstructedTU/CompiledObject. CandidateRegion is not a separate type. OriginalCUHypothesis and SemanticVerificationUnit get no new storage. Persistent evidence_digest provenance is deferred until a consumer exists.


*Editorial relation:* the following baseline RFC elements are superseded for M2 by these two decisions:

- the `CandidateRegion` type (baseline §7.1);
- new storage for `OriginalCUHypothesis` and `SemanticVerificationUnit` (baseline §4.2);
- persistent `evidence_digest` provenance (baseline §10.2).

### 5.4 Placement and integration acceptance

> **DEC-A03 r2** · UNANIMOUS · SHA-256 `58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda`  
> *Single preflight plan; integration only from actual link and comparison [editorial title]*
>
> For a new in-place Build A path, derive one input-bound partition plan with one physical provider per original loaded byte. Treat plan success as preflight. Accept integration only from actual assembly and link, materialized provider evidence, the existing comparison, and an expanded comparison of supported LE loader attributes and normalized typed fixups. Validate raw fixup records before collapsing agreeing page-straddle duplicates. Keep serialization differences diagnostic unless shown to be loader-relevant.


DEC-C15 r2, which held raw LE grouping and fixup-page offsets to hard equality, is **WITHDRAWN_SUPERSEDED** into DEC-A02, DEC-C02 and DEC-A03 (OBJ-A24, RESOLVED by all three). DEC-A03's last sentence governs those fields.

**B1 — leading jump tables**

> **DEC-A04 r1** · UNANIMOUS · SHA-256 `5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0`  
> *Admit verified leading tables*
>
> Derive a whole contribution base from a verified public binding and object offset. Admit leading bytes only with full region bounds, ownership and checked relocation obligations.

> **DEC-B05 r1** · UNANIMOUS · SHA-256 `8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac`  
> *Fix B1 via leading-byte region base*
>
> place() accepts an object whose first entry has _TEXT offset k>0 by setting base = first_entry_addr - k, only when RegionMatch (DEC-B02) has verified bytes and obligations of [0,k). Fixups from the leading bytes into the object's own range are internal. The plan must reject overlap with any other cut.


**B2 — cross-object transfers and fallthrough**

> **DEC-A05 r2** · UNANIMOUS · SHA-256 `414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5`  
> *Cross-object transfer and fallthrough rule (B2) [editorial title]*
>
> Prefer a verified whole-TU shared-tail group. For each cross-piece fallthrough prove physical adjacency. For each fixed relative branch prove decoded endpoints, field width, next instruction address, in-place cover, exact emitted bytes, and zero relocation over its displacement. Cover interior, entry and cut-spanning rel8 using checked piece-local expressions for supported ASM encodings. Reject edges whose proof depends on global or per-object legacy placement. Use existing valid symbolic rel32 bindings and require independent proof before adding interior exports. Require final link evidence and reject unsupported outgoing compiled-slice rel8.

> **DEC-B19 r2** · UNANIMOUS · SHA-256 `5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d`  
> *Plan-level exclusion of legacy-placed objects and fallthrough adjacency*
>
> The placement planner rejects any fixed-displacement cross-object transfer whose source-to-target span includes an object placed in legacy layout, whether by the global --legacy flag or the automatic per-object Unplaceable fallback, and records an adjacency obligation for every ASM piece that falls through into the next object, rejecting the plan if that successor is not the original in-place object.

> **DEC-C05 r4** · UNANIMOUS · SHA-256 `5d51b22bcefa20d67842a75dd643b9ee3856fd9486b15318bb977ea80b76ce68`  
> *Fix B1 and unified Fix B2 inside the single PlacementPlan [editorial title]*
>
> Implement Fix B1 (leading-byte region base first_entry_addr - first_entry_off gated on E0 RegionMatch of [0,k), zero overlap/foreign entry, branch analysis using physical table_start) and Unified Fix B2 inside the single derived PlacementPlan: keep extern symbolic rel32 for exported entries; emit remaining cross-object ASM relative branches (B2-interior, B2-entry, B2-span, and rel32-interior such as 0x2f6df with zero M2 OMF PUBDEF synthesis) via NASM piece-local label expressions (preferred, using decoded next_ip = ia + insn.size and typed encodings with assembled-byte verification) or verified literal displacement fallback, requiring verified original target identity, zero intersecting relocation over fixed displacement fields, and physical adjacency for every live cross-piece fallthrough per DEC-A05 r2, strictly rejecting any span containing a global --legacy or automatic per-object Unplaceable legacy-placed object (DEC-B19 r2), recording Build A placement debt, and requiring IntegratedResult with hardened wc1.compare (DEC-A03 r2). Qualify IntroOpSyncSound standalone regression tests by mode: rejected under legacy or B2-disabled, accepted only with explicit B2-span debt under in-place B2, zero debt as Group B.


### 5.5 Whole-TU promotion (shared tails, Group B)

> **DEC-A13 r1** · UNANIMOUS · SHA-256 `c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c`  
> *Admit an independent exact Group B proof*
>
> Permit the exact Group B whole-TU promotion independently of general B1, B2 and matcher rollout only with a commit-bound strict raw-object RegionMatch equivalent to the intended production rules, ordinary file and dual-compiler checks, actual in-place Build A with typed loader comparison, and preserved cited T4 checks or explicit owner approval for changes.

> **DEC-C06 r2** · UNANIMOUS · SHA-256 `ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23`  
> *Proof-gated multi-function TUs; Group B pilot [editorial title]*
>
> Admit proof-gated multi-function ReconstructedTUs when the whole compiled object passes RegionMatch and Build A IntegratedResult, preferring whole-TU co-compilation over B2 placement debt for shared-epilogue clusters. Pilot E1 Group B (IntroOpPlaySound 0x2315c, IntroOpSyncSound 0x23170, IntroOpWaitSound 0x231cc) as an independent -5r TU without waiting on generic B2, subject to owner confirmation of AGENTS.md ground-rule wording, dual-compiler checks, full make verify, and owner review of any xfailed PLAYFLIC test adjustment.

> **DEC-B06 r1** · UNANIMOUS · SHA-256 `22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc`  
> *Proof-gated multi-function TUs*
>
> A ReconstructedTU may contain several functions when the whole compiled object passes production RegionMatch (all publics MATCH, original spacing) and Build A is IDENTICAL. Immediately: Group B (IntroOpPlaySound, IntroOpSyncSound, IntroOpWaitSound) in one -5r TU. AGENTS.md's "one function per C object" ground rule is reworded accordingly, subject to owner approval. No consolidation is performed on the basis of heuristic CU signals.


**Owner checkpoints recorded in these decisions:**

- the AGENTS.md "one function per C object" ground-rule wording (DEC-B06, DEC-C06);
- any change to a cited T4 check or xfail (DEC-A13, DEC-C06).

### 5.6 Data ownership, Fix B3 and authority identity

> **DEC-A06 r1** · UNANIMOUS · SHA-256 `4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac`  
> *Separate storage identity from provider*
>
> Keep canonical storage and alias evidence independent of physical suppliers. Admit B3 initially for fully verified whole segments only, once a pilot justifies deployment and the strict transform and link tests pass.

> **DEC-B08 r1** · UNANIMOUS · SHA-256 `dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a`  
> *Fix B3 deferred to the M3 track*
>
> E5's Fix B3 is recorded as feasible for the verified subset. Its production implementation is scheduled after M2, or earlier only if a not-done function requires it. RFC §8.2's constraints 1–5 remain binding preconditions.

> **DEC-C10 r3** · UNANIMOUS · SHA-256 `a8756e094f269537ac7342f0d2c9361af01a4a63c54c1966a9c9d5fe6bea1e19`  
> *Data ownership separation, post-M2 B3, raw authority [editorial title]*
>
> Keep semantic_owner separate from physical_provider and defer Fix B3 to the post-M2/M3 track (triggered by justified need such as Q-B08). Admit B3 initially for strictly verified whole segments over the shared strict OMF32 subset (DEC-C09 r3) with RFC §8.2 constraints 1-5 and rev-e5-02 mutability/aliasing guards. Enforce DEC-A14 r1 on all authority-bearing receipts: normalized CONST digests may group candidates only and never substitute for exact raw-artifact identity on authority reuse. Any future CONST inter-literal alignment-gap rule must additionally: apply identically in matcher and build.place(), force Build A physical_provider = ASM, be explicitly disclosed in the proof receipt, and require independent extent/access evidence ruling out computed or overlapping reads (OBJ-A11).

> **DEC-C09 r3** · UNANIMOUS · SHA-256 `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b`  
> *Shared strict OMF32 codec before B3 or extraction [editorial title]*
>
> Before landing Fix B3 or any future selective OMF extraction pilot (post-M2), share one tested strict OMF32 record/fixup codec (record bounds, nonzero checksums, preserved explicit FRAME encodings, persistent cross-record THREAD, format/linker-verified record-length bounds) across verification and admitted OMF transforms, while leaving permissive library-signature readers untouched and avoiding unnecessary omfpatch refactoring during M2.

> **DEC-A14 r1** · UNANIMOUS · SHA-256 `bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7`  
> *Bind verification reuse to raw artifacts*
>
> Bind each authority-bearing verification or integration receipt to the exact raw artifacts and the verified context used in its claim. A normalized CONST digest may group candidates but shall never substitute for raw identity on authority reuse; reverify before accepting any different raw artifact.


"RFC §8.2 constraints 1–5", as cited by DEC-B08 and DEC-C10, means constraints 1–5 of §8.2 of the pinned **baseline** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`. They are incorporated by reference in §8 (row B-2). The pinned Russian text is normative; the English rendering in `editorial-notes.md` §3 is explanatory.

### 5.7 Selective OMF extraction

> **DEC-A07 r2** · UNANIMOUS · SHA-256 `5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d`  
> *General extraction deferred; narrow pilot conditions [editorial title]*
>
> Defer general extraction. Permit a narrowly justified pilot only with owner authorization for any source-gate semantics change, a region proof bound to the raw input object, independently established code and data bounds and targets, record and symbol handling validated for the admitted subset, and independent proof of the transformed artifact and actual link. Reject unsupported inputs.

> **DEC-C08 r2** · UNANIMOUS · SHA-256 `6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00`  
> *No selective extraction in M2; post-M2 pilot preconditions [editorial title]*
>
> REJECT adopting experiments/build_codegen/e4/omf_extract.py@e6150b8 or selective OMF extraction during M2 or as a default consolidation path. Whole-TU RegionMatch is the primary integration path. Any future narrow post-M2 extraction pilot requires: (1) explicit owner decision on Gate-2 / match --all semantics for src files with mismatching publics (DEC-B09); (2) proven canonical-TU benefit; (3) implementation over the shared strict OMF32 subset (DEC-C09) fixing confirmed Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), Probe 5c (typed table/code model), and rev-e4-01 F1-F4; and (4) post-transform verification and Build A IntegratedResult (without mandating unproved 64-fixup chunking or exhaustive Wave 4B).


### 5.8 Behavioural verification (T4)

> **DEC-A11 r1** · UNANIMOUS · SHA-256 `0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78`  
> *Certify paired starting state independently of outputs*
>
> A T4 pair must execute from equivalent per-side CPU, memory and declared mutable dependency state for each case. Implement independent initialization or a certified checkpoint with host- and guest-write accounting. Keep the effects compared by existing tests separate from state restoration. Report unsupported state when equivalence of inputs cannot be established. Apply this requirement to affected current witnesses before adopting multi-function extensions.

> **DEC-A16 r1** · UNANIMOUS · SHA-256 `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785`  
> *Implement and audit paired T4 state before reclassification [editorial title]*
>
> Implement DEC-A11 for current T4 pairs using independent equivalent initialization or a certified checkpoint. Account for CPU context including EFLAGS, mapped regions and permissions and their contents, host and guest writes, allocator state, and declared mutable host and stub dependencies. Report unsupported cases when equivalence cannot be established. Preserve existing output assertions and record the initial-state method and evidence in the production T4 audit. Before landing, run the full existing T4 suite once with the rule enabled and present any changes to existing test meaning or expected status to the owner. Record the five EV-3 witness outcomes as observations, establish attribution separately, and change inventory or DONE status only on current authorized verification evidence.

> **DEC-C16 r3** · UNANIMOUS · SHA-256 `d4fe9e9c5ce5769a66512b4f53cb098344d2bd5b7d233d64c2837f2f217fecbb`  
> *T4 witness observations and complete paired-state mechanism [editorial title]*
>
> Record the independently observed 3-passing (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2-persistent (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc) witness results under checkpoint restoration strictly as diagnostic observations; attribute root causes and update inventory, DONE, or xfail status only after production-equivalent verification, nonce-bound WC1_T4_AUDIT_LOG evidence, full T4 suite regression (Q-B05), and owner review. Adopt complete paired starting-state equivalence (per DEC-A11) in tools/wc1/cemu.py::run_pair across all T4 tests via independent initialization or a certified checkpoint: identical per-side CPU context (general registers, EFLAGS, segment registers, ESP), full set of mapped memory regions covering both host and guest writes, emulator allocator state, and declared mutable stub state (stubs must keep mutable state in emulator memory or declare a per-run reset, else report UNSUPPORTED); keep state restoration strictly separate from compared test effects and log restored state in WC1_T4_AUDIT_LOG.

> **DEC-A08 r2** · UNANIMOUS · SHA-256 `2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31`  
> *Demand-led E6 boundary machinery [editorial title]*
>
> Apply certified paired-state equivalence to affected current T4 witnesses. Before a new cited witness relies on a multi-function or substitution boundary, prove the allowed per-side execution and dependency edges, symmetric declared substitutions, exercised callback ABI and typed pointer identity, and production t4spec audit parity. Add boundary machinery only for demonstrated witness requirements.

> **DEC-C11 r2** · UNANIMOUS · SHA-256 `46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090`  
> *Paired state now; E6 machinery on demand [editorial title]*
>
> Keep full paired initial-state symmetry (DEC-A11/DEC-B18/DEC-C16) mandatory immediately for ALL T4 tests (single- and multi-function), independent of E6. Adopt E6 multi-function machinery (contiguous VerificationBoundary, symbol_aware_reloc primary + c_entry_hook defense in depth, generator callbacks with pre-restore ABI checks on PRESERVED_REGS ebx/ecx/edx/esi/edi/ebp plus esp, R2 typed pointer identity, and full t4spec production audit parity per DEC-A08) on demand whenever any M2 or post-M2 witness requires substituting an intra-TU sibling, executing real callbacks, or comparing logical pointer identities; treat switch-table relaxation and LogicalConstDataPtr (EXP-4) as optional extensions when needed.


### 5.9 Compiler behaviour, presets and toolchain paths

> **DEC-B10 r1** · UNANIMOUS · SHA-256 `51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0`  
> *Corrected Watcom 10.0a alignment model*
>
> The RFC and docs/subsystems/compiler.md state that 10.0a function spacing inside an object is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot, and 1 byte under -os/-od, with a PARA _TEXT SEGDEF for -ot. OW2 uses 16 bytes under -4r and -5r. This describes compiler behaviour and is not a claim about original CU flags.

> **DEC-C13 r3** · UNANIMOUS · SHA-256 `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02`  
> *E2 alignment matrix replaces RFC alignment premise [editorial title]*
>
> Replace RFC §2.2.5 alignment premises with E2 empirically measured compiler behavior: Watcom 10.0a function spacing is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot (with PARA 16-byte _TEXT SEGDEF for tested -ot), and 1 byte under -os/-od; OW2 uses 16 bytes under -4r and -5r. Keep -4r as the single-file project default with additive E7 presets (DEC-B11), rank -5r as the first-tried candidate family for multi-function -ot TUs requiring 4-byte spacing without claiming it was the universal 1994 project flag, and keep EXP-2/Q-B06 (5r -d1+ -zp1 and 5r -od) as optional additive probes.

> **DEC-B11 r1** · UNANIMOUS · SHA-256 `c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5`  
> *Presets remain additive; no global default change*
>
> The merged E7 presets stay additive to each file's declared flags; the project default stays -4r; S(f) is recorded per reconstructed-TU context and never promoted to a CU flag claim.

> **DEC-A09 r1** · UNANIMOUS · SHA-256 `2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e`  
> *Keep compiler search evidence scoped*
>
> Keep the merged additive presets and declared compiler policy. Record S(f) with its full measured context and coverage. Treat heuristic scores and freshness snapshots as scheduling inputs only.

> **DEC-A12 r1** · UNANIMOUS · SHA-256 `40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37`  
> *Protect effective Watcom 10.0a paths*
>
> Stage or reject effective Watcom 10.0a paths before launch. Prove that staging preserves source identity, include resolution, flags and output attribution, and isolate temporary outputs per compile. Report path failures as toolchain errors. Use measured limits on effective compiler-facing paths.

> **DEC-C04 r2** · UNANIMOUS · SHA-256 `083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37`  
> *Measured compiler-facing path guard in wc1.oldcc [editorial title]*
>
> Implement a measured compiler-facing Windows-path length guard and short-path staging policy in tools/wc1/oldcc.py checking all compiler-facing arguments (source, -fo, -i=, TMPDIR, translated Z: paths), failing fast with [TOOLCHAIN ERROR] before Watcom 10.0a path-buffer crashes while verifying unchanged compile/include semantics across checkout depths. (The three t3_audit.py R3 defects from rev 1 are delivered and closed as of EV-3 main@17733f9.)


### 5.10 Original CU evidence

> **DEC-A10 r1** · UNANIMOUS · SHA-256 `8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e`  
> *Record historical alternatives and premises*
>
> Store original CU evidence separately from scope and build inputs. Apply hard constraints only with their premises independently established. Do not drive automatic source consolidation from the measured signals.

> **DEC-C12 r2** · UNANIMOUS · SHA-256 `7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa`  
> *CU recovery as analyst-facing constraint graph [editorial title]*
>
> Explicitly REJECT _DATA/_BSS staircase splits, call_locality_drop, none16 auto-splits, weighted CU boundary scoring, empty-S(f) auto-splitting, and any automatic mutation of analysis/modules.toml or automatic source consolidation. Maintain original CU recovery strictly as an analyst-facing premise-carrying constraint graph (storage deferred to M3): shared_epilogue as a one-directional merge constraint under verified compiler/linker provenance; non_16_aligned_start evaluated at the actual segment base under a PARA-segment premise (with measured corpus precision 0.800/0.836/0.618, never 100%); shared_const_string_literal as conditional premise-dependent evidence requiring exclusion of explicit shared externs and linker pooling; filenames, zero16, none16, style_transition, and S(f)-disjointness as candidate generators preserving competing hypotheses.


### 5.11 Engineering style

> **DEC-C14 r1** · UNANIMOUS · SHA-256 `66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf`  
> *Reject Premature Multi-Backend Framework Abstractions in Warcraft I*
>
> REJECT introducing abstract multi-backend/plugin frameworks (`ICompilerBackend`, `IObjectFormatPlugin`, generic binary-rewriting frameworks) into `tools/wc1/`. Enforce architectural portability strictly via clean module boundaries and data-oriented contracts (`omf.py`, `match.py`, `build.py`, `cemu.py`).


(DEC-B15 is quoted in §5.2.)

## 6. Rejected alternatives (UNANIMOUS_REJECTED)

> **DEC-B07 r1** · UNANIMOUS_REJECTED · SHA-256 `2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b`  
> *T4 paired-execution state symmetry*
>
> cemu.run_pair (or t4spec) restores, before the C run, all memory written during the original run (by code or stubs), or fails closed when a stub writes outside the restored set. The audit log records the restored set. After adoption, every xfailed "reference-C divergence" is re-evaluated, and its blocker category is changed only by evidence.

> **DEC-B16 r1** · UNANIMOUS_REJECTED · SHA-256 `ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c`  
> *Inventory reclassification from probes*
>
> wc1.m2_inventory reclassifies 0x2315c/0x23170/0x231cc as "joint-TU T3 available (DEC-B06)", 0x1e380/0x2e96c/0x2efd0/0x2f73c as "fixed-displacement cross-object branches (DEC-B04)", and the IntroOpWaitSound divergence as "T4 harness state asymmetry (DEC-B07)".

> **DEC-B17 r1** · UNANIMOUS_REJECTED · SHA-256 `0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1`  
> *Integrated selective extraction (Approach D) as the M2 strategy*
>
> Selective OMF extraction is adopted in production as the mechanism for advancing M2.

> **DEC-C03 r1** · UNANIMOUS_REJECTED · SHA-256 `2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896`  
> *Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (Invariant V4)*
>
> In both E0 `RegionMatch` and Stage-3 Fix B3, explicitly exempt 1..3-byte alignment padding gaps in `CONST` **if and only if** all 5 conditions hold: (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A.


The baseline RFC's excluded directions (§19.2) also remain excluded. They are incorporated by reference (§8, B-7), not re-voted:

- Approach B as a T3 proof mechanism;
- Approach C as the only matching model;
- a C superoptimizer;
- automatic changes to scope, progress or gates;
- mass reorganisation of existing sources;
- synthesized ASM inserts.

## 7. Withdrawn and superseded decisions

| Withdrawn | Rev | Withdrawn by | Replacements (ledger) | Replacement status |
|---|---|---|---|---|
| DEC-B01 | r2 | claude | DEC-A01, DEC-C07 | DEC-A01: UNANIMOUS, DEC-C07: UNANIMOUS |
| DEC-B02 | r2 | claude | DEC-A02, DEC-C02 | DEC-A02: UNANIMOUS, DEC-C02: UNANIMOUS |
| DEC-B03 | r2 | claude | DEC-A03, DEC-C01, DEC-C05 | DEC-A03: UNANIMOUS, DEC-C01: UNANIMOUS, DEC-C05: UNANIMOUS |
| DEC-B04 | r2 | claude | DEC-A05, DEC-C05 | DEC-A05: UNANIMOUS, DEC-C05: UNANIMOUS |
| DEC-B09 | r2 | claude | DEC-A07, DEC-C08 | DEC-A07: UNANIMOUS, DEC-C08: UNANIMOUS |
| DEC-B12 | r1 | claude | DEC-A08, DEC-C11 | DEC-A08: UNANIMOUS, DEC-C11: UNANIMOUS |
| DEC-B13 | r2 | claude | DEC-A10, DEC-C12 | DEC-A10: UNANIMOUS, DEC-C12: UNANIMOUS |
| DEC-B18 | r2 | claude | DEC-A11, DEC-C16 | DEC-A11: UNANIMOUS, DEC-C16: UNANIMOUS |
| DEC-B20 | r1 | claude | DEC-A03, DEC-C15 | DEC-A03: UNANIMOUS, DEC-C15: WITHDRAWN_SUPERSEDED |
| DEC-B21 | r2 | claude | DEC-A02, DEC-C10 | DEC-A02: UNANIMOUS, DEC-C10: UNANIMOUS |
| DEC-B22 | r1 | claude | DEC-A12, DEC-C04 | DEC-A12: UNANIMOUS, DEC-C04: UNANIMOUS |
| DEC-C15 | r2 | gemini | DEC-A02, DEC-A03, DEC-C02 | DEC-A02: UNANIMOUS, DEC-A03: UNANIMOUS, DEC-C02: UNANIMOUS |

A withdrawn decision has no normative force. Its obligations live only in the replacement texts quoted in §5.

## 8. Baseline provisions incorporated by reference

The provisions below of the pinned baseline `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13` are **incorporated by reference** and remain binding at their pinned text.

- They are not re-voted. No ledger decision relaxes them.
- Where an accepted decision changes or replaces part of a provision, the "Governing decision" column names that decision, and the decision governs.
- The Russian original is normative. English summaries here are explanatory.

| Ref | Baseline provision | Status in this RFC | Governing decision where changed or replaced |
|---|---|---|---|
| B-1 | §13 invariants 1–10 (Build A IDENTICAL necessary but not sufficient; no matcher weakening; no ignored relocations; no MATCH with unresolved essential dependencies; no ASM inserts in C; no weakening of T4 and anti-cheat; fixed finish line; no hiding divergences by moving function boundaries; no mixing of temporary adapters with proof of original structure; reproducibility and fail-closed refusal) | Incorporated, all ten | None replaced. Invariant 1's fixup equality is evaluated as DEC-A03 r2 specifies: the existing comparison is kept, typed loader comparison and raw-occurrence validation are added, and raw serialization differences are diagnostic. DEC-A02/DEC-C02 strengthen invariants 2–4; DEC-A11/DEC-A16/DEC-C16 strengthen 6; DEC-A01 restates 7; DEC-A06/DEC-A10/DEC-C12 strengthen 9. |
| B-2 | §8.2 constraints 1–5 on Fix B3 (no `wc1_anchor_*` in `src/`/`analysis/`/`tests/`; full data and pointer verification before anchoring; FIXUPP32/THREAD and FRAME support; no compensation for layout errors; verified removal of artificial `extern` strings) | Incorporated, all five, as binding preconditions of any Fix B3 | Scheduling and scope: DEC-B08 r1, DEC-A06 r1, DEC-C10 r3. Codec: DEC-C09 r3. Receipts: DEC-A14 r1. §8.2's status line "not approved for production until E5" is replaced by these decisions. |
| B-3 | §6.1 Post-Codegen Symbolic Relocation Equivalence and its unconditional prohibitions, §6.2 policy for extracted-region references, and §6.3 data identity, string pooling and aliasing rules | Incorporated in their original scopes. §6.1 governs any post-codegen OMF transform, including B3. §6.2 governs an extraction pilot. §6.3 governs the data mappings to which it applies, including B3 under §8.2. | DEC-A07 r2 and DEC-C08 r2 govern a later extraction pilot. DEC-A05 r2, DEC-B19 r2 and DEC-C05 r4 govern B2 placement. Baseline §6.4 explains the distinction between B2 placement and extraction. |
| B-4 | §16 minimum admission criteria, per mechanism | Incorporated as **minimum** criteria; the decisions add to them (§10) | See rows B-4a to B-4g. |
| B-4a | Strengthened `wc1.match`: 100% E0; re-audit of all 519 T3 performed and analysed; `make verify` green; Build A IDENTICAL | Incorporated except the audit population | The audit population and trigger are replaced by DEC-A02 r2 / DEC-C02 r2: every live declared T3 and the file gate at cutover; all 55 controls as production tests. |
| B-4b | CodeRegion contract + Fix B1 + Fix B2: E0 and E1/E2 passed; type/state isolation CandidateRegion→VerifiedRegion→PlacementPlan; negatives for a corrupted jump table and for Fix B2 under `--legacy`; Build A IDENTICAL on real candidates | Incorporated except the CandidateRegion type | DEC-B14 r1 and DEC-C01 r3: no separate CandidateRegion type in M2; VerifiedRegion is matcher-minted and PlacementPlan is derived. Placement rules: DEC-A04, DEC-B05, DEC-A05, DEC-B19, DEC-C05. Integration: DEC-A03. |
| B-4c | Fix B3: E5 passed (THREAD, multi-segment, FLAT/DGROUP); full data byte and pointer verification; no `wc1_anchor_*` leakage; `make verify` green; Build A IDENTICAL | Incorporated | Scheduling and scope: DEC-B08, DEC-A06, DEC-C10, DEC-C09. |
| B-4d | Selective extraction: E3, E4, E5 passed; §6.1 equivalence with fail-closed negatives (outgoing rel8, interior target, ambiguous symbol, shift inside a structure); full provenance; `make verify` green; Build A IDENTICAL | Incorporated as minimum criteria for any post-M2 pilot | DEC-A07 r2 and DEC-C08 r2 add the owner gate-2 decision, proven benefit, strict codec and fixed E4 defects. Whether a pilot's provenance needs the persistent store that DEC-B14 r1 defers until a consumer exists is DQ-07, not decided here. |
| B-4e | Multi-function T4: E6 passed; verification_boundary + dependency_substitution_policy; anti-cheat, pointer-identity and callback negatives; fail-closed refusal of Isolated mode | Incorporated | Adoption on witness demand only: DEC-A08 r2, DEC-C11 r2. Paired state first: DEC-A11, DEC-A16, DEC-C16. |
| B-4f | Calibrated presets and idiom catalog: multidimensional E7 report; compiler regression tests per idiom entry; preconditions and T4 run per auto-transformation; no `make verify` regressions | Incorporated | Presets: DEC-A09 r1 and DEC-B11 r1 (additive, `-4r` default). The idiom-catalog criteria apply to any future catalog or auto-transformation. |
| B-4g | Automated CU recovery: E8 control-set validation; storage in `analysis/compilation_units.toml` without changing `modules.toml` or `wc1.progress`; epistemic labelling | **Replaced** | DEC-A10 r1 and DEC-C12 r2: CU evidence is analyst-facing only, with no automatic splitting or consolidation. DEC-B14 r1: no CU storage in M2 (DQ-06). |
| B-5 | §15 audit-handling rules: no automatic downgrade, no weakened checks, no scope change; no keeping a known-bad T3 proof; confirmed errors are resolved or the status is changed per `docs/GOAL.md` with the owner | Incorporated | The audit population and trigger are replaced by DEC-A02 r2 / DEC-C02 r2 (B-4a). |
| B-6 | §12.2 S(f) record (full observed set per context, five outcomes per (f, config), explored-space record) and the empty-intersection rule (never automatic evidence of a boundary) | Incorporated | Consistent with DEC-A09 r1, DEC-B11 r1 and DEC-C12 r2, which reject empty-S(f) auto-splitting. |
| B-7 | §19.2 excluded directions (Approach B as T3 proof; Approach C as the only model; C superoptimizer; automatic scope, progress or gate changes; mass reorganisation of existing sources before E0–E8; synthesized ASM inserts) | Incorporated | DEC-C14 r1 adds the framework exclusion. DEC-B17 r1 rejects extraction as the M2 strategy. Proof-gated consolidation of specific clusters is governed by DEC-B06, DEC-C06 and DEC-A13 (DQ-16). |

Other baseline sections provide context (see §9). References inside incorporated provisions still identify the applicable checks. The accepted ledger decisions supersede baseline §3.

## 9. Mapping from the baseline RFC (editorial)

| Baseline section | Disposition in this revision |
|---|---|
| §1, §3 items 1–4 (decoupled granularities; matcher gaps; CandidateRegion→VerifiedRegion→PlacementPlan; transform invariant) | Context; not incorporated as text. Their substance is carried by the ledger: the entity set is narrowed by DEC-B14 and DEC-C01; the §6.1 transform invariant is incorporated (§8, B-3). The matcher gap closure becomes DEC-A02/DEC-C02 with a live cutover audit instead of the baseline §15 one-off audit classification. |
| §3 item 9, §8.2, §8.3 (Fix B3 "strategically necessary") | Feasible but deferred: DEC-A06, DEC-B08, DEC-C10, DEC-C09. §8.2 constraints 1–5 are incorporated (§8, B-2). |
| §3 item 11, §6, E4 (selective extraction "preferred research direction") | Deferred and bounded by DEC-A07 and DEC-C08. Extraction as the M2 strategy is rejected (DEC-B17). The §6.1 invariant and the §6.2/§6.3 policies remain the binding preconditions of any future pilot (§8, B-3). |
| §3 item 12, §11 (Isolated/Group/Integrated T4) | Paired state first (DEC-A11, DEC-A16, DEC-C16). E6 machinery on demand (DEC-A08, DEC-C11). |
| §3 item 13, §12 (calibration, S(f)) | DEC-A09 and DEC-B11. The alignment premise is corrected by DEC-B10 and DEC-C13. The §12.2 five-outcome record of S(f) and the empty-intersection rule are incorporated (§8, B-6). |
| §3 item 15, §9 (CU recovery, `analysis/compilation_units.toml`) | Analyst-facing only; storage deferred (DEC-A10, DEC-C12, DEC-B14). |
| §4.2, §10.2, §10.3 (entities, provenance, invalidation) | Persistent provenance deferred until a consumer exists (DEC-B14). Reuse authority binds to raw artifacts (DEC-A14). |
| §7.2 (Fix B1/B2) | Replaced by DEC-A04, DEC-B05, DEC-A05, DEC-B19 and DEC-C05. These add legacy-object exclusion, fallthrough adjacency and the no-relocation-over-displacement rule. |
| §14 (E0–E8 programme) | Executed. Interpretation in `experimental-interpretation.md`. |
| §15 (mandatory re-audit of 519 T3) | Superseded by the cutover rule: every live declared T3 must pass at cutover (DEC-A02, DEC-C02). The baseline's audit-handling rules are incorporated (§8, B-5). |
| §16 (production admission criteria) | Incorporated as minimum criteria (§8, B-4a to B-4g), with the governing decision named where a criterion is changed or replaced. |
| §17 (open questions) | Moved to `deferred-questions.md`, each with its boundary and reopening condition. |
| §18.1 (phases A–E) | Replaced by `implementation-roadmap.md`, which follows DEC-A01, DEC-A15 and DEC-C07. |
| §18.2, §19 (portability, risks, exclusions) | §18.2 and §19.1 are context (§3 here separates the applicability classes). §19.2 exclusions are incorporated (§8, B-7); DEC-C14 adds the framework exclusion. |

## 10. Acceptance and verification gates

The existing gates are unchanged: `make verify`, `make goal` (gates 1–3), the tier definitions and the classification rules (DEC-A01). Every new mechanism is additionally gated as follows.

| Contract | (i) Architecture | (ii) Agreed acceptance test (from the decision texts, the r04 acceptance-criteria tables of all three Architects, and baseline RFC §16) | (iii) Executed? |
|---|---|---|---|
| Verifier (§5.2) | Agreed | All 55 E0 controls as production tests. Strict raw-OMF negatives (bounds, checksum, single MODEND, THREAD, FRAME, unsupported records). Function-extent and trim-target negatives. Every live declared T3 and the file gate pass at cutover. No import from experiments/. | **No.** E0 prototype audit only (519/519 at the experiments baseline). |
| Integration and comparator (§5.4, DEC-A03) | Agreed | Actual assemble/link/provider/comparison receipt. Occurrence validation before deduplication. The old comparator's three negatives (cleared OBJ_EXEC, changed src_type, contradictory duplicate) must fail. Baseline Build A must pass. Serialization deltas reported as diagnostics. | **No.** A R2 P1/P2 and A R4 P1 are probes. |
| Receipt authority (DEC-A14) | Agreed | Every authority-bearing verification or integration receipt binds the exact raw artifacts and verified context **when minted**; a receipt without that binding is not authority. On reuse, two raw artifacts sharing a normalized digest, or changed verified context, force a fresh verdict. The exact Group B proof meets this locally, without a cache (DEC-A13). | **No.** |
| Paired T4 state (§5.8) | Agreed | Coverage of every current T4 route: `cemu.run_pair` and the 12 legacy hand-written nodes that bypass it (`docs/ANALYST_GUIDE.md@17733f9`), each migrated or checked by an equivalent audited path with its output assertions preserved. Independent initialization or a certified checkpoint covers declared mutable host dependencies and stub state. Carry/EFLAGS, host-write, allocator and mutable-stub controls exercise the paired-state rule. Report UNSUPPORTED when equivalence cannot be established. Full existing T4 suite run once with the rule enabled (Q-B05). Changes to test meaning or expected status presented to the owner. Nonce-bound audit log. | **No.** B R3-P1 and A R3 P1 are disposable probes under tested checkpoints (3 pass, 2 persistent), not certified complete state. |
| Compiler paths (DEC-A12, DEC-C04) | Agreed | Measured effective-path envelope. Rejection outside it with `[TOOLCHAIN ERROR]`. Staging parity for source, includes, flags and output; isolated outputs. | **No.** |
| B1 (DEC-A04, DEC-B05, DEC-C05) | Agreed | Leading region and its relocations verified. Corrupted-table, wrong-base, out-of-extent and overlap negatives. Actual Build A. | **No.** B R0 P6 probe link only. |
| B2 (DEC-A05, DEC-B19, DEC-C05) | Agreed | Mode-qualified IntroOpSyncSound tests (rejected under legacy or B2-disabled; accepted with B2-span debt in place; zero debt as Group B). MissionDefeat entry and fallthrough. A prefixed rel8. Global and per-object legacy negatives. Zero relocation over fixed displacements. Final link evidence. | **No.** B R0 P5 and A R3 P2 probes only. |
| Group B whole TU (DEC-A13, DEC-C06, DEC-B06) | Agreed | Commit-bound strict raw-object RegionMatch. Ordinary file gate and dual-compiler checks. Actual in-place Build A with typed loader comparison. Full `make verify`. Cited T4 checks preserved or owner-approved. Owner confirmation of the AGENTS.md wording. | **No.** E1 and B R0 P3 establish feasibility only. |
| Fix B3 (§5.6) | Agreed (deferred) | Strict whole-segment verification, RFC §8.2 constraints 1–5, rev-e5-02 alias/mutability guards, shared strict codec (DEC-C09), transform and link proof. Any gap rule needs independent extent/access proof. | **No** (post-M2). |
| Extraction pilot (§5.7) | Agreed (deferred) | Owner gate-2 decision. Proven canonical-TU benefit. Shared strict codec with fixed THREAD, PUBDEF, typed-table and F1–F4 defects. Post-transform verification and IntegratedResult. | **No** (post-M2). |
| E6 machinery (DEC-A08, DEC-C11) | Agreed (on demand) | Per witness: per-side edges, symmetric substitution, callback ABI before restoration, typed pointer identity, production audit parity. | **No.** |
| Presets / alignment (§5.9) | Agreed | Documentation matches the measured matrix. Presets additive. EXP-2 optional. | Presets merged before EV-1 (E7 production campaign). The documentation change is **not executed.** |
| CU evidence (§5.10) | Agreed | Analyst-facing only. Shared-literal and leading-table counterexamples. No mutation of scope, build or sources. | **No** storage or tooling in scope. |

## 11. Objection history

The objection ledger (`02-OBJECTION-LEDGER-v2.json`, `aaf68de7…`) records 66 objections:

- **64 RESOLVED:** all three Architects recorded a closing disposition in frozen responses.
- **2 WITHDRAWN** by their originating Architect: OBJ-C09 and OBJ-C13.

None is open. The closing round for each objection, and the decisions it references, are listed per decision in `decision-rationale.md`. Two closures settle questions that are not settled elsewhere:

- **OBJ-A24, closed r06.** Raw LE grouping and fixup-page offsets stay diagnostic. DEC-C15 r2 was withdrawn and DEC-A03 r2 governs.
- **OBJ-B22, closed r07** with RESOLVED from all three. The architectural premise is removed by DEC-A02, DEC-C02 and DEC-A14 together with the rejected DEC-C03. The forensic question of CONST pad variance is DQ-04 in `deferred-questions.md`.

## 12. Ledger integrity notes (Secretary rulings)

Draft revision 1 reported five ledger items in this section. The Secretary ruled on them in `04-CORRECTION-NOTE.md` (`aa57ab0e…`) and rebuilt the ledgers from the same frozen responses. This draft now quotes the corrected canonical ledger, `00-CANONICAL-LEDGER-v2.json` (`dc6bda93…`).

The Secretary's comparison found the same `(id, status, current_revision, proposition_sha256)` for all 54 decisions. The Editor reproduced that comparison independently between `00-CANONICAL-LEDGER.json` (`71d7a988…`) and `00-CANONICAL-LEDGER-v2.json`. Status, revision, proposition text, hash, title, origin and positions are identical for all 54 decisions, and status is identical for all 66 objections. **No ledger proposition changed in that rebuild.**

1. **Withdrawal records on settled decisions — corrected (extraction defect).**
   - The records on DEC-A01, DEC-B06 and DEC-C02 came from the following excerpts, none of which is a withdrawal of that decision:
     - DEC-A01: a Markdown table row listing destinations;
     - DEC-B06: a negated withdrawal sentence;
     - DEC-C02: an identifier inside a replacement list.
   - These records are removed in v2. All three remain UNANIMOUS.
   - The three UNANIMOUS_REJECTED decisions are unchanged: DEC-B07, DEC-B16 and DEC-C03. Their authors did withdraw them, and all three Architects also rejected them. The ledger keeps the rejection as the status and the withdrawal in the history. Both labels mean "not adopted".
   - In v2, DEC-B07 lists no withdrawal record in the canonical file. Its withdrawal remains in the full ledger history. This does not affect status.
2. **DEC-C15 revision hint 4 — corrected.** The stray record is gone. DEC-C15 r2 is recorded as withdrawn by its author, with replacements DEC-A02 r2, DEC-C02 r2 and DEC-A03 r2. The §7 table is unchanged.
3. **OBJ-A24 resolving decisions — corrected.** OBJ-A24 now resolves to DEC-A02, DEC-A03, DEC-C02, DEC-C05 and DEC-C15, and it is closure-eligible. Its status (RESOLVED) is unchanged.
   - The rebuild also filled in or widened `referenced_decision_ids` for 46 other objections. That includes OBJ-A22, OBJ-A23 and OBJ-B08, which were previously empty. No objection status changed.
   - In draft revision 2, `decision-rationale.md` was not regenerated, so its per-decision lists of "objections referencing it" came from the v1 objection ledger. Draft revision 3 updates them to match the v2 objection references in `decision-ledger.json` (`CHANGELOG-v3.md`, O-B1). The lists are non-normative; the v2 objection ledger is authoritative.
4. **Evidence revisions.** The consilium package names EV-2 (`03-EV-2.json`, `0f546837…`) and EV-3 (`03-EV-3.json`, `3d3dfa43…`) as the authoritative post-campaign evidence records. The pinned campaign manifest remains EV-1. §2 uses EV-3 figures also recorded in the frozen r04 responses.
5. **Blank titles — unchanged by ruling.** Editorial titles remain marked `[editorial title]`.

## 13. Editors’ disclosure

The owner reassigned draft revision 3 from Architect B to Architect A after B prepared the partial draft. The reassignment leaves both Architects’ positions and the unanimity requirement intact. The canonical ledger records each Architect’s position on every current revision.

**Architect A (current Editor).** A held DEC-C15 r2 conditional before C withdrew it, and accepted DEC-C05 r4 in r07 once the comparator citation was corrected. A changed OBJ-B22 from DEFERRED in r06 to RESOLVED in r07. The forensic question remains DQ-04.

**Architect B (initial Editor, disclosure retained from revision 2).** B accepted DEC-C15 r2 in r04 and made it conditional in r05, before C withdrew it. B accepted DEC-C07 r2 and DEC-C16 r2 in r03, made them conditional in r04, and accepted r3. On OBJ-B22, B recorded RESOLVED in r04, DEFERRED in r05, and RESOLVED in r06 and r07.

## 14. References

- **Ledgers:**
  - `00-CANONICAL-LEDGER-v2.json` `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`
  - `01-DECISION-LEDGER-FULL-v2.json` `f5523c8c8023d1b34c3cae57ac6cf9ebc8be234a6887a0c34a7836408c9e4594`
  - `02-OBJECTION-LEDGER-v2.json` `aaf68de725dbf2df9730c097444d177b3b7b73e176f458cedd3aa560458510a3`
- **Evidence manifest:** `02-EVIDENCE-MANIFEST.json` `c2d059d32c50e0eccc3bb5c4b66a56fe27e7ee040b965547225abafe24c4c7eb` (EV-1).
- **Frozen closing responses r04–r07:** files 03–14 of the editor inbox, cited by inbox name and SHA-256 in `decision-rationale.md`.
- **Experiments:** `docs/research/build-codegen/summary.md@e6150b8` and the per-experiment reports `docs/research/build-codegen/E0…E8-*.md@e6150b8`, with contracts and results under `docs/research/build-codegen/{contracts,results}/@e6150b8`.
- **Baseline RFC:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`.
- **Production paths cited by decisions:** `tools/wc1/{match,build,emit,omf,omfpatch,compare,le,cemu,emu,t4spec,oldcc,m2_inventory}.py@17733f9`.
