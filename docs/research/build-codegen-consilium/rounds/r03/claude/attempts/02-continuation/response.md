# Consilium R3 — Targeted Deliberation, Architect B (Claude, `claude-opus-5-5`)

- **Round:** 3 (continuation of the interrupted attempt 01; drafts from attempt 01 were regenerated and re-verified against the index).
- **Inputs, re-verified by SHA-256:**
  - `00-LIVE-ISSUES.json` `3bc01dbe…`
  - `01-architect-gpt-response.md` `0b876293…`
  - `02-architect-gemini-response.md` `51f761d7…`
- **Evidence baseline:** EV-3 (`main@17733f9`).

## 0. Summary of this round

1. **Ledger consolidation (my main change).** A and C published revision 2 of most of their decisions. Those revisions absorb every condition I attached in R2. I checked each hash against its exact published proposition text (R3-P2). Where an accepted revision of another Architect carries the full content of one of my decisions, I **withdraw my duplicate**, so that the ledger converges on one proposition per contract:
   - DEC-B01, DEC-B02, DEC-B03, DEC-B04, DEC-B09, DEC-B12, DEC-B13, DEC-B18, DEC-B20, DEC-B21, DEC-B22.
   - The mapping is in §2. No content is lost; the replacing propositions are named in each issue block.
2. **I keep three B decisions with substance of their own:**
   - **DEC-B06 r1** (proof-gated joint TUs, Group B);
   - **DEC-B19 r2** (legacy exclusion plus fallthrough adjacency; C05 r2 cites it by name);
   - the unanimous B05/B08/B10/B11/B14/B15.
   - DEC-B07, DEC-B16 and DEC-B17 remain REJECT. All three Architects reject them.
3. **One new probe narrows the last factual dispute (OBJ-A20 / DEC-C16 / DEC-C07).** On a *pristine* `git archive` of `17733f9`, the five xfailed T4 tests were run three ways:
   - stock `run_pair`: **5/5 FAIL**;
   - memory **and** CPU context (GPRs, EFLAGS, segment registers) snapshotted before the original call and restored before the C call: **IntroOpWaitSound, IntroRunScript, IntroPlay PASS; IntroOpStartCredits and EndScreen still FAIL** at the same first difference.
   - Both still-failing tests use only constant-return `T4Stub`s, with no `fn=` closure state. So A's CPU and stub-state channels are excluded for these two. Allocator state is the only A11 channel I did not separately reset.
   - I therefore ACCEPT C16 r2 and C07 r2. Their 3/2 wording is supported, and they keep status and xfail changes owner-gated.
4. **Residual difference: DEC-C15 r1.** I stay CONDITIONAL: raw fixup occurrences must be validated before deduplication, with serialization deltas kept diagnostic. This is A03 r2's rule. A's R2 P2 mutant passes a type-extended unique projection. C can resolve this with a one-line revision.
5. **No unanimous decision is reopened.** No new evidence bears on any of them.

---

## 1. Live decisions (38 index entries)

The "Competing positions" lines below are the positions recorded in the mechanical index, which holds each Architect's R2 position on the *indexed* revision. A's and C's revision-2 propositions are not separate index entries. For those I give my position on both the indexed revision 1 (superseded) and the revision 2 hash.

```text
Issue: DEC-A02
Exact proposition under dispute: Implement two scopes of one bidirectional verifier, using strict raw-record admission for production proofs. Bind proof to actual supported compiler output and audit every declared T3 on the cutover revision.
Competing positions: A REJECT (r1); B ACCEPT (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `87a63b4cd465…`
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Supporting evidence: A's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Recording r1 as superseded removes a mechanical dispute; all substance moves to r2
Proposed resolution: Close r1 as superseded; adopt DEC-A02 r2 (`87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger) — r2 substantive and accepted
```

```text
Issue: DEC-A03
Exact proposition under dispute: Admit code through a partition plan covering every original byte with one provider. Require actual assembly, link, existing comparison and explicit loader-relevant identity and provider evidence for Build A acceptance.
Competing positions: A REJECT (r1); B ACCEPT (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `58e7c0dd039e…`
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Supporting evidence: A's R2 response §3 (rev 2 text; hash verified R3-P2); A R2 P1 (typed parity measured), R2 P2 (three comparator false passes incl. duplicate-occurrence mutant)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Recording r1 as superseded removes a mechanical dispute; all substance moves to r2
Proposed resolution: Close r1 as superseded; adopt DEC-A03 r2 (`58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda`); it also supersedes my DEC-B20 (withdrawn)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger) — r2 substantive and accepted
```

```text
Issue: DEC-A05
Exact proposition under dispute: Prefer a verified whole-TU shared-tail group. Allow an original ASM piece-local relative expression only where source, target and intervening fixed cover are proved and emitted bytes and final link agree. Reject unsupported outgoing compiled slice rel8.
Competing positions: A REJECT (r1); B ACCEPT (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `414da43a537e…`
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Supporting evidence: A's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Recording r1 as superseded removes a mechanical dispute; all substance moves to r2
Proposed resolution: Close r1 as superseded; adopt DEC-A05 r2 (`414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5`); together with C05 r2 it supersedes my DEC-B04 (withdrawn)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger) — r2 substantive and accepted
```

```text
Issue: DEC-A07
Exact proposition under dispute: Defer general extraction. Admit a narrow pilot only for a proven canonical-TU benefit, a region proof bound to the object, independently identified targets, and a verified post-transform artifact and link.
Competing positions: A REJECT (r1); B CONDITIONAL (r1); C CONDITIONAL (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `5d8aa99eec7e…`
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Supporting evidence: A's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Recording r1 as superseded removes a mechanical dispute; all substance moves to r2
Proposed resolution: Close r1 as superseded; adopt DEC-A07 r2 (`5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d`); with C08 r2 it supersedes my DEC-B09 (withdrawn)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger) — r2 substantive and accepted
```

```text
Issue: DEC-A08
Exact proposition under dispute: Require per-side execution boundaries, symmetric declared substitutions, real callback/ABI checks, typed pointer identity and production audit parity before using multi-function T4 for a cited proof.
Competing positions: A REJECT (r1); B ACCEPT (r1); C CONDITIONAL (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `2be94ebaca45…`
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Supporting evidence: A's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Recording r1 as superseded removes a mechanical dispute; all substance moves to r2
Proposed resolution: Close r1 as superseded; adopt DEC-A08 r2 (`2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31`); with C11 r2 it supersedes my DEC-B12 (withdrawn)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger) — r2 substantive and accepted
```

```text
Issue: DEC-A12
Exact proposition under dispute: Stage or reject effective Watcom 10.0a paths before launch. Prove that staging preserves source identity, include resolution, flags and output attribution, and isolate temporary outputs per compile. Report path failures as toolchain errors. Use measured limits on effective compiler-facing paths.
Competing positions: A ACCEPT (r1); B none; C none — all on the indexed revision 1
Your position: ACCEPT r1
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Supporting evidence: EV-3 report:64@17733f9 (rc=5 at ~130-char paths); oldcc.py unchanged a21772b..17733f9
Concrete counterexample or failure mode: a nominally short staging dir with long -i= arguments still crashes (A OBJ-A17)
Necessary assumptions: staging can preserve include resolution (to be proven)
Practical consequences: Removes intermittent toolchain failures from verify/overnight
Proposed resolution: Adopt DEC-A12 r1 (`40569d572c9a…`); it supersedes my DEC-B22 (withdrawn); compatible with C04 r2
Conditions under which you would change position: Evidence that staging changes compiled bytes and cannot be made neutral → reject-only variant
Classification: implementation risk
```

```text
Issue: DEC-A13
Exact proposition under dispute: Permit the exact Group B whole-TU promotion independently of general B1, B2 and matcher rollout only with a commit-bound strict raw-object RegionMatch equivalent to the intended production rules, ordinary file and dual-compiler checks, actual in-place Build A with typed loader comparison, and preserved cited T4 checks or explicit owner approval for changes.
Competing positions: A ACCEPT (r1); B none; C none — all on the indexed revision 1
Your position: ACCEPT r1
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Supporting evidence: R0 P3 (Group B MATCH x3, 542/535 IDENTICAL, compile-check 1x2), E1 E0 RegionMatch of the exact object
Concrete counterexample or failure mode: none
Necessary assumptions: an independently checkable strict proof is available for the exact object (E0 prototype already MATCHes it)
Practical consequences: +3 DONE without waiting for generic B2 or the production matcher cutover; resolves the former OBJ-C13 dispute
Proposed resolution: Adopt DEC-A13 r1 (`c2358d2447d3…`)
Conditions under which you would change position: A failing existing PLAYFLIC test (non-xfail) under the joint TU
Classification: implementation risk
```

```text
Issue: DEC-B01
Exact proposition under dispute: Until gate 1 passes, a production infrastructure change is admitted only if it removes an observed blocker of named not-done in-scope functions or closes a demonstrated verification or toolchain soundness defect; routine reconstruction work proceeds in parallel and is not serialized behind infrastructure stages. On main@17733f9 the admitted items are: the E0 matcher with strict raw admission (DEC-B02), the single placement planner with integration receipts (DEC-B03), the cross-object transfer rule (DEC-B04, DEC-B19), the B1 leading-byte base (DEC-B05), proof-gated joint TUs (DEC-B06), complete T4 paired-state symmetry (DEC-B18), measured comparator strengthening (DEC-B20) and the compiler-facing path guard (DEC-B22); a deterministic rename/migration helper is admitted when a reconstruction batch demonstrably needs it. Fix B3, selective extraction, E6 Group/Integrated machinery beyond a named witness, persistent provenance stores and CU databases are scheduled on a post-M2/M3 track unless a named not-done function requires them.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A01 (unanimous) + DEC-C07 r2
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Supporting evidence: see §2 (withdrawals); the admission principle and parallel tracks are carried by A01 and C07 r2; my r2 referenced decisions I am now also withdrawing
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B01 r2 as withdrawn; adopt DEC-A01 (unanimous) + DEC-C07 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B02
Exact proposition under dispute: tools/wc1/match.py adopts E0 semantics (bidirectional normalized obligations, leading bytes, local-data pointer targets, mutually exclusive verdicts with UNSUPPORTED precedence, untruncated machine findings), reimplemented in tools/ with E0's 55 controls as production tests. Production admission additionally requires strict raw-OMF input checks (record bounds, checksum when nonzero, single MODEND, record-type allow-list, cross-record THREAD state, explicit FRAME preserved) with unsupported input reported as UNSUPPORTED, and the proof is bound to the raw bytes of the exact object later consumed by the build. Local data, including CONST pad bytes, is matched exactly at cutover. A verdict may change from non-MATCH to MATCH only through a new, independently tested proof rule with positive and negative controls, never by relaxing an existing check; function-scoped diagnostic closure may record explicit external edge obligations but never grants placement. The cutover is admitted only if the full current T3 population returns MATCH under make verify.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A02 r2 + DEC-C02 r2
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Supporting evidence: see §2 (withdrawals); both revisions contain strict raw admission, scoped local closure with explicit external obligations, trim-target checks, live cutover audit and no V4 dependency
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B02 r2 as withdrawn; adopt DEC-A02 r2 + DEC-C02 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B03
Exact proposition under dispute: wc1.build exposes one planner, plan(p, regions), that computes cuts, entries, cross-object transfer encodings, adjacency obligations and data anchors, plus errors; check_t3_buildable, batch_driver, wave4a, m2_inventory and the emitter all consume that planner. A clean plan is a preflight result only: a function is promoted (src wiring for T3) only with an integration receipt recording the actual assembly, link and comparison (including the checks added by DEC-B20) of the exact plan. Regression tests are mode-qualified: standalone IntroOpSyncSound is rejected when the cross-object transfer rule is disabled or any spanned object is legacy-placed, accepted with recorded Build A debt when the rule is enabled in place, and Group B is accepted with no debt.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-C01 r2 + DEC-A03 r2 + DEC-C05 r2
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Supporting evidence: see §2 (withdrawals); C01 r2 names the shared planner consumers and the IntegratedResult receipt; A03 r2 the materialization contract; C05 r2 the mode-qualified Sync tests
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B03 r2 as withdrawn; adopt DEC-C01 r2 + DEC-A03 r2 + DEC-C05 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B04
Exact proposition under dispute: In Build A, an ASM relative transfer whose decoded target lies in a different link object is handled by one rule. The instruction is decoded with its exact length, prefixes and next-IP; rel32 to an exported entry stays symbolic. Otherwise it is admitted only if (a) every byte between source and target is supplied by in-place objects of original length (DEC-B19), (b) a target inside a C object lies within that object's VerifiedRegion at an instruction boundary, and it is encoded preferably as a piece-local label expression (assembler-checked range) or else as the original instruction bytes, (c) the assembled field equals the original bytes, and (d) the integration receipt is IDENTICAL. No compiled C object is transformed (no synthesized interior PUBDEF) to serve such a transfer during M2. Each such transfer is recorded as Build A placement debt. Joint TUs (DEC-B06) are preferred when available.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A05 r2 + DEC-C05 r2
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Supporting evidence: see §2 (withdrawals); both require decoded width/next-IP, in-place cover, fallthrough adjacency, emitted-byte checks and final link; C05 r2 additionally excludes M2 PUBDEF synthesis, which A05 r2 permits only under independent proof — both acceptable to me
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B04 r2 as withdrawn; adopt DEC-A05 r2 + DEC-C05 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B06
Exact proposition under dispute: A ReconstructedTU may contain several functions when the whole compiled object passes production RegionMatch (all publics MATCH, original spacing) and Build A is IDENTICAL. Immediately: Group B (IntroOpPlaySound, IntroOpSyncSound, IntroOpWaitSound) in one -5r TU. AGENTS.md's "one function per C object" ground rule is reworded accordingly, subject to owner approval. No consolidation is performed on the basis of heuristic CU signals.
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: ACCEPT r1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Supporting evidence: R0 P3; E1 Group B
Concrete counterexample or failure mode: none
Necessary assumptions: owner approves the ground-rule wording
Practical consequences: Group B lands as an exact joint TU
Proposed resolution: Adopt DEC-B06 r1 together with DEC-A13 (A's condition) and DEC-C06 r2
Conditions under which you would change position: A demonstrated failure of the joint TU under the full gate
Classification: implementation risk
```

```text
Issue: DEC-B07
Exact proposition under dispute: cemu.run_pair (or t4spec) restores, before the C run, all memory written during the original run (by code or stubs), or fails closed when a stub writes outside the restored set. The audit log records the restored set. After adoption, every xfailed "reference-C divergence" is re-evaluated, and its blocker category is changed only by evidence.
Competing positions: A CONDITIONAL (r1); B REJECT (r1); C CONDITIONAL (r1) — all on the indexed revision 1
Your position: REJECT r1 (withdrawn by me in R2)
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Supporting evidence: superseded by A11 + C16 r2
Concrete counterexample or failure mode: memory-only restoration (A Q1 carry leak)
Necessary assumptions: none
Practical consequences: none (all three REJECT or supersede)
Proposed resolution: Close as withdrawn; all three positions already reject or supersede it
Conditions under which you would change position: none
Classification: editorial (ledger)
```

```text
Issue: DEC-B09
Exact proposition under dispute: E3/E4 are not adopted into production during M2. Any later adoption first requires an owner decision on gate-2 semantics for src files containing mismatching publics (match --all currently fails them); then implementation over a strict shared OMF record/fixup subset with regression tests for the confirmed prototype defects (per-record THREAD reset, non-_TEXT PUBDEF/LPUBDEF rebasing, linear decode across tables) and rev-e4-01 F1-F4; record-size limits tested against the actual linker; then the RFC §16 criteria.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A07 r2 + DEC-C08 r2
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Supporting evidence: see §2 (withdrawals); both now include the owner gate-2 decision and the confirmed E4 defects, without a fixed 64-fixup mandate
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B09 r2 as withdrawn; adopt DEC-A07 r2 + DEC-C08 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B12
Exact proposition under dispute: Production cemu adopts symbol_aware_reloc for declared out-of-boundary dependencies, and VerificationBoundary/callback execution, only when a T4 needed for M2 requires Group mode with intra-TU calls or callbacks. Until then the existing whole-object c_stubbed rule remains. c_entry_hook is kept as defence in depth.
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C CONDITIONAL (r1) — all on the indexed revision 1
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A08 r2 + DEC-C11 r2
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Supporting evidence: see §2 (withdrawals); both make E6 demand-led per witness (M2 or later) with paired state independent of E6
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B12 r1 as withdrawn; adopt DEC-A08 r2 + DEC-C11 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B13
Exact proposition under dispute: CU recovery is analyst-facing only. shared_epilogue is a proven one-directional merge constraint only under stated producer premises (both functions compiler-generated by wcc386, correct block partition, no link-time tail merging or hand-written bridge). non_16_aligned_start is conditional on the actual segment base of a PARA-aligned next object, not on a function start that may follow leading bytes. shared_const_string_literal is conditional merge evidence that requires excluding explicit shared storage and linker pooling. zero16, none16, style_transition and S(f)-disjointness are candidate generators. Staircase breaks and call-locality drops are not used. No tool creates CU boundaries or consolidates sources automatically. compilation_units.toml is deferred to M3.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A10 (unanimous) + DEC-C12 r2
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Supporting evidence: see §2 (withdrawals); C12 r2 states producer premises, segment-base PARA, measured precision and conditional shared literals
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B13 r2 as withdrawn; adopt DEC-A10 (unanimous) + DEC-C12 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B16
Exact proposition under dispute: wc1.m2_inventory reclassifies 0x2315c/0x23170/0x231cc as "joint-TU T3 available (DEC-B06)", 0x1e380/0x2e96c/0x2efd0/0x2f73c as "fixed-displacement cross-object branches (DEC-B04)", and the IntroOpWaitSound divergence as "T4 harness state asymmetry (DEC-B07)".
Competing positions: A REJECT (r1); B REJECT (r1); C REJECT (r1) — all on the indexed revision 1
Your position: REJECT r1 (withdrawn by me in R2)
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Supporting evidence: superseded by C16 r2
Concrete counterexample or failure mode: diagnosis vs status (OBJ-A15)
Necessary assumptions: none
Practical consequences: none
Proposed resolution: Close as withdrawn/rejected — all three Architects REJECT
Conditions under which you would change position: none
Classification: editorial (ledger)
```

```text
Issue: DEC-B17
Exact proposition under dispute: Selective OMF extraction is adopted in production as the mechanism for advancing M2.
Competing positions: A REJECT (r1); B REJECT (r1); C REJECT (r1) — all on the indexed revision 1
Your position: REJECT r1 (the proposition is the rejected option)
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Supporting evidence: DEC-B09/A07 r2/C08 r2
Concrete counterexample or failure mode: none
Necessary assumptions: none
Practical consequences: none
Proposed resolution: Record as unanimously REJECTED (all three REJECT the option 'extraction as the M2 strategy'); the mechanical DISPUTED status is an artefact of a rejection-worded proposition
Conditions under which you would change position: none
Classification: editorial (ledger)
```

```text
Issue: DEC-B18
Exact proposition under dispute: Each T4 pair runs both sides from an equivalent complete starting state: CPU context (general registers, EFLAGS, segment registers and ESP), the full set of mapped memory regions and their contents (covering host and guest writes), emulator allocator state, and declared mutable stub state. Stubs keep mutable state in emulator memory or declare a per-run reset; otherwise the case reports UNSUPPORTED. State restoration is separate from the effects each test compares, and the audit log records the restored state. The rule applies to all T4 tests. Before landing, the full T4 suite runs once with the rule enabled; any change in an existing test's outcome or xfail status is presented to the owner. Reclassification of a divergence follows only from the test result after the change.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A11 (unanimous) + DEC-C16 r2
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Supporting evidence: see §2 (withdrawals); A11 is the contract; C16 r2 is the concrete mechanism (CPU/flags, all mapped memory, declared/stateless stubs, Q-B05, owner approval)
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B18 r2 as withdrawn; adopt DEC-A11 (unanimous) + DEC-C16 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B19
Exact proposition under dispute: The placement planner rejects any fixed-displacement cross-object transfer whose source-to-target span includes an object placed in legacy layout, whether by the global --legacy flag or the automatic per-object Unplaceable fallback, and records an adjacency obligation for every ASM piece that falls through into the next object, rejecting the plan if that successor is not the original in-place object.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: ACCEPT r2
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Supporting evidence: build.py:300-316@17733f9 (per-object Unplaceable fallback); A R2 P3 (0x2f73a jge → 0x2f73c fallthrough)
Concrete counterexample or failure mode: a fixed span over an automatically legacy-placed object
Necessary assumptions: none
Practical consequences: Planner rejects fixed spans over legacy objects and checks fallthrough adjacency; already incorporated by name in C05 r2 and in substance in A05 r2
Proposed resolution: Adopt DEC-B19 r2 (`5efd2b5a5855…`)
Conditions under which you would change position: A case where per-object legacy placement preserves original addresses (it does not by design)
Classification: correctness-verification
```

```text
Issue: DEC-B20
Exact proposition under dispute: Before any new placement path is admitted, measure the object flags, page/fixup records and fixup types of the current Build A against the original. If they agree, extend wc1.compare to compare them (strengthen-only). If they differ, present the difference to the owner before changing the Build A oracle.
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A03 r2 (+ DEC-C15 conditional)
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Supporting evidence: see §2 (withdrawals); A's R2 P1 measurement shows raw fixup order and last-page length differ while typed semantics agree; A03 r2's normalized-semantics comparison with raw-occurrence validation is the right rule (OBJ-A19, OBJ-A21)
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B20 r1 as withdrawn; adopt DEC-A03 r2 (+ DEC-C15 conditional)
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-B21
Exact proposition under dispute: Watcom 10.0a CONST inter-literal pad bytes are environment-dependent (they vary with compile-input paths and are stable for fixed inputs in our probes) and are excluded from proof-cache digests by normalization. No exemption from exact data matching is granted on the basis of literal shape or the absence of relocation targets; any future exclusion requires independent extent, ownership and access evidence covering computed reads, is applied identically by the matcher and build.place(), and keeps ASM as the Build A physical provider. Until then such objects fail closed and the extern-literal idiom remains available.
Competing positions: A none; B ACCEPT (r2); C none — all on the indexed revision 2
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-C10 r2 + DEC-A02 r2
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Supporting evidence: see §2 (withdrawals); A (R2) is right that proof authority must bind the exact raw object, so my r2 'excluded from proof-cache digests' was wrong for authority digests; C10 r2 carries the access-proof rule
Concrete counterexample or failure mode: A R2: normalizing pad bytes in an authority digest lets a differently initialized object reuse a proof
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B21 r2 as withdrawn; adopt DEC-C10 r2 + DEC-A02 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: correctness-verification (resolved by withdrawal)
```

```text
Issue: DEC-B22
Exact proposition under dispute: wc1.oldcc fails fast with a toolchain error (exit 78 path) when any compiler-facing argument (source, -fo output, -i= include, working directory) exceeds a measured safe Windows-path length, the limit being set from a measured envelope of the installed Watcom 10.0a under Wine rather than a fixed guess; a staging scheme to keep paths short may follow if it is proven to leave compiled bytes and include resolution unchanged.
Competing positions: A none; B ACCEPT (r1); C none — all on the indexed revision 1
Your position: WITHDRAWN by me (REJECT recorded); ACCEPT DEC-A12 + DEC-C04 r2
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Supporting evidence: see §2 (withdrawals); A12 and C04 r2 both measure and guard every compiler-facing argument and require semantic parity of staging
Concrete counterexample or failure mode: none
Necessary assumptions: the replacing decisions are adopted
Practical consequences: Removes a duplicate decision from the ledger without losing content
Proposed resolution: Close DEC-B22 r1 as withdrawn; adopt DEC-A12 + DEC-C04 r2
Conditions under which you would change position: If a replacing decision fails adoption, I would re-propose the missing content as a new decision
Classification: editorial (ledger)
```

```text
Issue: DEC-C01
Exact proposition under dispute: Retain the separation between `FunctionMatch` (local diagnostic), `RegionMatch` -> immutable `VerifiedRegion` (closed object/region proof), and `BuildAPlacementPlan` (integrated Build A admissibility), and require all pipeline tools (`wc1.match`, `wc1.build`, `wc1.t3_audit`, `wc1.m2_inventory`, `wc1.overnight`, `wc1.wave4`) to distinguish these three levels explicitly.
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `e7c48783a6fd…`
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C01 r2 (`e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C02
Exact proposition under dispute: Replace `tools/wc1/match.py`'s one-directional matcher with E0's bidirectional Normalized Addressing Obligation engine in Stage 0, fixing E2 Cause B (`FunctionMatch` MUST check branch closure against `[orig_fn.start, orig_fn.start + fn_len)`, NOT the first public's linear region) and preserving `trimmed_branch_target` checks across all modes (fixing E3 `partial_matcher.py:206`).
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `8f73dfdc9e75…`
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C02 r2 (`8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C03
Exact proposition under dispute: In both E0 `RegionMatch` and Stage-3 Fix B3, explicitly exempt 1..3-byte alignment padding gaps in `CONST` **if and only if** all 5 conditions hold: (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A.
Competing positions: A REJECT (r1); B REJECT (r1); C REJECT (r1) — all on the indexed revision 1
Your position: REJECT r1 (withdrawn by its author)
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Supporting evidence: A Q2 (computed read of a gap byte)
Concrete counterexample or failure mode: indexed read 0x8d vs 0x73
Necessary assumptions: none
Practical consequences: none
Proposed resolution: Record as unanimously REJECTED/withdrawn
Conditions under which you would change position: none
Classification: editorial (ledger)
```

```text
Issue: DEC-C04
Exact proposition under dispute: Immediately implement Watcom 10.0a short-path staging/length guard (`<= 48` char staging path + fail-fast `[TOOLCHAIN ERROR]` before ~129-char crash) in `tools/wc1/oldcc.py`, and fix the 3 `R3` provenance defects in `tools/wc1/t3_audit.py@a21772b` (checkout-rooted `_default_system_headers(repo_root)`, live `tool_sig` comparison, fail-closed `_git()`).
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `083f8ccd09b2…`
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C04 r2 (`083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C05
Exact proposition under dispute: Introduce non-forgeable `VerifiedRegion` (V5) and `BuildAPlacementPlan` in Stage 1, unifying `build.check_t3_buildable` with `BuildAPlacementPlan`, implementing Fix B1 (`LeadingJumpTableSpec` widened cut `[table_start, fn_end)`), and implementing **Unified Fix B2** handling ALL three cross-piece `rel8` classes (interior, cut-entry, cut-spanning) plus cross-piece fallthrough via NASM piece-boundary local-label offset expressions strictly in `in_place` mode (unconditionally forbidden under `--legacy`), plus `omfpatch` interior `_loc_<addr>` `PUBDEF` for cross-piece `rel32`.
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `0fa438f046f1…`
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C05 r2 (`0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C06
Exact proposition under dispute: Where all functions in a shared-epilogue cluster have C sources, prefer co-compiling them into a single contiguous multi-function `VerifiedRegion` under `-5r` / `-oa -5r` (starting with E1 Group B: `IntroOpPlaySound` `0x2315c` + `IntroOpSyncSound` `0x23170` + `IntroOpWaitSound` `0x231cc`), using Unified Fix B2 strictly as the incremental bridge while siblings remain ASM.
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `ae897988ef4e…`
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C06 r2 (`ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C07
Exact proposition under dispute: Sequence Stage 2 (deterministic atomic cross-module symbol renamer `wc1.symbol_migrate`, Wave 3R `upgrade-existing` + `low`-conf admission, `BULLET.C`, remaining 4–5 ref-C bugfixes, and user governance proposal on the 8 discovery/scope artifacts) immediately after Stage 1, and defer B3 (E5), multi-function T4 (E6), CU advisor (E8), and selective extraction (E4) to Stage 3 (post-M2).
Competing positions: A REJECT (r1); B REJECT (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `f92f2bc0a42e…`
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2); R3-P1 on pristine 17733f9 (the two remaining divergences persist with memory + CPU context restored; both tests use only constant-return stubs)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C07 r2 (`f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999`)
Conditions under which you would change position: A demonstration that 0x23530 or 0x2fcfc passes under a complete A11 state (e.g. allocator state, which my probe did not reset) — then the 'genuine' wording must change
Classification: editorial (ledger)
```

```text
Issue: DEC-C08
Exact proposition under dispute: REJECT adopting `experiments/build_codegen/e4/omf_extract.py@e6150b8` into production during M2 or as a default consolidation path. Whole-TU `RegionMatch` under `-5r` is the primary integration mechanism. Selective OMF extraction may only be introduced conditionally in Stage 3 if irreducible mismatching siblings remain after `-5r`/Wave 4B, and ONLY after rebuilding it over a unified OMF32 codec fixing all 8 defects (Probe 5 Bugs 5a–5d + `rev-e4-01` F1–F4).
Competing positions: A CONDITIONAL (r1); B ACCEPT (r1); C REJECT (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `6d614771ea47…`
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C08 r2 (`6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C09
Exact proposition under dispute: Before landing Fix B3 (Stage 3B) or any optional OMF extraction (Stage 3E), consolidate OMF32 parsing, persistent cross-record `THREAD` tracking, 64-fixup `FIXUPP32` chunking, and record emission into one tested module (`tools/wc1/omf.py`), removing duplicate ad-hoc OMF serializers.
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `802a18ef2052…`
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C09 r2 (`802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C10
Exact proposition under dispute: Adopt E5's data-anchor decoupling (`semantic_owner = C`, `physical_provider = ASM` in Build A) in Stage 3B over the unified OMF32 codec, strictly conditioned on implementing Invariant V4 (1..3B unreachable `CONST` alignment-gap verification), passing **EXP-1** on `SaveSlotPath` (`0x14740`), and enforcing `rev-e5-02` `_DATA` mutability/aliasing guards.
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `b609b22870c7…`
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C10 r2 (`b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C11
Exact proposition under dispute: Adopt E6's multi-function T4 architecture (`Isolated`/`Group`/`Integrated` modes, contiguous `VerificationBoundary`, 3-mechanism `DependencySubstitutionPolicy`, generator callbacks with pre-restore `watcall` ABI checks, R2 typed `LogicalFnPtr` extended with `LogicalConstDataPtr` and proven intra-function switch tables) in Stage 3C as a **hard prerequisite before consolidating any T4 function into a multi-function `.c` file**, while keeping single-function `wc1.cemu` unchanged during M2.
Competing positions: A REJECT (r1); B REJECT (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `46e66a775e59…`
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C11 r2 (`46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C12
Exact proposition under dispute: Explicitly REJECT `_DATA`/`_BSS` staircase splits, `call_locality_drop`, `none16` auto-splits, weighted CU boundary scoring, empty-`S(f)` auto-splitting, and any automatic mutation of `analysis/modules.toml`. Adopt instead an analyst-only **premise-carrying CU constraint graph** (`analysis/cu_hypotheses.toml` in Stage 3D) distinguishing Class 1 hard merges (`shared_epilogue`, `shared_const_string_literal`), Class 2 premise-dependent one-directional merges (`non_16_aligned_start` under `SEGDEF=PARA`), and Class 3 soft anchors (filenames, `zero16`), explicitly preserving competing hypotheses.
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C REJECT (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `7009936a27e2…`
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C12 r2 (`7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C13
Exact proposition under dispute: Replace RFC §2.2.5's incorrect "10.0a always aligns to 4B" premise with E2's empirically verified matrix (`10.0a -4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`; `OW2 -4r/-5r = 16B`), codify `-5r` as the primary Watcom 10.0a default family for contiguous CU reconstruction, and run **EXP-2** to evaluate `-5r -d1+ -zp1` and `-od -5r`.
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `eb85f6e2e75f…`
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2)
Concrete counterexample or failure mode: none for r2
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C13 r2 (`eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02`)
Conditions under which you would change position: If r2 were withdrawn, I would revert to my R2 position on r1
Classification: editorial (ledger)
```

```text
Issue: DEC-C15
Exact proposition under dispute: In Stage 0 (alongside E0 matcher cutover and wc1.oldcc short-path protection), enforce strict raw-OMF admission before production verification (validating record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, and preserved explicit FRAME encodings) and harden tools/wc1/compare.py to verify loader-relevant LE object flags, entry/stack object+offset, and fixup src_type alongside loaded bytes and fixup targets, after validating attribute parity on baseline Build A (EXP-A03).
Competing positions: A CONDITIONAL (r1); B CONDITIONAL (r1); C ACCEPT (r1) — all on the indexed revision 1
Your position: CONDITIONAL r1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Supporting evidence: A R2 P1/P2; compare.py@17733f9
Concrete counterexample or failure mode: the unique typed projection hides a conflicting second occurrence (A R2 P2, OBJ-A21)
Necessary assumptions: none
Practical consequences: Without raw-occurrence validation, a hardened comparator still accepts contradictory fixups
Proposed resolution: Adopt C15 r1 with A03 r2's conditions, or C revises C15 to: strict raw admission; validate raw fixup occurrences before deduplication; compare normalized loader semantics; raw serialization deltas diagnostic unless shown loader-relevant
Conditions under which you would change position: C15 r2 with that text → ACCEPT
Classification: correctness-verification
```

```text
Issue: DEC-C16
Exact proposition under dispute: Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per R1-Probe 2 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). Harden tools/wc1/cemu.py::run_pair (subject to owner approval and Q-B05 full T4 suite check) to restore all writable emulator RAM (or dirty pages via write hook, excluding read-only code/traps) before the C run, require T4Stub(fn=...) callbacks to store mutable state in emulator RAM or declare an explicit per-run reset hook, and record unwatched global writes in WC1_T4_AUDIT_LOG.
Competing positions: A REJECT (r1); B CONDITIONAL (r1); C PROPOSE (r1) — all on the indexed revision 1
Your position: REJECT r1 (superseded by its author's revision 2); ACCEPT r2 `06d885d45b91…`
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Supporting evidence: C's R2 response §3 (rev 2 text; hash verified R3-P2); R3-P1 on pristine 17733f9: stock harness 5/5 FAIL; memory + CPU context (GPRs, EFLAGS, segment regs) restored → 3 PASS, 2 FAIL unchanged; both failing tests use only constant-return stubs (no fn= state)
Concrete counterexample or failure mode: A OBJ-A20: Python-side and host state could still differ — R3-P1 shows the two failing tests have no such stub state; allocator state not separately reset (limitation)
Necessary assumptions: none
Practical consequences: Moves all substance to r2
Proposed resolution: Close r1 as superseded; adopt DEC-C16 r2 (`06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95`)
Conditions under which you would change position: As for C07; also if the full T4 suite under the rule (Q-B05) changes any currently passing test
Classification: correctness-verification
```

---

## 1b. Open objections (63 index entries)

Each objection is classified by its original severity. I propose closing an objection only where a named revision that I accept carries its remedy. Where the remedy is in a decision that is not yet unanimous, closure is conditional on that decision's adoption.

```text
Issue: OBJ-A01 (raised by gpt, r00)
Exact objection: - **OBJ-A01 — Correctness/verification.** Challenge the iff claim in production `check_placed_plan` and the older M2 roadmap’s unconditional Sync wiring. Actual addresses `0x231d7/0x231e1 → 0x2316c` cross retained providers when Sync is cut. Under the current NASM OMF path, both branches fail even with zero C-interior errors. The consequence is a false promotion candidate. Disposition requires a partition-aware pl…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD (my R0 P2 found the same edges)
Proposed resolution: CLOSE — absorbed by C01 r2, A03 r2, C05 r2 (shared planner + integration receipt + mode-qualified Sync tests) and A13 (Group B)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A02 (raised by gpt, r00)
Exact objection: - **OBJ-A02 — Correctness/verification.** Challenge using `wc1.compare` success alone as the new placement oracle (RFC §§7.2, 13, 16). Clearing `OBJ_EXEC` produces an `IDENTICAL` success receipt. A source kind is also omitted from the current relocation tuple. The assumption for the proposed correction is that the attributes enforced are loader relevant and measured against the real baseline. Keep the existing com…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD (conceded as OBJ-B19)
Proposed resolution: CLOSE — absorbed by A03 r2 (typed loader semantics after measurement; A R2 P1 parity)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A03 (raised by gpt, r00)
Exact objection: - **OBJ-A03 — Correctness/verification.** Challenge adopting E0 directly as a complete authoritative object validator (campaign D1). Its decoded input loses FRAME distinctions and does not attest raw record checksums. Assuming objects are trusted compiler output narrows the risk, but a production transformation must validate what the linker will consume. The concrete consequence is an accepted proof over an ambigu…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by A02 r2 and C02 r2 (strict raw admission, FRAME preserved, checksum when nonzero)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A04 (raised by gpt, r00)
Exact objection: - **OBJ-A04 — Unsupported factual claim.** Challenge the claim in campaign D4 that E5 unblocks arbitrary multi-function consolidation. Native SaveErrorDialog still has the wrong literal stride, and the experiment’s full real three-segment object supplies one function. Under off32 with proved identities, B3 removes anchor-order constraints. It cannot repair wrong code, incorrect aliases or unsupported OMF. Do not s…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — no live decision claims E5 unblocks arbitrary consolidation (A06, B08, C10 r2 all defer B3)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim
```

```text
Issue: OBJ-A05 (raised by gpt, r00)
Exact objection: - **OBJ-A05 — Blocking architectural.** Challenge the RFC §18 Phase D universal dependency on B3, extraction and E6 for consolidation pilots. An exact E1 whole object already links with ASM remainder. If the pilot changes no still-cited T4 semantics and the ordinary data plan is adequate, those extensions add risk without a dependency. Make admission per capability. [R §18, E1, E4–E6]
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by A13, C06 r2, B06 (whole-TU pilot needs no B3/E4/E6)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-A06 (raised by gpt, r00)
Exact objection: - **OBJ-A06 — Unsupported factual claim.** Challenge treating `-3r/-5r` as defeating paragraph alignment in the E8 interpretation. The E2 `-ot` controls retain PARA SEGDEF. Also a first public may follow a prefix, as in ChooseCampaignDialog. An align-based boundary constraint requires the actual candidate segment base and segment alignment. Function residue alone can yield a false historical split or merge. [E0, E…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by C12 r2 / C13 r2 (PARA at the actual segment base; -ot only)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim
```

```text
Issue: OBJ-A07 (raised by gpt, r00)
Exact objection: - **OBJ-A07 — Correctness/verification.** Challenge production extractor admission on the `VerifiedRegion` type check alone. E4’s `_require_verified` accepts an instance before consulting its context. Later checks narrow the risk but do not substitute for proof binding and a final post-B3 check. Given independently generated candidates or reused cache entries, stale or incomplete provenance can slip across the API…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by A07 r2 (proof bound to raw input object) and C08 r2 (rev-e4-01 F1)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A08 (raised by gpt, r00)
Exact objection: - **OBJ-A08 — Implementation risk.** Challenge treating E6 Integrated as a direct production T4 audit replacement. The experiment uses a different policy and runner, and real downstream code can be original. Shared process state, an execution boundary mistake or a stale compile could yield undeserved credit. Require parity and explicit per-side admissible execution, including fresh provenance and scenario effects.…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by A08 r2 and C11 r2 (production audit parity before a cited multi-function witness)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk
```

```text
Issue: OBJ-A09 (raised by gpt, r01)
Exact objection: - **OBJ-A09 — Correctness/verification.** B03/I-2 and C01/C05 place a clean plan and emitter acceptance at the integrated buildability boundary. With independently run assembly/link tools, that is insufficient. Sync exposes a preflight hole today. A forged-execute-flag image exposes the current comparator’s narrower projection. In the new design a plan must not mint promotion evidence before the actual output and …
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — absorbed by C01 r2 (IntegratedResult), A03 r2, C05 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A10 (raised by gpt, r01)
Exact objection: - **OBJ-A10 — Correctness/verification.** C02/V2 says cross-function edges force `UNSUPPORTED` in FunctionMatch, and B §3.2 I-1 restricts changes to losing matches. E1’s known geometry can make a scoped body match with a proved external context obligation. E2 shows why the first-public window is unusable on noncontiguous local comparisons. Under explicit support assumptions, replacing the bad bound and recording c…
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — absorbed by A02 r2 / C02 r2 (scoped local closure + explicit external obligations)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A11 (raised by gpt, r01)
Exact objection: - **OBJ-A11 — Correctness/verification.** C03 and C10 make the V4 predicates sufficient for a CONST exclusion. Database and decoded direct references omit computed effective addresses. Q2 reads such a byte with both explicit relocation sites outside the gap. Even ASM-provided output would only prove the original byte was retained. For source-data equivalence, require independent extent and access proof and exclude…
Competing positions: raised by gpt; R2 dispositions: gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — C03 withdrawn; C10 r2 requires independent extent/access proof; my B21 withdrawn
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A12 (raised by gpt, r01)
Exact objection: - **OBJ-A12 — Correctness/verification.** B07’s restoration scope covers memory. C11 freezes the current harness in M2 and makes full E6 plus extensions prerequisite to any consolidation. Q1 exhibits a carry-only false pass and a host write invisible to a guest hook. The experiment’s trusted setup still permits these ordinary behaviors. The needed correction is full paired initial-state accounting for affected wit…
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2; R2-P2 confirmed EFLAGS not reset)
Proposed resolution: CLOSE — absorbed by A11 (unanimous), A08 r2, C11 r2, C16 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A13 (raised by gpt, r01)
Exact objection: - **OBJ-A13 — Correctness/verification.** C05’s elaboration uses `t - (ia+2)` for every rel8 and mandates interior rel32 PUBDEF. B04’s literal path leaves encoding checks implicit. With x86 prefixes and loop forms, the next-IP arithmetic and assembler spelling can differ. Q3’s prefix changes the computed displacement by one. Fallthrough is instead an adjacency obligation. Require a typed encoding, exact endpoints …
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — absorbed by A05 r2 and C05 r2 (decoded width/next-IP, emitted-byte check, no mandatory PUBDEF)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A14 (raised by gpt, r01)
Exact objection: - **OBJ-A14 — Blocking architectural.** C08’s later extraction prerequisites omit owner disposition of existing `match --all` semantics for mismatching publics. The current per-public conjunction fails the canonical file even when a retained slice succeeds. This objection concerns credit for partial canonical TUs. A read-only partial diagnostic can remain useful without changing that policy. No promotion adapter c…
Competing positions: raised by gpt; R2 dispositions: gemini=UPHOLD
Your position: UPHOLD (it restates my OBJ-B04)
Proposed resolution: CLOSE — absorbed by A07 r2, C08 r2 (owner gate-2 decision first)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-A15 (raised by gpt, r01)
Exact objection: - **OBJ-A15 — Implementation risk.** C07 and B §8 S5 require generic placement work before the main reconstruction queue. B16 would turn probes into categorical status labels. B P3 shows an independent Group B route, and the latest inventory confirms already eligible work. Four other B2 candidates and B1 have bounded positive probes, while the tests and owner are still authoritative. Record candidates and diagnose…
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — B16 withdrawn; C07 r2 parallel tracks; A13 decouples Group B
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk
```

```text
Issue: OBJ-A16 (raised by gpt, r01)
Exact objection: - **OBJ-A16 — Unsupported factual claim.** C12 treats shared literals as hard merges and C13 couples the alignment correction to a default reconstruction family. B13’s hard epilogue rule also needs verified producer premises. E8’s sample does not exclude external storage or other producers. A PARA segment can have a leading prefix, and E7’s compatible contexts do not identify historical flags. The consequence is a…
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — absorbed by C12 r2, C13 r2, A10
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim
```

```text
Issue: OBJ-A17 (raised by gpt, r01)
Exact objection: - **OBJ-A17 — Implementation risk.** C04 bundles obsolete audit changes with a hard copy/staging limit, and B02/C02 do not by themselves ensure non-lossy raw binding. EV-3 covers the audit defects. A short nominal directory can still carry a long compiler-facing argument or alter include identity. A0 Q3 exposes why a parsed projection is insufficient for proof reuse. Separate staging parity, scheduling fingerprint…
Competing positions: raised by gpt; R2 dispositions: claude=UPHOLD, gemini=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — absorbed by A12, C04 r2 (measured effective paths) and A02 r2 (raw binding)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk
```

```text
Issue: OBJ-A18 (raised by gpt, r01)
Exact objection: - **OBJ-A18 — Unsupported factual claim.** C08/C09 treat missing 64-fixup chunking as an established production-blocking overflow and require broad serializer consolidation. The selected subset’s bound is below the encoded record length field, and Q3’s 256-fixup OMF record links on the tested linker. Q4 confirms a different concrete corruption. Keep record-limit tests for the actual linkers and share the strict su…
Competing positions: raised by gpt; R2 dispositions: gemini=UPHOLD
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by C08 r2 / C09 r2 (no fixed 64-fixup mandate; linker-measured limits)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim
```

```text
Issue: OBJ-A19 (raised by gpt, r02)
Exact objection: **OBJ-A19 — Correctness/verification.** B20 calls for equality checks over object flags, page/fixup records and types when the baseline agrees. R2 P1 finds raw fixup record order differs, although typed records, physical occurrence counts and grouping multiset agree. Last-page file length differs by one byte. Assuming the supported loader assigns no significance to serialization order after validation, making raw …
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD — against my DEC-B20
Proposed resolution: CLOSE — DEC-B20 withdrawn in favour of A03 r2 (normalized semantics; raw order/last-page delta diagnostic)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A20 (raised by gpt, r02)
Exact objection: **OBJ-A20 — Correctness/verification.** B18 claims every mapped region restored makes the two runs start in identical complete state. C16 prescribes RAM restoration or dirty-page hooks and definitive five-row classifications. A1 Q1 found a CPU-flags false pass and showed host API writes escape a guest hook. Even perfect RAM rollback leaves arbitrary host objects reachable by stubs unless declared and reset. Under …
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD in principle; NARROWED by R3-P1
Proposed resolution: CLOSE once C16 r2 and A11 are adopted — my B18 r2 is withdrawn into C16 r2. R3-P1 adjudicates the CPU channel for the five tests (memory + CPU restored: same 3/2 split) and shows the two failing tests use only constant-return stubs; allocator state remains unverified and is covered by A11's 'declared mutable dependency state'
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-A21 (raised by gpt, r02)
Exact objection: **OBJ-A21 — Correctness/verification.** The minimal reading of C15 would add types from `fixups_unique` to the comparator. LE’s first-wins normalization hides later conflicting occurrences. R2 P2 changes the second occurrence of a page-boundary fixup from type 7 to 6 and preserves the entire unique typed projection. A comparator using that projection alone would still accept contradictory records. Validate typed a…
Competing positions: raised by gpt; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — absorbed by A03 r2 (validate raw occurrences before deduplication); my C15 position carries it as a condition
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification
```

```text
Issue: OBJ-B01 (raised by claude, r00)
Exact objection: **OBJ-B01** - **Proposition challenged.** Group B (IntroOpPlaySound/IntroOpSyncSound) requires "cut-boundary relative branch emission in wc1.emit/wc1.build". The m2 inventory (`DG-03`) and `e1a4178` say so, and `summary.md` §18.9 PR2 counts Group A and B under "+5–6 more T3s via E1" without stating that no infrastructure is needed. - **Evidence.** P3: production tools on `main` give Group B as one TU MATCH and IDE…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own); facts confirmed by A and C
Proposed resolution: CLOSE — Group B independence adopted (A13, C06 r2, B06)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B02 (raised by claude, r00)
Exact objection: **OBJ-B02** - **Proposition challenged.** The campaign roadmap (`summary.md` §18.9; `decisions.md`) presents E0–E8 as covering the RFC's production mechanisms. Fix B2 (RFC §7.2) was never tested; `grep` finds no B2 implementation or test in `experiments/`. - **Evidence.** B2 blocks 4 not-done functions after Group B (P2, P5). - **Failure mode.** Production would adopt B3 and extraction (zero DONE) before B2 (+4 DO…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — B2 is now specified in A05 r2 / C05 r2 / B19 r2 and demonstrated (R0 P5)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-B03 (raised by claude, r00)
Exact objection: **OBJ-B03** - **Proposition challenged.** RFC §7.2 Fix B2 covers "ASM instruction in `piece_k` branches into a verified interior address `t`". - **Counterexample.** B2-a (IntroOpSyncSound: ASM→ASM across a cut) and B2-c (MissionDefeat `0x2f718`/`0x2f722`/`0x2f72e`: ASM rel8 → C entry). Neither is detected by `replaced_interior_refs`, and both fail in NASM (P2, P5). - **Consequence.** The §7.2 design repeats the fa…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — three-class B2 taxonomy in A05 r2 / C05 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B04 (raised by claude, r00)
Exact objection: **OBJ-B04** - **Proposition challenged.** D5 "ADOPT (SCOPED)" and D6 "ADOPT (CONDITIONAL)" (`decisions.md@e6150b8`). - **Evidence.** A `src =` TU with mismatching siblings fails `match --all` (`_match_one`, `ok &= status == "MATCH"`), and that is part of gate 2. Changing it is a finish-line change that needs owner approval. Neither decision states this. - **Severity.** Blocking architectural (governance).
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — governance prerequisite in A07 r2 / C08 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-B05 (raised by claude, r00)
Exact objection: **OBJ-B05** - **Proposition challenged.** D4 "ADOPT" Fix B3, and roadmap PR3 placed before the multi-function T4 and extraction work. - **Evidence.** Zero M2 DONE effect; its only real case (SaveErrorDialog) is DONE and its T3 route is an `-os` outlier. - **Failure mode.** OMF rewriting complexity on the Build A path with no M2 benefit. - **Severity.** Implementation risk / prioritisation.
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — B3 deferred (A06, B08 unanimous, C10 r2)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-B06 (raised by claude, r00)
Exact objection: **OBJ-B06** - **Proposition challenged.** "5 ref-C behavioural divergences … fix real behavioural bug in reference C" (`m2_inventory` DG-04; AGENTS.md next step 2 calls them "real ref-C divergences"). - **Evidence.** P4: for IntroOpWaitSound the reference C passes once the stub-mutated input is restored; the byte-exact C fails identically without the fix. - **Consequence.** Effort goes into "fixing" correct C. The…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — 3/5 artefacts agreed; C16 r2; R3-P1 corroborates
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B07 (raised by claude, r00)
Exact objection: **OBJ-B07** - **Proposition challenged.** `summary.md` §18.1: "single biggest discovery … unifying root cause … `-5r`". - **Evidence.** E7's own text says "not a claim that every original CU used Pentium options"; 51 T3 functions are `only_4r`; `-3r` also spaces at 4 bytes. The finding explains spacing, not the original flags. - **Severity.** Unsupported factual claim (editorial). It matters if used to justify a g…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C13 r2 drops the historical-flag claim
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B08 (raised by claude, r00)
Exact objection: **OBJ-B08** - **Proposition challenged.** RFC §2.2.4: "Формат OMF не поддерживает внешние 8-битные релокации". - **Evidence.** The observed limitation is NASM's OBJ backend ("OBJ format can only handle 16- or 32-byte relocations", P5 log). The OMF FIXUPP location type 0 (low-order byte) exists, and wlink's handling of it is untested. - **Consequence.** Small; I-3 sidesteps it. - **Severity.** Editorial / unsupport…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own); C conceded (R1 §1.1.7)
Proposed resolution: CLOSE — editorial RFC correction (NASM -f obj limit, not OMF)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: editorial
```

```text
Issue: OBJ-B09 (raised by claude, r00)
Exact objection: **OBJ-B09** - **Proposition challenged.** RFC §16 row "CodeRegion + Fix B1 + Fix B2" requires a "strict type/state separation CandidateRegion → VerifiedRegion → PlacementPlan" before B1/B2. - **Evidence.** The P5/P6 probes show B1 and B2 need about 30 lines of planner logic. The safety comes from the matcher-minted VerifiedRegion and IDENTICAL, not from a type hierarchy. - **Severity.** Maintainability (propose DE…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — B14 unanimous (no Candidate type)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: maintainability (resolved)
```

```text
Issue: OBJ-B10 (raised by claude, r00)
Exact objection: **OBJ-B10** - **Proposition challenged.** `summary.md` §18.9 PR1: "Zero T3 regressions guaranteed (519/519)". - **Evidence.** The population has changed (539); P1 re-establishes it at `a21772b`. It must be re-run at implementation. The population exercises 0 leading or data-pointer cases, so the "guarantee" is about the absence of regressions, not about coverage. - **Severity.** Unsupported claim (minor).
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — A02 r2 / C02 r2 require the live cutover audit
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B11 (raised by claude, r00)
Exact objection: **OBJ-B11** - **Proposition challenged.** E7 "13 buildable T3 opportunities" as a production metric. It uses `check_t3_buildable` (E7 "Inputs"). - **Evidence.** The predicate is incomplete (P2, P5). The 13 stand only because of the combined link. - **Consequence.** Wave4/batch_driver "buildable" filters may promote unbuildable candidates; `make verify` still catches them, but at a cost. - **Severity.** Correctness…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — shared planner + integration receipt (C01 r2, A03 r2)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B12 (raised by claude, r00)
Exact objection: **OBJ-B12** - **Proposition challenged.** E8 precision figures used as general classification of game-CU signals (RFC §9.2 re-mapping). - **Evidence.** B1 is library code dominated by `intxa386` and assembly objects; A is designed by the experimenters; the `zero16` premise is unverified in the game. - **Consequence.** Only the analyst-facing use is justified. - **Severity.** Unsupported factual claim (if generalis…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — analyst-only CU evidence (A10 unanimous, C12 r2)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B13 (raised by claude, r00)
Exact objection: **OBJ-B13** - **Proposition challenged.** RFC §4.2/§9.1 `analysis/compilation_units.toml` and §10.2's 13-field provenance as near-term deliverables. - **Evidence.** There is no M2 consumer; they risk the "second metadata DB" that RFC §4.1 forbids. - **Severity.** Maintainability. ---
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — storage deferred (B14 unanimous, C01 r2, C12 r2)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: maintainability (resolved)
```

```text
Issue: OBJ-B18 (raised by claude, r01)
Exact objection: **OBJ-B18** - **Proposition challenged:** "5 real ref-C behavioural divergences" (C §1, §8.0 item 5, DEC-C07; inventory DG-04; A §8 "repair the five"). - **Evidence:** R1-P4. - **Failure mode:** correct C is rewritten, and the harness asymmetry persists. - **Assumptions:** the full-memory restore introduces no new asymmetry (it equalizes inputs). - **Practical consequences:** −3 unnecessary C repairs; +3 potential…
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C07 r2 / C16 r2 adopt the 3/5 split; A withdrew 'repair the five'
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B19 (raised by claude, r01)
Exact objection: **OBJ-B19** - **Proposition challenged:** my own R0 I-3(c)/I-6 and the RFC §13.1 framing that Build A IDENTICAL is a complete Build A check. - **Evidence:** `compare.py@a21772b`, `17733f9` (flags printed, not compared; fixup tuple lacks type); A Q3. - **Failure mode:** a loader-relevant object attribute or fixup-type change passes as IDENTICAL. - **Severity:** correctness/verification. I accept this against myself.
Competing positions: raised by claude; R2 dispositions: gpt=UPHOLD
Your position: MAINTAIN (own concession)
Proposed resolution: CLOSE — A03 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B20 (raised by claude, r01)
Exact objection: **OBJ-B20** - **Proposition challenged:** C DEC-C02's dependency structure (matcher landing depends on DEC-C03/EXP-1). - **Evidence:** D-2; `save_slot_path.c@a21772b`; `build.py:94-104`. - **Failure mode:** a soundness fix is delayed by a completeness feature. - **Severity:** implementation risk.
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C02 r2 decoupled from V4
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-B21 (raised by claude, r01)
Exact objection: **OBJ-B21** - **Proposition challenged:** A DEC-A08 and C DEC-C11 placing paired-state reset only within multi-function T4 adoption. - **Evidence:** R1-P4. The defect is in single-function `run_pair` today. - **Failure mode:** current T4 proofs run on asymmetric inputs, with a false-pass possibility. - **Severity:** correctness/verification.
Competing positions: raised by claude; R2 dispositions: gpt=UPHOLD, gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — A08 r2, C11 r2, A11
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B22 (raised by claude, r01)
Exact objection: **OBJ-B22** - **Proposition challenged:** C OBJ-C01 and DEC-C03 "non-deterministic … flaky across runs" and V4 as Stage 0. - **Evidence:** R1-P2 (stable for fixed inputs; path-dependent); D-2. - **Failure mode:** a mis-specified root cause leads to the wrong mitigation. The practical risk is checkout-dependent digests, not run-to-run flakiness. - **Severity:** unsupported factual claim.
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: NARROWED
Proposed resolution: CLOSE — terminology settled as 'environment-dependent': C's R2-Probe 1 (stable within a session, different across sessions at a fixed path) and my R1-P2/R2-P1 (path-dependent; stable across fresh-wineserver compiles) are both consistent with it; no decision depends on the finer cause
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B23 (raised by claude, r01)
Exact objection: **OBJ-B23** - **Proposition challenged:** C DEC-C05's `omfpatch` `_loc_<addr>` PUBDEF synthesis for cross-piece rel32 into cut interiors. - **Evidence:** R0 P5 (`0x2f6df` built IDENTICAL with no object transform). - **Failure mode:** an unnecessary post-codegen object transform on the M2 path, requiring strict-codec work earlier. - **Severity:** implementation risk.
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C05 r2 drops M2 PUBDEF synthesis; A05 r2 requires independent proof
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-B24 (raised by claude, r01)
Exact objection: **OBJ-B24** - **Proposition challenged:** C "68 blocked by atomic cross-module symbol migration" and "1002/1010" (DEC-C07, OBJ-C04, Stage 2). - **Evidence:** inventory rows (`missing=[name,C]`, `requires_llm=True` for all 61). - **Failure mode:** over-projected deterministic yield; tooling is prioritised over reconstruction capacity. - **Severity:** unsupported factual claim.
Competing positions: raised by claude; R2 dispositions: gpt=REBUT
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C07 r2 reports the yield as an upper bound; A agrees reconstruction is binding
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B25 (raised by claude, r01)
Exact objection: **OBJ-B25** - **Proposition challenged:** C DEC-C11 "hard prerequisite before consolidating any T4 function into a multi-function `.c`"; "Multi-function T4 without E6 leaks intra-TU sibling calls". - **Evidence:** `src/playflic/player_reference.c@a21772b` (20 functions) tested today. The E6-identified hazard is stub bypass under declared substitution, not multi-function files per se. - **Severity:** unsupported fa…
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C11 r2 triggers E6 per witness need
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B26 (raised by claude, r01)
Exact objection: **OBJ-B26** - **Proposition challenged:** C §2.8 "[FACT] predominantly `-5r`", §2.9/§7.1 "`non_16_aligned_start` 100% precision", DEC-C13 "-5r primary default". - **Evidence:** E7 "R6 preservation" disclaimer and `only_4r = 51`; E8 epistemic table (0.800/0.836/0.618). - **Severity:** unsupported factual claim.
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C12 r2 / C13 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-B27 (raised by claude, r01)
Exact objection: **OBJ-B27** - **Proposition challenged:** all three roadmaps forbidding B2 only under the global `--legacy` flag. - **Evidence:** `build.py:310-314@a21772b` (automatic per-object legacy fallback on `Unplaceable`). - **Failure mode:** a fixed-displacement branch spans an object that silently fell back to legacy layout. IDENTICAL would catch it, but the planner must reject it first (I-2). - **Severity:** correctness…
Competing positions: raised by claude; R2 dispositions: gemini=UPHOLD
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — B19 r2, A05 r2, C05 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B28 (raised by claude, r02)
Exact objection: **OBJ-B28** - **Proposition challenged:** DEC-C11 rev 1, "while keeping single-function `wc1.cemu` unchanged during M2". - **Evidence:** - `tools/wc1/emu.py:188-240@a21772b` (EFLAGS not reset between runs); - `cemu.run_pair` restores only `watch` ranges; - R1-P4 (3/5 xfails pass under full state); - A's Q1 (carry-only false pass). - **Failure mode:** current single-function T4 proofs keep running on asymmetric inp…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C11 r2 makes paired state mandatory now
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-B29 (raised by claude, r02)
Exact objection: **OBJ-B29** - **Proposition challenged:** DEC-C07 rev 1, Stage 2 "immediately after Stage 1" as a serial dependency. - **Evidence:** reconstruction uses existing gates; Group B builds with current tools (R0 P3); the inventory shows 14 functions eligible now. - **Failure mode:** reconstruction capacity idles behind planner work. - **Severity:** implementation risk. - **Note:** this changes my position from R1 CONDI…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C07 r2 parallel tracks
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-B30 (raised by claude, r02)
Exact objection: **OBJ-B30** - **Proposition challenged:** DEC-C03 rev 1's five V4 conditions as sufficient. - **Evidence:** A's Q2 (indexed read of a gap byte while relocation targets sit only at literal starts; `0x8d` vs `0x73`). - **Failure mode:** certified data that behaves differently when the provider changes (Build B). - **Severity:** correctness/verification. - **Note:** this changes my position from R1 CONDITIONAL to REJ…
Competing positions: raised by claude; R2 dispositions: none recorded
Your position: MAINTAIN (own)
Proposed resolution: CLOSE — C03 withdrawn
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C01 (raised by gemini, r00)
Exact objection: ### `OBJ-C01` - **Severity:** `correctness/verification` (blocking for E0 production merge & E5 B3 rollout) - **Exact proposition challenged:** That E0 `RegionMatch` (`experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`) and E5 Fix B3 (`experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`, `decisions.md@e6150b8` D1/D5) can verify real multi-string Watcom 10.0a `-ot` `CONST` segments via whole-segment byt…
Competing positions: raised by gemini; R2 dispositions: gemini=UPHOLD
Your position: REBUT the remedy (V4); UPHOLD the premise
Proposed resolution: CLOSE — C03 withdrawn, C02 r2 fails closed, C10 r2 sets the future rule
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C02 (raised by gemini, r00)
Exact objection: ### `OBJ-C02` - **Severity:** `blocking architectural` + `correctness/verification` - **Exact proposition challenged:** RFC §7.2 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) and `tools/wc1/emit.py:45-84@a21772b` (`replaced_interior_refs`) modeling Fix B2 solely as branches targeting the *interior* of a replaced cut (`s < t < e`, `t not in entries`). - **Source:** `docs/architecture/rfc-build-c…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — three-class B2 plus fallthrough in A05 r2 / C05 r2 / B19 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C03 (raised by gemini, r00)
Exact objection: ### `OBJ-C03` - **Severity:** `implementation risk` + `correctness/verification` - **Exact proposition challenged:** `docs/research/build-codegen/decisions.md@e6150b8` (Decision D6) and `E4-omf-extraction.md@e6150b8` treating `experiments/build_codegen/e4/omf_extract.py` as ready for near-term production adoption pending only minor `rev-e4-01` polish. - **Source:** `docs/research/build-codegen/decisions.md@e6150b8…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — C08 r2, A07 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-C04 (raised by gemini, r00)
Exact objection: ### `OBJ-C04` - **Severity:** `blocking architectural` - **Exact proposition challenged:** `docs/research/build-codegen/summary.md@e6150b8` and `decisions.md@e6150b8` (§18.9 rollout priority) sequencing B3 (E5) and multi-function T4 (E6) ahead of or on the M2 completion critical path without accounting for the actual 98-function M2 blocker distribution on `main@a21772b`. - **Source:** `docs/research/build-codegen/…
Competing positions: raised by gemini; R2 dispositions: gemini=UPHOLD
Your position: UPHOLD
Proposed resolution: CLOSE — C07 r2, A01
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-C05 (raised by gemini, r00)
Exact objection: ### `OBJ-C05` - **Severity:** `correctness/verification` - **Exact proposition challenged:** E0 `matcher_proto.py:358-359@e6150b8` validating `FunctionMatch` branch closure against `[first_pub_base, first_pub_base + len(_TEXT))` instead of the target function's own `[base, base + fn_len)`. - **Source:** `experiments/build_codegen/e0/matcher_proto.py:358-359@e6150b8`. - **Supporting evidence & concrete counterexamp…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD as a completeness refinement (not soundness)
Proposed resolution: CLOSE — A02 r2 / C02 r2 scoped local closure
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C06 (raised by gemini, r00)
Exact objection: ### `OBJ-C06` - **Severity:** `unsupported factual claim` - **Exact proposition challenged:** RFC §2.2.5 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) asserting that Watcom 10.0a always aligns functions to 4 bytes while OW2 aligns to 16 bytes. - **Source:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (§2.2.5). - **Supporting evidence & concrete counterexample:** `E2-context-…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — B10 unanimous; C13 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-C07 (raised by gemini, r00)
Exact objection: ### `OBJ-C07` - **Severity:** `unsupported factual claim` + `blocking architectural` - **Exact proposition challenged:** RFC §9.3 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) proposing `_DATA`/`_BSS` staircases and `call_locality_drop` as primary CU boundary recovery signals. - **Source:** `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac` (§9.3). - **Supporting evidence & concret…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD
Proposed resolution: CLOSE — A10, C12 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-C08 (raised by gemini, r00)
Exact objection: ### `OBJ-C08` - **Severity:** `correctness/verification` - **Exact proposition challenged:** Production `tools/wc1/t3_audit.py@a21772b` claiming checkout-portable, fail-closed improved-T4 audit provenance, and `tools/wc1/oldcc.py@a21772b` omitting E7 D9 short-path protection. - **Source:** `tools/wc1/t3_audit.py@a21772b` (`_default_system_headers`, `build_improved_audit_snapshot`, `_git`); `tools/wc1/oldcc.py@a217…
Competing positions: raised by gemini; R2 dispositions: none recorded
Your position: UPHOLD for oldcc; t3_audit part delivered in EV-3
Proposed resolution: CLOSE — A12, C04 r2; t3_audit fixed at 17733f9
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C09 (raised by gemini, r01)
Exact objection: ### `OBJ-C09` - **Severity:** `correctness/verification` - **Exact proposition challenged:** `DEC-A06` (GPT: *"Admit B3 initially for fully verified whole segments only"*), `DEC-B02` (Claude: adopting E0 matcher semantics as-is), and `DEC-B08` (Claude: RFC §8.2 constraints 1–5 as-is for B3) omitting explicit handling of Watcom 10.0a's non-deterministic uninitialized 1..3-byte `CONST` alignment padding. - **Source:…
Competing positions: raised by gemini; R2 dispositions: gpt=REBUT, claude=REBUT
Your position: REBUT the V4 remedy; UPHOLD that exact matching rejects such objects (fail-closed)
Proposed resolution: CLOSE — C now accepts B21/C10 r2 with OBJ-A11's access-proof condition, which C10 r2 contains; my B21 is withdrawn into C10 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C10 (raised by gemini, r01)
Exact objection: ### `OBJ-C10` - **Severity:** `correctness/verification` + `blocking architectural` - **Exact proposition challenged:** `DEC-B04` (Claude) emitting cross-object `rel32` to cut interiors and cross-object `rel8` as raw literal bytes (`db`) while relying on unhardened `wc1.compare` as "a complete check", and both `DEC-B04` and `DEC-A05` omitting explicit cross-piece fallthrough guards. - **Source:** `02-architect-cla…
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD, claude=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — my B04 is withdrawn into A05 r2 / C05 r2, which contain all four of C's items
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C11 (raised by gemini, r01)
Exact objection: ### `OBJ-C11` - **Severity:** `correctness/verification` - **Exact proposition challenged:** Internal contradiction between `DEC-B03` (*"Regression tests: IntroOpSyncSound standalone is rejected; Group B is accepted"*) and `DEC-B04` (admitting fixed-layout in-place cross-object `rel8` branches spanning a cut). - **Source:** `02-architect-claude-opening.md` (`DEC-B03` line 500 vs `DEC-B04` line 512). - **Evidence &…
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD, claude=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — mode-qualified Sync tests in C05 r2 (my B03 withdrawn into C01 r2/C05 r2)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: correctness-verification (resolved)
```

```text
Issue: OBJ-C12 (raised by gemini, r01)
Exact objection: ### `OBJ-C12` - **Severity:** `unsupported factual claim` - **Exact proposition challenged:** `DEC-B16` (Claude) reclassifying only `IntroOpWaitSound` as T4 harness state asymmetry and estimating S4 as `"up to +4"` DONE. - **Source:** `02-architect-claude-opening.md` (`DEC-B16` line 656, §8 line 389). - **Evidence & counterexample:** **R1-Probe 2** proved on `main@a21772b` (identical at `17733f9`) that **3/5** xfa…
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD, claude=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — B16 withdrawn; C16 r2 adopted
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: unsupported factual claim (resolved)
```

```text
Issue: OBJ-C13 (raised by gemini, r01)
Exact objection: ### `OBJ-C13` - **Severity:** `correctness/verification` - **Exact proposition challenged:** Architect B's Stage S1 (`DEC-B06`) merging the first multi-function `src =` TU (Group B) into production **before** Stage S2 (`DEC-B02` production E0 `RegionMatch`). - **Source:** `02-architect-claude-opening.md` (§8 lines 386–387). - **Evidence & counterexample:** `tools/wc1/match.py@17733f9` lacks E0 bidirectional/leadin…
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD, claude=REBUT
Your position: REBUT (R2); C withdrew it in R2
Proposed resolution: CLOSE — withdrawn by its author; A13 provides the independent strict-proof path
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: editorial (withdrawn)
```

```text
Issue: OBJ-C14 (raised by gemini, r01)
Exact objection: ### `OBJ-C14` - **Severity:** `blocking architectural` + `implementation risk` - **Exact proposition challenged:** `DEC-A07` (GPT) and `DEC-B09` (Claude) specifying E4 pilot prerequisites without including all four Probe-5 defects in `e4/omf_extract.py` (and `DEC-A07` omitting Claude's Gate-2 governance prerequisite). - **Source:** `01-architect-gpt-opening.md` (`DEC-A07`); `02-architect-claude-opening.md` (`DEC-B…
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD
Your position: UPHOLD
Proposed resolution: CLOSE — A07 r2, C08 r2
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

```text
Issue: OBJ-C15 (raised by gemini, r01)
Exact objection: ### `OBJ-C15` - **Severity:** `implementation risk` - **Exact proposition challenged:** Omission of Watcom 10.0a short-path staging/guard (`tools/wc1/oldcc.py`, E7 Decision D9) from both Architect A's and Architect B's Stage 0 / M2 roadmaps. - **Source:** `01-architect-gpt-opening.md` (§8, §11); `02-architect-claude-opening.md` (`DEC-B01`, §8); `tools/wc1/oldcc.py@17733f9`. - **Evidence & counterexample:** EV-3's …
Competing positions: raised by gemini; R2 dispositions: gpt=UPHOLD, claude=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — A12, C04 r2 (my B22 withdrawn into them)
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: implementation risk (resolved)
```

```text
Issue: OBJ-C16 (raised by gemini, r01)
Exact objection: ### `OBJ-C16` - **Severity:** `blocking architectural` - **Exact proposition challenged:** `DEC-B01` (Claude) restricting M2 tooling strictly to E0/planner/B1/B2/joint-TUs/T4-state and assigning the remaining 78 functions to `"existing drivers"` (S5). - **Source:** `02-architect-claude-opening.md` (`DEC-B01`, §8 line 390). - **Evidence & counterexample:** `candidate_ledger.json@a21772b` and EV-3 `m2_inventory` (`1…
Competing positions: raised by gemini; R2 dispositions: claude=UPHOLD
Your position: UPHOLD (R2)
Proposed resolution: CLOSE — my B01 is withdrawn; A01 + C07 r2 keep admission principle-driven with enablers admitted on need
Conditions under which you would change position: failure of the named resolving decision(s) to be adopted, or new evidence contradicting it
Classification: blocking architectural (resolved)
```

---

## 2. New evidence and position changes

### 2.1 New evidence

**R3-P1 — The five xfailed T4 tests under memory + CPU paired-state restoration (pristine EV-3).**

```bash
D=/tmp/opencode/cn-claude/e3; mkdir -p $D
cd /mnt/data/projects/warcraft-1-decompile-wt/cons-b && git archive 17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9 | tar -x -C $D
ln -s /mnt/data/projects/warcraft-1-decompile/original $D/original
cd $D && WINEPREFIX=/mnt/data/projects/warcraft-1-decompile-wt/cons-b/build/oldcc/wineprefix TMPDIR=/tmp/opencode/cn-claude/t \
  nix develop -c sh -c 'python3 …/runtime/claude/probes/scripts/probe_q2.py; python3 …/runtime/claude/probes/scripts/probe_q1.py base'
```

- `probe_q2.py` (sha256 `019784fa…`) wraps `wc1.cemu.run_pair`, as `t4spec` sees it. Inside each pair, a class-level `Emu.call` wrapper does two things:
  - at the first call (original), it snapshots every `uc.mem_regions()` region and the CPU registers EAX..ESP, EFLAGS, DS, ES, SS, FS, GS;
  - at the second call (C), it restores them.
- **Output, memory + CPU restore (`memcpu`):**
  - wait_sound PASS;
  - start_credits FAIL `0x59eb9: original 01 != C 00`;
  - run_script PASS;
  - intro_play PASS;
  - end_screen FAIL `0x80054c: original 70 != C 50`.
- **Output, stock harness (`base`):** all five FAIL, with the messages recorded in R1.
- The same `memcpu` result was obtained first on my disposable `a21772b` export (attempt 01, 10:36Z) and reproduced on pristine `17733f9` at 14:35Z.
- **Stub-state check:**
  - `sed -n 176,192p tests/test_playflic_t4.py` (IntroOpStartCredits uses `T4Stub(0x32060, ret=width, …)` only);
  - `grep -n "def _es_stubs" -A22 tests/test_mod_2efd0_t4.py` (EndScreen: only `T4Stub(addr, ret=…/log_regs=…)`; no `fn=`).
- **Limitations:**
  - The emulator's Python-side allocator state is not separately reset.
  - The tests were run as direct function calls, not via pytest, so the xfail markers are not exercised.
  - `WC1_T4_AUDIT_LOG` was not enabled.
  - This is not Q-B05 (the full T4 suite under the rule).

**R3-P2 — Revision-2 hash verification.**
- I recomputed SHA-256 over the exact proposition texts of A02/A03/A05/A07/A08 rev 2 and A12/A13 (A's R2 §3, §6), and of C01, C02, C04–C13 and C16 rev 2 (C's R2 §3).
- All 7 A hashes equal the values A printed. All 13 C hashes equal the values C printed.
- Script: inline Python over the inbox files (regex on "New proposition." and "New (Rev 2):"). The values are embedded in `runtime/claude/r03/gen.py` (`H2`).

**Re-verified earlier evidence relied on here:** R0 P3 (Group B), R0 P5/P6 (B2/B1 links), R1-P2/R2-P1 (CONST pad environment-dependence), R2-P2 (EFLAGS not reset by `Emu.call`).

### 2.2 Position changes

**Withdrawals of my decisions.** The ledger records each as REJECT by its author. Each is superseded by decisions I ACCEPT:

| Withdrawn | Rev | Hash | Content now carried by |
|---|---|---|---|
| DEC-B01 | 2 | `3bf6d12e…` | DEC-A01 (unanimous) + DEC-C07 r2 (parallel tracks, need-driven enablers, deferrals) |
| DEC-B02 | 2 | `e3dcf170…` | DEC-A02 r2 + DEC-C02 r2 |
| DEC-B03 | 2 | `8055745b…` | DEC-C01 r2 (shared planner consumers + IntegratedResult) + DEC-A03 r2 + DEC-C05 r2 (mode-qualified Sync tests) |
| DEC-B04 | 2 | `445c252e…` | DEC-A05 r2 + DEC-C05 r2 |
| DEC-B09 | 2 | `da892344…` | DEC-A07 r2 + DEC-C08 r2 |
| DEC-B12 | 1 | `7fe4e537…` | DEC-A08 r2 + DEC-C11 r2 |
| DEC-B13 | 2 | `74e56068…` | DEC-A10 (unanimous) + DEC-C12 r2 |
| DEC-B18 | 2 | `eea41a0a…` | DEC-A11 (unanimous) + DEC-C16 r2 |
| DEC-B20 | 1 | `9827f947…` | DEC-A03 r2 (A's measurement R2 P1: typed semantics agree; raw fixup order and last-page length differ — OBJ-A19 upheld) |
| DEC-B21 | 2 | `fe41a923…` | DEC-C10 r2 + DEC-A02 r2. **This one is a substantive concession.** A is right that an authority digest must bind the exact raw object; my r2 wording "excluded from proof-cache digests by normalization" is unsound for proof authority. Normalization remains acceptable only for non-authoritative candidate grouping. |
| DEC-B22 | 1 | `1deaeb25…` | DEC-A12 + DEC-C04 r2 |

**Changes in my positions on others' decisions since R2:**
- A02/A03/A05/A07/A08 **r1 → REJECT** (superseded by their author); **r2 → ACCEPT**.
- C01, C02, C04–C13, C16 **r1 → REJECT** (superseded); **r2 → ACCEPT**.
- My R2 REJECTs of C07 r1 and C11 r1 are resolved by their r2 texts, which remove serialization and freezing.
- My R2 CONDITIONAL on C16 r1 becomes ACCEPT on r2, given R3-P1.
- DEC-A12 and DEC-A13: ACCEPT (new).
- DEC-C15 r1: unchanged CONDITIONAL.

**Not changed:** B05, B06 r1, B08, B10, B11, B14, B15, B19 r2 (ACCEPT); B07, B16, B17, C03 (REJECT).

### 2.3 New objections and decisions

None. Everything raised in R2 is absorbed by existing revision-2 propositions. A new ID would fragment the ledger.

---

## 3. Convergence assessment

| Issue (cluster) | Trend | Remaining difference | Kind | Cheapest decisive test |
|---|---|---|---|---|
| E0 matcher cutover (A02 r2, C02 r2; withdrawn B02) | **narrowed to agreement in substance** | none known | — | A's §7 row: port the E0 controls plus malformed/FRAME/non-contiguous/trim-target cases; audit every live T3 at the cutover commit |
| Planner and integration (C01 r2, A03 r2, C05 r2, B19 r2; withdrawn B03/B04/B20) | **narrowing** | the A05 r2 vs C05 r2 wording on interior exports ("only under independent proof" vs "none in M2"). Both forbid an unproven export, so I treat this as **editorial/design preference** for M2 | design preference | combined B1/B2 link fixture with the legacy/fallthrough/prefixed-branch negatives (A §5) |
| Comparator (A03 r2, C15 r1) | **narrowing** | C15 r1 lacks raw-occurrence validation before deduplication | **correctness-verification** (not editorial: A R2 P2 mutant) | run A's three R2 P2 mutants against the strengthened checker; C revising C15 to A03 r2's rule closes it |
| Group B (A13, B06, C06 r2) | **converged in substance** | A wants the A13 strict-proof path, C/B the ordinary full gate; these are compatible | — | the A13 run itself (strict proof of the exact object, dual compile, full gate) |
| Paired T4 state (A11 unanimous, C16 r2, C11 r2, A08 r2; withdrawn B18) | **narrowed** by R3-P1 | A's REJECT of C16 r1 rested on unadjudicated CPU/stub channels, now excluded for the five tests; allocator state remains | correctness-verification | Q-B05: the full T4 suite once under complete state restoration (memory + CPU + declared stubs); any change in a passing test goes to the owner |
| CONST pad (C10 r2, A06, B08; withdrawn B21; C03 withdrawn) | **converged** | none; the "environment-dependent" wording is accepted by all; the finer cause (path vs session) is irrelevant to any decision | — | only if B3/natural literals are triggered: SaveSlotPath with a computed-read negative (A's §7) |
| E4 / extraction (A07 r2, C08 r2, C09 r2; withdrawn B09) | **converged** | none | — | none until a named candidate exists |
| E6 (A08 r2, C11 r2; withdrawn B12) | **converged** | none | — | per witness when needed |
| CU evidence (A10, C12 r2, C13 r2; withdrawn B13) | **converged** | none | — | A's §7 historical-reach row (optional, post-M2) |
| oldcc paths (A12, C04 r2; withdrawn B22) | **converged** | none | implementation risk | controlled shallow/deep effective-path compile with include and out-path parity |
| M2 sequencing (A01, C07 r2; withdrawn B01) | **converged** | none | — | none (scheduling) |
| B07/B16/B17/C03 | settled (all REJECT) | mechanical DISPUTED status from rejection-worded or withdrawn propositions | **editorial (ledger)** | none |

**Overall:** apart from C15's raw-occurrence clause (correctness), the remaining items are ledger mechanics: superseded revision-1 entries, withdrawn duplicates, and rejection-worded propositions. They are not architectural disagreements, though I do not claim consensus.

---

## 4. Structured positions for every live decision

The positions below cover all 38 index entries, the 13 unanimous decisions (not reopened) and the 18 revision-2 propositions of A and C. Revision-2 hashes are verified (R3-P2).

### 8.1 Architect A

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A10
Revision: 1
Proposition SHA-256: 8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A11
Revision: 1
Proposition SHA-256: 0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 2
Proposition SHA-256: 87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A03
Revision: 2
Proposition SHA-256: 58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: OBJ-A19, OBJ-A21
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A05
Revision: 2
Proposition SHA-256: 414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 2
Proposition SHA-256: 5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A08
Revision: 2
Proposition SHA-256: 2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A12
Revision: 1
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Position: ACCEPT
Reason: Measured effective-path guard with staging parity; supersedes my DEC-B22.
Conditions: none
Related objections: OBJ-C15, OBJ-A17
```

```text
Decision: DEC-A13
Revision: 1
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Position: ACCEPT
Reason: Independent strict-proof path for the exact Group B TU (R0 P3; E1 E0 RegionMatch).
Conditions: none
Related objections: OBJ-C13
```

### 8.2 Architect B (own)

```text
Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-B01
Revision: 2
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A01 + C07 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B02
Revision: 2
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A02 r2 + C02 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B03
Revision: 2
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by C01 r2 + A03 r2 + C05 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B04
Revision: 2
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A05 r2 + C05 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: ACCEPT
Reason: Retained; compatible with A13 and C06 r2.
Conditions: none
Related objections: OBJ-C13
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: REJECT
Reason: Withdrawn by me in Round 2; all three positions reject or supersede it.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B09
Revision: 2
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A07 r2 + C08 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A08 r2 + C11 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B13
Revision: 2
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A10 + C12 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Withdrawn by me in Round 2; all three positions reject or supersede it.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: The proposition states the rejected option; all three Architects REJECT it.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B18
Revision: 2
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A11 + C16 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B19
Revision: 2
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Position: ACCEPT
Reason: Retained; incorporated by name in C05 r2 and in substance in A05 r2.
Conditions: none
Related objections: OBJ-B27, OBJ-C10
```

```text
Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A03 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B21
Revision: 2
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by C10 r2 + A02 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B22
Revision: 1
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Position: REJECT
Reason: Withdrawn by its author (me) in Round 3; content carried by A12 + C04 r2, which I ACCEPT.
Conditions: none
Related objections: none
```

### 8.3 Architect C

```text
Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: Unanimous; not reopened (no new evidence).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C01
Revision: 2
Proposition SHA-256: e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 2
Proposition SHA-256: 8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: Withdrawn by its author; A Q2 counterexample.
Conditions: none
Related objections: OBJ-A11, OBJ-B30
```

```text
Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C04
Revision: 2
Proposition SHA-256: 083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C05
Revision: 2
Proposition SHA-256: 0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: OBJ-B23, OBJ-C10, OBJ-C11
```

```text
Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C06
Revision: 2
Proposition SHA-256: ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C07
Revision: 2
Proposition SHA-256: f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2). R3-P1 supports the 3/2 split under memory + CPU equality with stateless stubs; status and xfail changes remain owner-gated as the proposition states.
Conditions: none
Related objections: OBJ-A15, OBJ-B24
```

```text
Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C08
Revision: 2
Proposition SHA-256: 6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C09
Revision: 2
Proposition SHA-256: 802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C10
Revision: 2
Proposition SHA-256: b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C11
Revision: 2
Proposition SHA-256: 46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C12
Revision: 2
Proposition SHA-256: 7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C13
Revision: 2
Proposition SHA-256: eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: CONDITIONAL
Reason: Strict raw admission and comparator hardening are right.
Conditions: Validate raw fixup occurrences before deduplication and compare normalized loader semantics; raw serialization deltas (fixup order, last-page length, A R2 P1) stay diagnostic unless shown loader-relevant — i.e. A03 r2's rule.
Related objections: OBJ-A19, OBJ-A21
```

```text
Decision: DEC-C16
Revision: 1
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Position: REJECT
Reason: Superseded by its author's revision 2 (positions do not carry over).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C16
Revision: 2
Proposition SHA-256: 06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95
Position: ACCEPT
Reason: Revision 2 incorporates the objections I raised; hash verified against the published text (R3-P2). R3-P1 supports the 3/2 split under memory + CPU equality with stateless stubs; status and xfail changes remain owner-gated as the proposition states.
Conditions: none
Related objections: OBJ-A20
```