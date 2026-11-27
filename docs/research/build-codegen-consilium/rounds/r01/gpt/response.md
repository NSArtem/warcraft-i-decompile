# Build & Codegen Infrastructure — Round 1 cross-review

Architect A — GPT · 2026-11-27 · Frozen Round 0 propositions, EV-1 with supplemental EV-2 and EV-3

## 1. Agreements

- **M2 priority and fixed gates.** Accept B01 and C07’s priority principle. E7 added 13 T3s and zero DONE. At both production observations, 912/1,010 are DONE. The tested B3 and E4 cases provide no demonstrated M2 gain. Keep B3, extraction and historical CU tooling off the default M2 path. B09 identifies a governance prerequisite that my A07 should have made explicit. A TU with a mismatching public fails the current file-level `match --all` even if a separately extracted slice links identically. Owner approval is required before changing that gate’s tested semantics. [P-GATE, P-M2, R]
- **One plan for preflight and emission.** Accept B03/C01/C05’s architectural core. Source and destination *providers* determine the treatment of an edge. B §5 P5 reports MissionDefeat’s three entry-targeting short branches, extending my Round 0 retained-to-retained Sync case. An entry exemption in `replaced_interior_refs` cannot stand in for encodability. Include incoming absolute references and actual fallthrough across provider boundaries as distinct constraints. [B §§5, 14; C §§4–5; P-BUILD; A0 Q2]
- **Group B can move earlier.** Prefer the whole-TU path in B06/C06. B P3 links the three handlers on a disposable copy of the production pin using existing tools and passes both compiler checks. That is stronger evidence than the isolated E1 link I used in Round 0. I would take Group B out of the generic B2 dependency chain. Normal source, test and build admission still applies. The results in B P3–P6 support concrete candidate links, with up to eight additional DONE across the combined cases when admitted. [B §14 P3–P6; E1; P-GATE]
- **Paired state is a separate soundness issue.** B07 and OBJ-B06 identify a problem my opening treated as a requirement for future multi-function T4. It affects current `run_pair`. B P4 reports the same WaitSound failure for reference C and byte-exact C, then both pass with the stub’s counter restored. My probes demonstrate false equality from unwatched memory and inherited CPU flags. This work belongs on the M2 verification track independently of E6. [B §14 P4; P-T4; Q1]
- **Small proof API and bounded codegen search.** Accept B14’s omission of a separate production candidate type for M2, provided the proof and plan retain input identity. This is simpler than the separate record in my Round 0 sketch. Accept B15 and the substance of C14. Keep the measured alignment matrix and additive presets (B10/B11). Keep CU evidence and proposal tooling outside scope, progress and placement authority (B13/C12’s policy). [B §§3, 11; C §§7, 11; E2; E7; E8; A0 §§3, 7]

## 2. Substantive disagreements

| Proposition challenged | Dispute, counterexample and practical consequence | Alternative and what would change my position |
|---|---|---|
| **B03 and C01**, including B §3.2 I-2 and C §5.0. The shared planner and emitter define integrated buildability. | Architectural. The planner can establish an encodable plan, while NASM, link resolution, parser errors, effective frames or final loader identity still fail. The stock Sync precheck is a live example. The comparison also ignores the object execute flag. Equating preflight with integration gives a promotion consumer authority before the artifact is verified. [P-BUILD; A0 Q2–Q3] | Have planner and emitter share one plan, then require a link-and-compare receipt for a promotion. The standalone Sync negative belongs to the configuration where the bridge is disabled or unproved. It can become a positive when that case is supported. A complete constructive proof of the actual assembler/linker contract could change the role of the oracle. The current evidence does not supply one. |
| **B02** as explained by I-1, and **C02/V2**. Fix E0 with a blanket rule that every same-object cross-function branch makes FunctionMatch unsupported. | Inferential and architectural. E2’s first-public window is an incorrect bound for local diagnostics on noncontiguous objects. The cure does not make E1’s proved helper-to-tail branch unmatchable. E1 Group A has individually matching helpers in a broader context, even in one case where the owner mismatches. An absolute “MATCH can only be lost” rule would also forbid correcting a false rejection on new proof. [E0; E1; E2] | Check branches using their actual source span, independently identify sibling targets, and attach the explicit unresolved or proved edge obligation. Distinguish a body that agrees with an external context obligation from a closed placement proof. Accept a revised local contract tested on both E2 ordinary internal branches and E1 cross-function tails, preserving extent and closure negatives. |
| **C03/C10**. The five V4 predicates are sufficient for exempting differing CONST bytes. | Correctness. Matching a NUL-terminated string and finding no relocation target in a candidate gap does not establish the gap’s ownership or non-use. Q2 uses a runtime index with only two literal-start relocations and reads an otherwise qualifying byte. Even with ASM supplying the final bytes, the verifier would have certified source data that can behave differently when loaded directly. Applying V4 in E0 also imposes an unnecessary dependency on initial matcher admission. [E0; E5; E8; Q2] | Keep exact data matching in the initial verifier. Later allow an explicit provider-accounted range only with independent bounds and evidence covering data access and fields overlapping the range, plus a final physical provider and comparison. Test a real need such as SaveSlotPath, with computed/indexed reads and overlapping fields as negatives. The evidence must prove the omitted bytes irrelevant to the stated source proof. |
| **B07 and C11**. Memory restoration is enough to establish paired state, or the single-function harness should remain untouched while all E6 extensions precede multi-function T4 consolidation. | Architectural. Q1 reproduces false equality with watched data even when the only leaked input is carry. Guest write hooks do not see host API writes. Shared allocator, callbacks and mutable Python stub state can also carry inputs. In addition, `player_reference.c` is already a multi-function file with cited T4s. A universal E6-plus-extensions gate would impose capabilities a particular test may never use. [P-T4; E6; B P4; Q1] | Give each side equivalent CPU, memory and declared dependency state from an independent case baseline. Preserve current observation and anti-cheat requirements. Add E6 capabilities when a witness requires them and keep the legacy proof path until parity is shown. Owner review is required if the change alters the meaning of an existing test. A state/ABI inventory and leakage-negative tests can justify a bounded restoration optimization. |
| **B04 and C05**. Emit any remaining relative branch with the old literal displacement, or always add an interior PUBDEF for rel32 and use `ia+2` for every short branch. | Correctness and design. A legitimate prefixed `jcxz` has a one-byte displacement in a three-byte instruction (Q3). B’s rule needs typed widths, the true next IP, verified endpoints and an instruction-boundary target. C’s new exports would affect binding and frame semantics, even when the in-place proof already suffices. Fallthrough must land on the adjacent provider and has no displacement to rewrite. [P-BUILD; E1; B P5; Q3] | Support only decoded, validated encodings. Emit a piece-local expression or the exact ordinary encoding under the same proof. Keep symbolic rel32 when a legitimate symbol already exists and frame semantics are verified. Consider synthesized symbols separately if a required use cannot be handled in that subset. A real all-provider link for prefixed branches, gap/legacy negatives and checked emitted bytes would broaden acceptance. |
| **C07’s sequential Stage 1→2, B §8 S5’s entry criteria, and C05/C06’s bundled rollout.** The ordinary backlog and Group B should wait for the generic planner and B1/B2. | Architectural. Stage 0 validation is material for new capabilities. BULLET.C’s ready subset and other routine area work can already use the existing gates, and B P3 is direct evidence that Group B works under the present link model. Blocking all reconstruction on the planner delays it without addressing an identified dependency. [P-M2; S; B P3] | Run reconstruction and shadow soundness work in parallel. Advance Group B separately once source-policy and integration conditions are met. Put each actual B1/B2 promotion behind only the capabilities it uses. I would serialize an area if a named function depended on the new placement path or a verification defect affected its proof. |
| **C08/C09**. Extraction requires exhaustive Wave 4B/`-5r`, all eight listed fixes and full consolidation of OMF parsing/emission first. | Architectural. Selective extraction needs proof of canonical-source benefit and owner disposition of the current whole-file gate. It needs a strict shared format core for what it accepts. C’s fixed list treats 64 fixups as an established limit and makes optional supported features mandatory even if explicitly rejected. Q3 links 256 off32 fixups with the current linker. Migrating permissive library readers is not an extraction prerequisite. [P-GATE; E4; E5; Q3–Q4] | Defer default rollout. Require a bounded candidate and owner-approved gate treatment. Share the strict record/fixup implementation for verification and admitted transforms. Require positive and adversarial controls for enabled cases and explicit rejection of unsupported cases. Exact linker-version evidence or a consumer could justify a lower record limit or broader codec work. |
| **C12/C13 and B13**. Classify shared literals as hard merges, or infer same object from a non-16-aligned function under a PARA next object. Prefer `-5r` as a default beyond a scoped search. | Inferential. A shared literal address leaves explicit shared storage and linker pooling as alternatives. PARA applies to a segment start. ChooseCampaignDialog’s public follows a table, and rel8/fallthrough alone describe geometry rather than compiler provenance. E7’s paired 417 and E2’s selected runs support a search order, with no identification of predominant original flags. [E0; E1; E2; E7; E8] | Carry premises per proposed object and record alternatives. Rank suitable `-5r -ot` attempts early where candidate spacing warrants it. A historical object map or independent compile/link evidence excluding alternate producers could justify a hard edge or a stronger default recommendation. |
| **C04**. Immediately ship all three audit fixes and a fixed staging-path limit. | Factual as of EV-3, and implementation. The audit-side defects are addressed on the new observed main. The historical 202-row snapshot is still unusable. The short-path issue remains, but `<=48` describes one possible staging choice and does not bound include paths, cwd, translated Windows paths or options. [S; E7; P-AUTO] | Record the audit work as delivered and keep a separate oldcc staging pilot. Test effective compiler-facing paths and preserved include/source semantics across root lengths and overrides. Require zero use of the historical snapshot as a live queue. A measured safe operational envelope can specify a concrete path policy. |

## 3. Unsupported conclusions

- **Historical compiler flags and E2 generalization.** C §2.8 calls predominant historical `-5r` a fact. E7 explicitly limits its conclusion to current reconstructed sources and a finite option grid. The paired 417 positives do not cover all `-4r` contexts. B Q-B06’s proposed negative would rule out a match in its expanded test matrix, with no direct refutation of the historical flag. C §2.3’s `0/96` refers to the native same-flags comparison. The observed shared-tail cases and other flag variants preclude a general codegen-independence claim. E2 Cause B is a contributing diagnostic artifact, and failures can also involve Cause C intra-TU address mapping, D data anchors or F flags. [B §§2, 13; C §§2.3, 2.8; E2; E7]
- **Original CONST census and causal attribution.** C’s live two-string result supports nondeterministic bytes in the three measured positions. A fixup-bounded scan of a historical data range does not classify 157 proven unobservable padding spans, show what allocated their bytes in 1994, or measure prevalence across CUs. E2’s pooling fixtures and E8’s digest repair had already exposed nondeterministic padding in fresh objects. Distinguish known synthetic/compiler gaps, probable original gaps and certified safe exclusions. [C §14 Probes 3/7; E2; E5; E8; Q2]
- **All five unchecked references as code bugs.** The status inventory measures five unchecked witness nodes. B P4 removes the observed WaitSound discrepancy on its input set by restoring a stub input, including for an exact implementation. It does not certify reference C for untested inputs. EndScreen has independent expected call/effect differences. The other three PLAYFLIC failures still need diagnosis. E6’s callback test validates six named GPRs (`ebx,ecx,edx,esi,edi,ebp`) and checks ESP separately. C §2.7’s register list and §6’s DS/DF claim exceed the executed contract. Added ABI checks require separately established convention evidence. [P-M2; P-T4; E6; B P4]
- **E0/E4 evidence scope and source corrections.** C’s Probe 4 freshly checks 20 additions. B P1 is the supplied fresh 539-function E0 audit on the production pin. E0 P1 is a real ChooseCampaignDialog compile and N1 its mutation, with no Build A link in E0. B P6 supplies a disposable real B1 link. E4 is a real two-slice plus controlled-relocation demonstration. Its exact results are in `results/e4/results.json`. Several C §15 paths such as `results/e0/summary.json`, `results/e1/build_a.json` and `test_e0_matcher.py` are absent at the cited commit. Use the pinned files in §12 below. [B §§2, 14; C §§2, 14–15; E0; E4; Q0]
- **Integration claims.** C §§4–5, 8–9 and EXP-3 call Build A IDENTICAL a SHA-256 of the whole EXE. `compare.py` compares a loader projection. A0 Q3 changed a loader-relevant flag and still got exit 0, and B P3–P6 did not run full verification on those disposable trees. These are useful scoped observations with no whole-file digest equality or production admission established. [P-BUILD; A0 Q3; B §14]
- **Scale and metadata.** The reports do not establish linear scaling to 100,000 functions, a fivefold code-size improvement or a universal 64-fixup record limit. A single production timing or benchmark role/task cell measures that configuration. The revised calibration explicitly treats its routing results as provisional and the R3 clean control as invalid. Direct audit code and EV-3 behavior support the provenance conclusions independently. [C §9; CAL; S; Q3]

## 4. Missing assumptions and hidden dependencies

- **Proof authority depends on effective bindings through link.** A frozen record is a programming guard inside the trusted process. It cannot authenticate an arbitrary object substituted after matching or a mutated Python module. Bind the proof to raw bytes, parser contract, ordered compiler invocation, valid extents, dependency identities and the exact object consumed. Recheck after transforms and before linking. A parsed digest alone loses FRAME distinctions (A0 Q3). Keep provenance for the current invocation even if no persistent store is added. [A0 Q3; P-BUILD; E4; E5]
- **An admitted byte contribution is neither a discovered function interval nor an analysis-only slice.** An original public may be inside a contribution, and a trailing byte that the linker places cannot be treated as trimmed just because the local body ends sooner. Ensure every concrete code/data field is owned and verified, especially when B1 widens one cut while B2 assumes the adjoining piece stayed fixed. Changed alignments, zero-sized segments, absolute references and deliberate fallthrough affect encodability and identity. [P-BUILD; E0; E1; E4]
- **State policy and effect policy are distinct.** Restoring an input should not implicitly authorize ignoring an output or shift it into `watch` without discussing the assertion. Conversely, comparing watched memory does not reset host-side counters, CPU flags, mapped pages or prior-case state. Stateful sequences need separate equivalent worlds and explicit transition assertions. Preserve test behavior under the fixed governance rule and treat trusted in-process setup as a stated premise. [P-GATE; P-T4; E6; Q1]
- **The placement tier, optional adapter and source gate are separate.** An E3 diagnostic can run under the current file-level policy. An E4 transform may require an E5 adapter only if the actual slice needs it. Build B needs canonical symbol-based storage and ABI closure, not Build A anchoring, a historical CU database, or a bulk source consolidation. C §8’s Stage 4 dependency on all of Stage 3 would impose those optional paths on M3. B §4’s assumption that every relevant bridge disappears because neighbors become C also needs an explicit audit of out-of-scope ASM/library interfaces. [P-GATE; E3–E6; B §4; C §8]
- **Estimate and ownership should remain separate.** The `98` rows and corrected (14/76/8) queue split describe current routing. Sixty-one placeholder rows are 40 cross-TOML plus 21 same-TOML, so “all require cross-module migration” is an unsupported dependency. Reuse proven rename transactions and admit automation by evidence. Record tentative probe remedies separately from status and from any classification change the owner must resolve. [P-M2; S]

## 5. Counterexamples and probe results

| Probe | Observed result | What it establishes |
|---|---|---|
| **Q1**, `probe.py` | Existing `run_pair` yields `[]` when the original increments unobserved memory and the C side merely reads it. Restoring those bytes exposes return/memory differences. The same runner returns `[]` for an inherited carry input even with memory watched, while a common CPU checkpoint gives `(1,0)`. The guest write hook sees the guest store and sees no event for host `mem_write`. | A false pass exists under trusted fixture code. Guest-only page journaling and memory-only rollback each leave a hole. The toy uses prebuilt OMF under the trusted runner, with no claim of passing a production audit citation. [P-T4; Q1] |
| **Q2**, `probe.py` | A candidate 3-byte gap follows a verified literal. Both sides’ relocation targets are at offsets 0 and 8. An indexed read of offset 5 returns `0x8d` vs `0x73`. E0’s exact RegionMatch rejects. | A pointer-site census and shape tests cannot prove absence of computed data access. Keeping ASM in Build A would preserve the original byte and does not show equivalence of the produced data. [E0; E5; Q2] |
| **Q3**, `probe.py` | `jcxz` emitted `67 e3 01 90 c3`. Actual displacement is 1. The `PC+2` formula gives 2. One 1,280-byte FIXUPP32 payload with 256 disjoint fields for one 1,024-byte LEDATA record links on the Nix OW2 linker and compares IDENTICAL to the NASM layout. | Use decoded encoding and next IP. Treat record packing limits as linker- and format-scoped. With at most 256 nonoverlapping off32 fields and at most 11 encoding bytes per field, the FIXUPP payload cannot overflow a 16-bit OMF record length in this subset. The link does not establish a limit for Watcom 10.0a or other encodings. [P-BUILD; E4; E5; Q3] |
| **Q4**, `probe_extract.py` | E3 mints a real `VerifiedRegion` for a TEXT slice at offset 4 in a synthetic OMF object with independently bounded DATA symbols. E4 rebases `Member_` from DATA+4 to DATA+0 and drops `First_` entirely. | Confirms C’s 5b from output, even with a legitimate proof. C’s 5a is supported by the observed resetting of `Threads()` at both raw passes. 5c warrants a typed byte/flow model or rejection of table-bearing slices, rather than claiming every such slice links wrong. [C §14 P5; E3; E4; Q4] |

## 6. Alternative designs

1. **One model, four outcomes.** Share a normalized address-obligation checker. Keep local body evidence, closed region proof, admitted plan and observed integration distinct. Stage 0 can carry explicit candidate arguments and a matcher-issued receipt, without a new metadata store. OMF and LE encode different stages. Compare equivalent resolved obligations and loader requirements, without requiring equality of raw FRAME encodings or treating original fields as sources for guessed compiler references. Keep strict parsing and artifact identity in the authoritative path. [A0 §§3–4; E0–E5; P-BUILD]
2. **Fast-track the whole object, then admit the bridge.** Try Group B under current declared compilers and the existing full gate once the owner resolves its source policy. Use the shared plan for B1 and for the remaining four evidenced B2 promotions. Model provider adjacency, decoded branch spans and separately supported absolute pointer bindings. Keep unsupported cases unpromoted. B P5’s literal method and C’s piece-local expression are two encodings of the same checked relationship. Choose by measured coverage and implementation cost. [B P3–P6; P-GATE; A0 Q2; Q3]
3. **Start T4 runs from explicit paired state.** Build one case fixture twice, or restore a certified checkpoint that includes CPU context, writable memory, relevant mappings/allocator state and declared external stub/device inputs. Configure per-side callable locations separately. Audit preconditions, completion and observations. A tracked-write optimization must cover trusted host writes or reject them. Keep all existing output and source checks, and investigate one failing citation at a time. [P-T4; E6; Q1]
4. **Optional transforms have narrow admission.** Record data proof per storage object/span, with exact ASM/C provider identity and independent alias evidence. Any explicit exclusion must be owned and disclosed as part of the resulting claim. Prefer whole-segment strict B3 where feasible. Make E4 use the same strict record/fixup codec as any dependent B3 path, preserve non-TEXT definitions and post-rewrite obligations, and defer the rest until a candidate deserves owner review. [E3–E5; P-GATE; Q2–Q4]

## 7. Decisions requiring further evidence

| Decisions | Cheapest decisive experiment | Falsification or admission condition |
|---|---|---|
| B02/B05, C02/C05 | On the production cutover pin, shadow-run the strict verifier on every declared T3, original E0 controls and distinct FRAME/checksum/extent cases. Link the real B1 candidate with a wrong-table negative. | Any unexplained current result, admitted wrong field or undesired ownership handoff blocks the corresponding capability. Include E1 and E2 controls to check the local-closure distinction. |
| B03/B04, C01/C05 | Use one shared plan to dry-run NASM and link Sync alone and MissionDefeat in an isolated export. Exercise entry, interior and retained-to-retained edges, adjacency, altered cuts, prefixed short control, and unsupported legacy. Mutate a required loader flag or fixup and check the stronger receipt. | Wrong encoding, an undeclared relocation, provider gap, or acceptance without actual identity bars promotion. A rejected unhandled case is an acceptable preflight outcome. |
| B06, C06 | Run Group B on the practical cutover revision with both compiler checks, current PLAYFLIC tests and the full existing gate. Obtain the source-rule interpretation or approval from the owner. | Failure of any existing obligation blocks promotion. The result need not depend on acceptance of any B2 bridge. |
| B07/B12, C11 | Test one real affected node under owner-reviewed equivalent initial-state handling. Add memory, carry, host API-write and mutable-stub controls. If a group witness is needed, add E6 entry/ABI/typed-pointer adversarial controls for that specific case. | Divergent cases that pass, swallowed failures or unaccounted state bar adoption. Do not infer that the other four xfails go away. |
| C03/C10 | Try a real natural-literal object plus independently classified data extents, with computed-index, straddling-fixup, named-data and alias negatives. Run strict baseline and final B3 link. | If the candidate cannot establish omitted-byte non-use, keep exact matching for that claim. A final IDENTICAL link alone cannot authorize the exclusion. |
| B09, C08/C09 | Settle the file-level gate with the owner for any mismatching-sibling proposal. Use the smallest justified slice, Q4 as a negative, threaded data, and dense records within the supported linker/format subset. | No change to gate behavior without approval. Unsupported records must reject. All retained definitions and final obligations must compare correctly. |
| C04/C13, B10/B11 | Compare compiled outputs and failure classification under short and long checkout layouts, include overrides and flags. Test OpenArchive’s missing flag pairing or OD variant only when it informs a concrete search. | Any include/ABI/runtime drift or a path crash suppresses that new staging/search assertion. Successful reconstruction does not identify original flags. |
| B13, C12 | Use held-out, object-known fixtures with pre-entry tables, explicitly shared extern storage and linker alignment. Apply constraints to actual segment bases and named provenance. | Any false *hard* edge under its claimed premises bars that rule. Several explanations can remain compatible with exact code. |

## 8. Structured positions

Positions apply to the exact propositions in the frozen index, including propositions worded as rejections. The position field records my response to that wording.

```text
Decision: DEC-B01
Revision: 1
Proposition SHA-256: 2e0072dfeacf3355c35ae8626056819ee56a56b22736ebe3c1b95f1ef350f7bb
Position: CONDITIONAL
Reason: The M2 priority rule is sound. A closed list of allowed implementations would obscure real dependencies.
Conditions: Keep capability admission tied to an observed blocker or soundness gap. Keep routine work moving and allow a concrete M2 case to justify a narrow E6 path.
Related objections: OBJ-A15
```

```text
Decision: DEC-B02
Revision: 1
Proposition SHA-256: 52e9b26dfdd3b6954ee162adfb0c71e128aa2aa696965fcd2c09b43b1e7e7a16
Position: CONDITIONAL
Reason: E0 closes measured gaps and the production census supports cutover.
Conditions: Use strict raw admission, preserve the existing file-level gate and audit the actual cutover cohort. Permit correcting a false rejection on independent proof.
Related objections: OBJ-A10, OBJ-A17
```

```text
Decision: DEC-B03
Revision: 1
Proposition SHA-256: e4227a079ab271526345bc98d3a54e8b6c12cccf6b476ee37748b7411375e6f3
Position: CONDITIONAL
Reason: Sharing the plan eliminates predicate/emitter drift. Assembly and link identity are separate evidence.
Conditions: Label planning and materialization separately. Reject standalone Sync under disabled or unsupported B2. Require an actual integration receipt for promotion.
Related objections: OBJ-A09, OBJ-A13
```

```text
Decision: DEC-B04
Revision: 1
Proposition SHA-256: 10f99b1cf2a534df1eb4b3a8f6dd0774a174e1e785dae2222be7ca52b3ce08a1
Position: CONDITIONAL
Reason: B P5 establishes fixed-displacement feasibility for concrete cases.
Conditions: Prove decoded source and destination, width, next IP, edge cover and mode. Check emitted bytes and typed loader identity. Let existing valid symbolic bindings remain symbolic.
Related objections: OBJ-A13
```

```text
Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: A proved affine base and leading coverage address the actual ChooseCampaignDialog defect. The dependencies supply the global plan.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: CONDITIONAL
Reason: B P3 supports immediate trial without a generic B2 dependency.
Conditions: Resolve the ground-rule wording with the owner and run current source/test/full-gate admission. Scope the flag choice to this group.
Related objections: OBJ-A15
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: CONDITIONAL
Reason: The memory defect is real, including a demonstrated false pass.
Conditions: Add equal CPU and declared external state. Cover host API writes. Keep restoration separate from effect assertions and obtain owner review for changed test meaning.
Related objections: OBJ-A12
```

```text
Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: ACCEPT
Reason: A bounded B3 pilot can wait. Its tested production use cases are already DONE.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B09
Revision: 1
Proposition SHA-256: 00ff7874640d8a9159ec0d393a17aac144a02a9b2126aafedc5883bc4e6135d6
Position: ACCEPT
Reason: Selective promotion from a mismatching source file needs owner disposition of the existing gate. Pure E3 diagnostics confer no such credit.
Conditions: none
Related objections: OBJ-A14
```

```text
Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: The stated matrix applies to the measured optimization contexts, with PARA under tested 10.0a -ot.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: The paired results justify additive search. Current reconstructed contexts do not identify historical settings.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: The feature should be demand-led and preserve the existing audit until parity is proved.
Conditions: Allow a later justified consumer as well as an M2 case. Entry hooks require a proved entry-only boundary and policy. Keep paired-state parity.
Related objections: OBJ-A12
```

```text
Decision: DEC-B13
Revision: 1
Proposition SHA-256: 84a9be5c34e2d9d48bff2c233da0fc9779e5ac2f64a01704f120998ce876741c
Position: CONDITIONAL
Reason: The analyst-only policy is supported. Hard constraints need premises on actual code and data production.
Conditions: Require compiler and linker provenance for shared-tail claims. Test PARA at the segment base. Keep shared literals as conditional evidence with competing explanations.
Related objections: OBJ-A16
```

```text
Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: A separate candidate record and persistent store can wait. An in-memory proof binds the raw object and current inputs.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Keep production independent of experiment scaffolding. Port and extend relevant controls under the existing gate.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Probe outcomes do not establish all proposed status labels or the full cause of WaitSound behavior.
Conditions: none
Related objections: OBJ-A15
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: Extraction offers no demonstrated M2 leverage and would require separate gate and format decisions.
Conditions: none
Related objections: OBJ-A14
```

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: CONDITIONAL
Reason: The three scopes should be visible to their consumers. The plan itself is a preflight.
Conditions: Use a separate observed integrated result. Tools can consume a typed status without implementing every proof layer.
Related objections: OBJ-A09
```

```text
Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: CONDITIONAL
Reason: Local bounds fix E2 Cause B and tail targets must be accounted for.
Conditions: Represent explicit sibling-context edges. Keep strict exact data matching for initial cutover and remove the dependency on C03. Re-audit under the existing file gate.
Related objections: OBJ-A10, OBJ-A11
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: The five conditions do not rule out computed or overlapping access and unnecessarily gate E0.
Conditions: none
Related objections: OBJ-A11
```

```text
Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: CONDITIONAL
Reason: EV-3 has addressed the audit defects. Short-path reliability still merits its own work.
Conditions: Remove already delivered fixes. Validate effective paths and unchanged compile semantics before standardizing a measured limit.
Related objections: OBJ-A17
```

```text
Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: CONDITIONAL
Reason: Provider-aware B1/B2 and verified adjacency address the observed failure classes.
Conditions: Use real instruction width, optional typed labels only when justified, exact output proof and non-legacy enforcement. Keep closure separate from actual integration.
Related objections: OBJ-A09, OBJ-A13
```

```text
Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: CONDITIONAL
Reason: Prefer exact whole-TU placement for the proved shared-tail cases.
Conditions: Do not require generic B2 to precede Group B. Use -5r or -oa -5r as tested candidate flags and verify each TU with current inputs.
Related objections: OBJ-A15, OBJ-A16
```

```text
Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: A mandatory serial dependency blocks routine area work, and the five unchecked references have not all been diagnosed as C bugs.
Conditions: none
Related objections: OBJ-A12, OBJ-A15
```

```text
Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: CONDITIONAL
Reason: I accept the exact proposition’s exclusion of near-term or default prototype rollout.
Conditions: Require owner gate disposition and a justified candidate. Admit only the tested format subset. Do not require exhaustive Wave 4B or 64-fixup chunking without a demonstrated need.
Related objections: OBJ-A14, OBJ-A18
```

```text
Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: CONDITIONAL
Reason: Share strict decoding and emission across admitted transforms.
Conditions: Scope the codec to supported needs. Leave permissive readers alone where appropriate and express record limits in bytes and format/linker terms.
Related objections: OBJ-A18
```

```text
Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: CONDITIONAL
Reason: E5 supports a bounded ASM-provider adapter. V4 cannot serve as its proof.
Conditions: Use strict whole-segment matching first. Any gap treatment needs independent access/layout evidence and a real reason for the pilot.
Related objections: OBJ-A11
```

```text
Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: Existing single-function witnesses need state hardening. E6 extensions should be required by the individual witness.
Conditions: none
Related objections: OBJ-A12
```

```text
Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: CONDITIONAL
Reason: Reject automatic splitting and keep competing hypotheses. Shared literals and epilogues need producer premises.
Conditions: Use true segment bases for alignment. Require evidence excluding pooling/shared storage for a literal hard edge. Defer new storage until needed.
Related objections: OBJ-A16
```

```text
Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: CONDITIONAL
Reason: Correct the measured alignment matrix and keep new paired tests available.
Conditions: PARA qualifies tested -ot, while tested -os/-od use byte alignment. Rank -5r for suitable contiguous candidates and retain the declared defaults.
Related objections: OBJ-A16
```

```text
Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: The existing target does not justify a multi-backend plugin framework. Clean boundaries suffice.
Conditions: none
Related objections: none
```

**Own Round 0 positions.** RETAIN A01–A06, A09 and A10. The separate candidate type in my sketch can be omitted. B P3 also changes my preferred sequencing for Group B without changing A05’s proposition. The two anticipated revisions below remain frozen at revision 1 for this round.

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: RETAIN
Reason: Round 2 should add an explicit owner decision on file-level gate semantics before selective T3 from a TU with mismatching siblings. B09 identifies a dependency my opening omitted.
Conditions: No revision in Round 1.
Related objections: OBJ-A14

Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: RETAIN
Reason: Round 2 should make paired initial-state symmetry a current T4 requirement and separate it from the timing of the group harness. B P4 and Q1 changed my prioritization.
Conditions: No revision in Round 1.
Related objections: OBJ-A12
```

## 9. New objections

- **OBJ-A09 — Correctness/verification.** B03/I-2 and C01/C05 place a clean plan and emitter acceptance at the integrated buildability boundary. With independently run assembly/link tools, that is insufficient. Sync exposes a preflight hole today. A forged-execute-flag image exposes the current comparator’s narrower projection. In the new design a plan must not mint promotion evidence before the actual output and its provider/loader checks are recorded. [P-BUILD; A0 Q2–Q3]
- **OBJ-A10 — Correctness/verification.** C02/V2 says cross-function edges force `UNSUPPORTED` in FunctionMatch, and B §3.2 I-1 restricts changes to losing matches. E1’s known geometry can make a scoped body match with a proved external context obligation. E2 shows why the first-public window is unusable on noncontiguous local comparisons. Under explicit support assumptions, replacing the bad bound and recording context solves both. A blanket rule loses useful distinctions and blocks corrections to false negatives. [E0; E1; E2]
- **OBJ-A11 — Correctness/verification.** C03 and C10 make the V4 predicates sufficient for a CONST exclusion. Database and decoded direct references omit computed effective addresses. Q2 reads such a byte with both explicit relocation sites outside the gap. Even ASM-provided output would only prove the original byte was retained. For source-data equivalence, require independent extent and access proof and exclude no intersecting obligations. The failure mode is unjustified verified data and potential drift if the provider ever changes. [E5; Q2]
- **OBJ-A12 — Correctness/verification.** B07’s restoration scope covers memory. C11 freezes the current harness in M2 and makes full E6 plus extensions prerequisite to any consolidation. Q1 exhibits a carry-only false pass and a host write invisible to a guest hook. The experiment’s trusted setup still permits these ordinary behaviors. The needed correction is full paired initial-state accounting for affected witnesses, with demand-led E6 extensions. Otherwise both false equality and false divergence can survive. [P-T4; E6; B P4; Q1]
- **OBJ-A13 — Correctness/verification.** C05’s elaboration uses `t - (ia+2)` for every rel8 and mandates interior rel32 PUBDEF. B04’s literal path leaves encoding checks implicit. With x86 prefixes and loop forms, the next-IP arithmetic and assembler spelling can differ. Q3’s prefix changes the computed displacement by one. Fallthrough is instead an adjacency obligation. Require a typed encoding, exact endpoints and final materialization, and only add exports under an independent symbol/effective-frame proof. [P-BUILD; Q3]
- **OBJ-A14 — Blocking architectural.** C08’s later extraction prerequisites omit owner disposition of existing `match --all` semantics for mismatching publics. The current per-public conjunction fails the canonical file even when a retained slice succeeds. This objection concerns credit for partial canonical TUs. A read-only partial diagnostic can remain useful without changing that policy. No promotion adapter can redefine the gate. [P-GATE; E3; E4]
- **OBJ-A15 — Implementation risk.** C07 and B §8 S5 require generic placement work before the main reconstruction queue. B16 would turn probes into categorical status labels. B P3 shows an independent Group B route, and the latest inventory confirms already eligible work. Four other B2 candidates and B1 have bounded positive probes, while the tests and owner are still authoritative. Record candidates and diagnoses separately, and run independent tracks. The proposed serial order delays real work and prematurely hardens the WaitSound label. [B §§8, 11, 14; S; P-M2]
- **OBJ-A16 — Unsupported factual claim.** C12 treats shared literals as hard merges and C13 couples the alignment correction to a default reconstruction family. B13’s hard epilogue rule also needs verified producer premises. E8’s sample does not exclude external storage or other producers. A PARA segment can have a leading prefix, and E7’s compatible contexts do not identify historical flags. The consequence is a false historical partition or needless rewrites. Record candidate contexts and edge-specific premises. [E0; E1; E2; E7; E8]
- **OBJ-A17 — Implementation risk.** C04 bundles obsolete audit changes with a hard copy/staging limit, and B02/C02 do not by themselves ensure non-lossy raw binding. EV-3 covers the audit defects. A short nominal directory can still carry a long compiler-facing argument or alter include identity. A0 Q3 exposes why a parsed projection is insufficient for proof reuse. Separate staging parity, scheduling fingerprints and strict raw artifact validation. [S; P-AUTO; A0 Q3]
- **OBJ-A18 — Unsupported factual claim.** C08/C09 treat missing 64-fixup chunking as an established production-blocking overflow and require broad serializer consolidation. The selected subset’s bound is below the encoded record length field, and Q3’s 256-fixup OMF record links on the tested linker. Q4 confirms a different concrete corruption. Keep record-limit tests for the actual linkers and share the strict subset. Unsupported records may reject. Overgeneralizing forces a broad rewrite before any benefit. [E4; E5; Q3–Q4]

## 10. New decision proposal

```text
Decision: DEC-A11
Title: Certify paired starting state independently of outputs
Proposition: A T4 pair must execute from equivalent per-side CPU, memory and declared mutable dependency state for each case. Implement independent initialization or a certified checkpoint with host- and guest-write accounting. Keep the effects compared by existing tests separate from state restoration. Report unsupported state when equivalence of inputs cannot be established. Apply this requirement to affected current witnesses before adopting multi-function extensions.
Revision: 1
Position: PROPOSE
Reason: A watched-range or memory-only reset can hide real differences. Prerequisite state can leak through CPU flags and host-written memory.
Evidence: P-T4, B §14 P4, Q1
Assumptions: Trusted in-process fixtures, explicit state/effect contracts, owner approval where an existing test's meaning changes.
Dependencies: DEC-A01, DEC-A08
```

## 11. Probe log

All reads and commands ran from the Architect A worktree via `nix develop -c`. The three specified inbox SHA-256 values matched the charter. I read Claude lines 1–895, Gemini lines 1–1063 and all 335 index lines in bounded reads. I recomputed each proposition hash from its exact indexed text. I used the supplied probe reports from B and C, without reading their runtimes or running their scripts. No production file, Git state, shared data or compiler installation changed. I ran no full verification, full test suite, Watcom 10.0a compiler or full Build A. The Secretary’s EV-3 verification is the full production result cited here.

**Q0 — Supplemental pin and artifact checks.** Read-only commands included:

```sh
nix develop -c git show -s --format='%h %T %P %s' d5d4d2c 122dc98 17733f9 d55d493
nix develop -c git merge-base --is-ancestor dae45bd d5d4d2c
nix develop -c git merge-base --is-ancestor d5d4d2c a21772b
nix develop -c git diff --stat a21772b 17733f9 -- \
  tools/wc1/build.py tools/wc1/emit.py tools/wc1/compare.py tools/wc1/le.py \
  tools/wc1/match.py tools/wc1/omf.py tools/wc1/oldcc.py tools/wc1/cemu.py \
  tools/wc1/emu.py tools/wc1/t4spec.py docs/GOAL.md Makefile
nix develop -c git ls-tree -r --name-only e6150b8 \
  docs/research/build-codegen/results experiments/build_codegen
nix develop -c bash -c 'git show 17733f9:docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/e7_snapshot_revalidation.json | jq -c ".summary.counts"'
```

EV-2 and EV-3 trees matched the notices. The ancestry commands returned 0 and 1 respectively. The scoped stat was empty. The tree listing supplied the corrected paths in §12. The snapshot summary counts are `{"total":202,"fresh":0,"stale":63,"partial":139,"malformed":0}`. The post-campaign report and code confirm checkout-rooted headers, live tool identity and unknown Git state rejection at the proof gate. `_git` itself still returns `None` on failure, which is propagated and refused. These checks do not replace the live audit needed for future Wave 4B inputs. [S]

**Q1–Q4 — Disposable probes.** Scripts and outputs are under `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r01-probes`. The exact commands were:

```sh
nix develop -c bash -c '
set -eu -o pipefail
P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r01-probes
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD:$PWD/tools"
python3 "$P/probe.py" 2>&1 | tee "$P/results.txt"
'
nix develop -c bash -c '
set -eu -o pipefail
P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r01-probes
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD:$PWD/tools"
python3 "$P/probe_extract.py" 2>&1 | tee "$P/extract-results.txt"
'
```

Both exited 0. `probe.py` calls the pinned `Emu`, `CModule` and `run_pair` on independently specified synthetic bytes, uses E0 for the CONST check, and invokes `nasm -O0 -f obj` and `wlink @<name>.lnk` on toy objects. It compares the two toy LE links with `python3 -m wc1.compare nasm.exe dense.exe`. `probe_extract.py` assembles a small OMF object with NASM, passes an independently constructed original mapping and data boundaries to E3, then runs E4 and inspects the resulting publics. The exact outputs follow.

```text
host_write_guest_hook_events 0
unwatched_guest_memory_pair [] guest_data_write_seen True
restored_guest_memory_pair ['eax: original 0x1 != C 0x0', 'memory 0x50000: original 01 != C 00']
carry_only_pair [] with_same_cpu_baseline (1, 0)
const_gap (5, 8) relocation_targets [0, 8] [0, 8] strict_region MISMATCH computed_read ['eax: original 0x8d != C 0x73']
dense_fixups 256 payload_bytes 1280
nasm link_exit 0
dense link_exit 0
dense_compare 0 IDENTICAL (loaded image, entry, stack, fixups)
jcxz_bytes 67e30190c3 disp 1 incorrect_pc_plus_2 2

E3 VerifiedRegion []
raw_input_publics {'Sibling_': (1, 0), 'Probe_': (1, 4), 'First_': (2, 0), 'Member_': (2, 4)}
raw_output_publics {'Probe_': (1, 0), 'Member_': (2, 0)}
dropped [{'offset': 0, 'reason': 'public_outside_slice', 'symbol': 'Sibling_'}, {'offset': 0, 'reason': 'public_outside_slice', 'symbol': 'First_'}]
```

The synthetic machine-code pairs exercise the trusted runner alone and have no cited production T4 status. The CONST example tests the proposed observable conditions, without asserting that real SaveSlotPath reads its gaps or that a specific C source declares access to them. The dense result covers the local Nix linker and one supported record shape. The E4 probe inspects the erroneous intermediate before any B3 plan and makes no claim of an IDENTICAL final link. The prefix probe is an encoding counterexample, with no assertion that this instruction occurs on a current cut.

## 12. Source index

`@E` = `@e6150b856106ae113bb023300b956fff318da7ef`. `@P` = `@a21772b8140b4b07012cde8da7da18ad3f6d56b6`. The latter remains the pinned production comparison for the openings. `@S` = additional main observation `@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`.

| ID | Source |
|---|---|
| A0, B, C | `CONSILIUM-R00-POSITION.md` in this worktree, the two frozen inbox openings identified by the charter’s SHA-256 values, and `00-PROPOSITION-INDEX.json` in the same inbox. B P1–P7 and C Probe 1–7 refer to each frozen opening’s §14. |
| R | `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8`, especially §§5–8, 13, 15–16 and 18. |
| P-GATE | `AGENTS.md@P`, `docs/{GOAL,METHODOLOGY}.md@P`, `Makefile@P`, `tools/wc1/match.py@P` `_match_one` and `all_srcs`. |
| P-BUILD | `tools/wc1/{build,emit,match,compare,le,omf,omfpatch}.py@P`. See `build.py` `place`, `check_placed_plan`, `check_t3_buildable`, and `emit.py` `replaced_interior_refs` and `emit_pieces`. |
| P-T4 | `tools/wc1/{emu,cemu,t4spec}.py@P`; `tests/test_playflic_t4.py@P` `test_intro_op_wait_sound`; `tests/test_mod_2efd0_t4.py@P` `test_end_screen`; `analysis/symbols/playflic.toml@P`; `src/playflic/player_reference.c@P`. |
| P-M2 | `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json}@P`; `docs/telemetry/campaigns/2026-11-27-e7-production/{report.md,t4_improved_audit.json}@P`; `docs/research/m2-completion/{inventory.json,dependency-groups.json,roadmap.md}@P`; `tools/wc1/{m2_inventory,overnight}.py@P`. |
| P-AUTO | `tools/wc1/{oldcc,t3_audit,wave4_fp,wave4,permuter}.py@P`; `docs/research/build-codegen/decisions.md@E` D9. |
| E0 | `docs/research/build-codegen/E0-matcher-soundness.md@E`, `results/e0/{controls.json,t3_reaudit.json}` under the same directory, `experiments/build_codegen/e0/{matcher_proto,controls,test_e0}.py@E`. |
| E1/E2 | `docs/research/build-codegen/{E1-shared-epilogues,E2-compilation-context}.md@E`, `results/e1/{results.json,disasm_evidence.txt}` and `results/e2/{results.json,consolidation_rows.csv}` under the same directory, `experiments/build_codegen/e1/fixtures/group_b_current.c@E`. |
| E3/E4/E5 | `docs/research/build-codegen/{E3-partial-matching,E4-omf-extraction,E5-data-anchors}.md@E` and `results/{e3,e4,e5}/results.json` under the same directory. `experiments/build_codegen/e3/partial_matcher.py@E`, `e4/omf_extract.py@E`, `e5/omf_b3.py@E` under the same experiment root. `docs/telemetry/campaigns/2026-11-25-build-codegen/summaries/{rev-e3-01,rev-e4-01,rev-e5-02}.md@E`. |
| E6/E7/E8 | `docs/research/build-codegen/{E6-multifunction-t4,E7-compiler-calibration,E8-cu-boundaries}.md@E`, `results/e6/results.json`, `results/e7/calibration_matrix.json`, `results/e8/{metrics.json,signal_metrics.csv}` under the same directory, `experiments/build_codegen/e6/{mf_cemu,test_e6}.py@E`. |
| S | EV-2 `d5d4d2c`, EV-3 merge `122dc98`, Secretary’s verification on `17733f9` (2,505 passed, 11 skipped, five xfailed, Build A IDENTICAL, 912 DONE). `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/{report.md,e7_snapshot_revalidation.json}@S`; `tools/wc1/{t3_audit,wave4_fp,m2_inventory}.py@S`; `tests/{test_t3_audit,test_m2_inventory}.py@S`. |
| CAL | `docs/research/model-calibration-engineering/{report.md,recommendations.md,REPRODUCIBILITY.md}@d55d493`. |
| Q0–Q4 | Round 1 checks and private probe logs in §11. Round 0 Q2 and Q3 are separate and cited as A0 Q2–Q3. |