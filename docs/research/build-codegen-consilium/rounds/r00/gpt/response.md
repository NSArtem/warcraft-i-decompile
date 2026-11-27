# Build & Codegen Infrastructure — Round 0 opening position

Architect A — GPT · Evidence revision EV-1 · 2026-11-27

## 1. Position summary

Retain the RFC’s separation of machine verification, physical placement, behavioral equivalence, and historical source recovery. Revise the implementation plan into a small verification and placement core with independently admitted capabilities. Start with the known matcher gaps, an audit of the **live pinned cohort of 539 T3 functions**, and a planner that reasons about the final partition of the whole image. Adopt B1 for verified leading tables and pursue B2 for short branches across fixed in-place providers. Prefer whole-TU integration where it reproduces the original, as E1 demonstrated for the dialog and PLAYFLIC groups. Keep B3 and selective extraction off M2’s critical path unless a named, still-incomplete function warrants the cost. [R, E0–E5, P-BUILD, P-M2, Q1–Q3]

The difference between local match and actual integration is now concrete. Inserting `IntroOpSyncSound` separates two **retained ASM** pieces and breaks assembly even though no edge enters the C cut’s interior. In a private probe, piece-local expressions reproduced both original short branches with zero relocation records. A separate probe showed that `wc1.compare` prints `IDENTICAL` for a change to the code object’s execute flag. Continue to require the existing comparison and verify provider and loader-relevant invariants explicitly for the new paths. [P-BUILD, P-M2, Q2, Q3]

Production at `a21772b` has **912/1010 DONE**, with 98 remaining, including 93 without accepted C and five unchecked reference functions. E7’s 13 T4→T3 promotions added zero DONE. The mechanical campaign added 13 DONE and reopened part of BULLET.C. Most remaining work needs area reconstruction, naming/dependency repair, or behavioral evidence. A T4 with the required evidence and blocker is a valid M2 outcome. Neither broad T4→T3 recovery nor historical TU consolidation should displace that work. [P-GOAL, P-E7, P-M2, Q1]

E0–E8 establish scoped feasibility and counterexamples. They leave open production parser conformance, all-provider branch closure, migration of T4 harness guarantees, historical CU identification and Build B’s data/ABI closure. The roadmap below gives each of those its own acceptance evidence and leaves scope, tier rules, existing gates and T5 authorization with the owner. This is my independent opening position. [R, P-GOAL, E0–E8]

## 2. Experiment-by-experiment interpretation

### E0 — Matcher soundness

**Hypothesis and method.** A bidirectional, placement-aware matcher can catch missing relocations, wrong local-data pointers, and bad leading bytes that the legacy matcher accepts, while preserving the declared-compiler corpus. `controls.py` compiles real fixtures and mutates copies alongside synthetic objects. `reaudit_t3.py` freshly compiles 514 files for 519 functions, using each declared compiler. The results record 55/55 controls and 519/519 FunctionMatch and RegionMatch. The 77-test suite adds CLI and artifact checks. [E0]

**Positive controls.** P1 includes all 16 leading bytes of ChooseCampaignDialog, P2/P5 distinguish InitPaths absolute and link-time relative obligations, P3 leaves the VGA constant literal, P4 checks a real-image-derived pointer table, and B-series controls cover intra-segment rel8/rel32 and transitive local data. **Negative controls.** N1 changes a table case target, N2 deletes a required OMF fixup while preserving the preferred-base value, N3/N4 corrupt or omit data-pointer obligations, and N8 retains three independent findings. Review repairs cover truncated functions, earlier siblings targeting a trimmed tail, contradictory local definitions, invalid extents and error exits. See `test_legacy_false_matches`, `test_earlier_function_uses_final_region_extent` and `test_entrypoint_exit_on_either_audit_error`. [E0]

**Interpretation and disposition.** Adopt the contract. Successful control coverage and the historical corpus establish a strong migration starting point. E0 trusts the parsed OMF and discovery inputs. Its use of a shared object base can also conservatively reject isolated functions in a noncontiguous TU, as E2 shows. I reproduced a bad nonzero record checksum yielding E0 RegionMatch, and distinct FRAME encodings collapsing into the same legacy parsed module. E0’s checks need a strict input boundary for authoritative admission. Run a fresh, declared-compiler audit of every current T3, with raw-record and cross-provider boundary negatives. [E0, E2, P-BUILD, Q3]

### E1 — Shared epilogues

**Hypothesis and method.** Natural Watcom 10.0a codegen can reproduce shared tails when TU membership, order, source spelling and options are chosen together. The experiment compiles 97 variants and records 196 function observations, public offsets, actual branch destinations, E0 verdicts and link results. It compares standalone, reversed, pair-only and original orders. [E1]

**Positive controls.** The revised readable Group A uses `-ot -oa -ol -5r` and covers `[0x16cc8,0x16d59)`. Group B uses `-ot -ol -5r` and covers `[0x2315c,0x231ea)`, including the intervening Sync handler. Both full regions pass. The two primary isolated game links and a second Group B flag variant are IDENTICAL with 8,770 matching fixups. **Negative controls.** Reversed Group A can emit the same `74 f3` targeting the wrong helper. With the supplied hit-test C, `74 f5` reflects the missing two-byte inter-function pad. With revised C and `-5r` alone the helpers match while the owner differs. `-os -4r` folds the helpers. Group B with `-4r` moves the publics and expands one short branch. See `test_group_a_separates_alias_scheduling_from_layout`, `test_pair_and_reverse_order_are_negative_exact_region_controls` and `test_closed_region_build_a_is_identical`. [E1]

**Interpretation and disposition.** Adopt exact whole-TU pilots where justified, starting with Group B on production. The experimental link has one C region with ASM remainder and excludes Group A’s three and Group B’s two final padding bytes. Revalidate both compilers, existing behavioral citations whose sources change, and the mixed production build. The successful group is sufficient for those machine bytes. It establishes no unique original source partition or generic B2 repair. [E1, P-GOAL]

### E2 — Compilation context and alignment

**Hypothesis and method.** Measure whether flags and neighbors alter function layout, machine code or data. Compile exact-length and natural C fixtures under 12 10.0a and two OW2 configurations, then measure 96 T3s from three areas against same-flags standalone controls. Eight context variants across 28 group definitions plus the exact one-file control yield 225 contexts. Three native RegionMatch TUs receive 63 controlled neighbor edits. STATUS needs an experiment-local declaration overlay, checked against all 58 standalone controls. [E2]

**Positive controls.** For the measured 10.0a configurations, `-4r -ot` spaces functions at 16 bytes, `-3r/-5r -ot` at four while retaining paragraph SEGDEF, and size/OD configurations pack at one byte. Tested OW2 `-ot` configurations space at 16 under both architectures. There are 96/96 standalone matches, nine native contiguous matches and 23/23 contiguous definitions matching under `-5r`, including a 40-function STATUS run. **Negative controls.** Forced native areas retain 83/96 strict function matches and zero whole-area region matches. No normalized instruction body changes from same-flags native consolidation were measured, but local offsets, CONST bases and conservative region bounds changed. Size optimization changes 23 bodies through tail sharing. An inserted GAMEDLG literal breaks a neighbor’s anchor without changing its non-address instructions. See `test_fresh_exact_length_alignment`, `test_real_e0_region_and_corruption_controls` and `test_perturbation_controls_are_region_matches_and_byte_lengths_measured`. [E2]

**Interpretation and disposition.** Adopt measured, compiler- and configuration-specific alignment. Context provenance includes *all* TU members even for a one-function claim. The chosen groups and perturbations are correlated, the loop fixtures cover two forms, and serialized CONST gaps are normalized only as research evidence. Whole-area migration and universal claims about loop alignment or register allocation require a new, independently selected sample and a concrete use. Rechecking each pilot beats repeating the full census. [E2]

### E3 — Partial matching

**Hypothesis and method.** A bounded slice can match even when siblings fail, provided its actual object dependencies are identified and its data mapping is proved. `partial_matcher.py` uses fresh anchors per candidate with E0 checks and explicit boundary inputs. `run_e3.py` exercises real dialog, Farm and Score objects and independent synthetic mappings. [E3]

**Positive controls.** FarmPanelChanged `[0x28254,0x28298)` has an existing symbolic call to `UnitPanelStateChanged_` at `0x281f4`. ScoreTickIncome `[0x24e90,0x24edd)` matches after reversing two C addends, while its siblings still mismatch. The shifted CONST fixture matches using separately bounded literals. A synthetic direct rel32 identifies a sibling entry and records a rewrite obligation. **Negative controls.** DialogHighlightOff’s short edge and folded public fail. Unknown/interior siblings, wrong targets, corrupt literal bytes, equality-topology changes, unproved mutable shifts, truncated extents and escaped fallthrough are rejected or conditional. `test_group_closes_rel8_only_when_target_is_also_verified` demonstrates closure by expanding the group. [E3]

**Interpretation and disposition.** Adopt the distinction between a matched body and a verified region with explicit dependencies. A conditional outgoing rel8 result confers no extraction permission. The data controls establish supplied-layout feasibility, and the prototype takes discovery and parsed objects as inputs. Preserve the design without promoting the general partial matcher as an M2 prerequisite. If a pilot earns its place, test only its relocation and data subset against the authoritative parser and Build A. [E0, E3, E4]

### E4 — Selective OMF extraction

**Hypothesis and method.** Some verified regions can be rewritten as OMF32 contributions while preserving independently identified address obligations and every ordinary byte. `omf_extract.py` reads input records, scans slice closure, rebuilds slices and checks output. `run_e4.py` links real and controlled images. [E4]

**Positive controls.** Score and Farm each link into a full game oracle, IDENTICAL. A Watcom A→C case keeps its existing symbolic call and uses an E5 CONST anchor. A separate NASM fixture converts an actually unfixed direct rel32 to EXTDEF/self-relative FIXUPP. A 1,500-byte control splits LEDATA at 1,022 bytes to avoid cutting a field. **Negative controls.** Both folded dialog helpers reject, as do an unnamed interior target, removed sibling identity, absent or wrong mutable layout, wrong external target, and a slice excluding a used jump table. `test_byte_invariant_self_check_rejects_a_changed_immediate`, `test_thread_definitions_expand_into_self_contained_fixups` and `test_record_checksums_and_modend_are_enforced` cover transform integrity. [E4]

**Interpretation and disposition.** Keep selective extraction as a conditional migration tool. The real slices have one function each, and the real Farm edge is already symbolic. Two successful image links do not qualify a general extractor. The reviewed prototype accepts a caller-constructed `VerifiedRegion` at its first provenance check. Production must bind/reverify the proof against raw input and current analysis, check chunk offsets, handle or reject 16-bit big SEGDEF, and verify the artifact after the last data rewrite. Add a real retained multi-entry slice and mixed-provider link before extending support to that case. [E4, C-REV]

### E5 — Data-anchor decoupling

**Hypothesis and method.** An original-address ASM provider can serve verified compiled data references independently of C code order. E5 checks data bytes and both directions of pointer obligations before emptying segments, rewrites supported off32 targets to generated externals, preserves addends and expands threads, then links with one ASM data provider. [E5]

**Positive controls.** All nine full-game variants compare IDENTICAL. Canonical SaveErrorDialog matches with `-os` at literal stride `0x22`. Native `-ot` can reproduce that stride with explicit `_DATA` arrays. The real DefeatDialog fixture has live CONST, DATA and BSS in one C object supplying one function. Synthetic controls cover three segments, retained data pointing to emptied CONST, all thread slots and alternative flat-target frames. A seeded cross-record thread on discarded data tests its real lifetime. **Negative controls.** The ordinary anchor-order check rejects DefeatDialog `0x56c0c` followed by SaveErrorDialog `0x51ea6`. The canonical `-ot` literal stride is `0x24`; adding a neighbor alone does not fix that input. Corrupt pointers/bytes, wrong aliasing, unjustified mutable boundaries and unsupported records fail. See `test_full_build_a_images_and_every_le_fixup`, `test_threads_survive_discarded_records_and_expand` and `test_weak_external_comments_rejected_before_renumbering`. [E5]

**Interpretation and disposition.** Adopt the semantic-owner/provider distinction now. Gate a whole-segment production adapter on verified identity and strict decoding. The corpus scan found zero native THREAD in 514 baseline objects plus the fixture. Expansion is necessary whenever accepted input contains threading, including on discarded records. For a first smaller path, explicit rejection is also safe. The flat frame results apply to the tested link/encoding subset. The per-symbol link has two independently bounded literals and establishes no general mutable remapping policy. SaveErrorDialog is already T4 on production, so defer deployment absent a stronger dependency. [E5, P-M2]

### E6 — Multi-function T4

**Hypothesis and method.** An explicit boundary and symmetric substitutions can support isolated, group and downstream-integrated comparisons with compiled callbacks. E6 compiles real Options and PLAYFLIC TUs and exercises ten positive scenarios, two legacy reproductions, fourteen rejected variants and a zero-fixup NASM control. It runs 96 tests. [E6]

**Positive controls.** Real Options callbacks execute at reconstructed addresses in Group/Integrated and vary watched effects. Four typed pointer slots carry exact logical identities and aliasing. PLAYFLIC reaches real TextWidth and memory-clear helpers on Integrated paths; isolated calls produce symmetric substitution logs. The real IntroFrame call has one EXTDEF self-relative FIXUPP (field `+0x12f`), resolved to the local compiled loader by legacy CModule. The zero-fixup case is separate. **Negative controls.** Interior entries, including unreachable trailing code reached indirectly, inlining/elimination, undeclared/asymmetric/boundary stubs, wrong callback or aliasing, ordinary byte differences, boundary redirection and bad callback register preservation/stack cleanup all reject. See `test_trailing_code_ownership_and_rejection`, `test_callback_abi_before_context_restore`, `test_pointer_callbacks_must_execute` and `test_fresh_source_provenance`. [E6]

**Interpretation and disposition.** Adopt these boundary rules, with real callbacks preferred in group comparisons. E6 is scenario evidence under trusted Python setup. Its relocation loader and audit are experimental, and Integrated may execute original code beyond the reconstructed boundary. Before replacing any cited T4 test, demonstrate parity with production fresh-compile and runtime audit, original-side execution isolation, correct reset of mutable state, and rejection of skipped or vacuous evidence for the new witness. An exact E1 TU with no remaining T4 ownership change needs no new group harness. [E1, E6, P-T4]

### E7 — Compiler calibration

**Hypothesis and method.** Measure capability, TU-specific compatibility, and search yield separately. Probe 31 options, then run 26 configurations across 519 T3 and 385 T4 functions, including 373 eligible dependency-clean T4. Retain 23,504 cells, 21,618 actual 10.0a compiles and explicit untested cells. E0 determines exactness and production score ranks misses. Four actual Build A links check the promotable cohort. [E7]

**Positive controls.** Nineteen previously nonmatching T4s gain FunctionMatch, 14 whole/region and 13 integrated. The paired default change c01→c06 keeps all 417 T3 positives in that pair. The native OW2 InitNewCampaign control passes. **Negative controls.** Five new functions have mismatching siblings, SaveErrorDialog hits anchor order, and InitNewCampaign under 10.0a has an unresolved intrinsic even at a zero score. Compile failures, unsupported, and untested stay distinct. The R6 OpenArchive match also changes `-zp1` to `-zp2`, with the exact architecture-only alternative untested. See `test_every_config_compiled_even_after_match`, `test_committed_r6_preserves_declared_debug_context` and `test_committed_buildable_population_linked`. [E7]

**Interpretation and disposition.** Keep additive search. Production already applied six added 10.0a presets and the 13 promotions, without changing the default or native OW2 fallback. The 202 improved-score records, 193 labeled dependency-clean in that snapshot, are triage inputs. They deserve live freshness checks and confer no proof or fixed current queue size. Bounds and context qualify every `S(f)`; neither architecture-wide bins nor incomplete intersections recover historical flags. Re-run only relevant stale cells or new paired questions. [E7, P-E7, P-AUTO]

### E8 — Original CU evidence

**Hypothesis and method.** Test proposed boundary signals against labels independent of those signals. A has 22 recipe-known C/ASM objects, 65 functions and 64 adjacent pairs. B1 has 447 pairs admitted by full masked library segment comparison and relocation-field coverage, with conflicting extents removed. B2 has 25 inferred setup.exe transitions under whole-object/membership and minimum-length premises, with no same-object labels. Exploratory game results use 890 pairs outside the label-quality measurements. [E8]

**Positive controls.** Shared epilogue fires twice correctly on A and four times on B1. `zero16` has 11/13 positives on A, 2/2 on B1 with 2.7% recall, and finds 7/25 B2 transitions. One literal-sharing positive and a cross-object duplicate control support a conditional hypothesis. **Negative controls.** NASM can add zeros inside objects. `none16` is 4/23 on B1. Staircase breaks and call-locality drops overproduce splits. Non-paragraph objects and leading bytes invalidate unconditional start-alignment inference. `intxa386` heavily skews B1 and is removed in a sensitivity reading. The former cstrtx32 phantom extent is rejected, and a minimum function length excludes false B2 transitions. See `test_scrambling_every_evaluated_feature_does_not_change_truth`, `test_every_admitted_b1_extent_passes_full_segment_masked_verification` and `test_zero16_recall_gap_is_quantified`. [E2, E8, C-REV]

**Interpretation and disposition.** Adopt premise-carrying constraints and analyst-facing hints. E8’s B1 label check is scoped masked segment identity, with limitations on relocated target identity and corpus transfer. B2’s eight overlaps with B1 agree after filtering. B2 estimates recall for its accepted boundary set, with no precision estimate. A new independent game-like corpus is needed for numerical boundary inference or automated consolidation. In particular, the E8 report’s suggestion that `-5r/-3r` defeats paragraph alignment needs correction against E2. Those tested `-ot` objects have four-byte function spacing and a paragraph-aligned segment. The segment’s start matters, and the first public can have leading bytes. [E0, E2, E8]

## 3. Verification architecture proposal

Use one address-obligation checker with two explicit scopes. **FunctionMatch** covers a function’s required instruction/data extents and the obligations needed for that claim under one actual compiled TU. It can report remaining context or integration dependencies. **RegionMatch** verifies a complete contribution under a proposed affine mapping `original = orig_start + (obj_offset - obj_lo)`. Include all entries, leading data, internal padding, owned tables and data dependencies in scope. A RegionMatch can carry explicit external obligations the planner must discharge. A missing identity or an unproved edge is unresolved, even when the bytes or diff score agree. Neither result alone changes `src`, `ref` or progress. [R §§5–7, E0, E2, E3, P-GOAL]

Use small immutable records with the following minimum content.

| Record | Required information |
|---|---|
| CandidateRegion | Object identity and segment index, source and original intervals, compiler-produced entries, and the binding evidence that proposes the affine base |
| AddressObligation | Source object/segment and byte interval, field kind and width, canonical target plus signed addend, evaluated object/offset, effective frame and next-IP rule where relevant, and whether the linker or loader must resolve it |
| VerifiedRegion | Candidate, proof dependencies and obligations on retained data and code, permissible materialization, and context digest |
| PlacementPlan | Complete interval cover of each original loadable object with unique providers, global edge dispositions, link order and materialization inputs |
| Integrated result | Exact input/plan/output identities, actual assembly/link results, comparison and provider receipts |

Index original loader fields and decoded direct edges once per binary/discovery fingerprint. Map object symbols and local definitions to semantic targets before comparing with original observations. A loader-adjusted absolute field requires a matching compiler or justified linker obligation, even if its raw value happens to equal the preferred address. OMF link-time rel32 and a resolved same-segment branch may satisfy the same original target without generating an LE fixup. For address fields in both code and data, compare the forward and reverse sets and all remaining bytes. Reject overlaps, unsupported locations/frames, missing fields, contradictory publics, wrap outside the declared address model, and inconsistent storage or aliases. Treat unrelocated hardware constants as ordinary bytes. An original operand may propose a whole-segment translation for a compiler-known segment/offset. Require corroboration from the full extent, consistent references and known definitions. Per-symbol remapping requires independent extent, identity and addend evidence. Equal contents alone cannot authorize it. [E0, E3–E5, P-BUILD]

Use the discovered body extent and validated instruction/data boundaries. Trim only terminal padding established as filler and unreachable, with no entry, field overlap, reference, or fallthrough into the trimmed bytes. Treat a zero-filled range as padding only with ownership evidence. Preserve actual internal bytes and ownership. If a whole object has a trimmable analysis tail that the linker would still place, either prove that tail as part of the contribution or use an admitted extraction. RegionMatch over a shorter range cannot authorize linking the longer object. Report `MISMATCH`, `UNSUPPORTED`, `ERROR` and unsatisfied dependencies separately. None can mint placement permission. [E0, E3, E4]

For new admission paths, decode a strict supported OMF subset before verification. Retain record widths, segment combine/group semantics, relocation frame and external index identity. Validate record bounds, checksum policy, single module termination, definition and field bounds, supported record semantics and thread lifetime. Existing library-signature and diagnostic consumers can keep their permissive reader with an explicit purpose. Bind proof to raw input and verify the final transformed artifact. Changes are limited to symbolic binding, verified segment representation and link placement. Preserve opcodes, encoding widths, non-address values and meaningful bytes. [E0, E4, E5, P-BUILD, Q3]

Preserve the existing Build A comparison and require explicit identity across the accepted image and effective loader obligations. The present comparator compares preferred-base bytes, entry/stack addresses, object base/size and source/target fixup tuples. It prints flags without checking them and omits source kind from those tuples. Audit and enforce loader-relevant object attributes, entry and stack object/offset, and typed fixups, including coherent page-split duplicates, alongside the existing oracle. Establish the exact attribute policy with the real original and linked image. Require a non-legacy plan and a receipt tying each claimed C-owned byte to a compiler artifact. A matching final image cannot recover proof of discarded data or certify C ownership. Make any strictness correction in the underlying proof path under the existing gate, with an explicit owner checkpoint if compatibility would require changing the gate. [R §13, P-BUILD, Q3]

Keep provenance layered. Compile identity includes the effective ordered options, compiler/headers/environment, recursive include closure and full TU. Region identity adds the target and discovery/symbol/data dependencies, object bytes, verifier version and range. Placement identity adds neighbors, edge/provider bindings, transformation manifest and assembler/linker identities. Historical CU hypotheses and search budgets stay out of machine-proof keys. Record raw hashes and conservative semantic digests separately. Exclude path/debug metadata only where understood. An empirically uninitialized CONST gap can be normalized in a research serialization, with separate ownership and byte proof required for a loadable contribution. On incomplete closure, bypass cache and recompute or refuse proof. Reuse existing fingerprints where their declared trust boundary fits. Defer a durable proof database and persistent compiled-object cache until measured need. [E1, E2, E4, E7, E8, P-AUTO]

## 4. Compilation and placement architecture proposal

An **original CU hypothesis** is an evidence-backed claim about historical object membership, order or flags, with competing alternatives. A **reconstructed TU** is the source actually compiled with its declarations, members, headers and options. It may realize part of a hypothesis or serve a different grouping. An emitted **object** is identified by that invocation and bytes. It can yield no machine proofs, one whole-object proof, or several bounded proofs. Whole-object integration is the default when exact. A separately authored standalone file is legitimate if it is the actual checked and linked source. A generated subset of C from a differently compiled canonical TU proves only that generated variant. [R §§4, 9, 18–19, E1–E4]

A verified region is a possible physical code provider. The plan chooses disjoint C contributions and complements them with original ASM, with one physical provider per byte including padding, alignment gaps and jump tables. Publics are entries within ranges, not range boundaries by definition. For a table preceding a public, derive the physical base from the original public address minus its object offset. Validate every independently known entry, table target and boundary. A shared tail can belong physically to one range and execute on paths from several entries. Keep that relationship explicit, separately from semantic function membership and discovery limits. Embedding branch closure in the planner allows both whole-TU tails and verified fixed-layout ASM crossings. [E0, E1, E3, P-BUILD, Q2]

Data semantics and placement likewise have separate lifecycles. Named objects, types, extents and alias relations belong to symbol/layout evidence. Historical TU ownership is a claim. A Build A provider can be ASM while C faithfully describes and references the storage. Build B requires legitimate linked definitions and initialization, with third-party providers where in scope rules allow, and should never need synthetic original-address anchors in canonical C. A Build A anchor names one already identified storage location and supplies no bytes itself. [R §§7–9, E3, E5, P-GOAL]

Keep declared flags distinct from bounded search presets and recorded compiler capabilities. Segment alignment, intra-object function padding and literal layout are distinct. Prefer a verified whole-TU fit, then separate canonical source where context permits. Consider extraction only when the canonical grouping has independent value and a compact proof covers its real object. No mandatory historical consolidation pass. [E1–E5, E7, P-E7]

## 5. B1/B2/B3 evaluation

**B1 — leading regions. Adopt after verifier shadow audit.** Production `place()` uses the lowest function address as the physical base, so ChooseCampaignDialog fails with its first public at `+0x10` and table at `0x157d8..0x157e8`. E0 proves this prefix’s bytes and obligations and rejects a wrong case target or missing fixup. It does not itself execute a B1 production link. Require one agreed base, full bounded TEXT ownership including every leading field, no split instruction, foreign entry or field, unique providers, and a real link with ChooseCampaignDialog under the new path. Corrupt the table in both directions in regression tests. For MainMenu, distinguish the table at `0x15578` from the entry at `0x15588` and verify the `owner_5aa90` dependency separately. Its candidacy is conditional. [E0, P-BUILD, P-M2]

**B2 — final partition edges. Adopt a bounded in-place bridge after the Group B pilot or in parallel if another M2 case needs it.** Production rejects references to a C interior, but misses some retained-to-retained crossings. Inserting Sync between Play and Wait causes `je` at `0x231d7` and `jne` at `0x231e1` to target Play’s interior `0x2316c` from a different generated ASM object. The targets are outside the C cut. Preflight passes, and NASM cannot encode an external rel8 record for this path. The historical toy bridge is confirmed on the affected retained piece by Q2. E1 instead closes the three functions in one exact object. [E1, P-BUILD, P-M2, Q2]

Index all original direct edges, relevant fallthroughs and loader references, then classify by the final source and target providers. For original ASM relative transfers with fixed in-place layout, a piece-local label plus signed distance may encode the already-established target. Check both endpoint ownership and complete fixed cover between them, original instruction identity, exact next-IP and range, and no emitted relocation for this fixed rel8 field. Verify the assembled bytes. Include forward/backward, multiple intervening pieces, inter-ASM and ASM-to-C-interior cases, and failures for gap, overlap, moved target, overflow and legacy. Keep external near relocations symbolic where supported and independently resolved. An absolute pointer into an interior requires a verified symbol/offset provider and the loader fixup. An outgoing compiled rel8 across an extracted region is a different case and remains unsupported. Require actual assembly, link and identity for admitted production candidates. [R §§6–7, E1, E3, E4, P-BUILD, Q2]

**IntroOpSyncSound disposition.** Withdraw the older inventory’s immediate standalone wiring recommendation. A local Match and empty `check_placed_plan` errors are insufficient. Pilot E1’s exact Group B with current sources and both compilers, retaining coverage in tests that still reference the old TU. If the group cannot be integrated now, require the partition bridge or obtain a legitimate T4 proof with its documented blocker. Apply the same reasoning to B2’s other cases without promising a promotion count from a geometric check. [E1, P-GOAL, P-M2, Q2]

**B3 — independent data placement. Adopt conditionally, defer deployment for M2 by default.** The legacy patcher empties matched data segments, ties anchor locations to code-link order and rejects multiple different anchors per object. E5 demonstrates that one ASM provider plus generated aliases removes that ordering dependency in supported cases. Begin with whole segments, prove both sides of all pointer obligations before emptying, preserve frames/addends and external indices, reject unknown record types, check retained-to-emptied references, and reparse/verify the final output. For whole-plan adoption, test interaction with legacy anchor users and B1/B2 and prove exact ownership of emitted labels, including non-addressable label positions. To admit THREAD, expand with full cross-record lifetime including discarded records. For per-symbol support, require a real independent storage/alias case and evidence of benefit. SaveErrorDialog’s T4 status makes B3 a Build A capability with secondary M2 priority. [E3–E5, P-BUILD, P-M2]

## 6. Behavioral verification proposal

Keep a single-function default. Use Group where the C interactions are part of the claim and Integrated where realistic downstream behavior is material. Record the exact root, original and compiled ownership spans, expected entries, observed callees, declared substitutions and effects. A real original implementation beyond the group boundary is allowed when the scenario declares it and contributes no proof of a compiled implementation for that callee. On the reference side, disallow execution of reconstructed code. On the C side, disallow execution of the original implementation within the claimed boundary. Keep whole-symbol ownership through terminal and trailing code distinct from entry reachability. Treat shared tails as explicit group ranges rather than overlapping function claims. [E6, P-T4]

Use symmetric substitutions only at named dependency entries and audit mechanism, ABI and invocation behavior. Resolve actual EXTDEF/LEXTDEF records with a verified boundary-aware symbol rule. Where no fixup exists, a vetted hook at the exact entry can serve the symmetric model. If inlining, alternate/interior entries, fallthrough or unresolved transfers make isolation unprovable, fail that mode and try a real group test. Enforce code integrity, allowed entry/transfer rules and stub identity during execution as well as before and after it. Audit original-side spans too. Reject silent fallback to running the original on the C side and undeclared runtime helpers or stubs. Retain the documented bounded trusted-runtime policy, such as the existing memcpy model when explicitly applicable. [E6, P-T4]

For callbacks, execute actual target pointers on both sides. Check ABI against the declared convention before restoring context, including preserved registers, stack arguments, cleanup, return behavior and relevant effects. Compare declared pointer slots by symbol or proved allocation-plus-offset identity with bijective aliasing across applicable observations, and require that behaviorally relevant callbacks actually run. Ordinary bytes and untyped integers compare exactly. Initialize both executions from equivalent fixtures and reset relevant writable state. Use positive proofs of observed behavior and report paths not exercised. Carry over fresh canonical C recompilation, exact per-node selection and completed-case receipts, absence of unsupported patching/stubbing, nonzero execution of claimed bodies and meaningful observations. Keep trusted in-process setup as the threat boundary. Require equivalently strong new audit before migration of existing citations. [E6, P-T4]

## 7. Compilation-unit recovery interpretation

Record observations separately from conclusions. A direct shared epilogue into another owner’s return block gives a same-object constraint *if* the code was generated by the relevant compiler, the block and entries are correctly partitioned, and the original linker did not synthesize or merge the tail across objects. E1 shows the compiler can produce it across an intervening function. Q2 shows a deliberate in-place bridge can produce the same encodings from distinct link contributions, which illustrates why the historical toolchain premise matters. Literal sharing only constrains a CU when independent evidence excludes explicit shared storage, a common external or linker pooling. The non-paragraph address argument applies to the actual segment base under a known paragraph-placement premise. A public at a nonzero offset supplies insufficient information by itself. [E1, E2, E8, Q2]

Treat `zero16` as a conditional hint, `none16` as an enumeration cue, and style, literal windows, named object progression and positive call locality as corroborating evidence with recorded counterexamples and denominator. Give no split authority to staircase inversions or lack of an adjacent call. Compare observed compatible flag sets under stated contexts. For a disjoint set, keep alternatives for missing configurations, wrong C, local pragmas, source/context sensitivity and a real boundary. For agreement, keep distinct alternatives that reproduce the same encodings. [E2, E7, E8]

An initial record can be a small analyst-maintained list of ranges and alternatives, dated premises, tool/input identities, observed evidence, contradiction witnesses and falsifiers. Keep it outside scope metadata. Add a constraint solver only when conflicting cases actually need it. A mechanically checked link or library match verifies its stated fact and can raise confidence in an object constraint. It does not name the original C file or justify automatic source edits. [R §9, E8, P-GOAL]

## 8. Production roadmap

Stages 0 and 1 can proceed in parallel. The stage numbering expresses dependencies for infrastructure admission. Each production unit needs targeted negatives, declared-compiler matches or cited T4 behavior as appropriate, dual compiler check, full existing `make verify`, and Build A IDENTICAL. Build changes also need an actual candidate link, current-corpus audit as applicable, and a clear rollback boundary. This is a proposed implementation sequence. [P-GOAL]

| Stage | Entry and work | Exit, risk and reversibility |
|---|---|---|
| 0. Refresh and harden in shadow | Use pinned reproducible inventory. Retain additive E7 presets. Port the E0 checker on a strict parsed subset, add comparator/plan diagnostics and test overrides and actual input identities. Add partition-edge findings before promotion logic trusts the precheck. | Every existing T3 accounted for under its declared compiler, failures attributed to input, verifier limitation or genuine mismatch. Validate compare policy on baseline and mutants. Retain old authoritative path until the audited cutover. |
| 1. Close the M2 area backlog | Current inventory has 40 cross-TOML and 21 same-TOML placeholder/stub cases, ten missing-DB Wave-3 primary cases and seven low-confidence named cases. Process coherent batches, starting with the clean BULLET.C work and dependency hubs. Repair the five unchecked reference divergences in parallel with bounded runs. Use existing syntax-aware renaming/mapping logic when it preserves ABI, cross-TOML identity and cited tests. | Track DONE and blocked counts without double counting, exact difftest execution for new T4s and zero tier/test regressions. Patch or roll back per atomic unit. Treat eight discovery/scope suspects as evidence packets for separate owner disposition. |
| 2. Admit in-place whole regions and B1 | Stage 0 shadow is clean enough for a production cutover. Start with the flat off32/rel32 subset and ChooseCampaignDialog, then rerun MainMenu/dependency evidence. | One valid leading-table link, corrupt prefix/field rejections, no foreign bytes attributed to C, and current corpus still green. A narrow plan path decouples rollback from source promotion. |
| 3. Close M2 shared-tail cases | Run the exact Group B pilot under stage 2’s proof path. Apply partition-aware B2 to remaining cases where the fixed-layout bridge is justified. Review six outstanding records across direct-interior and cross-retained-piece cases. | Positive actual links and plan/assembly negatives. If an individual case needs a broader rewrite, T4 remains viable with evidence. Test B2 first on unchanged ASM plus the minimum proposed C cut so failures are attributable. |
| 4. Pilot multi-function T4 on demand | Existing isolated tests remain authoritative. Choose a blocked or migrated T4 whose boundary cannot be proved by the current single-function path. Port only the necessary E6 subset. | End-to-end fresh audit and a real, useful migrated node with the original adversarial controls plus both-side isolation and reset tests. Rollback is per node. Avoid moving already-DONE functions for harness adoption alone. |
| 5. Optional placement and recovery work | B3 whole-segment pilot after strict frame/data proof and a demonstrated need. E3/E4 extraction only after the planner and supported writer exist and a canonical-TU pilot earns it. B3 is a dependency only for slices that use its data adapter. | Independent links, post-rewrite verification, no synthetic anchors in canonical source, and a rollback to the verified existing layout. Defer broad extraction, per-symbol mutable remapping, CU consolidation and residual Wave 4B volume until after M2 unless a concrete M2 dependency changes. |
| 6. Build B and T5 | Complete M2 under the current definition and obtain owner agreement on T5. Build per-area C link closure, typed physical data providers, initialized data/BSS, out-of-scope library/ASM interfaces, and audit layout-dependent idioms and callback/ABI joins. | Build B uses accepted C for every in-scope function, links by symbol and satisfies the agreed T5 scenarios. Preserve Build A. Keep Build A anchor machinery outside canonical source and Build B’s interface. |

The 98-row refresh assigns seven build cases, five current reference divergences and eight discovery/scope questions, besides the 78 name/source cases. Under the default overnight selection it finds 14 eligible, eight skipped and 76 needing human handling. Those flags describe routing. They are not separate workload counts. Ask for evidence and owner disposition for `0x110a0`, `0x11530`, STATUS split blocks `0x28090/0x28093` and the four AIL-mixer candidates. The scope list already treats six unclassified runtime functions as in scope. Libsig or documented semantic evidence must precede any runtime classification. The five unchecked references are four PLAYFLIC nodes and EndScreen. Group B can close the WaitSound item via T3 when its integrated proof and existing test obligations are satisfied. [P-M2, P-GOAL, Q1]

Extend the existing overnight/batch and Wave 4 work queues with receipts distinguishing a mismatch, unsupported construct, preflight failure, toolchain failure, interrupted work and a complete miss. Key retries on actual dependencies and verification versions. Bound time, make outputs transactional, keep workers isolated and route uncertain identity/ABI work to supervised review. Favor small independently reviewable units, an independent negative-control review for verifier changes, and short compiler-facing paths with isolated warmed prefixes. The campaign and 39-trial calibration support these as operational practices in this environment. The sample is sparse, tasks and harnesses differ, and quota measurements can be shared or unavailable. Model selection and effort remain workload decisions, never architectural authority. [C-REV, CAL, P-AUTO]

## 9. Scale and generalization

- **Warcraft-specific.** Preserve the pinned DOS image, project scope and symbol evidence, current tiers, known switch/epilogue ownership, historical module references and current T4 oracle policy. Treat addresses and Work Wave heuristics as local data. [P-GOAL, P-M2]
- **Watcom/OMF/LE-specific.** Effective CPU flags, Watcom register ABI, segment and function alignment, initialized versus uninitialized CONST gaps, FRAME/THREAD/index semantics, LEDATA field offsets, observable NASM OMF rel8 limitation, LE fixup and DOS/4GW loader model, and Wine path constraints need target-specific tests. [E1, E2, E4–E8, Q2, Q3]
- **General.** Separate source, compiler product, proof and final provider. Compare typed address obligations bidirectionally, verify transformation boundaries against an independent oracle, preserve logical identity in behavioral tests, and scope invalidation by actual dependencies. Reuse range/edge indexes, shared image and symbol snapshots, and per-TU compilation within invocations. Profile before adopting persistent cross-process caches. COFF/ELF, unwind tables, COMDAT, templates and linker folding require new premises and tests if a real project adopts this approach. A generic plugin framework, global metadata database, and automated graph classifier have no current dependency. [R §18.2, E2–E8, P-AUTO]

## 10. Proposed RFC changes

| RFC section | Action | Replacement or amendment |
|---|---|---|
| 1 | Replace | State actual M2 baseline, independent proof layers, whole-TU preference and deferred optional machinery. |
| 2 | Revise | Keep verified strengths. Add lossy OMF parsing, incomplete comparator coverage and the cross-ASM preflight counterexample. Qualify compiler alignment. |
| 3 | Replace | Use the decision set in §11, treating the E7 production rollout as delivered. |
| 4 | Revise | Keep source-of-truth policy. Add integrated-result receipt and make external obligations explicit. Keep records adjacent to their current owners. |
| 5 | Retain and revise | Use two scopes on one obligation checker. Require certified extents, inward edge checks for trimming and exact correspondence between verified and emitted extents. |
| 6 | Retain and revise | Specify independent binding and effective frame/addend semantics. Limit production to supported cases. Distinguish assembler bridge, object transform and loader obligation. |
| 7 | Replace | Plan the whole final partition. Add retained-to-retained crossings, frozen inputs, artifact admission and real link/compare outcomes. |
| 8 | Retain §8.1, revise §§8.2–8.3 | Treat B3 as a proven subset and optional deployment. Start with whole segments. Define ownership and verified relocatable providers for Build B separately. |
| 9 | Revise | Apply E8’s exceptions and E2’s actual SEGDEF result. No automatic partition on heuristics or incomplete flag intersections. |
| 10 | Revise | Separate compile, match and placement identities. Move historical hypotheses out of machine-proof keys and distinguish proof cache from scheduling hints. |
| 11 | Revise | Correct the real intra-TU EXTDEF result. Formalize exact entry substitutions, actual callbacks, per-side execution and audit parity. |
| 12 | Retain and revise | Record delivered presets and paired coverage limits. Keep capability, historical hypothesis and search strategy separate. Require compiled evidence for any idiom change. |
| 13 | Retain and strengthen | Require strict provider provenance, typed loader identities and the final oracle. Keep existing scope, tiers and gates. |
| 14 | Replace | Preserve contracts and artifacts as historical records. Summarize measured outcomes, rejected premises and the remaining probes in §13 below. |
| 15 | Replace | Treat 519 as research history. Audit every live declared T3 on the production cutover revision and resolve differences explicitly. |
| 16 | Replace | Use capability-specific exits. Require one real candidate link and relevant negative controls. A whole exact region needs neither extraction nor the group T4 harness unless it changes a cited T4. |
| 17 | Replace | Record which timing questions are decided, which deployments are conditional and what would reopen each deferral. |
| 18 | Replace | Follow the roadmap in §8. State migration benefit per TU and require a fresh proof before ownership changes. |
| 19 | Retain and revise | Keep excluded directions. Add comparator completeness, parser projection, cross-provider ASM edges and nondeterministic data padding. |
| 20 | Replace | Include the source index and production pins, with experimental results and implementation changes traceable separately. |

## 11. Structured decision proposals

```text
Decision: DEC-A01
Title: Keep the M2 completion contract
Proposition: Sequence work by remaining DONE obligations under the existing scope, tiers and gates. Count a T4-to-T3 conversion separately. Leave T5 authorization to the owner.
Revision: 1
Position: PROPOSE
Reason: Most of the pinned backlog requires named, proven source or governed resolution.
Evidence: P-GOAL, P-E7, P-M2, Q1
Assumptions: The owner has supplied no change to the finish line.
Dependencies: none

Decision: DEC-A02
Title: Verify function and region obligations
Proposition: Implement two scopes of one bidirectional verifier, using strict raw-record admission for production proofs. Bind proof to actual supported compiler output and audit every declared T3 on the cutover revision.
Revision: 1
Position: PROPOSE
Reason: Mutation controls demonstrate the gaps, and the research cohort predates the current tree.
Evidence: E0, E2, P-BUILD, Q3
Assumptions: Unsupported valid inputs can be surfaced and resolved before cutover.
Dependencies: DEC-A01

Decision: DEC-A03
Title: Plan and verify actual integration
Proposition: Admit code through a partition plan covering every original byte with one provider. Require actual assembly, link, existing comparison and explicit loader-relevant identity and provider evidence for Build A acceptance.
Revision: 1
Position: PROPOSE
Reason: A local or plan-level match can fail at materialization, and equal loaded bytes can mask invalid provider or loader attributes.
Evidence: E1, P-BUILD, P-M2, Q2, Q3
Assumptions: The required loader attribute policy is validated on the pinned real link before enforcement.
Dependencies: DEC-A02

Decision: DEC-A04
Title: Admit verified leading tables
Proposition: Derive a whole contribution base from a verified public binding and object offset. Admit leading bytes only with full region bounds, ownership and checked relocation obligations.
Revision: 1
Position: PROPOSE
Reason: The current first-public rule cannot place ChooseCampaignDialog.
Evidence: E0 P1/N1/B_leading_reverse, P-BUILD, P-M2
Assumptions: The first pilot is an independently verified table and region.
Dependencies: DEC-A02, DEC-A03

Decision: DEC-A05
Title: Close shared tails and partition edges
Proposition: Prefer a verified whole-TU shared-tail group. Allow an original ASM piece-local relative expression only where source, target and intervening fixed cover are proved and emitted bytes and final link agree. Reject unsupported outgoing compiled slice rel8.
Revision: 1
Position: PROPOSE
Reason: Group B closes the tail in pure C, while real retained ASM crossings also need coverage.
Evidence: E1, E3, E4, P-M2, Q2
Assumptions: The bridge applies only to fixed Build A layout.
Dependencies: DEC-A02, DEC-A03

Decision: DEC-A06
Title: Separate storage identity from provider
Proposition: Keep canonical storage and alias evidence independent of physical suppliers. Admit B3 initially for fully verified whole segments only, once a pilot justifies deployment and the strict transform and link tests pass.
Revision: 1
Position: PROPOSE
Reason: E5 validates a bounded mechanism and its flagship current target is already DONE.
Evidence: E3, E5, P-GOAL, P-M2
Assumptions: Build A retains a proven original-address provider for each anchored object.
Dependencies: DEC-A02, DEC-A03

Decision: DEC-A07
Title: Bound any selective extraction
Proposition: Defer general extraction. Admit a narrow pilot only for a proven canonical-TU benefit, a region proof bound to the object, independently identified targets, and a verified post-transform artifact and link.
Revision: 1
Position: PROPOSE
Reason: Feasibility for two real slices does not justify default adoption.
Evidence: E3, E4, C-REV
Assumptions: A whole-TU or canonical standalone solution is evaluated for the pilot.
Dependencies: DEC-A02, DEC-A03, DEC-A06 only if using B3

Decision: DEC-A08
Title: Authorize behavioral boundaries explicitly
Proposition: Require per-side execution boundaries, symmetric declared substitutions, real callback/ABI checks, typed pointer identity and production audit parity before using multi-function T4 for a cited proof.
Revision: 1
Position: PROPOSE
Reason: Whole-object and raw-pointer comparisons produce the wrong outcomes in the documented fixtures.
Evidence: E6, P-T4
Assumptions: Trusted in-process fixture code and independently corroborated ABI/identity.
Dependencies: DEC-A01

Decision: DEC-A09
Title: Keep compiler search evidence scoped
Proposition: Keep the merged additive presets and declared compiler policy. Record S(f) with its full measured context and coverage. Treat heuristic scores and freshness snapshots as scheduling inputs only.
Revision: 1
Position: PROPOSE
Reason: Exactness and historical flags are different claims, and some architecture pairs were untested.
Evidence: E2, E7, P-E7, P-AUTO
Assumptions: New presets remain bounded and evaluated before production changes.
Dependencies: DEC-A01

Decision: DEC-A10
Title: Record historical alternatives and premises
Proposition: Store original CU evidence separately from scope and build inputs. Apply hard constraints only with their premises independently established. Do not drive automatic source consolidation from the measured signals.
Revision: 1
Position: PROPOSE
Reason: Sparse true positives, biased corpora and false boundary signals do not identify a unique original partition.
Evidence: E1, E2, E7, E8
Assumptions: Original source/object maps for the game areas are absent from EV-1.
Dependencies: DEC-A09
```

## 12. Objections

- **OBJ-A01 — Correctness/verification.** Challenge the iff claim in production `check_placed_plan` and the older M2 roadmap’s unconditional Sync wiring. Actual addresses `0x231d7/0x231e1 → 0x2316c` cross retained providers when Sync is cut. Under the current NASM OMF path, both branches fail even with zero C-interior errors. The consequence is a false promotion candidate. Disposition requires a partition-aware planner and actual link evidence or an exact joint object. [P-BUILD, P-M2, Q2]
- **OBJ-A02 — Correctness/verification.** Challenge using `wc1.compare` success alone as the new placement oracle (RFC §§7.2, 13, 16). Clearing `OBJ_EXEC` produces an `IDENTICAL` success receipt. A source kind is also omitted from the current relocation tuple. The assumption for the proposed correction is that the attributes enforced are loader relevant and measured against the real baseline. Keep the existing compare and add validated typed/attribute checks and provider provenance. [R, P-BUILD, Q3]
- **OBJ-A03 — Correctness/verification.** Challenge adopting E0 directly as a complete authoritative object validator (campaign D1). Its decoded input loses FRAME distinctions and does not attest raw record checksums. Assuming objects are trusted compiler output narrows the risk, but a production transformation must validate what the linker will consume. The concrete consequence is an accepted proof over an ambiguous or malformed representation. Add strict input admission and a live audit. [E0, P-BUILD, Q3]
- **OBJ-A04 — Unsupported factual claim.** Challenge the claim in campaign D4 that E5 unblocks arbitrary multi-function consolidation. Native SaveErrorDialog still has the wrong literal stride, and the experiment’s full real three-segment object supplies one function. Under off32 with proved identities, B3 removes anchor-order constraints. It cannot repair wrong code, incorrect aliases or unsupported OMF. Do not schedule adoption based on a count of supposed broad promotions. [E5, P-M2]
- **OBJ-A05 — Blocking architectural.** Challenge the RFC §18 Phase D universal dependency on B3, extraction and E6 for consolidation pilots. An exact E1 whole object already links with ASM remainder. If the pilot changes no still-cited T4 semantics and the ordinary data plan is adequate, those extensions add risk without a dependency. Make admission per capability. [R §18, E1, E4–E6]
- **OBJ-A06 — Unsupported factual claim.** Challenge treating `-3r/-5r` as defeating paragraph alignment in the E8 interpretation. The E2 `-ot` controls retain PARA SEGDEF. Also a first public may follow a prefix, as in ChooseCampaignDialog. An align-based boundary constraint requires the actual candidate segment base and segment alignment. Function residue alone can yield a false historical split or merge. [E0, E2, E8]
- **OBJ-A07 — Correctness/verification.** Challenge production extractor admission on the `VerifiedRegion` type check alone. E4’s `_require_verified` accepts an instance before consulting its context. Later checks narrow the risk but do not substitute for proof binding and a final post-B3 check. Given independently generated candidates or reused cache entries, stale or incomplete provenance can slip across the API. Use a bound receipt or replay the verifier. [E4, C-REV]
- **OBJ-A08 — Implementation risk.** Challenge treating E6 Integrated as a direct production T4 audit replacement. The experiment uses a different policy and runner, and real downstream code can be original. Shared process state, an execution boundary mistake or a stale compile could yield undeserved credit. Require parity and explicit per-side admissible execution, including fresh provenance and scenario effects. [E6, P-T4]

## 13. Open questions and required experiments

| Question | Cheapest decisive probe and falsification criterion | Decision affected |
|---|---|---|
| Does the strict verifier preserve live T3 and adequately decode their OMF? | Single fresh declared-compiler sweep of the current cohort, with checksum, contradictory FRAME/target, boundary and truncated-field mutations. Any accepted invalid object or untriaged existing result blocks cutover. | A02 |
| Which loader attributes and typed fixups agree between the true production link and the original? | Check exact tuples and object/entry/stack metadata on one known Build A, then mutate direction, type or flag with a narrow fixture. Acceptance of a loader-changing mutant, or a real attribute mismatch, blocks the stronger claim until explained. | A03 |
| Does B1 survive the real mixed plan? | Build ChooseCampaignDialog in place on the current baseline and run leading pointer/ordinary-byte negatives. Any wrong case target accepted, neighboring byte attributed to C or failed exact link blocks B1. Then test MainMenu only with its dependency closure. | A04 |
| Does the B2 bridge cover residual geometry beyond Q2? | Use unchanged original pieces with one real cut, exercise cross-ASM and ASM-to-C in both directions, and test changed cut length, out-of-range and legacy. A changed target/byte, missing provider, unsupported source encoding or nonidentical final link excludes that case. | A05 |
| Can E1 Group B replace the three handlers on current production? | Recompile the E1 source order under current declarations using its 10.0a options and OW2 compile-check. Relink with every existing contributor and run the applicable PLAYFLIC tests. Any retained-body, graph or behavioral regression blocks the joint promotion. | A05, A08 |
| Is a B3 or extraction pilot cheaper than existing paths? | Compare the cost of one current blocked candidate across whole-object, standalone and optional adaptation. For B3 use SaveErrorDialog plus a retained-to-emptied pointer fixture; for extraction use a retained multi-entry slice before generalizing. Failure of full data identity, final-artifact proof, link oracle or meaningful backlog benefit keeps deployment deferred. | A06, A07 |
| Can a real multi-function T4 witness replace an existing citation without weakening it? | Port one needed case with real callbacks. Add original-to-reconstructed escape, stale digest, asymmetric reset, callback ABI and alias mutations. Any accepted induced divergence or omitted cited observation blocks migration. | A08 |
| Are ambiguous flag and historical boundary hypotheses distinguishable? | For a concrete candidate, compile the missing paired joint context, such as OpenArchive’s `-5r -d1+ -zp1` if it becomes relevant. For any proposed automatic boundary rule, use held-out object-known game-like fixtures with leading tables, linked duplicates and similar-style neighbors. An accepted counterexample invalidates a hard rule. Multiple exact groupings keep the historical inference underdetermined. | A09, A10 |
| Which residual discovery/classification cases and Build B behaviors may change the finish-line inputs? | Prepare per-address decoded/relocation and libsig evidence for owner disposition, then propose and trial concrete T5 replays with state oracles. Contradictory control-flow evidence blocks reclassification. The T5 set remains a proposal until approved. | A01 |

## 14. Probe and reproduction log

All shell work ran through `nix develop -c` from the Architect A worktree. `P` below is `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r00-probes`. All writes besides the position file went there. NASM was 3.02. The installed linker identified itself as Open Watcom Linker 2.0 beta. The original SHA-256 was `1e966220bf09ab007c49c5ea5ebc42eb494f5cf2f74f894d3969b6115df8d8a9`. The probes invoked no Watcom compiler, Wine worker, full Build A or full repository test suite. I used the manifest and pinned campaign results for full verification evidence. The targeted checks were sufficient for the specific questions. [Q1–Q4]

**Q1 — Revision, progress and inventory.** Read `git rev-parse HEAD HEAD^{tree}` and `git rev-parse 6f319ac:docs/architecture/rfc-build-codegen-infrastructure.md HEAD:docs/architecture/rfc-build-codegen-infrastructure.md`. HEAD and tree match EV-1, and both RFC blobs are `e81b117a1ece4f90e8b5cf17c0085b9cfb441b19`. `git merge-base --is-ancestor <tip> a21772b` returned 0 for `3123a47` and `dae45bd`, 1 for `28839d3`. Export and reproduce with:

```sh
nix develop -c bash -c '
set -eu -o pipefail
P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r00-probes
mkdir -p "$P/main"
git archive a21772b analysis asm tools/wc1 | tar -x -C "$P/main"
git archive a21772b src tests | tar -x -C "$P/main"
git ls-tree -r --name-only a21772b > "$P/pinned-main-tracked.txt"
test -L "$P/main/original" || ln -s "$PWD/original" "$P/main/original"
export WC1_ROOT="$P/main" PYTHONDONTWRITEBYTECODE=1 WC1_ANALYSIS_CACHE=0
export PYTHONPATH="$WC1_ROOT/tools"
cd "$WC1_ROOT"
python3 -m wc1.progress --todo 20 | tee "$P/production-progress.txt"
python3 -c "
from pathlib import Path
from wc1 import m2_inventory
base = Path.cwd().parent
tracked = set((base / \"pinned-main-tracked.txt\").read_text().splitlines())
m2_inventory._git_head = lambda: \"a21772b\"
m2_inventory.batch_driver._git_tracked_files = lambda cwd=None: tracked
raise SystemExit(m2_inventory.main([\"--summary\", \"--out-dir\", str(base / \"inventory\")]))
" | tee "$P/inventory-probe.txt"
'
```

Both analytical commands exited 0. Output was 1,710 discovered, 1,010 in scope, 912 DONE, 539 T3 (537 historical compiler, two OW2), 373 T4, five unchecked, 93 without C and 926 named. Inventory has 98 rows and 23 dependency groups. Only Git HEAD/tracked-file metadata was supplied from the pin because the archive has no Git index. Inventory labels are diagnostic and do not certify scope or candidate buildability. [P-M2, Q1]

**Q2 — IntroOpSyncSound partition.** Run the preserved `$P/probe.py` against the archive and original:

```sh
nix develop -c bash -c '
set -eu -o pipefail
P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r00-probes
export PYTHONDONTWRITEBYTECODE=1 WC1_ROOT="$P/main"
export PYTHONPATH="$WC1_ROOT/tools" WAR_INPUT="$PWD/original/install/war.exe"
cd "$P"
python3 probe.py 2>&1 | tee intro-sync.txt
'
```

The script uses `analysis.run(..., cache=False)`, `emit.replaced_interior_refs`, `build.check_placed_plan`, and `Emitter.emit_pieces` on a logical Sync cut `[0x23170,0x231cc)`. Both validation lists were empty. The WaitSound short edges were `7493` (−109) and `7589` (−119), both to `0x2316c`. The stock piece’s NASM command (`-O0 -f obj -I main/asm/ -w-number-overflow -w+error=label-orphan`) exited 1 with two “OBJ format can only handle 16- or 32-byte relocations” errors. On a private copy, a start label plus the known offset made the same command exit 0. The emitted fields retained `7493` and `7589`, with zero fixups at either field. The simulated cut includes two following original filler bytes. This probes exact retained-piece emission with a fixed boundary and does not link or prove an inserted C contribution. Initial setup attempts failed at the incomplete archive’s symbol validation and at a shell-quoting error in the probe’s print statement. Adding the pinned `src` and `tests` exports and correcting the print fixed those attempts. Artifacts are `probe.py`, `intro-sync.txt`, and the scratch `pieces/`. [P-BUILD, Q2]

**Q3 — Raw OMF parsing and final comparator.** Run:

```sh
nix develop -c bash -c '
set -eu -o pipefail
export P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r00-probes
export PYTHONDONTWRITEBYTECODE=1 PROBES="$P"
export WAR_INPUT="$PWD/original/install/war.exe"
PYTHONPATH="$PWD:$PWD/tools" python3 "$P/format_probe.py" | tee "$P/format-probe.txt"
'
```

The script uses `nasm -O0 -f obj` on a synthetic one-byte return object and two same-source OMF near-call fixtures. It changes one nonzero record checksum, which legacy parsing and E0 RegionMatch accept while E4 record preflight rejects. Explicit DGROUP and FLAT raw FIXUPP bodies `a401160201` and `a401160101` yield equal legacy parsed modules. An initial default-vs-FLAT control used a fixture without DGROUP and correctly produced the same raw record; the revised fixture tests distinct explicit frames. The script then compares the read-only original with a disposable copy changing only object 1 flags from `0x2045` to `0x2041` via `^ OBJ_EXEC`. The comparator returned 0, reported two equal loaded images and all 8,770 fixup tuples equal, and printed `IDENTICAL`. The probe proves projection/coverage gaps, with no claim that the two toy frames produce different linked bytes or that the flag mutant was executed. The mutant was auto-removed by the private temporary directory. The production and research pins have identical relevant format and compare files. [P-BUILD, Q3]

**Q4 — Targeted tests.**

```sh
nix develop -c bash -c '
set -eu -o pipefail
export PYTHONDONTWRITEBYTECODE=1
P=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/r00-probes
python3 -m pytest -q -p no:cacheprovider \
  experiments/build_codegen/e0/test_e0.py::test_full_audit_inventory_and_evidence \
  experiments/build_codegen/e3/test_e3.py \
  -k "not dialog_shared and not farm_uses and not score_swapped" | tee "$P/proof-tests.txt"
'
```

Result was 22 passed, three compiler-backed cases deselected, 5.56 s. This independently exercises the saved E0 census assertions and E3’s selected synthetic proof cases. Other experiment execution counts and full Build A comparisons are from the pinned artifacts reviewed above. [E0, E3, Q4]

## 15. Source index

`@E` means `@e6150b856106ae113bb023300b956fff318da7ef`. `@P` means `@a21772b8140b4b07012cde8da7da18ad3f6d56b6`. Paths in this index are relative to the repository. The experimental tests named in §2 are in the corresponding `test_eN.py`, with E5’s extra THREAD controls in `test_omf_b3.py`.

| ID | Pinned sources |
|---|---|
| R | `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8`, §§1–20. |
| P-GOAL | `AGENTS.md`, `README.md`, `docs/{GOAL,METHODOLOGY,ANALYST_GUIDE,HISTORY}.md@E`; `AGENTS.md`, `Makefile`, `docs/{GOAL,METHODOLOGY,ANALYST_GUIDE,HISTORY,STATUS}.md`, `tools/wc1/progress.py@P`. EV-1 records Build A IDENTICAL and full verification on P with 2,283 passed, 11 skipped and five xfailed. Older STATUS figures are historical. |
| E0 | `docs/research/build-codegen/{E0-matcher-soundness.md,contracts/E0-contract.md,results/e0/{controls.json,t3_reaudit.json,t3_reaudit.csv}}@E`; `experiments/build_codegen/e0/{controls,matcher_proto,reaudit_t3,run_e0,test_e0}.py@E`. Tip `dfd2a4c3`. |
| E1 | `docs/research/build-codegen/{E1-shared-epilogues.md,contracts/E1-contract.md,results/e1/{results.json,disasm_evidence.txt}}@E`; `experiments/build_codegen/e1/{run_e1.py,test_e1.py,fixtures/}@E`. Tip `720b3358`. |
| E2 | `docs/research/build-codegen/{E2-compilation-context.md,contracts/E2-contract.md,results/e2/{results.json,consolidation_rows.csv}}@E`; `experiments/build_codegen/e2/{harness,synthetic,run_e2,test_e2}.py@E`. Tip `2ef81e04`. |
| E3 | `docs/research/build-codegen/{E3-partial-matching.md,contracts/E3-contract.md,results/e3/results.json}@E`; `experiments/build_codegen/e3/{partial_matcher.py,run_e3.py,test_e3.py,fixtures/}@E`. Tip `eaaf87af`. |
| E4 | `docs/research/build-codegen/{E4-omf-extraction.md,contracts/E4-contract.md,results/e4/results.json}@E`; `experiments/build_codegen/e4/{omf_extract.py,run_e4.py,test_e4.py,fixtures/}@E`. Tip `1a32b171`. |
| E5 | `docs/research/build-codegen/{E5-data-anchors.md,contracts/E5-contract.md,results/e5/results.json}@E`; `experiments/build_codegen/e5/{omf_b3.py,build_e5.py,run_e5.py,test_e5.py,test_omf_b3.py,fixtures/}@E`. Tip `54d610ac`. |
| E6 | `docs/research/build-codegen/{E6-multifunction-t4.md,contracts/E6-contract.md,results/e6/results.json}@E`; `experiments/build_codegen/e6/{mf_cemu.py,scenarios.py,run_e6.py,test_e6.py,fixtures/}@E`. Tip `b6e25542`. |
| E7 | `docs/research/build-codegen/{E7-compiler-calibration.md,contracts/E7-contract.md,results/e7/{calibration_matrix.json,capability_db.json,cu_hypotheses.json,proposed_presets.json,t4_new_matches.csv}}@E`; `experiments/build_codegen/e7/{calibrate,capability_probe,common,analyze,link_check,test_e7}.py@E`. Tip `4194a2f1`. |
| E8 | `docs/research/build-codegen/{E8-cu-boundaries.md,contracts/E8-contract.md,results/e8/{metrics.json,synthetic_manifest.json,signal_metrics.csv,game_exploratory.json}}@E`; `experiments/build_codegen/e8/{real_corpus,synthetic_corpus,evaluate_signals,run_e8,test_e8}.py@E`. Tip `06235f6d`. |
| C-REV | `docs/research/build-codegen/{README.md,summary.md,decisions.md,ledger.json}@E`; `docs/telemetry/campaigns/2026-11-25-build-codegen/{report.md,campaign.json,events.jsonl,sessions.jsonl,experiments.csv,prompts/,summaries/}@E`, especially `rev-e0-01/-02`, `rev-e4-01`, `rev-e5-02`, `rev-e6-01/-02` and `rev-e8-02/-03`. Runner evidence under `experiments/build_codegen/_infra/@E`. |
| P-BUILD | `tools/wc1/{match,build,emit,omf,omfpatch,le,compare}.py@P`; `docs/subsystems/{build,codegen,compiler,modules}.md@P`; `tests/{test_pipeline,test_match_all,test_match_relocations,test_match_diff}.py@P`; `analysis/modules.toml@P`; `analysis/symbols/{gamedlg,mod_104b0,mod_13f60,playflic}.toml@P`. |
| P-T4 | `tools/wc1/{cemu,emu,t4spec}.py@P`; `tests/{test_cemu,test_t4spec,test_playflic_t4,test_mod_2efd0_t4}.py@P`; `docs/ANALYST_GUIDE.md@P`. |
| P-AUTO | `tools/wc1/{permuter,t3_audit,wave4,wave4a,wave4_fp,codegen_survey,modules_scan,oldcc,overnight,batch_driver}.py@P`; `tests/{test_t3_audit,test_wave4_fingerprints,test_wave4a_end_to_end,test_permuter,test_oldcc,test_overnight}.py@P`. |
| P-E7 | `docs/telemetry/campaigns/2026-11-27-e7-production/{report.md,sessions.json,t4_improved_audit.json}@P`; production commits `196153c`, `2b10939`, `59efdd2`, `5667e2f`, telemetry tip `3123a47`. |
| P-M2 | `docs/research/m2-completion/{blocker-analysis.md,roadmap.md,inventory.json,dependency-groups.json}@P` and research pin `ca82750f`; `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/{report.md,candidate_ledger.json,sessions.json}@P`; `tools/wc1/m2_inventory.py@P` and `e1a4178` for Sync reclassification. |
| CAL | `docs/research/model-calibration-engineering/{methodology.md,report.md,recommendations.md,results/{model_matrix.json,quota_snapshots.jsonl,resource_usage.csv}}@cea804e1`. |
| Q1–Q4 | Round 0 probes in §14 and private runtime artifacts under `r00-probes/`. These are independent bounded observations of the pinned inputs, with the stated limitations. |