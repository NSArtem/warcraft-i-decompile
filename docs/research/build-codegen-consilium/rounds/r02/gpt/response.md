# Build & Codegen Infrastructure — Architecture Consilium
## Round 2 — Architect A response

The experimental baseline is `e6150b856106ae113bb023300b956fff318da7ef`. I use `a21772b8140b4b07012cde8da7da18ad3f6d56b6` for EV-1 production evidence and `17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9` for EV-3. EV-3 records 912/1010 DONE, 98 outstanding, and a green existing verification gate. The revisions below preserve that gate and its scope. [S, G]

## 1. Dispositions

### Verification and placement

| Challenge | Attacked position | Disposition and resulting position |
|---|---|---|
| B §8 on A02 | Raw admission might imply a complete OMF rewrite, with invalid inputs handled as unsupported. | **UPHOLD** the scope correction. Validate record bounds, nonzero checksums and termination, retain FRAME and model cross-record THREAD where admitted, and reject unknown proof-relevant records. A malformed object gets an invalid-input diagnostic, a valid artifact outside the supported subset gets unsupported, and a failed invocation gets a tool error. None can mint a proof. A02 rev 2 leaves transform coverage demand-led. [P, E0, E4, A0 Q3] |
| C §3 U4 and §8 on A02, B P1 | Round 0 lacked evidence for the full current matcher cohort. | **UPHOLD** the evidentiary correction. B P1 reports E0 results for all 539 declared T3 functions on EV-1 main. C reports an independent check of the 20 additions. These results exercise E0 as it existed, and the strict production implementation still owes a fresh audit. C §3 and B §3 U4 also support bounding local checks to the intended function. Nine E2 losses involved the conservative first-public window. Keep genuine external edges explicit, retain the trim-target guard in both scopes, and test both a true exterior edge and an interior edge displaced by a non-contiguous TU. A02 rev 2. [E0–E3, B1 P1, C1 §3 U4 and §8] |
| C `OBJ-C09`, §3 U6 and §4.6, B §4.1 and §4.6 | A02/A06 would reject natural multi-string CONST pools or make caches checkout-dependent. | **REBUT** the prescribed V4 exemption and the proposed cache normalization for acceptance evidence. The reported varying pad bytes are a real completeness issue. B R1-P2 reports stable fixed-input repeats and path-dependent bytes, so an unconditional flakiness claim remains unestablished. A1 Q2 has two valid literal slots, no direct reference to the gap, and a computed read with a different result. Retaining ASM bytes preserves the Build A storage here and supplies no equivalence proof for the differently initialized C bytes. A06 remains a conservative first admission. A02 rev 2 explicitly keeps the exemption off its critical path. If a later proof excludes a gap on independently established bounds and access evidence, matcher and planner must consume the same policy. Bind authority to the exact raw object. A normalized research digest may group candidates. [E0, E5, E8, B1 R1-P2, C1 §2.1, A1 Q2] |
| B §4.4 and §4.8, `OBJ-B19`, C §8 on A03 and `DEC-C15` | Loader identity requires a measured attribute policy. Provider evidence could become persistent, and a typed fixup comparison could still rely on lossy deduplication. | **UPHOLD** the measurement requirement and make receipts derived. R2 P1 measured parity for object flags, entry/stack descriptors and typed fixups. Raw fixup record order and last-page file length differ. R2 P2 produced three legacy-comparator false passes, including one that survives adding types to the deduplicated projection. A03 rev 2 checks supported loader semantics, validates the raw occurrences before deduplication and keeps materialization distinct from preflight. [P, R2 P1–P2] |
| B `OBJ-B27` and §4.3, C `OBJ-C10` and §4.5 | A04/A05 omit the interaction of B1 cuts, automatic legacy fallback and cross-piece fallthrough. | **UPHOLD.** The physical cut begins at the bound table base. The current builder can move an individual contribution via `Unplaceable` even in the default mode. Conditional `jge` at `0x2f73a` has a distinct fallthrough to the `0x2f73c` cut. A05 rev 2 checks adjacency separately from relative displacement and prohibits fixed edges relying on legacy placement. R2 P3 corrects C’s serial example: `0x20258` is `push ebx`, next `0x20259`. The decoded `pop ebx` at `0x202bb` falls through to the separately discovered `ret` at `0x202bc`. [P, B1 §4, C1 §2.2, R2 P3] |
| C `OBJ-C10` and §8 on A05 | Mandatory synthetic interior `PUBDEF` for every cross-piece rel32 and explicit handling of the rel8 classes. | **UPHOLD** the explicit interior, entry and cut-spanning rel8 cases. **REBUT** mandatory interior exports. C’s nine-site census establishes the edge class. B P5 actually linked the `0x2f6df → 0x2f746` case with a checked fixed-layout opportunity, using literal bytes in that trial. A0 Q2 assembled exact `74 93` and `75 89` through piece-local expressions, without a final link. Preserve native symbolic paths given a valid binding. A synthetic export adds symbol resolution, frame and transformation obligations and remains optional. Compute next IP from the decoded instruction, including prefixes. A05 rev 2. [P, B1 §2 D-5, C1 R1-Probe 1, A0 Q2, A1 Q3] |
| B `D-7` and §4.5, C `OBJ-C13` and §2.4 | My roadmap put Group B behind the general placement stage. C would make production E0 rollout a prerequisite. | **UPHOLD** B’s scheduling objection. B P3 reports an EV-1 export with 542 functions from 535 C files, three matches, Build A identity and both compiler checks. It lacks the complete test/cutover record. **REBUT** the universal rollout prerequisite. An equivalent commit-bound strict region proof plus current file, compiler, integration and test checks is sufficient for this exact promotion. Production already has more wired functions than C objects. Keep the owner checkpoint for changing the old PLAYFLIC reference test or its expected status. Offer the independent path in A13. [E1, P, G, B1 §2 D-7 and §4.5] |
| C `OBJ-C11` and §4.1, applied to the Sync recommendation in A §5 | “Standalone rejected” could survive as an unconditional test. | **UPHOLD** mode qualification. The present standalone cut still fails under stock emission. With B2 off or a legacy dependency, reject. With the checked bridge enabled, accept only after the specific assembly and linked proof and record its fixed-layout debt. Joint TU acceptance needs its own proof and should eliminate these crossing edges. Whole-TU feasibility alone establishes none of the standalone positives. [P, E1, A0 Q2, C1 §2.4] |
| B §8 on A07 and C `OBJ-C14`, §2.6 and §3 U5 | Any extraction pilot needs owner approval for mismatching siblings and wider extractor controls. | **UPHOLD** the source-gate prerequisite and the failure families. `match --all` is a conjunction over current wired source publics. Cross-record THREAD is a reproduced parser defect. A1 Q4 shows a slice from offset 4 dropping one data public and changing another from DATA+4 to DATA+0. Linear decoding requires trusted code/data classification or rejection. **REBUT** a mandatory 64-fixup limit and an exhaustive “four more defects” criterion. A1 Q3 linked 256 disjoint off32 fixups in one 1280-byte FIXUPP32 record with the deployed linker. A supported subset can reject anything beyond its independently validated bounds. A07 rev 2. [G, E3, E4, B1 U10, C1 Probe 5 as cited in §2.6, A1 Q3–Q4] |

### Behavioral witnesses and M2 sequencing

| Challenge | Attacked position | Disposition and resulting position |
|---|---|---|
| B `OBJ-B18`, `D-1`, U7, C §1.1/§2.3 and `OBJ-C12` | My “repair the five” roadmap treats five unchecked reference-C cases as five C repairs. | **UPHOLD.** The two Round 1 reports independently show three existing scenarios flipping from fail to pass after RAM restoration: WaitSound `0x231cc`, IntroRunScript `0x23668`, IntroPlay `0x23ae0`. StartCredits `0x23530` and EndScreen `0x2fcfc` still disagree at `0x59eb9` and `0x80054c`, respectively. Queue the first three for harness revalidation and the other two for diagnosis. **REBUT** an exhaustive “two confirmed C bugs” conclusion or any immediate DONE credit. The interventions exercised specified memory and existing assertions. CPU state, host setup and unwatched output differences still need adjudication. Count WaitSound once if the whole TU is admitted first. [P-T4, G, B1 R1-P4, C1 R1-Probe 2, A1 Q1] |
| B `OBJ-B21`, §8 on A08, C §8 on A08 and §6.3 | My R0 boundary decision left current paired-state defects on the multi-function track. | **UPHOLD.** A08 rev 2 explicitly puts A11 into affected existing witnesses now. A1 Q1 demonstrates a false pass even after enlarging `watch` when flags leak, and a host API write invisible to a guest write hook. A separately initialized emulator per side or a certified checkpoint must equalize relevant CPU, mapped state and declared host dependencies. Require a fresh/reset callback state contract. Retain the current outputs as assertions, with unwatched effects visible for audit. Protect existing check semantics under the owner rule. [P-T4, G, E6, A1 Q1, B1 `OBJ-B21`, C1 §4.4] |
| C §8 on A08 and §6.4 | Require full E6 and new CONST/switch support on the consolidation path. | **REBUT** a dependency based on file size or a blanket post-M2 chain. Existing `player_reference.c` has multiple functions. A new cited boundary must prove the executed closure and substitutions. Request the typed CONST and switch controls when a real proof needs those features. B3 data placement has no general dependency on E6. A08 rev 2. [P-T4, E6, B1 D-6, C1 §6.4] |
| C `OBJ-C15` and §2.5 | My roadmap omitted a discrete `oldcc` reliability task. | **UPHOLD.** EV-3 records a long-path Watcom failure, and `oldcc.py` is unchanged. Use validated effective paths and establish include/flag parity in the actual entry paths. The reported `rc=-11` lacks a single-variable cause for every invocation. A12 separates path work from R3 provenance fixes delivered in EV-3. [S, T, E7, C1 R1-Probe 4] |
| C §2.5 and `OBJ-C16`, B §3 U6 and `OBJ-B24` | The roadmap needs cross-TOML migration/Wave 3R, with a serial dependency or a large projected yield. | **REBUT** the serial dependency and bulk-yield inference. Retain the Round 0 small supervised routing/migration pilot, and run already-eligible and analyst-led work in parallel. The 61 placeholder cases need semantic/name and C work. Seven more require low-confidence evidence. The 14 eligible, 76 needs-human and eight skipped rows describe routing. A transactional rename and redirect test can earn its place when a ready candidate encounters that failure. No confidence or scope change comes from a rename. [I, G, B1 §2 D-3, C1 §2.5] |

## 2. Retained decisions

| Decision | Revision | Proposition SHA-256 |
|---|---:|---|
| DEC-A01 | 1 | `cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31` |
| DEC-A04 | 1 | `5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0` |
| DEC-A06 | 1 | `4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac` |
| DEC-A09 | 1 | `2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e` |
| DEC-A10 | 1 | `8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e` |
| DEC-A11 | 1 | `0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78` |

A11 sets the paired-input contract for current witnesses. A08 rev 2 uses that contract for new boundaries. Current paired-state work can proceed without new boundary machinery. A04’s base is the physical contribution start used by A05. A09 retains additive presets. EV-3’s historical 202-row snapshot has zero fresh entries, 139 partial and 63 stale, and is unused by Wave 4B. [S]

## 3. Changed decisions

### DEC-A02 — Revision 1 → 2

**Old proposition.** Implement two scopes of one bidirectional verifier, using strict raw-record admission for production proofs. Bind proof to actual supported compiler output and audit every declared T3 on the cutover revision.

**New proposition.** Use one bidirectional obligation engine for FunctionMatch and RegionMatch. Bound local branch checks to the independently verified function extent and carry independently proven external context as explicit obligations. Check trim targets in both scopes. Admit only the strictly decoded raw OMF subset of the actual declared compiler output, and cut over only after the existing file gate and every live declared T3 pass. Defer unproven CONST gap exemptions.

E2’s nine conservative Cause B outcomes and the E3 trim-guard finding justify the scoped checks. The 539-function E0 result supports the migration, and the new decoder/proof combination still needs its own audit. A04, A07 and A13 may consume the resulting region contract. None depends on V4. [E0–E4, B1 P1, C1 §8.1]

### DEC-A03 — Revision 1 → 2

**Old proposition.** Admit code through a partition plan covering every original byte with one provider. Require actual assembly, link, existing comparison and explicit loader-relevant identity and provider evidence for Build A acceptance.

**New proposition.** For a new in-place Build A path, derive one input-bound partition plan with one physical provider per original loaded byte. Treat plan success as preflight. Accept integration only from actual assembly and link, materialized provider evidence, the existing comparison, and an expanded comparison of supported LE loader attributes and normalized typed fixups. Validate raw fixup records before collapsing agreeing page-straddle duplicates. Keep serialization differences diagnostic unless shown to be loader-relevant.

B’s measurement requirement and the raw-duplicate mutant changed the admission rule. The stock loader model reduces each site to its first record. Three original duplicate sites agree, so the initial supported decoder can validate page-straddling copies before canonicalizing. A04/A05/A06/A07/A13 may share derived receipts from the actual link. There is no new persistent proof store. [P, R2 P1–P2]

### DEC-A05 — Revision 1 → 2

**Old proposition.** Prefer a verified whole-TU shared-tail group. Allow an original ASM piece-local relative expression only where source, target and intervening fixed cover are proved and emitted bytes and final link agree. Reject unsupported outgoing compiled slice rel8.

**New proposition.** Prefer a verified whole-TU shared-tail group. For each cross-piece fallthrough prove physical adjacency. For each fixed relative branch prove decoded endpoints, field width, next instruction address, in-place cover, exact emitted bytes, and zero relocation over its displacement. Cover interior, entry and cut-spanning rel8 using checked piece-local expressions for supported ASM encodings. Reject edges whose proof depends on global or per-object legacy placement. Use existing valid symbolic rel32 bindings and require independent proof before adding interior exports. Require final link evidence and reject unsupported outgoing compiled-slice rel8.

C’s confirmed MissionDefeat fallthrough and B’s per-object fallback expose gaps in the old wording. A04 supplies the true contribution base and A03 supplies final integration evidence. The bridge is an incremental path while siblings remain ASM. Group B can proceed via A13. [P, B1 §4, C1 §2.2, R2 P3]

### DEC-A07 — Revision 1 → 2

**Old proposition.** Defer general extraction. Admit a narrow pilot only for a proven canonical-TU benefit, a region proof bound to the object, independently identified targets, and a verified post-transform artifact and link.

**New proposition.** Defer general extraction. Permit a narrowly justified pilot only with owner authorization for any source-gate semantics change, a region proof bound to the raw input object, independently established code and data bounds and targets, record and symbol handling validated for the admitted subset, and independent proof of the transformed artifact and actual link. Reject unsupported inputs.

B identified the source-gate constraint. C’s cross-record THREAD evidence and my non-TEXT public probe strengthen the transform contract. A02 supplies raw admission and A03 the link receipt. Read-only partial diagnostics remain available within the existing gate. [G, E3, E4, B1 §8, C1 §2.6, A1 Q4]

### DEC-A08 — Revision 1 → 2

**Old proposition.** Require per-side execution boundaries, symmetric declared substitutions, real callback/ABI checks, typed pointer identity and production audit parity before using multi-function T4 for a cited proof.

**New proposition.** Apply certified paired-state equivalence to affected current T4 witnesses. Before a new cited witness relies on a multi-function or substitution boundary, prove the allowed per-side execution and dependency edges, symmetric declared substitutions, exercised callback ABI and typed pointer identity, and production t4spec audit parity. Add boundary machinery only for demonstrated witness requirements.

Current T4 is affected, including cases that already share a reference TU. A11 supplies the paired-state contract. Verify the already-cited affected witnesses and the production audit path before extending E6. Retain existing owner authority over any changed assertion or expected outcome. [G, P-T4, E6, B1 R1-P4, C1 R1-Probe 2, A1 Q1]

## 4. Withdrawn or superseded

Revisions 2 supersede A02, A03, A05, A07 and A08 revision 1. Their prior approvals have no effect on revision 2. I withdraw my Round 0 treatment of all five xfails as presumptive C repairs and the staged dependency of the Group B pilot on general placement work. I keep the five rows outstanding pending legitimate individual completion. No independent A decision is withdrawn.

## 5. Unresolved objections

- **A11 and current T4** (`OBJ-B21`, `OBJ-A12`, `OBJ-A20`). Resolve the paired-state implementation with independent-world or checkpoint tests for guest RAM, host writes, CPU flags and host callbacks, then rerun the five scenarios under the real audit. Determine the two persistent differences from equivalent state before attributing either to C.
- **CONST completeness** (`OBJ-C09`, `OBJ-A11`). A real blocking candidate plus independent literal extents and exclusion of computed, aliased and external accesses to the gap would justify a specialized proof. A finite reference scan alone leaves my objection open.
- **B2 general admission** (`OBJ-C10`, `OBJ-B27`, `OBJ-A13`). Require a combined B1/B2 fixture with actual accepted output and explicit negatives for both legacy routes, displaced adjacency, a prefixed branch and an invalid interior target. Require a separate checked link for any synthesized export.
- **Selective extraction** (`OBJ-B04`, `OBJ-C14`, `OBJ-A18`). A justified candidate, an owner decision if the source gate changes, supported-record controls and independent transformation/link validation would resolve the adoption objection. Evidence for an actual record limit must identify the linker, record shape and failing size.
- **Short paths** (`OBJ-C15`, `OBJ-A17`). A controlled effective-path boundary and identical source/include semantics with a warmed private prefix would establish a safe staging contract. EV-3’s path issue stays open.

## 6. New objections and decisions

**OBJ-A19 — Correctness/verification.** B20 calls for equality checks over object flags, page/fixup records and types when the baseline agrees. R2 P1 finds raw fixup record order differs, although typed records, physical occurrence counts and grouping multiset agree. Last-page file length differs by one byte. Assuming the supported loader assigns no significance to serialization order after validation, making raw order an identity condition would reject the current Build A. Compare semantics after strict admission. Report raw deltas and escalate any loader-significant difference under the existing owner rule. [P, R2 P1]

**OBJ-A20 — Correctness/verification.** B18 claims every mapped region restored makes the two runs start in identical complete state. C16 prescribes RAM restoration or dirty-page hooks and definitive five-row classifications. A1 Q1 found a CPU-flags false pass and showed host API writes escape a guest hook. Even perfect RAM rollback leaves arbitrary host objects reachable by stubs unless declared and reset. Under ordinary shared-state execution this can miscredit equality and assign persistent differences to C prematurely. Require A11 state accounting and treat the reported split as observation-specific. [P-T4, A1 Q1, B1 R1-P4, C1 R1-Probe 2]

**OBJ-A21 — Correctness/verification.** The minimal reading of C15 would add types from `fixups_unique` to the comparator. LE’s first-wins normalization hides later conflicting occurrences. R2 P2 changes the second occurrence of a page-boundary fixup from type 7 to 6 and preserves the entire unique typed projection. A comparator using that projection alone would still accept contradictory records. Validate typed agreement, supported ordering/placement and page coverage before deduplication. A03 rev 2 addresses this; I do not assert that this mutant was executed by DOS/4GW. [P, R2 P2]

```text
Decision: DEC-A12
Title: Protect effective Watcom 10.0a paths
Proposition: Stage or reject effective Watcom 10.0a paths before launch. Prove that staging preserves source identity, include resolution, flags and output attribution, and isolate temporary outputs per compile. Report path failures as toolchain errors. Use measured limits on effective compiler-facing paths.
Revision: 1
Position: PROPOSE
Reason: Long compiler paths already interrupt repeatable verification and production work.
Evidence: tools/wc1/oldcc.py@17733f9, E7 D9, EV-3 post-campaign report, C R1-Probe 4
Assumptions: The supported input set can be staged without changing include resolution or compiler selection.
Dependencies: DEC-A01
```

```text
Decision: DEC-A13
Title: Admit an independent exact Group B proof
Proposition: Permit the exact Group B whole-TU promotion independently of general B1, B2 and matcher rollout only with a commit-bound strict raw-object RegionMatch equivalent to the intended production rules, ordinary file and dual-compiler checks, actual in-place Build A with typed loader comparison, and preserved cited T4 checks or explicit owner approval for changes.
Revision: 1
Position: PROPOSE
Reason: The tested whole-TU contribution closes its own shared tail and need not wait on generic placement support.
Evidence: E1 Group B @e6150b8, B R0 P3 as reported in R1 D-7, tools/wc1/build.py@17733f9, tests/test_playflic_t4.py@17733f9
Assumptions: An independently checkable strict proof is available on the exact candidate, or the promotion waits for production RegionMatch.
Dependencies: DEC-A01, DEC-A02 revision 2 proof contract, DEC-A03 revision 2 acceptance contract
```

## 7. Convergence assessment

The reviewed positions are close on the existing M2 finish line, keeping local, regional and linked claims distinct, whole-TU preference for exact shared-tail groups, the B1 base, additive compiler presets, and analyst-only historical CU evidence. The remaining architecture choices concern exactly which evidence enters a new proof, when a specialized candidate justifies an extension and how to express fixed-layout debt. A whole-TU pilot with an equivalent strict shadow proof and a production-first rollout are scheduling choices so long as the same proof contract and gates apply. A comprehensive OMF codec, persistent provenance, synthetic rel32 exports and optional E6 modes are design choices that need a justified consumer.

| Remaining factual dispute | Cheapest decisive experiment and falsifier | Changes |
|---|---|---|
| Scope and viability of strict E0 cutover | Port the E0 controls and add malformed records, distinct frames, a non-contiguous local branch, an independently resolved sibling and a target into trimmed filler. Run every live T3 under its declared context on one cutover commit. A permissive false match or an unexplained live loss blocks cutover. | A02, B02, C02 |
| Group B independent promotion and B2 mode-specific feasibility | First run the exact Group B source through strict raw/region verification, existing tests and a fresh actual Build A. Separately link standalone Sync and MissionDefeat with the specified edges. Force an `Unplaceable` in the span, global legacy, altered fallthrough and a B1 prefix cut. Any supported positive losing exact output or rejected-path plan gaining credit falsifies its rule. Test synthesized rel32 separately only if needed. | A04, A05, A13, B03–B06, B19, C05–C06 |
| LE comparator scope | R2 P1 settled parity for the measured normalized EV-3 attributes. Run the three P2 mutants against the strengthened checker and the live control. A mutant pass or a live false reject blocks the change. If an additional field is plausibly loader-relevant, inspect the admitted loader’s handling before adding it to equality. | A03, B20, C15 |
| CONST access and variability | On a concrete blocker such as SaveSlotPath, vary source path and environment one at a time, then use proven bounds for each literal. Include the computed-gap-read negative and one changed literal. A gap read within the claimed domain or any passing changed-literal negative refutes the proposed exemption. | A06, B08, B21, C03, C10 |
| Five xfail root causes and audit viability | On the five cases, compare fresh-world execution with certified checkpoint execution and reverse side order. Include host/guest/CPU state negatives and verify nonce-bound audit records. Diagnose remaining first divergence from equivalent inputs before changing expectations. A valid witness sensitive to order or a false audit pass falsifies the implementation. Then run the affected T4 suite under the existing assertions. | A08, A11, B07, B16, B18, C07, C11, C16 |
| Watcom path class | Compile the same fixture at controlled shallow/deep effective paths with the same warmed prefix, including a relative include and an out path. Compare against the supported shallow control. Path-only failure or changed supported output dependencies blocks the staging contract. | A12, C04 |
| Useful E4/E6 extensions | For E4 use one named canonical-TU blocker and a subset test with cross-record THREAD, a nonzero slice with data publics, code/data bounds and true record limits. An accepted transform changing a retained obligation falsifies admission. For E6 use one needing a real callback or switch/CONST pointer, with wrong ABI, original-side escape and raw-integer negatives. A passing negative or missing audit evidence falsifies its use as a cited witness. | A07, A08, B09, B12, C08–C11 |
| Historical reach of tested flags and boundaries | Extend per-context searches with `-5r -d1+ -zp1` and `-od -5r`; test next-TU alignment against a proved contribution base with and without a prefix. A matching alternate context refutes a uniqueness claim. A verified legal boundary under the stated premises refutes its supposed hard merge. | A09, A10, B10–B13, C12–C13 |

## 8. Structured positions

Revision 1 hashes for all 48 indexed decisions are from the frozen index. For my five revisions and two new decisions, I computed SHA-256 over the exact UTF-8 proposition text above. The index remains unchanged. Revision 1 rejections for the five superseded A decisions refer only to the superseded wording.

### Architect A

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: M2 credit, conversions and owner-governed T5 remain distinct.
Conditions: none
Related objections: none

Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: REJECT
Reason: Superseded by revision 2, which specifies local bounds, external obligations and trim checks.
Conditions: none
Related objections: OBJ-A03, OBJ-C09

Decision: DEC-A02
Revision: 2
Proposition SHA-256: 87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca
Position: ACCEPT
Reason: Names the strict proof boundary without requiring V4 or a general serializer.
Conditions: none
Related objections: OBJ-A03, OBJ-C09

Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: REJECT
Reason: Superseded by revision 2 after the baseline measurement and duplicate fixup mutant.
Conditions: none
Related objections: OBJ-A02, OBJ-A19, OBJ-A21

Decision: DEC-A03
Revision: 2
Proposition SHA-256: 58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda
Position: ACCEPT
Reason: Distinguishes preflight, materialization and lossless loader checks.
Conditions: none
Related objections: OBJ-A02, OBJ-A19, OBJ-A21

Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: The verified offset gives the physical contribution base.
Conditions: none
Related objections: none

Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: REJECT
Reason: Superseded by revision 2, including fallthrough and automatic fallback.
Conditions: none
Related objections: OBJ-B27, OBJ-C10

Decision: DEC-A05
Revision: 2
Proposition SHA-256: 414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5
Position: ACCEPT
Reason: Closes fallthrough and each fixed-rel8 class under the same layout contract.
Conditions: none
Related objections: OBJ-B27, OBJ-C10

Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: ACCEPT
Reason: Conservative whole-segment admission remains useful for a justified subset.
Conditions: none
Related objections: OBJ-A11, OBJ-C09

Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: REJECT
Reason: Superseded by revision 2 with source-gate and transform constraints.
Conditions: none
Related objections: OBJ-B04, OBJ-C14

Decision: DEC-A07
Revision: 2
Proposition SHA-256: 5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d
Position: ACCEPT
Reason: Bounds the hypothetical transform and preserves the current gate.
Conditions: none
Related objections: OBJ-B04, OBJ-C14

Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: REJECT
Reason: Superseded by revision 2 with the present T4 prerequisite.
Conditions: none
Related objections: OBJ-B21

Decision: DEC-A08
Revision: 2
Proposition SHA-256: 2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31
Position: ACCEPT
Reason: Addresses current witnesses before need-driven E6 extensions.
Conditions: none
Related objections: OBJ-B21, OBJ-A20

Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Presets and scheduling evidence retain their measured scope.
Conditions: none
Related objections: none

Decision: DEC-A10
Revision: 1
Proposition SHA-256: 8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e
Position: ACCEPT
Reason: Historical alternatives need independent premises and no build effects.
Conditions: none
Related objections: none

Decision: DEC-A11
Revision: 1
Proposition SHA-256: 0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78
Position: ACCEPT
Reason: RAM and CPU evidence require a separate paired-input contract.
Conditions: none
Related objections: OBJ-A12, OBJ-A20

Decision: DEC-A12
Revision: 1
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Position: ACCEPT
Reason: A current operational blocker warrants a controlled path contract.
Conditions: none
Related objections: OBJ-C15

Decision: DEC-A13
Revision: 1
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Position: ACCEPT
Reason: The exact group can satisfy strict proof independently of generic rollout.
Conditions: none
Related objections: OBJ-C13

```

### Architect B

```text
Decision: DEC-B01
Revision: 1
Proposition SHA-256: 2e0072dfeacf3355c35ae8626056819ee56a56b22736ebe3c1b95f1ef350f7bb
Position: CONDITIONAL
Reason: The admission criterion is sound. The enumerated M2 set is incomplete.
Conditions: Allow measured path reliability, typed loader checks, small proven workflow fixes and witness-specific E6 when required. Keep independent work moving.
Related objections: OBJ-C15, OBJ-C16

Decision: DEC-B02
Revision: 1
Proposition SHA-256: 52e9b26dfdd3b6954ee162adfb0c71e128aa2aa696965fcd2c09b43b1e7e7a16
Position: CONDITIONAL
Reason: The proposed bidirectional core and live audit are warranted.
Conditions: Require A02 rev 2 raw admission and scoped checks, including the current file gate. Do not gate on V4.
Related objections: OBJ-A03, OBJ-B20, OBJ-C09

Decision: DEC-B03
Revision: 1
Proposition SHA-256: e4227a079ab271526345bc98d3a54e8b6c12cccf6b476ee37748b7411375e6f3
Position: CONDITIONAL
Reason: Use one planner. Emitter acceptance is preflight.
Conditions: Require A03 rev 2 for integration. Qualify standalone Sync by bridge mode and proof.
Related objections: OBJ-A09, OBJ-C11

Decision: DEC-B04
Revision: 1
Proposition SHA-256: 10f99b1cf2a534df1eb4b3a8f6dd0774a174e1e785dae2222be7ca52b3ce08a1
Position: CONDITIONAL
Reason: Fixed displacement can be a bounded Build A bridge.
Conditions: Require A05 rev 2, including real encoding, fallthrough, no legacy dependency and actual typed link comparison.
Related objections: OBJ-A13, OBJ-B27, OBJ-C10

Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: The affine physical base and proof of the prefix handle B1.
Conditions: none
Related objections: none

Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: CONDITIONAL
Reason: Exact verified joint regions are preferred.
Conditions: Use tested flags for this group, apply A13 if early, and preserve cited tests or obtain owner approval for changes.
Related objections: OBJ-C13

Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: CONDITIONAL
Reason: RAM isolation addresses one reproduced cause.
Conditions: Meet A11 for CPU, guest and host writes, and declared host state. Preserve output assertions and audit meaning.
Related objections: OBJ-B21, OBJ-A20

Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: ACCEPT
Reason: No current M2 result requires general B3, and a case could qualify earlier.
Conditions: none
Related objections: OBJ-C09

Decision: DEC-B09
Revision: 1
Proposition SHA-256: 00ff7874640d8a9159ec0d393a17aac144a02a9b2126aafedc5883bc4e6135d6
Position: ACCEPT
Reason: A partial canonical source gate requires the owner. Existing pilot risks justify deferral.
Conditions: none
Related objections: OBJ-B04, OBJ-C14

Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: This is a measured in-object alignment model, scoped to tested compiler contexts.
Conditions: none
Related objections: none

Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: Existing default and additive per-file preset policy are warranted.
Conditions: none
Related objections: none

Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: Extensions should follow actual execution or substitution needs.
Conditions: Admit qualified post-M2 consumers too. Entry hooks require proved entry-only edges. Apply A08 rev 2 and A11.
Related objections: OBJ-A12, OBJ-B25

Decision: DEC-B13
Revision: 1
Proposition SHA-256: 84a9be5c34e2d9d48bff2c233da0fc9779e5ac2f64a01704f120998ce876741c
Position: CONDITIONAL
Reason: Analyst-only constraints are appropriate.
Conditions: Require producer and linker premises for shared tails, use the actual prospective segment base for PARA, and keep shared literals as conditional evidence.
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: Matcher-minted proof and a derived plan suffice for the M2 entity model.
Conditions: none
Related objections: none

Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Production implementations should own their supported surface and controls.
Conditions: none
Related objections: none

Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Probe outcomes justify candidate labels. Three cases flipped under RAM restoration, and current proof is required for status or credit.
Conditions: none
Related objections: OBJ-A15, OBJ-C12, OBJ-A20

Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: An M2 extraction strategy lacks a demonstrated need and ready proof contract.
Conditions: none
Related objections: OBJ-B04, OBJ-C14

Decision: DEC-B18
Revision: 1
Proposition SHA-256: ac26e81cd7b7a4b5425bf06c8bbf108dcaad0a36836455c2f7ed8a7f034a02db
Position: CONDITIONAL
Reason: The current input symmetry gap needs immediate repair. RAM alone is incomplete.
Conditions: Require A11, with independent initialization or certified reset of CPU, mapped and declared host state. Keep effect assertions and owner approval.
Related objections: OBJ-A20, OBJ-B21

Decision: DEC-B19
Revision: 1
Proposition SHA-256: 2b1f46b75f348a9e7f6ddf23f2bec3b1cb47e9de6674c5f4d6b534b562b1a78f
Position: ACCEPT
Reason: An automatic Unplaceable fallback must disqualify a fixed span that relies on the moved object.
Conditions: none
Related objections: OBJ-B27

Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: CONDITIONAL
Reason: Measurement was useful. Typed fixups and object flags agree, while serialized record order and last-page file size differ.
Conditions: Strengthen supported normalized semantics and reject conflicting duplicates. Keep raw deltas diagnostic unless loader relevance is established.
Related objections: OBJ-A19, OBJ-A21

Decision: DEC-B21
Revision: 1
Proposition SHA-256: adec6bc4ed881a8a7e8279ce049851261811bf95e2144723b0a91dbe7d3a94cd
Position: REJECT
Reason: Excluding all apparent alignment gaps from authority digests is unsound. Exact binding is intentionally artifact-local.
Conditions: none
Related objections: OBJ-A11, OBJ-C09

```

### Architect C

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: CONDITIONAL
Reason: Separate local and regional proof from preflight and actual integration.
Conditions: Use A03 rev 2 as the materialization boundary. Consumers may use typed results without owning proof logic.
Related objections: OBJ-A09

Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: CONDITIONAL
Reason: Scoped closure and trimmed-branch diagnostics improve E0.
Conditions: Carry valid external obligations explicitly. Add strict admission and the live gate. Leave V4 independent.
Related objections: OBJ-A03, OBJ-A10, OBJ-B20

Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: Literal shape plus a direct-reference scan cannot exclude a computed read.
Conditions: none
Related objections: OBJ-A11, OBJ-C09

Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: CONDITIONAL
Reason: Short-path reliability remains relevant. R3 fixes already landed.
Conditions: Separate the delivered R3 work. Validate effective compiler paths and preserve build semantics before fixing a numeric ceiling.
Related objections: OBJ-A17, OBJ-C15

Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: CONDITIONAL
Reason: A minimal plan with B1 and B2 is appropriate.
Conditions: Use actual decoded instruction width, checked fallthrough and both legacy paths, with A03 link evidence. New interior exports are optional.
Related objections: OBJ-A13, OBJ-B23, OBJ-B27, OBJ-C10

Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: CONDITIONAL
Reason: The tested exact shared-tail group is a good candidate.
Conditions: Use A13 for an independent path. Scope flags to proven TUs and keep the owner checkpoint.
Related objections: OBJ-C13

Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: Generic placement and migration need not precede ordinary M2 work. The five xfails require different investigations.
Conditions: none
Related objections: OBJ-A15, OBJ-B24, OBJ-A20

Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: CONDITIONAL
Reason: General E4 production rollout should remain deferred.
Conditions: Apply A07 rev 2. Do not require exhaustive flag sweeps or an unsupported 64-fixup limit for a justified subset.
Related objections: OBJ-A14, OBJ-A18, OBJ-C14

Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: CONDITIONAL
Reason: Share a strict codec subset for the supported transforms.
Conditions: Use measured record-size and linker limits. Avoid rewriting unrelated permissive readers or mandating 64-fixup chunks.
Related objections: OBJ-A18, OBJ-C14

Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: CONDITIONAL
Reason: A need-driven B3 pilot with ownership separation makes sense.
Conditions: Use A06 first. Permit any gap exclusion only with independent extent and access proof and shared matcher/planner policy.
Related objections: OBJ-A11, OBJ-C09

Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: File count does not determine the trust boundary. Freezing current cemu leaves a demonstrated gap.
Conditions: none
Related objections: OBJ-A12, OBJ-B21, OBJ-B25

Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: CONDITIONAL
Reason: An analyst-only evidence graph with competing hypotheses is appropriate.
Conditions: Shared literals require evidence excluding external sharing and pooling. Start tests at actual contribution bases and defer extra storage.
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: CONDITIONAL
Reason: Correct the tested alignment matrix and add missing flag trials.
Conditions: Scope PARA to the measured mode. Keep -4r default and treat -5r as a candidate for suitable exact TUs.
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: Clean interfaces suffice without speculative plugin frameworks.
Conditions: none
Related objections: none

Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: CONDITIONAL
Reason: The raw OMF and typed LE comparison gaps are reproduced.
Conditions: Use the supported strict subset and A03 rev 2. Check raw fixup occurrences before normalizing and keep raw ordering differences diagnostic.
Related objections: OBJ-A02, OBJ-A03, OBJ-A19, OBJ-A21

Decision: DEC-C16
Revision: 1
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Position: REJECT
Reason: The three flips are observed scenarios, and two persistent differences need diagnosis. RAM or guest hooks alone cannot certify input symmetry.
Conditions: none
Related objections: OBJ-A12, OBJ-A20

```

## 9. Probe log and source index

All commands ran from the Architect A worktree through `nix develop -c`. `git rev-parse HEAD` returned `e6150b856106ae113bb023300b956fff318da7ef`. The following source diff exited 0 and printed no differences.

```bash
nix develop -c bash -c 'git diff --exit-code a21772b 17733f9 -- tools/wc1/{oldcc,build,emit,match,cemu,compare,le,omf}.py tests/test_{playflic,mod_2efd0}_t4.py'
```

The inbox files were read in full. I checked their byte counts and advertised SHA-256 digests, and recalculated all 48 proposition digests from the indexed text. No production or Git state was changed. I did not run `make verify` or the repository test suite. A single scoped Build A was necessary because the recorded verification output lacks raw LE attributes and the linked binary is needed to measure them.

### R2 P1 — Live EV-3 Build A and loader metadata

The build ran in a new export under this worktree with the existing Architect A Wine prefix, no `WC1_CFLAGS` override, and relative `TMPDIR=.` inside the disposable tree. The Nix shell reported Python 3.14.7, NASM 3.02, Open Watcom Linker 2.0 beta (64-bit) and Wine 11.0. The build used the sources’ declared compilers.

```bash
nix develop -c bash -c '
set -eu
set -o pipefail
probe_repo="$PWD/build/r2e"
test ! -e "$probe_repo"
mkdir "$probe_repo"
git archive 17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9 | tar -x -C "$probe_repo"
ln -s "$PWD/original" "$probe_repo/original"
export WINEPREFIX="$PWD/build/oldcc/wineprefix"
export WC1_ROOT="$probe_repo"
export PYTHONPATH="$probe_repo/tools"
export PYTHONDONTWRITEBYTECODE=1
unset WC1_CFLAGS
cd "$probe_repo"
export TMPDIR=.
timeout 180s python3 -m wc1.build --out "$probe_repo/war.exe" 2>&1 |
  tee /mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r02-build.log'
```

Exit 0. The build printed `539 functions from 534 C files (534 placed in sequence, 0 legacy layout)` and `IDENTICAL (loaded image, entry, stack, fixups)`. Its output is `build/r2e/war.exe` inside my worktree. Only the private export and private prefix were used for writes.

The metadata and first two mutations used this command.

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r2e"
export PYTHONPATH="$WC1_ROOT/tools"
export PYTHONDONTWRITEBYTECODE=1
r=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt
python3 "$r/r02-le.py" "$WC1_ROOT" "$r" | tee "$r/r02-le.log"'
```

Both images have flags `0x2045/0x2043`, entry `(1,0x24584)`, initial stack `(2,0x155f0)`, module flags `0x200`, page size 4096, page count 60, and 8,770 unique typed fixups, all type 7. Typed records, physical typed multiplicities, page map, fixup page offsets and raw record grouping multiset agree. There are 8,773 physical fixup occurrences and no conflicting duplicates in either control. Last-page file size is 1339 original and 1340 rebuilt. Ordered raw fixup tables each measure 64,165 bytes and hash to `86d4daaf7da5e915fef58dab90759d9d47aa37fab0dbbe6cc5c8fce74da272e5` and `d59a6d35099cdcd8fff4fb4c0f725e3d3b2393636398bab6733e7584a0da1c62`, respectively. This measures one baseline and the current parser’s supported LE projection.

### R2 P2 — LE negative controls

The P1 metadata script cleared `OBJ_EXEC` in one private mutant and changed an OFF32 record to PTR16:32 at file offset `0x2d88` in another. The corresponding typed record changed from `(1,2475,7,2,34132)` to `(1,2475,6,2,34132)`. Both mutants returned comparator exit 0 and `IDENTICAL`.

A second script changed only the second occurrence at `(1,53246)`, file offset `0x6c95`. Its raw source types became `[7,6]`, the unique typed projection stayed equal, and the comparator returned exit 0 and `IDENTICAL`.

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r2e"
export PYTHONPATH="$WC1_ROOT/tools"
export PYTHONDONTWRITEBYTECODE=1
r=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt
python3 "$r/r02-edges.py" "$WC1_ROOT" "$r" | tee "$r/r02-edges.log"'
```

The scripts wrote `r02-noexec.exe`, `r02-selector.exe` and `r02-duplicate.exe` to the private runtime. These tests exercise the comparator and parser. They do not run the mutants under DOS/4GW.

### R2 P3 — Branch and fallthrough locations

The P2 edge script printed these decoded values from the original.

```text
0x20258 53 push ebx next 0x20259
0x20259 51 push ecx next 0x2025a
0x202c0 60 pushal  next 0x202c1
0x231d7 7493 je 0x2316c next 0x231d9
0x231e1 7589 jne 0x2316c next 0x231e3
0x2f6df 0f8561000000 jne 0x2f746 next 0x2f6e5
0x2f73a 7d0a jge 0x2f746 next 0x2f73c
0x2f73c c70560a8050028ab0100 mov dword ptr [0x5a860], 0x1ab28 next 0x2f746
```

The supplemental read was:

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r2e"
export PYTHONPATH="$WC1_ROOT/tools"
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'"'"'PY'"'"'
from wc1 import analysis
p = analysis.run()
for i in p.insns.values():
    if 0x20250 <= i.address < 0x20260 or 0x202b8 <= i.address < 0x202c2:
        print(hex(i.address), bytes(i.bytes).hex(), i.mnemonic, i.op_str)
for f in p.functions:
    if 0x20250 <= f["start"] <= 0x202c0:
        print("function", hex(f["start"]), hex(f["end"]), hex(f["limit"]))
PY'
```

It showed `0x202bb 5b pop ebx` and `0x202bc c3 ret`. Discovered start/end/limit triples were `0x20258/0x202bc/0x202bc`, `0x202bc/0x202bd/0x202c0` and `0x202c0/0x20448/0x20448`. This is a decoding and boundary check. It does not link any new B2 placement.

| Runtime artifact | SHA-256 |
|---|---|
| `r02-build.log` | `4ce59c564eeedde16fa2fe134103db44c0e212dc8699d8f158583799be5de1b9` |
| `r02-le.py` | `d6aefd4fee1732b7eef8112c12756a7ba2cb6f504f802a00524d4f7166ab2cb3` |
| `r02-le.log` | `15e36681c9f5a1e3cbf7b339beb48583c0da7fad0fcb35c38be87d7745f1f37a` |
| `r02-edges.py` | `63835e79a15597f38a58e09922f10b097d13bac7527889da16100ffd1e7cf668` |
| `r02-edges.log` | `88f1a9f732c7bb3735d5a3613265448239215829ce3ed440f29c8b7ae7d85850` |

### Source index

| Key | Pinned source |
|---|---|
| G | `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `Makefile`, `tools/wc1/progress.py` @ `a21772b` and `17733f9`. |
| S | EV-1 through EV-3 notices and recorded verify/progress outputs. `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/{report.md,e7_snapshot_revalidation.json}@17733f9`. |
| I | `tools/wc1/m2_inventory.py@17733f9`, `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/candidate_ledger.json@a21772b`, A0 Q1. |
| P | `tools/wc1/{match,build,emit,compare,le,omf,omfpatch,analysis}.py@17733f9`. Particularly `build.py:305–353`, `compare.py:24–27,45–47`, and LE `_parse_fixups` and `loaded_image`. |
| P-T4 | `tools/wc1/{cemu,emu,t4spec}.py@17733f9`, especially `cemu.py:344–415`. `src/playflic/player_reference.c@17733f9`. `tests/test_playflic_t4.py::{test_intro_op_wait_sound,test_intro_op_start_credits,test_intro_run_script,test_intro_play}@17733f9` and `tests/test_mod_2efd0_t4.py::test_end_screen@17733f9`. |
| T | `tools/wc1/oldcc.py@17733f9`, `docs/subsystems/compiler.md@a21772b`, EV-3 cleanup report operational notes. |
| E0–E3 | `docs/research/build-codegen/{E0-matcher-soundness,E1-shared-epilogues,E2-compilation-context,E3-partial-matching}.md@e6150b8` and respective results. `experiments/build_codegen/e0/matcher_proto.py@e6150b8`, `experiments/build_codegen/e3/partial_matcher.py@e6150b8`, `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/rev-e3-01.md@e6150b8` (trim-target remains fail-closed there, with a less specific diagnostic). |
| E4–E6 | `docs/research/build-codegen/{E4-omf-extraction,E5-data-anchors,E6-multifunction-t4}.md@e6150b8`. `experiments/build_codegen/{e4/omf_extract.py,e5/omf_b3.py,e6/mf_cemu.py}@e6150b8`. `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/{rev-e4-01,rev-e5-02}.md@e6150b8`. |
| E7–E8 | `docs/research/build-codegen/{E7-compiler-calibration,E8-cu-boundaries}.md@e6150b8`, respective results, and `docs/telemetry/campaigns/2026-11-27-e7-production/report.md@a21772b`. |
| A0, A1 | Own frozen `CONSILIUM-R00-POSITION.md` and `CONSILIUM-R01-CROSSREVIEW.md`, probe logs under this Architect’s private runtime `r00-probes` and `r01-probes`. |
| B1, C1 | Frozen Round 1 discussion material in this Architect’s `r02-inbox`. B SHA-256 `ee07dd4bfd85cd8d706da39f262739f3eb7cfb601327ea52cd658d79869806d5`. C SHA-256 `aecdde79852ef02bef2206c6243ad90da483c980982f413a4ef6d9a6714edf66`. The reviewed reports’ private probes are attributed to their authors. |
| Frozen index | `r02-inbox/00-PROPOSITION-INDEX.json`, SHA-256 `62db5e6ae8d2d165ebd617d2f686f62a3bd731022e05881a6923ee1b3e3f23d8`. |