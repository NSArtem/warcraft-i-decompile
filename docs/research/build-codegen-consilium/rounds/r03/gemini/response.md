# Build & Codegen Infrastructure — Consilium Round 3 Targeted Deliberation

- **Architect:** Architect C — Gemini (`gemini-4-neon-high`, high effort, `agy 1.5.17`)
- **Round:** Round 3 — Targeted Deliberation
- **Evidence Baseline:** `EV-3` (`research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`; RFC `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`; production `main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`: `912/1010 DONE`, `98` not-done, `2505 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`)
- **Inbox Verified:** `00-LIVE-ISSUES.json` (`3bc01dbe...`), `01-architect-gpt-response.md` (`0b876293...`), `02-architect-claude-response.md` (`a4593962...`)
- **Unanimous Decisions Not Reopened (13):** `DEC-A01`, `DEC-A04`, `DEC-A06`, `DEC-A09`, `DEC-A10`, `DEC-A11`, `DEC-B05`, `DEC-B08`, `DEC-B10`, `DEC-B11`, `DEC-B14`, `DEC-B15`, `DEC-C14`.

---

## Part A — Per-Issue Deliberation: Non-Unanimous Decisions (38)

```text
Issue: DEC-A02
Exact proposition under dispute: Two-scope bidirectional verifier with strict raw-OMF admission, bound to compiler output, audited on all live T3s at cutover (rev 1).
Competing positions: GPT REJECT (superseded by rev 2); Claude ACCEPT; Gemini ACCEPT (R2).
Your position: REJECT rev 1 (superseded); ACCEPT DEC-A02 rev 2 (87a63b4c...) and DEC-B02 rev 2.
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Supporting evidence: E0/E2 Cause B (matcher_proto.py:358-359@e6150b8); E3 partial_matcher.py:206@e6150b8; R0 Probe 4 & Claude R0 P1 (539/539 MATCH@a21772b).
Concrete counterexample or failure mode: Rev 1 omits function-extent local bounds, explicit external context obligations, and trim checks in both scopes (OBJ-A10, OBJ-C05).
Necessary assumptions: Strict raw-OMF subset covers every live declared T3 at cutover.
Practical consequences: Adopting rev 2 / DEC-B02 rev 2 closes all three gaps with zero T3 regressions.
Proposed resolution: Reject DEC-A02 rev 1 as superseded; adopt DEC-A02 rev 2 and DEC-B02 rev 2.
Conditions under which you would change position: A live production T3 failing strict raw-OMF admission or local-bounds closure at cutover.
Classification: correctness-verification
```

```text
Issue: DEC-A03
Exact proposition under dispute: Single-provider partition plan plus actual assembly, link, existing compare, and explicit loader/provider evidence for Build A acceptance (rev 1).
Competing positions: GPT REJECT (superseded by rev 2); Claude ACCEPT; Gemini ACCEPT (R2).
Your position: REJECT rev 1 (superseded); ACCEPT DEC-A03 rev 2 (58e7c0dd...).
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Supporting evidence: GPT R2 P1 (Build A@17733f9: flags/entry/stack/8770 typed fixups/8773 physical occurrences agree; raw order & last-page 1339 vs 1340 differ); GPT R2 P2 (LE.fixups_unique hides conflicting 2nd occurrence at (1, 53246)).
Concrete counterexample or failure mode: Rev 1 omits validating raw physical fixup records before deduplicating page-straddle copies (OBJ-A21) and keeping serialization deltas diagnostic (OBJ-A19).
Necessary assumptions: DOS/4GW assigns no semantics to raw fixup serialization order after raw validation and normalized typed equality.
Practical consequences: DEC-A03 rev 2 closes the first-wins deduplication hole without breaking baseline Build A.
Proposed resolution: Reject DEC-A03 rev 1 as superseded; adopt DEC-A03 rev 2 and DEC-C15 rev 2.
Conditions under which you would change position: Proof that DOS/4GW semantics depend on raw fixup order or the 1B last-page delta.
Classification: correctness-verification
```

```text
Issue: DEC-A05
Exact proposition under dispute: Prefer whole-TU shared-tail groups; allow proved piece-local relative ASM expressions; reject unsupported outgoing compiled-slice rel8 (rev 1).
Competing positions: GPT REJECT (superseded by rev 2); Claude ACCEPT; Gemini ACCEPT (R2).
Your position: REJECT rev 1 (superseded); ACCEPT DEC-A05 rev 2 (414da43a...) and DEC-B04/B19 rev 2.
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Supporting evidence: R0 Probe 2 (0x2f73a->0x2f73c); GPT R2 P3 (0x202bb pop ebx -> 0x202bc ret); build.py:310-314@a21772b (Unplaceable fallback); GPT R1 Q3 (prefixed branch width).
Concrete counterexample or failure mode: Rev 1 omits cross-piece fallthrough adjacency, per-object legacy rejection, and decoded width/next-IP checks (OBJ-B27, OBJ-C10).
Necessary assumptions: Fixed inter-object distances hold only when all spanned providers are in-place and original-length.
Practical consequences: Adopting rev 2 / DEC-B04 rev 2 + DEC-B19 rev 2 closes all transfer edge gaps.
Proposed resolution: Reject DEC-A05 rev 1 as superseded; adopt DEC-A05 rev 2, DEC-B04 rev 2, and DEC-B19 rev 2.
Conditions under which you would change position: A supported ASM encoding uncheckable via decoded width/next-IP and piece-local expressions.
Classification: correctness-verification
```

```text
Issue: DEC-A07
Exact proposition under dispute: Defer general extraction; allow a narrow pilot only with canonical-TU benefit, object-bound region proof, independent targets, and post-transform/link verification (rev 1).
Competing positions: GPT REJECT (superseded by rev 2); Claude CONDITIONAL; Gemini CONDITIONAL (R2).
Your position: REJECT rev 1 (superseded); ACCEPT DEC-A07 rev 2 (5d8aa99e...) and DEC-B09 rev 2.
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Supporting evidence: match.py:368-390@a21772b (Gate-2 match --all fails mismatching publics); R0 Probe 5a/5b/5c (omf_extract.py:258,378,798-807,823@e6150b8); GPT R1 Q4.
Concrete counterexample or failure mode: Rev 1 omits owner source-gate authorization and validated subset record/symbol handling (OBJ-B04, OBJ-C14).
Necessary assumptions: Gate-2 finish-line semantics remain owner-controlled per AGENTS.md.
Practical consequences: Adopting rev 2 and DEC-B09 rev 2 keeps M2 focused and prevents silent symbol corruption in any later pilot.
Proposed resolution: Reject DEC-A07 rev 1 as superseded; adopt DEC-A07 rev 2 and DEC-B09 rev 2.
Conditions under which you would change position: An irreducible M2 blocker requiring extraction plus owner Gate-2 authorization and strict codec.
Classification: blocking architectural
```

```text
Issue: DEC-A08
Exact proposition under dispute: Require execution boundaries, symmetric substitutions, callback/ABI checks, typed pointers, and audit parity before cited multi-function T4 (rev 1).
Competing positions: GPT REJECT (superseded by rev 2); Claude ACCEPT; Gemini CONDITIONAL (R2).
Your position: REJECT rev 1 (superseded); ACCEPT DEC-A08 rev 2 (2be94eba...).
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Supporting evidence: GPT R1 Q1 (carry-flag false pass + host-write escape); Claude R2-P2 (emu.py:188-240@a21772b never resets EFLAGS); R1-Probe 2 & R1-P4.
Concrete counterexample or failure mode: Rev 1 did not apply DEC-A11 paired-state equivalence to affected current T4 witnesses immediately (OBJ-B21).
Necessary assumptions: Current T4 witnesses run on shared mutable emulator state and need DEC-A11 now.
Practical consequences: Rev 2 fixes present T4 asymmetry immediately while keeping E6 machinery demand-led.
Proposed resolution: Reject DEC-A08 rev 1 as superseded; adopt DEC-A08 rev 2 alongside DEC-A11 and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-A12
Exact proposition under dispute: Stage or reject effective Watcom 10.0a paths using measured limits, proving staging preserves source identity/includes/flags/output attribution and reporting failures as toolchain errors.
Competing positions: GPT ACCEPT (PROPOSED); Claude unvoted; Gemini unvoted.
Your position: ACCEPT rev 1.
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Supporting evidence: EV-3 report.md:64@17733f9 (rc=5 at ~130-char pytest tmp paths); R1-Probe 4 (rc=-11 at ~129+ Windows chars); oldcc.py@17733f9; E7 D9.
Concrete counterexample or failure mode: Unprotected paths crash wcc386 under Wine; unverified staging risks altering include resolution or parallel outputs (OBJ-A17, OBJ-C15).
Necessary assumptions: Safe effective compiler-facing path limit is empirically measurable on installed Watcom 10.0a under Wine.
Practical consequences: Eliminates recurring path crashes cleanly as exit-78 toolchain errors, replacing DEC-C04 rev 1.
Proposed resolution: Adopt DEC-A12 rev 1 alongside DEC-B22 rev 1; withdraw DEC-C04 rev 1.
Conditions under which you would change position: Crashes occurring unpredictably below a measured safe envelope after isolating Wine prefix/env.
Classification: implementation risk
```

```text
Issue: DEC-A13
Exact proposition under dispute: Permit exact Group B whole-TU promotion independently of generic B1/B2/matcher rollout only with commit-bound strict raw-object RegionMatch, dual-compiler checks, typed Build A comparison, and preserved cited T4 checks or owner approval.
Competing positions: GPT ACCEPT (PROPOSED); Claude unvoted; Gemini unvoted.
Your position: ACCEPT rev 1.
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Supporting evidence: E1 Group B@e6150b8; Claude R0 P3 (Group B MATCH + IDENTICAL on main); build.py@17733f9; tests/test_playflic_t4.py@17733f9.
Concrete counterexample or failure mode: Early promotion without commit-bound strict RegionMatch weakens verification (OBJ-C13); gating on generic B1/B2 delays +3 DONE (OBJ-A15).
Necessary assumptions: Commit-bound strict raw-object RegionMatch and typed LE comparison run on the exact Group B candidate.
Practical consequences: Unblocks Group B (+3 DONE, zero B2 debt) without lowering verification rigor.
Proposed resolution: Adopt DEC-A13 rev 1 alongside DEC-B06 rev 1; withdraw DEC-C06 rev 1.
Conditions under which you would change position: Group B failing strict raw-object RegionMatch, dual-compiler check, or typed LE comparison.
Classification: correctness-verification
```

```text
Issue: DEC-B01
Exact proposition under dispute: Principle-driven M2 admission for blocker/soundness fixes with parallel reconstruction tracks, admitting E0, single planner/receipts, B2/legacy/fallthrough, B1, joint TUs, T4 symmetry, comparator hardening, oldcc guard, and on-demand rename helper; deferring B3/E4/E6/stores/CU DB post-M2 (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Supporting evidence: EV-3 main@17733f9 (912/1010 DONE; 14 eligible, 76 needs_human, 8 default-skipped); candidate_ledger.json@a21772b; OBJ-A15, OBJ-C15, OBJ-C16.
Concrete counterexample or failure mode: Serializing reconstruction idles ready work (OBJ-B29); premature B3/E4/E6/E8 yields 0/98 M2 DONE (OBJ-C04).
Necessary assumptions: M2 Gate-1 completion governs admission while demonstrated soundness fixes remain admissible.
Practical consequences: Unifies all M2 infrastructure priorities and parallel tracks, allowing withdrawal of DEC-C07 rev 1.
Proposed resolution: Adopt DEC-B01 rev 2 alongside DEC-A01 (UNANIMOUS); withdraw DEC-C07 rev 1.
Conditions under which you would change position: A named not-done M2 function genuinely requiring B3, E4, or E6.
Classification: blocking architectural
```

```text
Issue: DEC-B02
Exact proposition under dispute: Adopt E0 bidirectional matcher in tools/wc1/match.py with 55 controls, strict raw-OMF admission, raw-byte binding, exact local-data/CONST matching at cutover, function-scoped diagnostic external obligations, and live full-T3 make verify gate (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Supporting evidence: E0 55 controls@e6150b8; R0 Probe 4 & Claude R0 P1 (539/539 MATCH@a21772b); GPT R0 Q3 & R1 Q2; E2 Cause B.
Concrete counterexample or failure mode: Omitting strict raw-OMF admission admits malformed inputs (OBJ-A03); coupling V4 delays cutover with an unproven gap rule (OBJ-A11, OBJ-B20).
Necessary assumptions: All live T3s at cutover pass strict raw-OMF admission and exact local-data matching.
Practical consequences: Lands hardened E0 cleanly in Stage 0, fully subsuming DEC-C02 rev 1.
Proposed resolution: Adopt DEC-B02 rev 2 alongside DEC-A02 rev 2; withdraw DEC-C02 rev 1.
Conditions under which you would change position: A live T3 failing strict raw-OMF checks at cutover (requiring subset adjustment with controls).
Classification: correctness-verification
```

```text
Issue: DEC-B03
Exact proposition under dispute: One placement planner plan(p, regions) as preflight across all tools; T3 promotion requires an actual assemble/link/hardened-compare integration receipt; mode-qualified IntroOpSyncSound regression tests (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Supporting evidence: R0 Probe 1 & Claude R0 P2 (Sync 0x23170 false positive); OBJ-A09; OBJ-C11.
Concrete counterexample or failure mode: Split planners produce false buildable verdicts; treating preflight as acceptance bypasses actual link/loader checks (OBJ-A09).
Necessary assumptions: DEC-B20 checks reflect post-R2 P1/P2 semantics (DEC-A03 rev 2 / DEC-C15 rev 2).
Practical consequences: Single preflight planner, mandatory integration receipts, and contradiction-free regression tests.
Proposed resolution: Adopt DEC-B03 rev 2 alongside DEC-A03 rev 2 and DEC-C01 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-B04
Exact proposition under dispute: Unified Build A cross-object transfer rule using exact decoded length/prefixes/next-IP, symbolic rel32 to exported entries, in-place original-length cover (DEC-B19), piece-local expression preferred, assembled-byte + receipt checks, no M2 synthesized interior PUBDEF, recorded debt, and joint-TU preference (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Supporting evidence: R0 Probe 1 & Claude R0 P5 (0x2f73c, 0x2f6df->0x2f746 IDENTICAL without C-object mutation); GPT R1 Q3 (prefixed branch width); OBJ-A13, OBJ-B23, OBJ-C10.
Concrete counterexample or failure mode: Fixed ia+2 breaks prefixed rel8 (GPT R1 Q3); M2 interior PUBDEF synthesis adds unneeded C-object mutation (OBJ-B23).
Necessary assumptions: In-place layout + DEC-B19 preserves distances; emitted bytes and integration receipt match.
Practical consequences: Unblocks all 4 non-Group-B B2 functions cleanly without mutating C objects, allowing withdrawal of DEC-C05 rev 1.
Proposed resolution: Adopt DEC-B04 rev 2 alongside DEC-A05 rev 2 and DEC-B19 rev 2; withdraw DEC-C05 rev 1.
Conditions under which you would change position: An M2-blocking rel32-interior edge provably requiring an interior export.
Classification: correctness-verification
```

```text
Issue: DEC-B06
Exact proposition under dispute: Admit multi-function ReconstructedTUs gated on whole-object production RegionMatch and Build A IDENTICAL (starting with Group B under -5r), updating AGENTS.md with owner approval and prohibiting heuristic consolidation (rev 1).
Competing positions: GPT CONDITIONAL (tested flags, A13 if early, preserve cited tests or owner approval); Claude ACCEPT; Gemini ACCEPT (R2).
Your position: ACCEPT rev 1 (paired with DEC-A13 rev 1 whenever promoted before production E0 cutover).
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Supporting evidence: E1 Group B@e6150b8; Claude R0 P3 (MATCH + IDENTICAL on main); tests/test_playflic_t4.py@17733f9.
Concrete counterexample or failure mode: Heuristic consolidation or unapproved cited-test edits risk layout drift or governance breach.
Necessary assumptions: Owner approves AGENTS.md rewording and any test change; DEC-A13 governs early promotion.
Practical consequences: Unblocks Group B (+3 DONE, zero B2 debt), subsuming DEC-C06 rev 1.
Proposed resolution: Adopt DEC-B06 rev 1 paired with DEC-A13 rev 1; withdraw DEC-C06 rev 1.
Conditions under which you would change position: Group B failing strict raw-object RegionMatch or typed LE comparison.
Classification: blocking architectural
```

```text
Issue: DEC-B07
Exact proposition under dispute: Restore memory written during the original T4 run before the C run and re-evaluate xfailed divergences (rev 1).
Competing positions: Claude REJECT (withdrawn, superseded by DEC-B18 rev 2); GPT CONDITIONAL; Gemini CONDITIONAL (R2).
Your position: REJECT rev 1 (superseded by DEC-A11 and DEC-B18 rev 2).
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Supporting evidence: GPT R1 Q1 (carry-flag false pass + host-write escape); Claude R2-P2 (emu.py:188-240@a21772b).
Concrete counterexample or failure mode: Memory-only restoration leaves EFLAGS, registers, allocator, and stub state asymmetric (OBJ-A12, OBJ-A20).
Necessary assumptions: Complete paired starting state is carried by DEC-A11 (UNANIMOUS) and DEC-B18 rev 2.
Practical consequences: Cleanly closes withdrawn rev 1.
Proposed resolution: Reject DEC-B07 rev 1 as superseded by DEC-A11 and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-B09
Exact proposition under dispute: Defer E3/E4 during M2; require owner Gate-2 decision, strict shared OMF subset with Probe 5a/5b/5c and rev-e4-01 F1-F4 regression tests, linker-tested record limits, and RFC §16 criteria before any later adoption (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Supporting evidence: OBJ-B04 (match.py:368-390@a21772b); R0 Probe 5a/5b/5c (omf_extract.py@e6150b8); GPT R1 Q3 & Q4; rev-e4-01 F1-F4.
Concrete counterexample or failure mode: M2 extraction violates Gate-2 governance and exposes THREAD/non-_TEXT PUBDEF/table-decode bugs for 0/98 M2 yield.
Necessary assumptions: Zero M2 functions require selective extraction.
Practical consequences: Captures complete post-M2 governance and technical gates, allowing withdrawal of DEC-C08 rev 1.
Proposed resolution: Adopt DEC-B09 rev 2 alongside DEC-A07 rev 2 and DEC-C09 rev 2; withdraw DEC-C08 rev 1.
Conditions under which you would change position: An irreducible M2 blocker requiring extraction (still needing owner Gate-2 sign-off and all listed fixes).
Classification: blocking architectural
```

```text
Issue: DEC-B12
Exact proposition under dispute: Adopt E6 symbol_aware_reloc and VerificationBoundary/callback execution only when a T4 needed for M2 requires Group mode with intra-TU calls or callbacks, keeping c_entry_hook as defence in depth (rev 1).
Competing positions: Claude ACCEPT; GPT CONDITIONAL (admit post-M2 consumers, proved entry-only edges for c_entry_hook, apply A08 rev 2 & A11); Gemini CONDITIONAL (R2).
Your position: CONDITIONAL rev 1 (aligned with GPT's conditions).
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Supporting evidence: src/playflic/player_reference.c@a21772b (20 fns tested without E6); E6-multi-t4.md@e6150b8; DEC-A08 rev 2; DEC-A11.
Concrete counterexample or failure mode: Literal "needed for M2" excludes post-M2 witnesses; c_entry_hook without proved entry-only edges misses interior jumps; missing audit parity/paired-state leaves gaps.
Necessary assumptions: Paired-state symmetry (DEC-A11 / DEC-B18 rev 2) applies immediately to all current T4s.
Practical consequences: Aligns demand-led E6 cleanly across M2 and post-M2 witnesses.
Proposed resolution: Revise DEC-B12 to rev 2 adding post-M2 consumers, proved entry-only edges for c_entry_hook, and DEC-A08 rev 2/DEC-A11 parity, or supersede with DEC-A08 rev 2.
Conditions under which you would change position: Incorporating those three clarifications.
Classification: correctness-verification
```

```text
Issue: DEC-B13
Exact proposition under dispute: Analyst-facing premise-carrying CU constraint graph with stated producer premises for shared_epilogue, PARA segment-base evaluation for non_16_aligned_start, conditional shared_const_string_literal excluding shared storage/pooling, rejection of staircases/call-locality/auto-consolidation, and M3 deferral of compilation_units.toml (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Supporting evidence: E8-cu-boundaries.md@e6150b8 (staircases 0.250/0.281, call_locality 0.323/0.179, none16 0.174); E0/E2 leading bytes; OBJ-A06, OBJ-A16, OBJ-B26, OBJ-C07.
Concrete counterexample or failure mode: Unconditional shared literals or function-start alignment tests cause false historical merges/splits; §9.3 heuristics yield >70% false splits.
Necessary assumptions: CU signals remain strictly analyst guidance.
Practical consequences: Captures E8 cleanly without premature TOML schemas, allowing withdrawal of DEC-C12 rev 1.
Proposed resolution: Adopt DEC-B13 rev 2 alongside DEC-A10 (UNANIMOUS); withdraw DEC-C12 rev 1.
Conditions under which you would change position: New game-corpus evidence refuting a stated signal premise.
Classification: unsupported factual claim
```

```text
Issue: DEC-B16
Exact proposition under dispute: Reclassify Group B, four B2 functions, and IntroOpWaitSound directly in wc1.m2_inventory from probes (rev 1).
Competing positions: GPT REJECT; Claude REJECT (withdrawn); Gemini REJECT (R2).
Your position: REJECT rev 1 (maintain 3/3 REJECT).
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Supporting evidence: R1-Probe 2 & R1-P4 (3/5 xfails flip, not just 0x231cc); OBJ-A15 (diagnostic vs verified status).
Concrete counterexample or failure mode: Incomplete 1/5 scope and conflates probe diagnosis with verified inventory status.
Necessary assumptions: Status updates follow landed proofs and post-change test runs (DEC-B18 rev 2).
Practical consequences: Already 3/3 REJECT; cleanly retired.
Proposed resolution: Maintain 3/3 REJECT (superseded by DEC-B18 rev 2 and DEC-B03 rev 2).
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: DEC-B17
Exact proposition under dispute: Adopt selective OMF extraction in production as the mechanism for advancing M2 (rev 1).
Competing positions: GPT REJECT; Claude REJECT; Gemini REJECT (R2).
Your position: REJECT rev 1 (maintain 3/3 REJECT).
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Supporting evidence: candidate_ledger.json@a21772b (0/98 M2 yield); OBJ-B04 (Gate-2 conflict); R0 Probe 5a-5c & GPT R1 Q4.
Concrete counterexample or failure mode: Defect-laden OMF rewriting with zero M2 yield and Gate-2 conflict.
Necessary assumptions: Whole-TU RegionMatch and Build A B1/B2 cover M2 needs.
Practical consequences: Already 3/3 REJECT; cleanly retired.
Proposed resolution: Maintain 3/3 REJECT (post-M2 deferral governed by DEC-A07 rev 2 & DEC-B09 rev 2).
Conditions under which you would change position: None for M2.
Classification: blocking architectural
```

```text
Issue: DEC-B18
Exact proposition under dispute: Run every T4 pair from complete equivalent starting state (CPU/EFLAGS/segments/ESP, all mapped memory covering host+guest writes, allocator, declared/reset stub state), separate from compared effects, audited, with pre-landing full-suite run and owner review before any status/xfail change (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Supporting evidence: GPT R1 Q1 (carry leak + host-write escape); Claude R2-P2 (emu.py:188-240@a21772b); R1-Probe 2 & R1-P4; DEC-A11 (UNANIMOUS).
Concrete counterexample or failure mode: Restoring watch ranges or guest RAM alone misses EFLAGS, host API writes, allocator drift, and closure stub state (OBJ-A12, OBJ-A20, OBJ-B28).
Necessary assumptions: Q-B05 full-suite check and owner presentation precede any xfail/status changes.
Practical consequences: Closes live T4 soundness defect across all T4 tests cleanly, allowing withdrawal of DEC-C16 rev 1.
Proposed resolution: Adopt DEC-B18 rev 2 alongside DEC-A11 (UNANIMOUS) and DEC-A08 rev 2; withdraw DEC-C16 rev 1.
Conditions under which you would change position: Discovery of an additional uncaptured host/emulator state channel (would expand restored state).
Classification: correctness-verification
```

```text
Issue: DEC-B19
Exact proposition under dispute: Reject fixed-displacement cross-object transfers spanning any legacy-placed object (global --legacy or per-object Unplaceable fallback) and require physical adjacency for every cross-piece ASM fallthrough (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 2.
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Supporting evidence: build.py:310-314@a21772b (Unplaceable fallback); R0 Probe 2 (0x2f73a->0x2f73c); GPT R2 P3 (0x202bb->0x202bc).
Concrete counterexample or failure mode: Guarding only global --legacy allows fixed-displacement branches across silently relocated objects; unguarded fallthrough breaks moved cuts (OBJ-B27, OBJ-C10).
Necessary assumptions: Planner tracks per-object placement mode and physical adjacency before emission.
Practical consequences: Complete plan-level defence in depth for both fixed-displacement spans and fallthrough edges.
Proposed resolution: Adopt DEC-B19 rev 2 alongside DEC-A05 rev 2 and DEC-B04 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-B20
Exact proposition under dispute: Measure Build A object flags, page/fixup records, and fixup types against war.exe before new placement paths; extend wc1.compare where they agree and present differences to owner (rev 1).
Competing positions: GPT CONDITIONAL (R2 P1/P2: enforce normalized typed semantics after raw occurrence validation; keep raw order & 1B last-page diagnostic); Claude ACCEPT; Gemini ACCEPT (R2).
Your position: CONDITIONAL rev 1 (changed from R2 ACCEPT on new evidence GPT R2 P1 & R2 P2).
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Supporting evidence: GPT R2 P1 (Build A@17733f9: flags/entry/stack/module flags/page map/fixup offsets/grouping multiset/8770 typed fixups/8773 occurrences agree; raw record order & last-page 1339 vs 1340 differ); GPT R2 P2 (LE.fixups_unique hides conflicting 2nd occurrence at (1, 53246)).
Concrete counterexample or failure mode: Enforcing raw serialization order breaks live Build A (OBJ-A19); checking only fixups_unique passes contradictory page-straddle records (OBJ-A21).
Necessary assumptions: DOS/4GW semantics depend on validated normalized typed fixups and loader attributes, not raw record order.
Practical consequences: Aligns comparator enforcement to exact post-measurement semantics proven on live Build A@17733f9.
Proposed resolution: Incorporate OBJ-A19 and OBJ-A21 into DEC-B20 rev 2, or adopt DEC-A03 rev 2 + DEC-C15 rev 2.
Conditions under which you would change position: Would ACCEPT rev 2 explicitly mandating raw physical fixup validation before deduplication and normalized typed comparison with diagnostic raw-order/1B-size deltas.
Classification: correctness-verification
```

```text
Issue: DEC-B21
Exact proposition under dispute: Watcom 10.0a CONST pad bytes are environment-dependent and excluded from proof-cache digests by normalization; no shape-based V4 exemption; any future exclusion needs independent extent/ownership/access evidence covering computed reads, identical matcher/place() policy, and ASM provider (rev 2).
Competing positions: Claude ACCEPT (rev 2 PROPOSED); GPT unvoted on rev 2 (REJECTED rev 1 over proof-cache vs research-digest boundary); Gemini unvoted.
Your position: CONDITIONAL rev 2.
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Supporting evidence: R0 Probes 3 & 7; Claude R1-P2 & R2-P1 (fixed-input stability in isolated runs); Gemini R2-Probe 1 (cross-session 73002f/760061/660061 at same path, stable 4/4 within session); GPT R1 Q2; DEC-B02 rev 2 (raw-byte proof binding + exact CONST matching).
Concrete counterexample or failure mode: Normalizing CONST pad bytes in an authoritative *proof-cache* key conflicts with DEC-B02 rev 2's raw-byte proof binding and exact CONST matching, allowing a mismatching object to hit a cached MATCH key.
Necessary assumptions: Authoritative proof keys bind exact raw bytes consumed by the build; non-authoritative research/candidate-grouping digests may normalize pad bytes.
Practical consequences: Reconciles GPT's DEC-B21 rev 1 rejection with Claude's exact-matching rule cleanly.
Proposed resolution: Revise DEC-B21 to rev 3 restricting CONST pad normalization to non-authoritative research/candidate-grouping digests (never authoritative proof keys) and noting cross-session environment sensitivity.
Conditions under which you would change position: Would ACCEPT once "proof-cache digests" is narrowed to non-authoritative research/grouping digests and cross-session sensitivity is acknowledged.
Classification: correctness-verification
```

```text
Issue: DEC-B22
Exact proposition under dispute: Fail fast in wc1.oldcc with exit-78 toolchain error when any compiler-facing argument exceeds a measured safe Windows-path length under Wine; optional staging requires proof of unchanged compiled bytes and include resolution (rev 1).
Competing positions: Claude ACCEPT (PROPOSED); GPT unvoted; Gemini unvoted.
Your position: ACCEPT rev 1.
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Supporting evidence: EV-3 report.md:64@17733f9 (rc=5 at ~130 chars); R1-Probe 4 (rc=-11 at ~129+ Windows chars); oldcc.py@17733f9; OBJ-C15, OBJ-A17.
Concrete counterexample or failure mode: Unchecked long paths crash wcc386 unpredictably; unverified staging risks altering include resolution or compiled bytes.
Necessary assumptions: Safe Windows-path ceiling is measured on installed Watcom 10.0a under Wine.
Practical consequences: Closes OBJ-C15 and OBJ-A17 alongside DEC-A12 rev 1, allowing withdrawal of DEC-C04 rev 1.
Proposed resolution: Adopt DEC-B22 rev 1 alongside DEC-A12 rev 1; withdraw DEC-C04 rev 1.
Conditions under which you would change position: Evidence that non-length path characters alone explain the crashes (refining the guard predicate).
Classification: implementation risk
```

```text
Issue: DEC-C01
Exact proposition under dispute: Retain three-level separation across FunctionMatch, RegionMatch/VerifiedRegion, and BuildAPlacementPlan across all six pipeline tools (rev 1).
Competing positions: GPT CONDITIONAL (use A03 rev 2 as materialization boundary; consumers use typed results without owning proof logic); Claude ACCEPT (noting integration receipt DEC-B03 rev 2); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (superseded); PROPOSE/ACCEPT DEC-C01 rev 2 (9d4022c2...).
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Supporting evidence: R0 Probe 1 & Claude R0 P2 (Sync 0x23170 false positive); OBJ-A09; DEC-A03 rev 2; DEC-B03 rev 2.
Concrete counterexample or failure mode: Rev 1 conflated BuildAPlacementPlan (preflight) with integrated Build A acceptance (materialization receipt) (OBJ-A09).
Necessary assumptions: Pipeline consumers distinguish levels via typed results without owning proof logic.
Practical consequences: DEC-C01 rev 2 incorporates GPT's and Claude's exact integration-receipt boundary across all 6 tools.
Proposed resolution: Reject DEC-C01 rev 1 as superseded; adopt DEC-C01 rev 2 (Section 2.3).
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-C02
Exact proposition under dispute: Land E0 bidirectional matcher in Stage 0 with function-scoped FunctionMatch bounds and trimmed_branch_target checks across all modes (rev 1).
Competing positions: GPT CONDITIONAL (explicit external obligations, strict raw admission, live gate, independent V4); Claude CONDITIONAL (decouple DEC-C03, exact data at cutover, explicit external obligations); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-B02 rev 2 and DEC-A02 rev 2).
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Supporting evidence: DEC-B02 rev 2 (e3dcf170...) and DEC-A02 rev 2 (87a63b4c...); OBJ-A03, OBJ-A10, OBJ-B20.
Concrete counterexample or failure mode: Rev 1 omitted strict raw-OMF admission and explicit external context obligations, and was coupled to withdrawn DEC-C03.
Necessary assumptions: DEC-B02 rev 2 and DEC-A02 rev 2 carry 100% of V1-V3 + strict admission + live cutover gate.
Practical consequences: Removes redundant proposition cleanly.
Proposed resolution: Withdraw/reject DEC-C02 rev 1 as superseded by DEC-B02 rev 2 and DEC-A02 rev 2.
Conditions under which you would change position: Only if neither DEC-B02 rev 2 nor DEC-A02 rev 2 were adopted.
Classification: correctness-verification
```

```text
Issue: DEC-C03
Exact proposition under dispute: Exempt 1..3B Watcom 10.0a CONST alignment gaps in E0 and Fix B3 under five syntactic/reference-scan conditions (Invariant V4) (rev 1).
Competing positions: GPT REJECT; Claude REJECT; Gemini REJECT (withdrawn R2).
Your position: REJECT rev 1 (maintain 3/3 REJECT).
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Supporting evidence: GPT R1 Q2 (computed indexed read of gap byte 0x8d vs 0x73 with all relocations outside gap); OBJ-A11, OBJ-B30.
Concrete counterexample or failure mode: Five conditions fail to exclude computed effective-address reads of a gap byte (GPT R1 Q2).
Necessary assumptions: Exact CONST matching holds at cutover; future exemptions require independent access proof (DEC-B21).
Practical consequences: Already 3/3 REJECT; cleanly retired.
Proposed resolution: Maintain 3/3 REJECT (superseded by DEC-B21 and DEC-A06).
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-C04
Exact proposition under dispute: Implement <=48 char short-path guard in wc1.oldcc and fix three t3_audit.py R3 provenance defects in Stage 0 (rev 1).
Competing positions: GPT CONDITIONAL (separate delivered R3; validate effective paths before numeric ceiling); Claude CONDITIONAL (drop R3; use measured envelope per DEC-B22); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-A12 rev 1 and DEC-B22 rev 1).
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Supporting evidence: EV-3 main@17733f9 (delivered R3 fixes); OBJ-A17; DEC-A12 rev 1 & DEC-B22 rev 1.
Concrete counterexample or failure mode: R3 clause is obsolete; arbitrary <=48 staging limit lacks include/output parity proof (OBJ-A17).
Necessary assumptions: DEC-A12 and DEC-B22 fully cover measured compiler-facing path protection.
Practical consequences: Retires obsolete rev 1 cleanly.
Proposed resolution: Withdraw/reject DEC-C04 rev 1 as superseded by DEC-A12 rev 1 and DEC-B22 rev 1.
Conditions under which you would change position: Only if neither DEC-A12 nor DEC-B22 were adopted.
Classification: implementation risk
```

```text
Issue: DEC-C05
Exact proposition under dispute: Stage-1 VerifiedRegion, BuildAPlacementPlan, Fix B1, Unified Fix B2 (in_place only), plus omfpatch interior _loc_ PUBDEF for cross-piece rel32 (rev 1).
Competing positions: GPT CONDITIONAL (decoded width, fallthrough, both legacy paths, A03 receipt, optional interior exports); Claude CONDITIONAL (no M2 interior PUBDEF, typed decode, receipt, DEC-B19 rev 2); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-B03/B04/B19/A05 rev 2 and DEC-B05).
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Supporting evidence: GPT R1 Q3 (prefixed rel8 width); Claude R0 P5 (0x2f6df->0x2f746 IDENTICAL without PUBDEF mutation); build.py:310-314@a21772b; OBJ-A09, OBJ-A13, OBJ-B23, OBJ-B27.
Concrete counterexample or failure mode: Mandated unneeded M2 C-object PUBDEF mutation and omitted per-object legacy fallback and integration receipts.
Necessary assumptions: DEC-B03/B04/B19/A05 rev 2 + DEC-B05 carry all surviving placement requirements.
Practical consequences: Removes stale duplicate while keeping all 7 B1/B2 functions unblocked.
Proposed resolution: Withdraw/reject DEC-C05 rev 1 as superseded by DEC-B03 rev 2, DEC-B04 rev 2, DEC-B05, DEC-B19 rev 2, and DEC-A05 rev 2.
Conditions under which you would change position: Only if superseding decisions dropped any rel8 class or fallthrough adjacency.
Classification: correctness-verification
```

```text
Issue: DEC-C06
Exact proposition under dispute: Prefer co-compiling shared-epilogue clusters into one contiguous multi-function VerifiedRegion under -5r (starting with Group B), using Fix B2 only while siblings remain ASM (rev 1).
Competing positions: GPT CONDITIONAL (A13 for early path, scope flags to proven TUs, owner checkpoint); Claude ACCEPT (same as DEC-B06); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-B06 rev 1, DEC-A13 rev 1, DEC-A05 rev 2, DEC-B04 rev 2).
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Supporting evidence: E1 Group B@e6150b8; Claude R0 P3; DEC-B06 rev 1; DEC-A13 rev 1; OBJ-A16.
Concrete counterexample or failure mode: Duplicate of DEC-B06 + DEC-A13 without rev 1's explicit owner checkpoint and early-path proof contract.
Necessary assumptions: Whole-TU preference and Group B promotion are fully carried by DEC-A05/B04 rev 2, DEC-B06, and DEC-A13.
Practical consequences: Removes redundant proposition cleanly.
Proposed resolution: Withdraw/reject DEC-C06 rev 1 as superseded by DEC-B06 rev 1, DEC-A13 rev 1, DEC-A05 rev 2, and DEC-B04 rev 2.
Conditions under which you would change position: None.
Classification: editorial
```

```text
Issue: DEC-C07
Exact proposition under dispute: Sequence Stage 2 (symbol_migrate, Wave 3R, BULLET.C, 4-5 ref-C bugfixes, governance) serially after Stage 1 and defer B3/E4/E6/E8 to Stage 3 (rev 1).
Competing positions: GPT REJECT; Claude REJECT; Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; now 3/3 REJECT; superseded by DEC-A01 and DEC-B01 rev 2).
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Supporting evidence: OBJ-A15, OBJ-B24, OBJ-B29 (parallel reconstruction; 61 needs_human rows require LLM naming/C; 3/5 xfails flipped under RAM restore per R1-Probe 2 / R1-P4).
Concrete counterexample or failure mode: Serializing Stage 2 idles ready M2 work (14 eligible + Group B) and mislabels 3/5 xfails as C bugs.
Necessary assumptions: DEC-A01 and DEC-B01 rev 2 preserve M2-first priority, parallel tracks, deferral of B3/E4/E6/E8, and on-demand rename tooling.
Practical consequences: Achieves 3/3 REJECT on stale rev 1 cleanly.
Proposed resolution: Withdraw/reject DEC-C07 rev 1 (3/3 REJECT); adopt DEC-B01 rev 2 alongside DEC-A01.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: DEC-C08
Exact proposition under dispute: Reject M2/default rollout of E4 omf_extract.py and defer conditionally to Stage 3 after fixing 8 defects including 64-fixup chunking (rev 1).
Competing positions: GPT CONDITIONAL (apply A07 rev 2; drop exhaustive flag sweep and 64-fixup limit); Claude ACCEPT; Gemini REJECT (rev 1 sign ambiguity).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-B09 rev 2, DEC-A07 rev 2, and DEC-B17 rev 1).
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Supporting evidence: GPT R1 Q3 (256-fixup record links, OBJ-A18); OBJ-A14/OBJ-B04 (Gate-2 owner approval); DEC-B17 (3/3 REJECT); DEC-B09/A07 rev 2.
Concrete counterexample or failure mode: Rev 1 had sign ambiguity, omitted owner Gate-2 authorization, and assumed an unproved 64-fixup limit.
Necessary assumptions: DEC-B09 rev 2 and DEC-A07 rev 2 carry all post-M2 E4 preconditions cleanly.
Practical consequences: Eliminates sign ambiguity and redundant E4 clauses.
Proposed resolution: Withdraw/reject DEC-C08 rev 1 as superseded by DEC-B09 rev 2, DEC-A07 rev 2, and DEC-B17 rev 1.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: DEC-C09
Exact proposition under dispute: Consolidate OMF32 parsing, persistent THREAD tracking, 64-fixup chunking, and record emission into wc1.omf before B3 or E4 (rev 1).
Competing positions: GPT CONDITIONAL (strict subset for supported transforms; measured linker limits, not 64-fixup cap; leave unrelated readers alone); Claude CONDITIONAL (supported subset; linker-tested limits; post-M2 only); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (superseded); PROPOSE/ACCEPT DEC-C09 rev 2 (c56d3bf3...).
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Supporting evidence: R0 Probe 5a (duplicated THREAD bug in omf_extract.py:258,823@e6150b8); GPT R1 Q3 (256-fixup record links, OBJ-A18).
Concrete counterexample or failure mode: Rev 1 mandated an unproved 64-fixup ceiling and overly broad serializer rewrite across unrelated permissive readers (OBJ-A18).
Necessary assumptions: Post-M2 Fix B3 and any later extraction pilot share one strict OMF32 subset codec.
Practical consequences: DEC-C09 rev 2 incorporates every GPT/Claude condition while binding both B3 and extraction to one strict codec post-M2.
Proposed resolution: Reject DEC-C09 rev 1 as superseded; adopt DEC-C09 rev 2 (Section 2.3).
Conditions under which you would change position: A linker-confirmed record-size limit (automatically handled by rev 2's linker-tested limit clause).
Classification: implementation risk
```

```text
Issue: DEC-C10
Exact proposition under dispute: Adopt Fix B3 in Stage 3B over unified OMF32 codec conditioned on Invariant V4, EXP-1 on SaveSlotPath, and rev-e5-02 guards (rev 1).
Competing positions: GPT CONDITIONAL (use A06 first; gap exclusion only with independent extent/access proof and shared policy); Claude CONDITIONAL (replace V4 with DEC-B21 rev 2); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-A06, DEC-B08, DEC-B21, and DEC-C09 rev 2).
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Supporting evidence: GPT R1 Q2 & OBJ-A11 (refuted V4); DEC-A06 (UNANIMOUS); DEC-B08 (UNANIMOUS); DEC-B21; DEC-C09 rev 2.
Concrete counterexample or failure mode: Rev 1 conditioned B3 on withdrawn Invariant V4 (OBJ-A11, OBJ-B30).
Necessary assumptions: DEC-A06 + DEC-B08 + DEC-B21 + DEC-C09 rev 2 completely specify post-M2 Fix B3 preconditions.
Practical consequences: Eliminates duplicate B3 decision carrying refuted V4.
Proposed resolution: Withdraw/reject DEC-C10 rev 1 as superseded by DEC-A06, DEC-B08, DEC-B21, and DEC-C09 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-C11
Exact proposition under dispute: Gate any multi-function T4 file consolidation strictly behind E6 in Stage 3C while freezing single-function wc1.cemu unchanged during M2 (rev 1).
Competing positions: GPT REJECT; Claude REJECT; Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; now 3/3 REJECT; superseded by DEC-A11, DEC-B18 rev 2, DEC-A08 rev 2, DEC-B12).
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Supporting evidence: src/playflic/player_reference.c@a21772b (20 fns tested today, OBJ-B25); GPT R1 Q1 & Claude R2-P2 (freezing cemu leaves EFLAGS/RAM asymmetry unfixed, OBJ-A12, OBJ-B21, OBJ-B28).
Concrete counterexample or failure mode: Freezing single-function cemu preserves a live T4 soundness defect, and file count is not the trust boundary.
Necessary assumptions: Immediate paired-state symmetry is in DEC-A11/DEC-B18 rev 2; demand-led E6 is in DEC-A08 rev 2/DEC-B12.
Practical consequences: Achieves 3/3 REJECT on flawed rev 1 cleanly.
Proposed resolution: Withdraw/reject DEC-C11 rev 1 (3/3 REJECT); rely on DEC-A11, DEC-B18 rev 2, DEC-A08 rev 2, and DEC-B12.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: DEC-C12
Exact proposition under dispute: Reject RFC §9.3 staircases/call-locality/auto-splits and adopt analyst-only cu_hypotheses.toml with hard shared_const_string_literal merges (rev 1).
Competing positions: GPT CONDITIONAL (shared literals need exclusion of sharing/pooling; actual base alignment; defer extra storage); Claude CONDITIONAL (same + measured precision); Gemini REJECT (rev 1 sign ambiguity).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-B13 rev 2 and DEC-A10).
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Supporting evidence: OBJ-A16, OBJ-B26; DEC-B13 rev 2 (74e56068...) and DEC-A10 (UNANIMOUS).
Concrete counterexample or failure mode: Sign ambiguity, unconditional shared_const_string_literal classification, and premature cu_hypotheses.toml schema.
Necessary assumptions: DEC-B13 rev 2 and DEC-A10 cover 100% of E8's refuted signals and premise-carrying graph.
Practical consequences: Removes duplicate/ambiguous rev 1 cleanly.
Proposed resolution: Withdraw/reject DEC-C12 rev 1 as superseded by DEC-B13 rev 2 and DEC-A10.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: DEC-C13
Exact proposition under dispute: Replace RFC §2.2.5 alignment table with E2's Watcom 10.0a/OW2 matrix, codify -5r as primary default family for contiguous CUs, and run EXP-2 (rev 1).
Competing positions: GPT CONDITIONAL (scope PARA to measured modes; keep -4r default; -5r as candidate); Claude CONDITIONAL (-5r as first-tried search family for 4B multi-function TUs, no historical/default claim); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (superseded); PROPOSE/ACCEPT DEC-C13 rev 2 (8b17fb93...).
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Supporting evidence: E2 alignment_matrix.json@e6150b8; E7 only_4r = 51 & R6 disclaimer@e6150b8; OBJ-A16, OBJ-B26, OBJ-C06.
Concrete counterexample or failure mode: "Primary default family" overclaimed beyond E7 evidence (51 only_4r functions) and left PARA unscoped (OBJ-A16, OBJ-B26).
Necessary assumptions: No other decision codifies the RFC §2.2.5 matrix replacement and EXP-2.
Practical consequences: DEC-C13 rev 2 incorporates all GPT/Claude conditions while preserving the RFC §2.2.5 correction.
Proposed resolution: Reject DEC-C13 rev 1 as superseded; adopt DEC-C13 rev 2 (Section 2.3).
Conditions under which you would change position: EXP-2 or new probes altering any measured matrix entry.
Classification: unsupported factual claim
```

```text
Issue: DEC-C15
Exact proposition under dispute: Stage-0 strict raw-OMF admission and hardened wc1.compare checking LE object flags, entry/stack, and fixup src_type after EXP-A03 parity validation (rev 1).
Competing positions: GPT CONDITIONAL (supported subset + A03 rev 2; validate raw fixups before normalizing; raw order diagnostic); Claude CONDITIONAL (nonzero checksum; measure first, escalate genuine mismatches); Gemini ACCEPT (rev 1 in R2).
Your position: REJECT rev 1 (superseded on new evidence GPT R2 P1 & R2 P2); PROPOSE/ACCEPT DEC-C15 rev 2 (a44884bb...).
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Supporting evidence: GPT R2 P1 (live Build A@17733f9 parity measurement); GPT R2 P2 (LE.fixups_unique hides conflicting 2nd occurrence at (1, 53246)); GPT R0 Q3; OBJ-A02, OBJ-A03, OBJ-A19, OBJ-A21.
Concrete counterexample or failure mode: Checking only LE.fixups_unique types misses contradictory page-straddle duplicates (OBJ-A21); enforcing raw record order breaks baseline Build A (OBJ-A19).
Necessary assumptions: DOS/4GW semantics depend on validated raw physical records + normalized typed fixups + loader attributes, not raw record order.
Practical consequences: DEC-C15 rev 2 incorporates GPT R2 P1/P2 and Claude's conditions completely, unifying the Stage-0 admission + comparator contract with DEC-A03 rev 2.
Proposed resolution: Reject DEC-C15 rev 1 as superseded; adopt DEC-C15 rev 2 (Section 2.3) alongside DEC-A03 rev 2.
Conditions under which you would change position: Proof that DOS/4GW depends on raw fixup order or the 1B last-page delta.
Classification: correctness-verification
```

```text
Issue: DEC-C16
Exact proposition under dispute: Reclassify 5 xfailed T4s in m2_inventory as 3 harness-asymmetry + 2 confirmed C bugs and harden run_pair with writable-RAM/dirty-page restore and stub reset (rev 1).
Competing positions: GPT REJECT (RAM/guest hook misses EFLAGS/host writes; 3-vs-2 split is observation-specific, not definitive C attribution); Claude CONDITIONAL (diagnosis only; restore CPU/EFLAGS/allocator per DEC-A11/DEC-B18 rev 2; Q-B05 first); Gemini PROPOSE (rev 1).
Your position: REJECT rev 1 (withdrawn; superseded by DEC-A11 and DEC-B18 rev 2).
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Supporting evidence: GPT R1 Q1 & OBJ-A20 (EFLAGS leak, host-write escape, premature C-bug attribution); Claude R2-P2; R1-Probe 2 & R1-P4 (observed diagnostic split); DEC-A11 & DEC-B18 rev 2.
Concrete counterexample or failure mode: Guest hooks miss host API writes, RAM-only restore misses EFLAGS, and attributing 0x23530/0x2fcfc before full-state + t4spec audit is premature (OBJ-A20).
Necessary assumptions: DEC-A11 and DEC-B18 rev 2 carry complete starting-state symmetry and gate status updates on post-landing pytest results + owner review.
Practical consequences: Retires flawed rev 1 cleanly while keeping R1-Probe 2 / R1-P4 strictly as diagnostic evidence.
Proposed resolution: Withdraw/reject DEC-C16 rev 1 as superseded by DEC-A11 (UNANIMOUS) and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

---

## Part B — Per-Issue Deliberation: Open Objections (63)

```text
Issue: OBJ-A01
Exact proposition under dispute: Production check_placed_plan iff claim and unconditional standalone IntroOpSyncSound wiring without partition-aware planning or link evidence.
Competing positions: GPT raised; Claude agrees (DEC-B03 rev 2); Gemini agrees (R0 Probe 1).
Your position: UPHOLD.
Supporting evidence: R0 Probe 1 & Claude R0 P2 (0x231d7/0x231e1 -> 0x2316c cross retained providers and fail NASM on standalone Sync 0x23170).
Concrete counterexample or failure mode: check_t3_buildable emits a false buildable verdict on standalone Sync, crashing Build A.
Necessary assumptions: None (directly reproduced).
Practical consequences: Mandates one partition-aware planner + actual integration receipts (DEC-B03/A03 rev 2) or Group B (DEC-B06/A13).
Proposed resolution: Close via DEC-B03 rev 2, DEC-A03 rev 2, DEC-B06, and DEC-A13.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A02
Exact proposition under dispute: Treating current wc1.compare IDENTICAL alone as a complete Build A placement oracle (RFC §§7.2, 13, 16).
Competing positions: GPT raised; Claude UPHOLD (OBJ-B19, DEC-B20); Gemini UPHOLD (R1-Probe 3, DEC-C15 rev 2).
Your position: UPHOLD.
Supporting evidence: GPT R0 Q3 & R1-Probe 3 (clearing OBJ_EXEC passes compare.py; fixup tuple omits src_type); GPT R2 P1/P2.
Concrete counterexample or failure mode: Corrupted object flags or fixup source types pass current wc1.compare silently.
Necessary assumptions: Enforced attributes are loader-relevant and baseline-measured (completed in GPT R2 P1).
Practical consequences: Strengthens wc1.compare in Stage 0 via DEC-A03 rev 2 and DEC-C15 rev 2.
Proposed resolution: Close via DEC-A03 rev 2, DEC-C15 rev 2, and aligned DEC-B20.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A03
Exact proposition under dispute: Adopting E0 directly as an authoritative object validator without strict raw-OMF admission and live cutover audit.
Competing positions: GPT raised; Claude UPHOLD (DEC-B02 rev 2); Gemini UPHOLD (DEC-C15 rev 2).
Your position: UPHOLD.
Supporting evidence: GPT R0 Q3 (decoded OMF projection drops explicit FRAME encodings and skips raw checksum/bounds checks); wc1/omf.py@a21772b.
Concrete counterexample or failure mode: Malformed or ambiguous raw OMF objects could receive MATCH before reaching wlink.
Necessary assumptions: Strict raw-OMF subset covers all live production T3 objects at cutover.
Practical consequences: Enforces strict raw-OMF admission and raw-byte proof binding in Stage 0.
Proposed resolution: Close via DEC-B02 rev 2, DEC-A02 rev 2, and DEC-C15 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A04
Exact proposition under dispute: Campaign D4 claim that E5 (Fix B3) unblocks arbitrary multi-function consolidation.
Competing positions: GPT raised; Claude agrees (OBJ-B05, DEC-B08); Gemini agrees (DEC-A06 UNANIMOUS).
Your position: UPHOLD.
Supporting evidence: E5-data-decoupling.md@e6150b8 (native SaveErrorDialog has wrong literal stride; real 3-segment test supplied one fn); candidate_ledger.json@a21772b (0/98 M2 yield).
Concrete counterexample or failure mode: Scheduling B3 ahead of M2 work wastes effort and adds Build A OMF-rewriting risk.
Necessary assumptions: None.
Practical consequences: Unanimously defers B3 to post-M2 need-driven adoption over whole verified segments (DEC-A06, DEC-B08).
Proposed resolution: Close via DEC-A06 (UNANIMOUS) and DEC-B08 (UNANIMOUS).
Conditions under which you would change position: A named not-done M2 blocker genuinely requiring B3.
Classification: unsupported factual claim
```

```text
Issue: OBJ-A05
Exact proposition under dispute: RFC §18 Phase D universal dependency on B3, extraction, and E6 before any consolidation pilot.
Competing positions: GPT raised; Claude agrees (DEC-B06, R0 P3); Gemini agrees (DEC-B06, DEC-A13).
Your position: UPHOLD.
Supporting evidence: E1 Group B@e6150b8; Claude R0 P3 (Group B builds MATCH + IDENTICAL needing zero B3/E4/E6).
Concrete counterexample or failure mode: Artificial bundling delays exact whole-TU pilots behind unrelated post-M2 work.
Necessary assumptions: Admission is per capability required by each candidate TU.
Practical consequences: Enables independent admission of exact whole-TU pilots like Group B (DEC-B06, DEC-A13).
Proposed resolution: Close via DEC-B06, DEC-A13, and DEC-A01 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-A06
Exact proposition under dispute: Treating -3r/-5r as defeating PARA alignment in E8 and testing alignment at function starts instead of candidate segment bases.
Competing positions: GPT raised; Claude agrees (DEC-B13 rev 2); Gemini agrees (DEC-B13 rev 2, DEC-C13 rev 2).
Your position: UPHOLD.
Supporting evidence: E2 alignment_matrix.json@e6150b8 (-3r/-5r -ot emit PARA SEGDEF); E0 ChooseCampaignDialog (first public follows leading bytes).
Concrete counterexample or failure mode: Testing alignment on a function start after leading bytes produces false CU merges/splits.
Necessary assumptions: Segment alignment applies to actual object contribution bases.
Practical consequences: Scopes non_16_aligned_start strictly to actual PARA segment bases in DEC-B13 rev 2 and DEC-A10.
Proposed resolution: Close via DEC-B13 rev 2, DEC-A10 (UNANIMOUS), and DEC-C13 rev 2.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-A07
Exact proposition under dispute: Relying on a bare VerifiedRegion isinstance check in E4 _require_verified without raw-input proof binding and post-transform verification.
Competing positions: GPT raised; Claude agrees (DEC-B09 rev 2, DEC-B14); Gemini agrees (DEC-A07 rev 2, DEC-B09 rev 2).
Your position: UPHOLD.
Supporting evidence: experiments/build_codegen/e4/omf_extract.py@e6150b8 (_require_verified checks type before context/raw binding); rev-e4-01.
Concrete counterexample or failure mode: Stale or forged VerifiedRegion objects pass type-only admission into an OMF transform.
Necessary assumptions: Any OMF transform binds proof to exact raw input bytes and re-verifies output + link.
Practical consequences: Enforced as mandatory post-M2 preconditions in DEC-A07 rev 2 and DEC-B09 rev 2.
Proposed resolution: Close via DEC-A07 rev 2, DEC-B09 rev 2, and DEC-B14 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A08
Exact proposition under dispute: Treating E6 Integrated mode as a direct production T4 audit replacement without parity and per-side admissible execution checks.
Competing positions: GPT raised; Claude agrees (DEC-A08 rev 2, DEC-B12); Gemini agrees (DEC-A08 rev 2).
Your position: UPHOLD.
Supporting evidence: E6-multi-t4.md@e6150b8; tools/wc1/t4spec.py@17733f9 (policy and audit log differ from prototype).
Concrete counterexample or failure mode: Shared process state, boundary mistakes, or stale compiles grant undeserved T4 credit.
Necessary assumptions: Cited multi-function T4 requires production t4spec audit parity and per-side boundaries.
Practical consequences: Enforced by DEC-A08 rev 2 before any cited multi-function witness is admitted.
Proposed resolution: Close via DEC-A08 rev 2 and DEC-A11 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-A09
Exact proposition under dispute: Treating a clean placement plan (preflight) as the Build A integrated-acceptance boundary (DEC-B03/C01/C05 rev 1).
Competing positions: GPT raised; Claude UPHOLD (DEC-B03 rev 2); Gemini UPHOLD (DEC-C01 rev 2, DEC-C05 withdrawn).
Your position: UPHOLD.
Supporting evidence: R0 Probe 1 (Sync preflight hole); GPT R0 Q3 & R2 P1-P2 (compare gaps).
Concrete counterexample or failure mode: Preflight acceptance without actual assemble/link/provider/hardened-compare receipts admits broken or loader-divergent builds.
Necessary assumptions: Promotion requires recorded actual integration receipts.
Practical consequences: Cleanly separates preflight from materialization across DEC-A03/B03/C01 rev 2.
Proposed resolution: Close via DEC-A03 rev 2, DEC-B03 rev 2, and DEC-C01 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A10
Exact proposition under dispute: Forcing UNSUPPORTED on all cross-function edges in FunctionMatch (DEC-C02 rev 1) and restricting matcher changes solely to losing matches.
Competing positions: GPT raised; Claude UPHOLD (DEC-B02 rev 2); Gemini UPHOLD (DEC-C02 withdrawn, DEC-B02/A02 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: E1 Group B geometry; E2 Cause B (9 false UNSUPPORTED rejections on identical non-contiguous multi-function code).
Concrete counterexample or failure mode: Blanket UNSUPPORTED destroys diagnostic distinctions on valid scoped bodies with known external context edges.
Necessary assumptions: Function-scoped external obligations remain diagnostic only and never grant placement.
Practical consequences: FunctionMatch bounds checks to verified function extent and carries explicit external context obligations.
Proposed resolution: Close via DEC-A02 rev 2, DEC-B02 rev 2, and withdrawal of DEC-C02 rev 1.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A11
Exact proposition under dispute: Treating DEC-C03/V4's five syntactic/reference-scan conditions as sufficient to exempt Watcom 10.0a CONST alignment gaps.
Competing positions: GPT raised; Claude UPHOLD (OBJ-B30, DEC-B21 rev 2); Gemini UPHOLD (DEC-C03 & DEC-C10 withdrawn).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q2 (computed effective-address read of gap byte 0x8d vs 0x73 while all explicit relocations sit outside the gap).
Concrete counterexample or failure mode: Computed read accesses a V4-exempted gap byte, causing behavioral drift if Build B changes provider.
Necessary assumptions: Source-data equivalence requires independent extent/ownership/access proof before excluding any byte.
Practical consequences: Exact CONST matching holds at cutover; V4 is permanently withdrawn (3/3 REJECT).
Proposed resolution: Close via 3/3 REJECT of DEC-C03 rev 1, withdrawal of DEC-C10 rev 1, DEC-B02 rev 2, and updated DEC-B21.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A12
Exact proposition under dispute: Limiting T4 paired-state restoration to memory only (DEC-B07 rev 1) or freezing single-function cemu during M2 (DEC-C11 rev 1).
Competing positions: GPT raised; Claude UPHOLD (DEC-B07 withdrawn, DEC-B18 rev 2, OBJ-B28); Gemini UPHOLD (DEC-C11/C16 withdrawn, DEC-A11 UNANIMOUS).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q1 (carry-flag false pass + host-write escape); Claude R2-P2 (emu.py:188-240 never resets EFLAGS); R1-Probe 2 & R1-P4.
Concrete counterexample or failure mode: Unreset EFLAGS enables carry-only false passes; guest hooks miss host API writes; freezing cemu leaves both live.
Necessary assumptions: Full paired starting state covers CPU/EFLAGS, all mapped memory, allocator, and declared/reset stub state.
Practical consequences: Immediately hardens all T4 runs via DEC-A11 and DEC-B18 rev 2.
Proposed resolution: Close via DEC-A11 (UNANIMOUS), DEC-B18 rev 2, DEC-A08 rev 2, and withdrawal of DEC-B07/DEC-C11/DEC-C16.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A13
Exact proposition under dispute: Hardcoding next_ip = ia + 2 for rel8 and mandating M2 interior rel32 PUBDEF synthesis (DEC-C05 rev 1), or leaving literal-byte checks implicit (DEC-B04 rev 1).
Competing positions: GPT raised; Claude UPHOLD (DEC-B04 rev 2); Gemini UPHOLD (DEC-C05 withdrawn, DEC-A05/B04 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q3 (prefix changes rel8 next-IP by 1); Claude R0 P5 (0x2f6df->0x2f746 IDENTICAL without C-object PUBDEF mutation).
Concrete counterexample or failure mode: Prefixed rel8/loop instructions compute wrong displacement under ia+2; unproved interior exports risk symbol/frame errors.
Necessary assumptions: Exact decoded length, prefixes, next-IP, and assembled-byte equality are checked on every cross-object transfer.
Practical consequences: Unified in-place transfer rule avoids M2 C-object mutation and closes prefix/width bugs.
Proposed resolution: Close via DEC-A05 rev 2, DEC-B04 rev 2, and withdrawal of DEC-C05 rev 1.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A14
Exact proposition under dispute: Omitting explicit owner authorization for Gate-2 / match --all semantics changes from DEC-C08 rev 1's later extraction prerequisites.
Competing positions: GPT raised; Claude agrees (OBJ-B04, DEC-B09 rev 2); Gemini UPHOLD (DEC-C08 withdrawn, DEC-A07/B09 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: match.py:368-390@a21772b (match --all fails src files with mismatching publics); AGENTS.md fixed finish-line rule.
Concrete counterexample or failure mode: Promotion adapter admitting partial canonical TUs without owner approval silently alters Gate 2.
Necessary assumptions: Read-only partial diagnostics remain permitted; Gate-2 changes require owner approval.
Practical consequences: Codified explicitly in both DEC-A07 rev 2 and DEC-B09 rev 2.
Proposed resolution: Close via DEC-A07 rev 2, DEC-B09 rev 2, and withdrawal of DEC-C08 rev 1.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-A15
Exact proposition under dispute: Serializing routine M2 reconstruction behind generic placement work (DEC-C07 rev 1, Claude R0 S5) and turning probe diagnoses into inventory status labels (DEC-B16 rev 1).
Competing positions: GPT raised; Claude UPHOLD (DEC-B01 rev 2, DEC-B16 withdrawn, OBJ-B29); Gemini UPHOLD (DEC-C07/C16 withdrawn, DEC-B01 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: EV-3 main@17733f9 (14 eligible functions now); Claude R0 P3 (Group B independent route); DEC-A13.
Concrete counterexample or failure mode: Serializing reconstruction idles ready work; hard-coding probe diagnoses bypasses post-landing test authority.
Necessary assumptions: Parallel tracks run under existing gates; status updates follow landed proofs/tests.
Practical consequences: Routine reconstruction and Group B run in parallel with Stage-0/1 soundness work.
Proposed resolution: Close via DEC-A01 (UNANIMOUS), DEC-B01 rev 2, DEC-A13, and 3/3 REJECT of DEC-B16/DEC-C07.
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-A16
Exact proposition under dispute: Treating shared_const_string_literal as a hard CU merge (DEC-C12 rev 1), coupling alignment to a -5r default (DEC-C13 rev 1), and omitting producer premises on shared_epilogue (DEC-B13 rev 1).
Competing positions: GPT raised; Claude UPHOLD (DEC-B13 rev 2); Gemini UPHOLD (DEC-C12 withdrawn, DEC-C13 rev 2 proposed).
Your position: UPHOLD.
Supporting evidence: E7 only_4r = 51 & R6 disclaimer@e6150b8; E8@e6150b8 (does not exclude external sharing/pooling); E2 PARA SEGDEF.
Concrete counterexample or failure mode: False historical CU merges from externally shared literals or misleading default-flag claims overriding 51 only_4r functions.
Necessary assumptions: Every CU signal carries explicit premises; -4r stays project default while -5r is a candidate family.
Practical consequences: Tightens CU epistemic rigor and alignment policy in DEC-B13 rev 2 and DEC-C13 rev 2.
Proposed resolution: Close via DEC-B13 rev 2, DEC-C13 rev 2, and withdrawal of DEC-C12 rev 1.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-A17
Exact proposition under dispute: Bundling delivered t3_audit R3 fixes with an unmeasured <=48 staging limit (DEC-C04 rev 1) and blurring raw-artifact proof binding with staging/scheduling fingerprints.
Competing positions: GPT raised; Claude UPHOLD (DEC-B02 rev 2, DEC-B22); Gemini UPHOLD (DEC-C04 withdrawn, DEC-A12 & DEC-B22 accepted).
Your position: UPHOLD.
Supporting evidence: EV-3 main@17733f9 (R3 delivered); oldcc.py@17733f9; GPT R0 Q3 (parsed projection lossy vs raw bytes).
Concrete counterexample or failure mode: Arbitrary short staging can still pass long compiler args or alter include identity; parsed projections cannot substitute for raw-byte proof binding.
Necessary assumptions: Path guard uses measured limits over all effective compiler-facing arguments; staging requires parity proof.
Practical consequences: Cleanly separates measured oldcc protection (DEC-A12/B22) from raw-byte proof binding (DEC-B02 rev 2).
Proposed resolution: Close via DEC-A12, DEC-B22, DEC-B02 rev 2, and withdrawal of DEC-C04 rev 1.
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-A18
Exact proposition under dispute: Treating missing 64-fixup FIXUPP32 chunking as an established production-blocking overflow and mandating broad serializer consolidation across unrelated readers (DEC-C08/C09 rev 1).
Competing positions: GPT raised; Claude agrees (DEC-B09 rev 2); Gemini UPHOLD (DEC-C08 withdrawn, DEC-C09 rev 2 proposed).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q3 (256-fixup FIXUPP32 record links on tested wlink); R0 Probe 5a-5b & GPT R1 Q4 (THREAD and non-_TEXT PUBDEF defects remain confirmed).
Concrete counterexample or failure mode: Mandating a fixed 64-fixup cap and rewriting unrelated permissive readers imposes unjustified scope.
Necessary assumptions: Record-size limits are validated against actual linkers for the supported subset.
Practical consequences: Scopes DEC-C09 rev 2 strictly to one shared OMF32 subset codec for post-M2 B3/extraction with linker-tested limits.
Proposed resolution: Close via DEC-C09 rev 2, DEC-B09 rev 2, and withdrawal of DEC-C08 rev 1.
Conditions under which you would change position: A tested linker failing on a specific FIXUPP32 size (handled by DEC-C09 rev 2).
Classification: unsupported factual claim
```

```text
Issue: OBJ-A19
Exact proposition under dispute: DEC-B20 rev 1 requiring equality on raw page/fixup records when live Build A@17733f9 differs in raw fixup serialization order and 1B last-page length.
Competing positions: GPT raised (R2 P1); Claude unvoted; Gemini UPHOLD (moved DEC-B20 to CONDITIONAL, proposed DEC-C15 rev 2, accepted DEC-A03 rev 2).
Your position: UPHOLD.
Supporting evidence: GPT R2 P1 (Build A@17733f9 vs war.exe: flags/entry/stack/module flags/page map/fixup offsets/grouping multiset/8770 typed fixups/8773 physical occurrences agree; raw record order & last-page 1339 vs 1340 differ).
Concrete counterexample or failure mode: Raw fixup serialization equality would falsely reject live identical Build A.
Necessary assumptions: DOS/4GW semantics do not depend on raw record serialization order after raw validation and normalized typed equality.
Practical consequences: Enforces validated normalized typed semantics while reporting raw order & 1B size as diagnostics.
Proposed resolution: Close via DEC-A03 rev 2, DEC-C15 rev 2, and aligned DEC-B20 rev 2.
Conditions under which you would change position: Proof that DOS/4GW semantics depend on raw fixup order or 1B last-page length.
Classification: correctness-verification
```

```text
Issue: OBJ-A20
Exact proposition under dispute: DEC-B18 rev 1 claiming mapped-memory restoration alone yields identical complete state, and DEC-C16 rev 1 prescribing RAM/dirty-page hooks plus definitive 5-row C classifications.
Competing positions: GPT raised; Claude addressed in DEC-B18 rev 2; Gemini UPHOLD (DEC-C16 withdrawn, DEC-B18 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q1 (carry-flag leak + host API write escaping guest hook); Claude R2-P2 (emu.py:188-240); R1-Probe 2 & R1-P4 (observation-specific RAM-restore split).
Concrete counterexample or failure mode: Guest hooks miss host API writes; RAM-only restore misses EFLAGS and undeclared host objects; classifying 0x23530/0x2fcfc before full-state + t4spec audit is premature.
Necessary assumptions: Complete paired-state accounting (DEC-A11 + DEC-B18 rev 2) precedes formal status/root-cause reclassification.
Practical consequences: Retires DEC-C16 rev 1 and aligns all three Architects on DEC-A11 + DEC-B18 rev 2.
Proposed resolution: Close via DEC-A11 (UNANIMOUS), DEC-B18 rev 2, and withdrawal of DEC-C16 rev 1.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-A21
Exact proposition under dispute: Minimal reading of DEC-C15 rev 1 checking fixup src_type only on LE.fixups_unique, whose first-wins collapse hides conflicting page-straddling duplicates.
Competing positions: GPT raised (R2 P2); Claude unvoted; Gemini UPHOLD (revised DEC-C15 to rev 2; accepted DEC-A03 rev 2; conditioned DEC-B20).
Your position: UPHOLD.
Supporting evidence: GPT R2 P2 (mutating 2nd physical occurrence at (1, 53246), file offset 0x6c95, from src_type=7 to 6 leaves all 8,770 LE.fixups_unique entries unchanged).
Concrete counterexample or failure mode: Contradictory page-straddling fixup records pass a fixups_unique-only typed comparator silently.
Necessary assumptions: All 3 original page-straddling duplicate pairs in war.exe agree (confirmed by GPT R2 P1: 8,773 physical -> 8,770 unique, 0 conflicts).
Practical consequences: Mandates validating all raw physical fixup occurrences before collapsing agreeing page-straddle duplicates.
Proposed resolution: Close via DEC-A03 rev 2, DEC-C15 rev 2, and aligned DEC-B20 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B01
Exact proposition under dispute: Claim in m2_inventory (DG-03), e1a4178, and summary.md §18.9 that Group B requires B2 cut-boundary relative branch emission.
Competing positions: Claude raised; GPT agrees (DEC-A13); Gemini agrees (DEC-B06, DEC-A13).
Your position: UPHOLD.
Supporting evidence: Claude R0 P3 (Group B builds MATCH + IDENTICAL as one TU on current main tools without B2).
Concrete counterexample or failure mode: Treating Group B as B2-blocked delays +3 DONE unnecessarily behind generic B2.
Necessary assumptions: Group B satisfies DEC-A13's strict commit-bound RegionMatch, dual-compiler, typed Build A, and owner checks.
Practical consequences: Decouples Group B from generic B2 immediately.
Proposed resolution: Close via DEC-B06 rev 1 and DEC-A13 rev 1.
Conditions under which you would change position: Group B failing DEC-A13 strict checks.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B02
Exact proposition under dispute: Campaign summary.md §18.9 and decisions.md claiming E0–E8 cover RFC production mechanisms while omitting any Fix B2 implementation or test.
Competing positions: Claude raised; GPT agrees (DEC-A05 rev 2); Gemini agrees (R0 Probe 1, DEC-B04 rev 2).
Your position: UPHOLD.
Supporting evidence: Zero Fix B2 code/tests under experiments/build_codegen/@e6150b8; R0 Probe 1 & Claude R0 P2/P5 (B2 blocks 4 M2 fns; B3/E4 block 0).
Concrete counterexample or failure mode: Production adopts zero-yield B3/E4 ahead of M2-blocking B2.
Necessary assumptions: None.
Practical consequences: Admits unified B2 into M2 infrastructure and defers B3/E4.
Proposed resolution: Close via DEC-B01 rev 2, DEC-B04 rev 2, and DEC-A05 rev 2.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-B03
Exact proposition under dispute: RFC §7.2 modeling Fix B2 solely as ASM branches into a cut interior, missing ASM->ASM cut-spanning and ASM->C-entry rel8 transfers.
Competing positions: Claude raised (mirroring OBJ-C02); GPT agrees (DEC-A05 rev 2); Gemini agrees.
Your position: UPHOLD.
Supporting evidence: R0 Probe 1 & Claude R0 P2/P5 (Sync 0x231d7/0x231e1->0x2316c; EndCheckSurvive->MissionDefeat 0x2f73c entry).
Concrete counterexample or failure mode: Interior-only B2 leaves MissionDefeat unbuildable and repeats Sync false positives.
Necessary assumptions: None.
Practical consequences: Unified three-class cross-object transfer rule adopted in DEC-B04/A05 rev 2.
Proposed resolution: Close via DEC-B04 rev 2, DEC-A05 rev 2, and DEC-B19 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B04
Exact proposition under dispute: Campaign D5/D6 proposing scoped/conditional E3/E4 adoption without addressing the Gate-2 / match --all finish-line governance conflict.
Competing positions: Claude raised; GPT agrees (OBJ-A14, DEC-A07 rev 2); Gemini agrees (OBJ-C14, DEC-B09 rev 2).
Your position: UPHOLD.
Supporting evidence: match.py:368-390@a21772b (_match_one fails any src= TU with mismatching publics); AGENTS.md fixed finish-line rule.
Concrete counterexample or failure mode: Admitting partial canonical TUs without owner approval silently alters Gate 2.
Necessary assumptions: Only the user may modify Gate-2 semantics.
Practical consequences: Explicit owner Gate-2 authorization is required in DEC-A07 rev 2 and DEC-B09 rev 2.
Proposed resolution: Close via DEC-A07 rev 2 and DEC-B09 rev 2.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-B05
Exact proposition under dispute: Campaign D4 adopting Fix B3 and sequencing PR3 ahead of M2-blocking work.
Competing positions: Claude raised; GPT agrees (OBJ-A04, DEC-A06); Gemini agrees (OBJ-C04, DEC-B08).
Your position: UPHOLD.
Supporting evidence: candidate_ledger.json@a21772b (0/98 M2 DONE from B3; SaveErrorDialog 0x1aca8 already DONE as T4, -os outlier).
Concrete counterexample or failure mode: Adds Build A OMF-rewriting complexity for zero M2 progress.
Necessary assumptions: None.
Practical consequences: Fix B3 is unanimously deferred post-M2 (DEC-A06, DEC-B08).
Proposed resolution: Close via DEC-A06 (UNANIMOUS), DEC-B08 (UNANIMOUS), and DEC-B01 rev 2.
Conditions under which you would change position: A named not-done M2 function genuinely requiring B3.
Classification: implementation risk
```

```text
Issue: OBJ-B06
Exact proposition under dispute: Inventory DG-04 and AGENTS.md calling all 5 xfailed T4 tests "real ref-C divergences".
Competing positions: Claude raised; GPT agrees (OBJ-A20, DEC-A11); Gemini agrees (R1-Probe 2, OBJ-C12).
Your position: UPHOLD.
Supporting evidence: Claude R0 P4 & R1-P4 and Gemini R1-Probe 2 (3/5 xfails pass under RAM restore; byte-exact C fails identically without restore).
Concrete counterexample or failure mode: Wastes effort rewriting correct C while leaving T4 harness asymmetry unfixed.
Necessary assumptions: Formal reclassification follows full paired-state landing (DEC-B18 rev 2) and post-change pytest runs.
Practical consequences: Prioritizes full paired-state symmetry in cemu.run_pair immediately.
Proposed resolution: Close via DEC-A11 (UNANIMOUS) and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B07
Exact proposition under dispute: Campaign summary.md §18.1 claiming -5r is the "unifying root cause" of original compiler flags.
Competing positions: Claude raised; GPT agrees (OBJ-A16); Gemini agrees (DEC-C13 rev 2).
Your position: UPHOLD.
Supporting evidence: E7@e6150b8 (only_4r = 51; R6 preservation disclaimer); E2@e6150b8 (-3r also spaces at 4B).
Concrete counterexample or failure mode: Conflates spacing compatibility with original flags and could justify a harmful global -5r default.
Necessary assumptions: None.
Practical consequences: Keeps -4r default and treats -5r as a candidate search family (DEC-C13 rev 2).
Proposed resolution: Close via DEC-C13 rev 2 and DEC-A09 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B08
Exact proposition under dispute: RFC §2.2.4 claiming "OMF format does not support external 8-bit relocations".
Competing positions: Claude raised; GPT agrees; Gemini agrees.
Your position: UPHOLD.
Supporting evidence: Claude R0 P5 log (NASM error: "OBJ format can only handle 16- or 32-byte relocations"); OMF FIXUPP defines location type 0 (untested in wlink).
Concrete counterexample or failure mode: Misattributes a NASM OBJ backend restriction to the OMF specification itself.
Necessary assumptions: None; Build A B2 sidesteps external rel8 regardless.
Practical consequences: Editorial fix in revised RFC §2.2.4.
Proposed resolution: Update RFC §2.2.4 wording to attribute the restriction to NASM's OBJ backend.
Conditions under which you would change position: None.
Classification: editorial
```

```text
Issue: OBJ-B09
Exact proposition under dispute: RFC §16 mandating a heavyweight CandidateRegion->VerifiedRegion->PlacementPlan type hierarchy before B1/B2.
Competing positions: Claude raised (DEC-B14 UNANIMOUS); GPT accepted DEC-B14; Gemini accepted DEC-B14.
Your position: UPHOLD (retaining lightweight non-forgeable VerifiedRegion + typed plan/receipt boundaries per DEC-B14 & DEC-C01 rev 2).
Supporting evidence: Claude R0 P5/P6 (~30 lines of planner logic); DEC-B14 (UNANIMOUS).
Concrete counterexample or failure mode: Speculative class hierarchy delays B1/B2 with zero extra verification soundness.
Necessary assumptions: Safety comes from matcher-minted VerifiedRegion + actual integration receipt.
Practical consequences: Already settled unanimously via DEC-B14.
Proposed resolution: Close via DEC-B14 (UNANIMOUS), DEC-B03 rev 2, and DEC-C01 rev 2.
Conditions under which you would change position: None.
Classification: maintainability
```

```text
Issue: OBJ-B10
Exact proposition under dispute: Campaign summary.md §18.9 PR1 claiming "Zero T3 regressions guaranteed (519/519)" on a stale population with 0 leading-byte/data-pointer cases.
Competing positions: Claude raised; GPT agrees (DEC-A02 rev 2); Gemini agrees (R0 Probe 4; DEC-B02 rev 2).
Your position: UPHOLD.
Supporting evidence: Population grew 519 -> 539 (main@17733f9); 0 current T3s cover leading bytes or local-data pointers; live cutover gate required.
Concrete counterexample or failure mode: Stale snapshot misses regressions on new T3s or untested E0 paths.
Necessary assumptions: Fresh full-population make verify + E0's 55 controls gate cutover.
Practical consequences: Enforced by DEC-B02 rev 2 and DEC-A02 rev 2.
Proposed resolution: Close via DEC-B02 rev 2 and DEC-A02 rev 2.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B11
Exact proposition under dispute: Using E7's "13 buildable T3 opportunities" metric from incomplete check_t3_buildable as a production oracle.
Competing positions: Claude raised; GPT agrees (OBJ-A01, DEC-A03 rev 2); Gemini agrees (R0 Probe 1, DEC-B03 rev 2).
Your position: UPHOLD.
Supporting evidence: R0 Probe 1 & Claude R0 P2/P5 (check_t3_buildable misses cut-spanning & cut-entry rel8).
Concrete counterexample or failure mode: Wave4/batch_driver waste cycles promoting unbuildable candidates until make verify fails.
Necessary assumptions: None.
Practical consequences: All callers migrate to one planner plan(p, regions) + actual integration receipts (DEC-B03 rev 2).
Proposed resolution: Close via DEC-B03 rev 2 and DEC-C01 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B12
Exact proposition under dispute: Generalizing E8 library/synthetic corpus precision (B1/A) as game-CU classification accuracy.
Competing positions: Claude raised; GPT agrees (DEC-A10 UNANIMOUS); Gemini agrees (DEC-B13 rev 2).
Your position: UPHOLD.
Supporting evidence: E8-cu-boundaries.md@e6150b8 (B1 dominated by Watcom library/intxa386 asm; A synthetic; zero16 unverified in game code).
Concrete counterexample or failure mode: Over-trusting synthetic precision leads to automated or false game CU boundaries.
Necessary assumptions: None.
Practical consequences: Restricts CU recovery strictly to analyst-facing premise-carrying guidance (DEC-B13 rev 2, DEC-A10).
Proposed resolution: Close via DEC-A10 (UNANIMOUS) and DEC-B13 rev 2.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B13
Exact proposition under dispute: RFC §4.2/§9.1 compilation_units.toml and §10.2 13-field persistent provenance store as near-term deliverables.
Competing positions: Claude raised (DEC-B15 UNANIMOUS); GPT accepted DEC-B15; Gemini accepted DEC-B15 (and withdrew DEC-C12's cu_hypotheses.toml).
Your position: UPHOLD.
Supporting evidence: Zero M2 consumers; RFC §4.1 warns against a second metadata DB; DEC-B15 (UNANIMOUS).
Concrete counterexample or failure mode: Duplicate metadata schemas drift from analysis/symbols/*.toml during M2.
Necessary assumptions: None.
Practical consequences: Already deferred unanimously via DEC-B15 and DEC-B13 rev 2.
Proposed resolution: Close via DEC-B15 (UNANIMOUS) and DEC-B13 rev 2.
Conditions under which you would change position: None.
Classification: maintainability
```

```text
Issue: OBJ-B18
Exact proposition under dispute: Characterizing all 5 xfailed T4 tests as "5 real ref-C behavioural divergences" (DEC-C07 rev 1, DG-04, GPT R0 §8).
Competing positions: Claude raised (R1-P4); GPT agrees (OBJ-A20); Gemini UPHOLD (R1-Probe 2, DEC-C07/C16 withdrawn).
Your position: UPHOLD.
Supporting evidence: R1-Probe 2 & Claude R1-P4 (3/5 xfails—0x231cc, 0x23668, 0x23ae0—pass under RAM restore).
Concrete counterexample or failure mode: Rewriting already-correct C while leaving T4 paired-state asymmetry unfixed.
Necessary assumptions: Formal status changes follow DEC-B18 rev 2 landing and post-change pytest runs under owner review.
Practical consequences: Retires the "5 real C bugs" framing across all three Architects.
Proposed resolution: Close via DEC-A11 (UNANIMOUS), DEC-B18 rev 2, and withdrawal of DEC-C07/DEC-C16.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B19
Exact proposition under dispute: Framing current Build A wc1.compare IDENTICAL as a complete Build A verification check (RFC §13.1, Claude R0 I-3(c)/I-6).
Competing positions: Claude raised against self; GPT UPHOLD (OBJ-A02, R2 P1/P2); Gemini UPHOLD (R1-Probe 3, DEC-C15 rev 2).
Your position: UPHOLD.
Supporting evidence: compare.py@17733f9 (flags printed, not compared; fixup tuple omits src_type); GPT R0 Q3 & R2 P1/P2.
Concrete counterexample or failure mode: Corrupted LE object flags, fixup types, or conflicting duplicate fixups pass current compare.py.
Necessary assumptions: Enforced checks use measured-identical normalized semantics after raw occurrence validation (OBJ-A19, OBJ-A21).
Practical consequences: Strengthens wc1.compare via DEC-A03 rev 2, DEC-C15 rev 2, and aligned DEC-B20.
Proposed resolution: Close via DEC-A03 rev 2, DEC-C15 rev 2, and aligned DEC-B20.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B20
Exact proposition under dispute: Coupling Stage-0 E0 matcher cutover (DEC-C02 rev 1) to Invariant V4 / DEC-C03 / EXP-1.
Competing positions: Claude raised; GPT agrees (DEC-A02 rev 2); Gemini UPHOLD (DEC-C02/C03 withdrawn; DEC-B02 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: R0 Probe 4 & Claude R0 P1 (539/539 T3s pass exact E0 matching without V4); build.py:94-104@a21772b.
Concrete counterexample or failure mode: Delays a zero-regression soundness upgrade behind an unproven CONST gap rule.
Necessary assumptions: Exact CONST matching holds at cutover; extern-literal idiom remains available.
Practical consequences: Decouples Stage-0 E0 cutover completely from CONST pad handling.
Proposed resolution: Close via DEC-B02 rev 2, DEC-A02 rev 2, and withdrawal of DEC-C02/DEC-C03.
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-B21
Exact proposition under dispute: Deferring paired-state reset to post-M2 multi-function T4 (DEC-A08/C11 rev 1) despite live single-function run_pair defects.
Competing positions: Claude raised; GPT UPHOLD (DEC-A08 rev 2, DEC-A11); Gemini UPHOLD (DEC-C11 withdrawn, DEC-B18 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: Claude R1-P4 & R2-P2 (emu.py:188-240 never resets EFLAGS); Gemini R1-Probe 2; GPT R1 Q1.
Concrete counterexample or failure mode: Current T4 proofs keep running on asymmetric inputs, admitting false divergences and false passes.
Necessary assumptions: Complete paired-state symmetry applies to all current T4s immediately, independent of E6.
Practical consequences: Elevates DEC-A11 + DEC-B18 rev 2 into immediate M2 soundness work.
Proposed resolution: Close via DEC-A11 (UNANIMOUS), DEC-B18 rev 2, DEC-A08 rev 2, and withdrawal of DEC-C11.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B22
Exact proposition under dispute: Characterizing Watcom 10.0a CONST padding as universally "non-deterministic / flaky across runs" and scheduling V4 in Stage 0 (OBJ-C01, DEC-C03 rev 1).
Competing positions: Claude raised (R1-P2/R2-P1: path-dependent, fixed-input stable); GPT agrees on deferring V4 (OBJ-A11); Gemini UPHOLD on decoupling V4 and refining mechanism to environment-dependent (noting R2-Probe 1 cross-session variation).
Your position: UPHOLD in substance (V4 withdrawn; mechanism refined to environment-dependent across paths and sessions, stable within a fixed session/prefix).
Supporting evidence: Claude R1-P2 & R2-P1 (5/5 identical at fixed path); Gemini R2-Probe 1 (4/4 identical 660061 within session vs 73002f/760061 across sessions at same path).
Concrete counterexample or failure mode: Misstating root cause yields wrong mitigation; normalizing pad bytes inside authoritative proof keys conflicts with exact CONST matching (DEC-B21 condition).
Necessary assumptions: Mechanism nuance does not change exact CONST matching at cutover or raw-byte proof keys.
Practical consequences: Removes V4 from Stage 0 and refines wording cleanly.
Proposed resolution: Close via DEC-B02 rev 2, 3/3 REJECT of DEC-C03 rev 1, and DEC-B21 rev 3 restricting normalization to non-authoritative research/grouping digests.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B23
Exact proposition under dispute: DEC-C05 rev 1 mandating omfpatch _loc_<addr> interior PUBDEF synthesis on compiled C objects for cross-piece rel32 during M2.
Competing positions: Claude raised (R0 P5); GPT agrees (OBJ-A13, DEC-A05 rev 2); Gemini UPHOLD (DEC-C05 withdrawn, DEC-B04 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: Claude R0 P5 (0x2f6df->0x2f746 built IDENTICAL with zero C-object mutation).
Concrete counterexample or failure mode: Forces unneeded post-codegen OMF mutation onto M2 Build A before strict codec consolidation.
Necessary assumptions: Verified in-place transfers cover M2 rel32-interior edges without mutating C objects.
Practical consequences: Keeps M2 Build A free of C-object mutation; any future interior export requires independent proof (DEC-A05 rev 2).
Proposed resolution: Close via DEC-B04 rev 2, DEC-A05 rev 2, and withdrawal of DEC-C05 rev 1.
Conditions under which you would change position: An M2 blocker provably requiring a synthesized interior PUBDEF.
Classification: implementation risk
```

```text
Issue: OBJ-B24
Exact proposition under dispute: Framing 68 functions as deterministically blocked by atomic cross-module symbol migration projecting 1002/1010 yield (DEC-C07 rev 1, OBJ-C04).
Competing positions: Claude raised (61 rows carry missing=[name,C], requires_llm=True); GPT REBUT (rename tooling still helps batches); Gemini UPHOLD on correcting yield projection (DEC-C07 withdrawn, DEC-B01 rev 2 accepted).
Your position: UPHOLD the factual correction (61 rows require semantic naming + C reconstruction; deterministic rename helper is an on-demand enabler per DEC-B01 rev 2, not a deterministic +68 yield button).
Supporting evidence: candidate_ledger.json@a21772b & EV-3 m2_inventory@17733f9 (61 missing=[name,C], requires_llm=True; 7 low-conf).
Concrete counterexample or failure mode: Over-projecting deterministic yield misallocates effort ahead of semantic reconstruction capacity.
Necessary assumptions: Deterministic cross-TOML rename helper remains admissible on demand per DEC-B01 rev 2.
Practical consequences: Reconciles OBJ-B24 and OBJ-C16 cleanly inside DEC-B01 rev 2.
Proposed resolution: Close via DEC-B01 rev 2 and 3/3 REJECT of DEC-C07 rev 1.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B25
Exact proposition under dispute: DEC-C11 rev 1 gating any multi-function T4 file consolidation behind E6 and claiming multi-function files intrinsically leak sibling calls.
Competing positions: Claude raised; GPT agrees (DEC-A08 rev 2); Gemini UPHOLD (DEC-C11 withdrawn, DEC-A08 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: src/playflic/player_reference.c@a21772b (20 functions tested in one TU today).
Concrete counterexample or failure mode: File count does not define the T4 trust boundary; E6 is triggered by declared intra-TU sibling substitution, callbacks, or typed pointer identity.
Necessary assumptions: Paired-state symmetry (DEC-A11/DEC-B18 rev 2) applies to all T4s regardless of file count.
Practical consequences: Removes artificial file-count gating while preserving strict E6 gates for real boundary witnesses.
Proposed resolution: Close via DEC-A08 rev 2, aligned DEC-B12, and 3/3 REJECT of DEC-C11 rev 1.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B26
Exact proposition under dispute: Round 0 overclaims that war.exe was "predominantly -5r", non_16_aligned_start has "100% precision", and -5r should be primary default (DEC-C12/C13 rev 1).
Competing positions: Claude raised; GPT agrees (OBJ-A16); Gemini UPHOLD (DEC-C12 withdrawn, DEC-C13 revised to rev 2).
Your position: UPHOLD.
Supporting evidence: E7 R6 disclaimer & only_4r = 51@e6150b8; E8 epistemic table (0.800/0.836/0.618)@e6150b8.
Concrete counterexample or failure mode: Overstates historical compiler flags and signal precision beyond E7/E8 evidence.
Necessary assumptions: None.
Practical consequences: Corrected in DEC-B13 rev 2 and DEC-C13 rev 2 (-4r stays default; -5r is candidate search family; actual PARA bases + measured precision).
Proposed resolution: Close via DEC-B13 rev 2, DEC-C13 rev 2, and withdrawal of DEC-C12 rev 1.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-B27
Exact proposition under dispute: Round 0 roadmaps forbidding fixed-displacement B2 only under global --legacy while overlooking automatic per-object Unplaceable legacy fallback.
Competing positions: Claude raised; GPT UPHOLD (DEC-A05 rev 2); Gemini UPHOLD (DEC-B19 rev 2 accepted, DEC-C05 withdrawn).
Your position: UPHOLD.
Supporting evidence: tools/wc1/build.py:310-314@a21772b (automatic per-object Unplaceable fallback).
Concrete counterexample or failure mode: Fixed-displacement branch spans a silently legacy-relocated object, breaking distance invariants.
Necessary assumptions: Planner tracks per-object placement mode explicitly.
Practical consequences: Both global and per-object legacy placement are rejected across fixed-displacement spans.
Proposed resolution: Close via DEC-B19 rev 2 and DEC-A05 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B28
Exact proposition under dispute: DEC-C11 rev 1 freezing single-function wc1.cemu unchanged during M2.
Competing positions: Claude raised; GPT agrees (OBJ-A12, DEC-A11); Gemini UPHOLD (DEC-C11 withdrawn, DEC-B18 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: tools/wc1/emu.py:188-240@a21772b (Claude R2-P2: EFLAGS never reset); GPT R1 Q1; R1-Probe 2 & R1-P4.
Concrete counterexample or failure mode: Preserves live EFLAGS/RAM/stub asymmetry in single-function T4 proofs across M2.
Necessary assumptions: None.
Practical consequences: DEC-C11 rev 1 is 3/3 REJECT; DEC-A11 + DEC-B18 rev 2 fix all T4 runs now.
Proposed resolution: Close via 3/3 REJECT of DEC-C11 rev 1, DEC-A11 (UNANIMOUS), and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-B29
Exact proposition under dispute: DEC-C07 rev 1 sequencing Stage 2 reconstruction serially "immediately after Stage 1".
Competing positions: Claude raised; GPT agrees (OBJ-A15); Gemini UPHOLD (DEC-C07 withdrawn, DEC-B01 rev 2 accepted).
Your position: UPHOLD.
Supporting evidence: EV-3 main@17733f9 (14 eligible functions now); Claude R0 P3 (Group B independent route); DEC-A01.
Concrete counterexample or failure mode: Idles reconstruction capacity behind planner infrastructure work.
Necessary assumptions: Parallel reconstruction proceeds under existing verification gates.
Practical consequences: DEC-C07 rev 1 is 3/3 REJECT; parallel tracks codified in DEC-B01 rev 2 and DEC-A01.
Proposed resolution: Close via 3/3 REJECT of DEC-C07 rev 1, DEC-A01 (UNANIMOUS), and DEC-B01 rev 2.
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-B30
Exact proposition under dispute: DEC-C03 rev 1's five V4 conditions treated as sufficient to exempt CONST alignment gap bytes.
Competing positions: Claude raised (citing GPT R1 Q2); GPT agrees (OBJ-A11); Gemini UPHOLD (DEC-C03 withdrawn in R2).
Your position: UPHOLD.
Supporting evidence: GPT R1 Q2 (indexed read of qualifying gap byte 0x8d vs 0x73 with all relocations outside gap).
Concrete counterexample or failure mode: Certifies semantically divergent CONST data if Build B changes the physical provider.
Necessary assumptions: None.
Practical consequences: DEC-C03 rev 1 is 3/3 REJECT; exact CONST matching holds at cutover.
Proposed resolution: Close via 3/3 REJECT of DEC-C03 rev 1, DEC-B02 rev 2, and updated DEC-B21.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C01
Exact proposition under dispute: Assumption in E0/E5 (matcher_proto.py:333, omf_b3.py:172-173@e6150b8) that multi-string Watcom 10.0a -ot CONST segments match byte-for-byte without addressing 1..3B alignment padding.
Competing positions: Gemini raised (R0 Probes 3 & 7); GPT & Claude REBUT the V4 exemption remedy (OBJ-A11, OBJ-B22, OBJ-B30) while confirming the underlying CONST pad phenomenon (DEC-B21, DEC-A02 rev 2).
Your position: MODIFY/CLOSE — retain empirical finding (157/293 war.exe CONST strings carry non-zero 1994 pad bytes; Watcom 10.0a emits environment-dependent pad bytes), withdraw V4 remedy (DEC-C03 rejected 3/3), and adopt exact matching at cutover + independent access-proof precondition (DEC-B02 rev 2, DEC-B21 with proof-key separation).
Supporting evidence: R0 Probes 3 & 7; Gemini R2-Probe 1 (cross-session 73002f/760061/660061); Claude R1-P2 & R2-P1; GPT R1 Q2 (computed read refuting V4).
Concrete counterexample or failure mode: Multi-string -ot CUs with non-mod-4 string lengths fail exact CONST matching unless using extern-literal idioms or an independently proved access-exclusion rule.
Necessary assumptions: Exact CONST matching protects against computed gap reads (GPT R1 Q2); extern-literal idiom remains available in M2.
Practical consequences: Documents phenomenon cleanly without weakening Stage-0 verification soundness.
Proposed resolution: Close via DEC-B02 rev 2, DEC-A02 rev 2, DEC-A06 (UNANIMOUS), and updated DEC-B21 (restricting normalization to non-authoritative research/grouping digests).
Conditions under which you would change position: A real M2 blocker unable to use extern-literal idioms (motivating an independent access prover per DEC-B21).
Classification: correctness-verification
```

```text
Issue: OBJ-C02
Exact proposition under dispute: RFC §7.2 and emit.py:45-84@a21772b modeling Fix B2 solely as interior-targeting branches, missing cut-spanning and cut-entry rel8 edges.
Competing positions: Gemini raised (R0 Probe 1); Claude agrees (OBJ-B03, DEC-B04 rev 2); GPT agrees (OBJ-A01, DEC-A05 rev 2).
Your position: UPHOLD (resolved by converged decisions).
Supporting evidence: R0 Probe 1 (11 cut-spanning rel8 incl. Sync 0x231d7/0x231e1->0x2316c; 14 cut-entry rel8 incl. EndCheckSurvive->MissionDefeat 0x2f73c); Claude R0 P2/P5.
Concrete counterexample or failure mode: Interior-only B2 fails on MissionDefeat and repeats false-positive buildability on Sync.
Necessary assumptions: None.
Practical consequences: All three rel8 classes are unified in DEC-A05 rev 2 and DEC-B04 rev 2.
Proposed resolution: Close via DEC-A05 rev 2, DEC-B04 rev 2, DEC-B03 rev 2, and DEC-B19 rev 2.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-C03
Exact proposition under dispute: Campaign D6 / E4-omf-extraction.md@e6150b8 treating omf_extract.py as near-ready for production adoption.
Competing positions: Gemini raised (R0 Probe 5); GPT agrees (DEC-A07 rev 2, R1 Q4; rebutted fixed 64-fixup cap via OBJ-A18); Claude agrees (DEC-B09 rev 2).
Your position: UPHOLD (dropping unproved 64-fixup cap per OBJ-A18; retaining confirmed Probe 5a THREAD, Probe 5b/Q4 non-_TEXT PUBDEF, Probe 5c linear decode, and rev-e4-01 F1-F4).
Supporting evidence: R0 Probe 5a/5b/5c (omf_extract.py:258,378,798-807,823@e6150b8); GPT R1 Q4; rev-e4-01 F1-F4.
Concrete counterexample or failure mode: M2 adoption introduces silent symbol corruption and crashes for 0/98 M2 yield.
Necessary assumptions: Linker record-size limits are tested empirically against actual linkers.
Practical consequences: E4 is deferred post-M2 with all confirmed defects and Gate-2 governance codified.
Proposed resolution: Close via DEC-A07 rev 2, DEC-B09 rev 2, DEC-C09 rev 2, and 3/3 REJECT of DEC-B17.
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-C04
Exact proposition under dispute: Campaign summary.md §18.9 / decisions.md sequencing B3 (E5) and multi-function T4 (E6) ahead of M2 completion work on main@a21772b/17733f9.
Competing positions: Gemini raised; GPT agrees (DEC-A01); Claude agrees (OBJ-B05, DEC-B01 rev 2; corrected "68 deterministic rename" framing in OBJ-B24).
Your position: UPHOLD M2-priority core (0/98 M2 DONE from B3/E4/E6/E8) while accepting OBJ-B24's correction that the 61 needs_human rows require semantic naming/C rather than deterministic renaming alone.
Supporting evidence: candidate_ledger.json@a21772b & EV-3 m2_inventory@17733f9 (912/1010 DONE; 0/98 unlocked by B3/E4/E6/E8).
Concrete counterexample or failure mode: Spending M2 capacity on B3/E4/E6/E8 delays Gate 1 for zero DONE progress.
Necessary assumptions: M2 Gate-1 completion governs infrastructure admission (DEC-A01, DEC-B01 rev 2).
Practical consequences: B3, E4, E6 (beyond named witnesses), and E8 are deferred post-M2.
Proposed resolution: Close via DEC-A01 (UNANIMOUS) and DEC-B01 rev 2.
Conditions under which you would change position: A named not-done M2 function genuinely requiring B3/E4/E6.
Classification: blocking architectural
```

```text
Issue: OBJ-C05
Exact proposition under dispute: E0 matcher_proto.py:358-359@e6150b8 checking FunctionMatch closure against [first_pub_base, first_pub_base + len(_TEXT)) instead of [orig_fn.start, orig_fn.start + fn_len).
Competing positions: Gemini raised; GPT agrees (DEC-A02 rev 2); Claude agrees (DEC-B02 rev 2).
Your position: UPHOLD (resolved by converged decisions).
Supporting evidence: E2-context-alignment.md@e6150b8 (Cause B: 9 false UNSUPPORTED external_rel8 rejections on identical non-contiguous multi-function code).
Concrete counterexample or failure mode: Breaks FunctionMatch as a diagnostic on non-contiguous multi-function TUs.
Necessary assumptions: Function-scoped external obligations remain diagnostic only.
Practical consequences: Fixed in DEC-A02 rev 2 and DEC-B02 rev 2.
Proposed resolution: Close via DEC-A02 rev 2 and DEC-B02 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C06
Exact proposition under dispute: RFC §2.2.5 asserting Watcom 10.0a always aligns functions to 4B while OW2 aligns to 16B.
Competing positions: Gemini raised; GPT agrees (OBJ-A16 scope fix); Claude agrees (OBJ-B26 default-flag fix).
Your position: UPHOLD (refined via DEC-C13 rev 2).
Supporting evidence: E2 alignment_matrix.json@e6150b8 (10.0a -4r -ot = 16B, -5r/-3r -ot = 4B, -os/-od = 1B, PARA SEGDEF in measured modes; OW2 -4r/-5r = 16B).
Concrete counterexample or failure mode: Misleads analysts on -4r vs -5r spacing in multi-function TUs.
Necessary assumptions: None.
Practical consequences: Replaced by verified matrix in DEC-C13 rev 2 without overclaiming historical flags or altering -4r default.
Proposed resolution: Close via DEC-C13 rev 2 and DEC-A09 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-C07
Exact proposition under dispute: RFC §9.3 proposing _DATA/_BSS staircases and call_locality_drop as primary CU boundary recovery signals.
Competing positions: Gemini raised; GPT agrees (DEC-A10); Claude agrees (DEC-B13 rev 2).
Your position: UPHOLD (resolved by converged decisions).
Supporting evidence: E8-cu-boundaries.md@e6150b8 (staircase precision 0.250/0.281; call_locality_drop precision 0.323/0.179).
Concrete counterexample or failure mode: Produces >70% false CU splits, fragmenting true CUs.
Necessary assumptions: None.
Practical consequences: Both signals are explicitly rejected in DEC-B13 rev 2 and DEC-A10.
Proposed resolution: Close via DEC-A10 (UNANIMOUS) and DEC-B13 rev 2.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-C08
Exact proposition under dispute: Production t3_audit.py@a21772b R3 provenance defects and unguarded long paths in oldcc.py@a21772b.
Competing positions: Gemini raised (R0 Probe 6); GPT & Claude agree R3 landed at EV-3 17733f9 and oldcc needs measured path limits (DEC-A12, DEC-B22).
Your position: UPHOLD (R3 delivered at EV-3 17733f9; oldcc guard carried by DEC-A12 & DEC-B22).
Supporting evidence: EV-3 main@17733f9 (R3 landed; report.md:64 hit rc=5 at ~130 chars); R1-Probe 4 (rc=-11 at ~129+ Windows chars).
Concrete counterexample or failure mode: Unprotected effective paths crash wcc386 under Wine in worktrees/CI.
Necessary assumptions: Measured limits replace any hardcoded 48-char guess.
Practical consequences: Closed cleanly by EV-3 delivery + DEC-A12 rev 1 + DEC-B22 rev 1.
Proposed resolution: Close via EV-3 main@17733f9 (R3) and DEC-A12/DEC-B22 (oldcc).
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C09
Exact proposition under dispute: DEC-A06, DEC-B02, and DEC-B08 omitting handling of Watcom 10.0a CONST alignment padding via Invariant V4.
Competing positions: Gemini raised (R1); GPT REBUT (OBJ-A11/R1 Q2); Claude REBUT (OBJ-B30/DEC-B21 rev 2); Gemini now concedes V4 remedy (DEC-C03 withdrawn).
Your position: WITHDRAW V4-in-E0/B3 remedy (upholding OBJ-A11 and OBJ-B30); retain only factual documentation of CONST padding and independent access-proof precondition (DEC-B21 with proof-key vs research-digest separation).
Supporting evidence: GPT R1 Q2 (computed read of gap byte 0x8d vs 0x73 refuting V4); R0 Probes 3 & 7 + R2-Probe 1.
Concrete counterexample or failure mode: V4 would certify semantically divergent CONST data under computed reads.
Necessary assumptions: Exact CONST matching holds at cutover; extern-literal idiom remains available.
Practical consequences: Closes the last R1 disagreement over Stage-0 E0 and post-M2 B3 exact matching.
Proposed resolution: Withdraw OBJ-C09's V4 demand; close via DEC-A06 (UNANIMOUS), DEC-B02 rev 2, DEC-A02 rev 2, and updated DEC-B21.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C10
Exact proposition under dispute: DEC-B04 rev 1 emitting unchecked raw bytes on unhardened compare.py, and DEC-B04/DEC-A05 rev 1 omitting cross-piece fallthrough guards.
Competing positions: Gemini raised; GPT UPHOLD (DEC-A05 rev 2, R2 P3 correcting 0x20258->0x202bb/0x202bc); Claude UPHOLD (DEC-B04 rev 2, DEC-B19 rev 2).
Your position: UPHOLD (accepting GPT R2 P3 correction: 0x202bb pop ebx -> 0x202bc ret, not 0x20258 -> 0x202c0, and dropping M2 interior PUBDEF synthesis per OBJ-B23).
Supporting evidence: R0 Probe 2 (0x2f73a->0x2f73c); GPT R2 P3 (0x202bb->0x202bc); GPT R0 Q3 & R2 P1/P2.
Concrete counterexample or failure mode: Unguarded fallthrough breaks moved cuts; unchecked literal bytes lack assembly-time range/byte verification.
Necessary assumptions: Piece-local expressions (or verified original bytes) + assembled-byte check + fallthrough adjacency + hardened receipt close all edges without mutating C objects in M2.
Practical consequences: Fully incorporated into DEC-A05/B04/B19/A03 rev 2.
Proposed resolution: Close via DEC-A05 rev 2, DEC-B04 rev 2, DEC-B19 rev 2, and DEC-A03 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C11
Exact proposition under dispute: Internal contradiction between DEC-B03 rev 1 (standalone Sync rejected) and DEC-B04 rev 1 (admitting in-place cut-spanning rel8).
Competing positions: Gemini raised; GPT UPHOLD; Claude UPHOLD (DEC-B03 rev 2 mode-qualified regression tests).
Your position: UPHOLD (resolved by DEC-B03 rev 2).
Supporting evidence: DEC-B03 rev 1 vs DEC-B04 rev 1; R0 Probe 1 (Sync 0x231d7/0x231e1->0x2316c).
Concrete counterexample or failure mode: Unqualified regression spec fails once DEC-B04 is enabled in-place.
Necessary assumptions: None.
Practical consequences: DEC-B03 rev 2 cleanly qualifies Sync tests across disabled/legacy, in-place B2, and Group B modes.
Proposed resolution: Close via DEC-B03 rev 2.
Conditions under which you would change position: None.
Classification: correctness-verification
```

```text
Issue: OBJ-C12
Exact proposition under dispute: DEC-B16 rev 1 reclassifying only IntroOpWaitSound (1/5) as T4 harness asymmetry and estimating S4 as "up to +4".
Competing positions: Gemini raised (R1-Probe 2); GPT UPHOLD (noting split is observation-specific, OBJ-A20); Claude UPHOLD (R1-P4, withdrew DEC-B16).
Your position: UPHOLD (with OBJ-A20 refinement: 3-vs-2 split is an observation under RAM restoration; formal inventory/xfail updates follow full DEC-A11/DEC-B18 rev 2 landing + owner review).
Supporting evidence: R1-Probe 2 & R1-P4 (0x231cc, 0x23668, 0x23ae0 flip under RAM restore; 0x23530 and 0x2fcfc persist and need full-state diagnosis).
Concrete counterexample or failure mode: Omitting 0x23668 and 0x23ae0 misdirects debugging onto already-correct C.
Necessary assumptions: Final attribution waits for DEC-A11 + DEC-B18 rev 2 landing and real t4spec audit.
Practical consequences: DEC-B16 rev 1 is 3/3 REJECT; DEC-C16 rev 1 withdrawn in favor of DEC-A11 + DEC-B18 rev 2.
Proposed resolution: Close via 3/3 REJECT of DEC-B16 rev 1, withdrawal of DEC-C16 rev 1, DEC-A11 (UNANIMOUS), and DEC-B18 rev 2.
Conditions under which you would change position: None.
Classification: unsupported factual claim
```

```text
Issue: OBJ-C13
Exact proposition under dispute: Merging Group B (DEC-B06) into production before Stage-0 E0 matcher cutover under the legacy one-directional matcher.
Competing positions: Gemini raised (R1), withdrew in R2; GPT UPHOLD (proposed DEC-A13 rev 1); Claude REBUT (R0 P3 already MATCH+IDENTICAL; sequencing is roadmap choice).
Your position: WITHDRAWN as a generic B1/B2 blocker, RESOLVED via DEC-A13 rev 1 (independent Group B promotion allowed only with commit-bound strict raw-object RegionMatch, dual-compiler checks, typed Build A comparison, and preserved cited T4 checks / owner approval).
Supporting evidence: Claude R0 P3; E1 Group B@e6150b8; DEC-A13 rev 1.
Concrete counterexample or failure mode: Early promotion without commit-bound strict RegionMatch weakens verification; gating on generic B1/B2 delays +3 DONE.
Necessary assumptions: DEC-A13's strict proof contract is satisfied on the exact Group B commit.
Practical consequences: Reconciles GPT's UPHOLD and Claude's REBUT completely inside DEC-A13 rev 1 + DEC-B06 rev 1.
Proposed resolution: Close via DEC-A13 rev 1 and DEC-B06 rev 1.
Conditions under which you would change position: Group B failing DEC-A13 strict checks.
Classification: correctness-verification
```

```text
Issue: OBJ-C14
Exact proposition under dispute: DEC-A07 rev 1 and DEC-B09 rev 1 omitting confirmed E4 prototype defects (Probe 5a THREAD, Probe 5b/Q4 non-_TEXT PUBDEF, Probe 5c linear decode) and DEC-A07 omitting Gate-2 governance.
Competing positions: Gemini raised; GPT UPHOLD (DEC-A07 rev 2, rejecting only fixed 64-fixup cap via OBJ-A18); Claude UPHOLD (DEC-B09 rev 2).
Your position: UPHOLD (dropping unproved 64-fixup cap per OBJ-A18; all confirmed defects and Gate-2 governance are now in DEC-A07/B09/C09 rev 2).
Supporting evidence: R0 Probe 5a/5b/5c; GPT R1 Q3 & Q4; OBJ-B04 (Gate-2 match --all).
Concrete counterexample or failure mode: Future E4 pilot could silently corrupt non-_TEXT publics or violate Gate 2.
Necessary assumptions: Linker record-size limits are empirically tested rather than fixed at 64.
Practical consequences: Fully incorporated into DEC-A07 rev 2, DEC-B09 rev 2, and DEC-C09 rev 2.
Proposed resolution: Close via DEC-A07 rev 2, DEC-B09 rev 2, and DEC-C09 rev 2.
Conditions under which you would change position: None.
Classification: blocking architectural
```

```text
Issue: OBJ-C15
Exact proposition under dispute: Omitting Watcom 10.0a compiler-facing path protection (tools/wc1/oldcc.py, E7 D9) from M2 roadmaps.
Competing positions: Gemini raised; GPT UPHOLD (DEC-A12 rev 1); Claude UPHOLD (DEC-B22 rev 1, DEC-B01 rev 2).
Your position: UPHOLD (resolved by DEC-A12 rev 1, DEC-B22 rev 1, and DEC-B01 rev 2).
Supporting evidence: EV-3 report.md:64@17733f9 (rc=5 at ~130 chars); R1-Probe 4 (rc=-11 at ~129+ Windows chars); oldcc.py@17733f9.
Concrete counterexample or failure mode: Unprotected long paths cause intermittent toolchain crashes during make verify and overnight waves.
Necessary assumptions: Guard limit is empirically measured over all effective compiler-facing paths; optional staging requires parity proof.
Practical consequences: Admitted into M2 infrastructure via DEC-A12 rev 1, DEC-B22 rev 1, and DEC-B01 rev 2.
Proposed resolution: Close via DEC-A12 rev 1, DEC-B22 rev 1, and DEC-B01 rev 2 (withdrawing DEC-C04 rev 1).
Conditions under which you would change position: None.
Classification: implementation risk
```

```text
Issue: OBJ-C16
Exact proposition under dispute: DEC-B01 rev 1 excluding deterministic cross-TOML symbol migration / Wave 3R helper tooling from M2 despite 68 needs_human functions.
Competing positions: Gemini raised; Claude UPHOLD partially (DEC-B01 rev 2 admits deterministic rename/migration helper on demand while correcting deterministic yield via OBJ-B24); GPT agrees via DEC-A01.
Your position: UPHOLD as resolved by DEC-B01 rev 2 (accepting OBJ-B24's correction that semantic naming/C still requires analyst/LLM work, while admitting deterministic rename/migration helper on demand).
Supporting evidence: EV-3 m2_inventory@17733f9 (76 needs_human incl. 61 fn_* + 7 low-conf); DEC-B01 rev 2 (3bf6d12e...).
Concrete counterexample or failure mode: Barring deterministic rename helpers forces error-prone manual multi-file edits across 68 symbols.
Necessary assumptions: Helper tooling is admitted when a reconstruction batch needs it, without serializing routine work behind it.
Practical consequences: Cleanly resolved inside DEC-B01 rev 2.
Proposed resolution: Close via DEC-B01 rev 2 and DEC-A01 (UNANIMOUS).
Conditions under which you would change position: None.
Classification: blocking architectural
```

---

## 1. New evidence

No new Round 3 disposable probes were required; Round 3 responds directly to the genuinely new Round 2 evidence from Architects A and B (baseline `EV-3` / `main@17733f9` and `e6150b8`):

1. **GPT `R2 P1` (`OBJ-A19` — live Build A@17733f9 LE attribute parity measurement, settling `EXP-A03` / `DEC-B20`):** Live Build A (`539` fns / `534` files) vs `original/install/war.exe` agrees 100% on object flags (`0x2045`/`0x2043`), entry `(1, 0x24584)`, stack `(2, 0x155f0)`, module flags (`0x200`), page size (`4096`), page count (`60`), page map, fixup page offsets, raw record grouping multiset, `8,770` unique typed fixups (all `src_type=7`), and `8,773` physical fixup occurrences (`0` conflicts), while differing solely in serialization attributes (raw fixup record order and 1-byte last-page file length `1339` vs `1340`). **Impact:** I uphold `OBJ-A19`, change `DEC-B20` rev 1 from `ACCEPT` to `CONDITIONAL`, accept `DEC-A03` rev 2, and revise `DEC-C15` to rev 2.
2. **GPT `R2 P2` (`OBJ-A21` — `LE.fixups_unique` first-wins duplicate-fixup vulnerability):** Mutating the second physical occurrence at `(1, 53246)` (file offset `0x6c95`) from `src_type=7` to `6` leaves all `8,770` `LE.fixups_unique` entries unchanged. **Impact:** I uphold `OBJ-A21`; hardened `wc1.compare` must validate all raw physical fixup occurrences (typed agreement, supported placement/ordering, page coverage) **before** deduplicating agreeing page-straddle copies (`DEC-A03` rev 2, `DEC-C15` rev 2, `DEC-B20` condition).
3. **GPT `R2 P3` (factual correction to Round 0 Probe 2):** `0x20258` is `push ebx` (`53`); the `pop ebx` (`5b`) falling through into the separately discovered `ret` sits at **`0x202bb -> 0x202bc`** (`0x202bc..0x202bd`), not `0x20258 -> 0x202c0`. Correction accepted cleanly; fallthrough adjacency (`DEC-B19`/`DEC-A05` rev 2) stands unchanged.
4. **Claude `R2-P1` & `R2-P2`:** `R2-P2` confirmed `tools/wc1/emu.py:188-240@a21772b` (unchanged at `17733f9`) never resets `EFLAGS`, confirming GPT `R1 Q1`'s carry-leak channel is live (`DEC-B18` rev 2 / `DEC-A11`). `R2-P1` confirmed 5/5 identical `CONST` pad bytes at a fixed path with fresh `wineserver -k`, vs my `R2-Probe 1` cross-session variation (`73002f`/`760061`/`660061` at `/tmp/opencode/cn-gemini/p7/net_sav.c`, stable `4/4` within session); neither alters exact `CONST` matching at cutover (`DEC-B02` rev 2) or restricting pad normalization to non-authoritative research/grouping digests (`DEC-B21` rev 2 condition).

---

## 2. Position changes

### 2.1 Peer decisions

- **`DEC-A02` rev 1 (`20349fbc...`):** `ACCEPT` -> **`REJECT`** (superseded by GPT's `DEC-A02` rev 2 `87a63b4c...`, which I **`ACCEPT`**).
- **`DEC-A03` rev 1 (`f48dd625...`):** `ACCEPT` -> **`REJECT`** (superseded by GPT's `DEC-A03` rev 2 `58e7c0dd...`, which I **`ACCEPT`**).
- **`DEC-A05` rev 1 (`aa4d747d...`):** `ACCEPT` -> **`REJECT`** (superseded by GPT's `DEC-A05` rev 2 `414da43a...`, which I **`ACCEPT`**).
- **`DEC-A07` rev 1 (`9c28c5b2...`):** `CONDITIONAL` -> **`REJECT`** (superseded by GPT's `DEC-A07` rev 2 `5d8aa99e...`, which I **`ACCEPT`**).
- **`DEC-A08` rev 1 (`652a1d04...`):** `CONDITIONAL` -> **`REJECT`** (superseded by GPT's `DEC-A08` rev 2 `2be94eba...`, which I **`ACCEPT`**).
- **`DEC-B07` rev 1 (`2bfe76f4...`):** `CONDITIONAL` -> **`REJECT`** (withdrawn by author; superseded by `DEC-A11` + `DEC-B18` rev 2).
- **`DEC-B20` rev 1 (`9827f947...`):** `ACCEPT` -> **`CONDITIONAL`** (on new evidence GPT `R2 P1`/`R2 P2`: validate raw physical fixups before deduplication per `OBJ-A21`; enforce normalized typed semantics while keeping raw order and 1B last-page length diagnostic per `OBJ-A19`).
- **First positions on R2 newly proposed/revised peer decisions:** **`ACCEPT`** on `DEC-A12` rev 1, `DEC-A13` rev 1, `DEC-B01` rev 2, `DEC-B02` rev 2, `DEC-B03` rev 2, `DEC-B04` rev 2, `DEC-B09` rev 2, `DEC-B13` rev 2, `DEC-B18` rev 2, `DEC-B19` rev 2, `DEC-B22` rev 1; **`CONDITIONAL`** on `DEC-B21` rev 2 (restrict `CONST` pad normalization strictly to non-authoritative research/grouping digests, never authoritative proof keys, and note cross-session sensitivity).

### 2.2 Withdrawals of superseded `DEC-C*` rev-1 propositions (10 newly withdrawn; 11 total with `DEC-C03`)

To eliminate redundant propositions fully carried by converged peer decisions, I formally **withdraw (`REJECT` rev 1 as superseded)**:
`DEC-C02` (-> `DEC-B02`/`A02` rev 2), `DEC-C03` (remains 3/3 `REJECT` -> `DEC-B21`/`A06`), `DEC-C04` (-> `DEC-A12`/`B22` + EV-3 R3), `DEC-C05` (-> `DEC-B03`/`B04`/`B19`/`A05` rev 2 + `DEC-B05`), `DEC-C06` (-> `DEC-B06`/`A13` + `DEC-A05`/`B04` rev 2), `DEC-C07` (now 3/3 `REJECT` -> `DEC-A01`/`DEC-B01` rev 2), `DEC-C08` (-> `DEC-B09`/`A07` rev 2 + `DEC-B17`), `DEC-C10` (-> `DEC-A06`/`B08`/`B21`/`C09` rev 2), `DEC-C11` (now 3/3 `REJECT` -> `DEC-A11`/`B18` rev 2/`A08` rev 2/`B12`), `DEC-C12` (-> `DEC-B13` rev 2 + `DEC-A10`), `DEC-C16` (-> `DEC-A11` + `DEC-B18` rev 2).

### 2.3 Revised `DEC-C*` propositions (`rev 1 -> rev 2`, invalidating prior approvals on rev 1)

```text
Decision: DEC-C01
Title: Retain RFC core entity separation and three-level verification hierarchy with actual integration receipt
Proposition: Retain the separation between FunctionMatch (local diagnostic), RegionMatch -> immutable VerifiedRegion (closed object/region proof), and BuildAPlacementPlan (preflight placement plan), and enforce actual assemble, link, provider-provenance, and hardened loader comparison receipts (per DEC-A03 rev 2 / DEC-B03 rev 2) as the sole Build A integration-acceptance boundary. Pipeline consumers (wc1.match, wc1.build, wc1.t3_audit, wc1.m2_inventory, wc1.overnight, wc1.wave4) distinguish these levels using typed results without owning proof logic.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 9d4022c2b6e59f6bcd9d2bbd83d318609299120b33cd3aaaf173d4124e5240ec
```

```text
Decision: DEC-C09
Title: Share one strict OMF32 subset codec before post-M2 Fix B3 or any selective extraction
Proposition: Before landing post-M2 Fix B3 or any later selective OMF extraction pilot, share one strict OMF32 subset codec for the supported record and fixup types (validating record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD state, explicit FRAME encodings, and linker-tested record-size limits rather than an assumed 64-fixup ceiling), removing duplicate transform serializers without rewriting unrelated permissive readers or scheduling this work ahead of M2 completion.
Revision: 2
Position: PROPOSE
Proposition SHA-256: c56d3bf32c4008225933ad3823b12dd61eb3101e511d484de021aef1b9e0492c
```

```text
Decision: DEC-C13
Title: Replace RFC §2.2.5 alignment model with verified Watcom 10.0a / OW2 alignment matrix
Proposition: Replace RFC §2.2.5's incorrect "10.0a always aligns to 4B" premise with E2's empirically verified alignment matrix (Watcom 10.0a -4r -ot = 16B, -5r/-3r -ot = 4B, -os/-od = 1B, with _TEXT SEGDEF = PARA 16B in the measured modes; OW2 -4r/-5r = 16B). Keep -4r as the project default, treat -5r as a first-tried candidate search family for multi-function TUs requiring 4-byte spacing without claiming original historical flags, and run EXP-2 to measure -5r -d1+ -zp1 and -od -5r.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 8b17fb93b1562ea17877185226d4e2ea7b99c4073ba6773598a80dc8a7a46517
```

```text
Decision: DEC-C15
Title: Stage-0 strict raw-OMF admission and hardened wc1.compare typed LE verification
Proposition: In Stage 0, enforce strict raw-OMF admission over the supported subset before production verification (record bounds, checksum when nonzero, single MODEND, record-type allow-list, persistent cross-record THREAD state, preserved explicit FRAME encodings, bound to the exact raw object bytes consumed by the build), and harden tools/wc1/compare.py to validate all raw physical fixup occurrences for typed agreement, supported placement/ordering, and page coverage before deduplicating agreeing page-straddle copies, then enforce equality on the measured-identical LE loader attributes (object flags, entry/stack, module flags, page size/count, page map, fixup page offsets, raw grouping multiset) and normalized typed fixups (src_type and target), keeping measured serialization-only deltas (raw fixup serialization order and 1-byte last-page file size) diagnostic unless loader relevance is established and escalating any genuine mismatch to the owner.
Revision: 2
Position: PROPOSE
Proposition SHA-256: a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc
```

---

## 3. New objections/decisions

- **New objections:** None.
- **New decision IDs:** None (Round 3 consolidates existing IDs: 11 `DEC-C*` withdrawn, 4 revised to rev 2).

---

## 4. Convergence assessment

### 4.1 Non-unanimous decisions (38)

| Issue | Trend | Cheapest decisive test / action | Nature |
|---|---|---|---|
| `DEC-A02` (r1->r2) | narrowing | Index/vote `DEC-A02` r2 + live `make verify` cutover audit | architectural |
| `DEC-A03` (r1->r2) | narrowing | Index/vote `DEC-A03` r2 + `R2 P2` raw-duplicate negative test | architectural |
| `DEC-A05` (r1->r2) | narrowing | Index/vote `DEC-A05` r2 + B1/B2/fallthrough/legacy fixture | architectural |
| `DEC-A07` (r1->r2) | narrowing | Index/vote `DEC-A07` r2 (post-M2 only) | architectural |
| `DEC-A08` (r1->r2) | narrowing | Index/vote `DEC-A08` r2 + `Q-B05` full T4 suite | architectural |
| `DEC-A12` (r1) | narrowing | Measure Watcom 10.0a safe path ceiling + staging parity test | architectural |
| `DEC-A13` (r1) | narrowing | Commit-bound strict `RegionMatch` + typed Build A on Group B | architectural |
| `DEC-B01` (r2) | narrowing | Peer vote check on r2 | architectural |
| `DEC-B02` (r2) | narrowing | Peer vote check on r2 + live `make verify` cutover | architectural |
| `DEC-B03` (r2) | narrowing | Peer vote check on r2 + mode-qualified Sync regression | architectural |
| `DEC-B04` (r2) | narrowing | Peer vote check on r2 + prefixed-rel8/in-place link fixture | architectural |
| `DEC-B06` (r1) | narrowing | Pair with `DEC-A13` r1 for early path + owner checkpoint | architectural |
| `DEC-B07` (r1) | narrowing | Record final REJECT on author-withdrawn r1 | architectural |
| `DEC-B09` (r2) | narrowing | Peer vote check on r2 (post-M2 deferral + Gate-2 + fixes) | architectural |
| `DEC-B12` (r1) | narrowing | Align wording with `DEC-A08` r2 (post-M2 + entry-only hooks) | architectural |
| `DEC-B13` (r2) | narrowing | Peer vote check on r2 (analyst-only premise graph) | architectural |
| `DEC-B16` (r1) | stable (3/3 REJECT) | Ready to close | editorial |
| `DEC-B17` (r1) | stable (3/3 REJECT) | Ready to close | architectural |
| `DEC-B18` (r2) | narrowing | Peer vote check on r2 + `Q-B05` + `A1 Q1` carry/host controls | architectural |
| `DEC-B19` (r2) | narrowing | Peer vote check on r2 + `Unplaceable`/fallthrough negatives | architectural |
| `DEC-B20` (r1) | narrowing | Align with `OBJ-A19`/`OBJ-A21` (`DEC-A03`/`DEC-C15` r2) | architectural |
| `DEC-B21` (r2) | narrowing | Narrow "proof-cache digests" to research/grouping digests (r3) | architectural |
| `DEC-B22` (r1) | narrowing | Peer vote check on r1 + measured path-ceiling probe | architectural |
| `DEC-C01` (r1->r2) | narrowing | Peer votes on `DEC-C01` r2 (`OBJ-A09` receipt boundary) | architectural |
| `DEC-C02` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-B02`/`A02` r2 | editorial |
| `DEC-C03` (r1) | stable (3/3 REJECT) | Ready to close | architectural |
| `DEC-C04` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-A12`/`B22` | editorial |
| `DEC-C05` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-B03`/`B04`/`B19`/`A05` r2 | editorial |
| `DEC-C06` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-B06`/`A13` | editorial |
| `DEC-C07` (r1) | narrowing (3/3 REJECT) | Withdrawn (`REJECT` r1) -> `DEC-A01`/`DEC-B01` r2 | architectural |
| `DEC-C08` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-B09`/`A07` r2 | editorial |
| `DEC-C09` (r1->r2) | narrowing | Peer votes on `DEC-C09` r2 (strict subset, linker-tested limits) | architectural |
| `DEC-C10` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-A06`/`B08`/`B21`/`C09` r2 | editorial |
| `DEC-C11` (r1) | narrowing (3/3 REJECT) | Withdrawn (`REJECT` r1) -> `DEC-A11`/`B18` r2/`A08` r2 | architectural |
| `DEC-C12` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-B13` r2/`DEC-A10` | editorial |
| `DEC-C13` (r1->r2) | narrowing | Peer votes on `DEC-C13` r2 + `EXP-2` | architectural |
| `DEC-C15` (r1->r2) | narrowing | Peer votes on `DEC-C15` r2 (`OBJ-A19`/`OBJ-A21`) | architectural |
| `DEC-C16` (r1) | narrowing | Withdrawn (`REJECT` r1) -> `DEC-A11`/`DEC-B18` r2 | architectural |

### 4.2 Open objections (63)

| Objections | Trend | Cheapest decisive test / closing action | Nature |
|---|---|---|---|
| `OBJ-A01`, `OBJ-A09`, `OBJ-B03`, `OBJ-B11`, `OBJ-C02`, `OBJ-C11` | narrowing | Mode-qualified Sync + MissionDefeat planner/link regression (`DEC-B03`/`B04` r2) | architectural |
| `OBJ-A02`, `OBJ-A19`, `OBJ-A21`, `OBJ-B19` | narrowing | Live Build A parity + `R2 P2` duplicate-fixup negative (`DEC-A03`/`C15` r2) | architectural |
| `OBJ-A03`, `OBJ-A10`, `OBJ-B10`, `OBJ-B20`, `OBJ-C05` | narrowing | E0 55 controls + strict raw-OMF negatives + live `make verify` (`DEC-B02`/`A02` r2) | architectural |
| `OBJ-A04`, `OBJ-B05`, `OBJ-C04` | narrowing | Reflected in unanimous `DEC-A01`/`A06`/`B08` + `DEC-B01` r2 | architectural |
| `OBJ-A05`, `OBJ-B01`, `OBJ-C13` | narrowing | Commit-bound strict `RegionMatch` + typed Build A on Group B (`DEC-A13`/`B06`) | architectural |
| `OBJ-A06`, `OBJ-A16`, `OBJ-B07`, `OBJ-B12`, `OBJ-B26`, `OBJ-C06`, `OBJ-C07` | narrowing | `EXP-2` probe + RFC §2.2.5/§9.3 replacement (`DEC-B13`/`C13` r2, `DEC-A10`) | architectural |
| `OBJ-A07`, `OBJ-A14`, `OBJ-A18`, `OBJ-B04`, `OBJ-C03`, `OBJ-C14` | narrowing | Deferred post-M2; owner Gate-2 + strict subset negatives (`DEC-A07`/`B09`/`C09` r2) | architectural |
| `OBJ-A08`, `OBJ-A12`, `OBJ-A20`, `OBJ-B06`, `OBJ-B18`, `OBJ-B21`, `OBJ-B25`, `OBJ-B28`, `OBJ-C12` | narrowing | `Q-B05` full T4 suite + `A1 Q1` controls under `DEC-A11`/`B18` r2/`A08` r2 | architectural |
| `OBJ-A11`, `OBJ-B22`, `OBJ-B30`, `OBJ-C01`, `OBJ-C09` | narrowing | V4 withdrawn (3/3 REJECT `DEC-C03`); narrow `DEC-B21` to research digests | architectural |
| `OBJ-A13`, `OBJ-B02`, `OBJ-B23`, `OBJ-B27`, `OBJ-C10` | narrowing | Combined B1/B2/fallthrough fixture + prefixed-rel8 & legacy negatives (`DEC-A05`/`B04`/`B19` r2) | architectural |
| `OBJ-A15`, `OBJ-B24`, `OBJ-B29`, `OBJ-C16` | narrowing | Resolved in `DEC-B01` r2 + `DEC-A01` (parallel tracks + on-demand rename helper) | architectural |
| `OBJ-A17`, `OBJ-C08`, `OBJ-C15` | narrowing | EV-3 delivered R3; measure Watcom 10.0a path ceiling + staging parity (`DEC-A12`/`B22`) | architectural |
| `OBJ-B08`, `OBJ-B09`, `OBJ-B13` | narrowing | RFC §2.2.4 wording (`OBJ-B08`); unanimous `DEC-B14` (`OBJ-B09`) & `DEC-B15` (`OBJ-B13`) | editorial / maintainability |

**Zero issues are widening.** Remaining substantive refinements reduce to: (1) aligning `DEC-B20` with `OBJ-A19`/`OBJ-A21` (`DEC-A03`/`C15` rev 2), (2) restricting `DEC-B21` rev 2's pad normalization to non-authoritative research/grouping digests, and (3) aligning `DEC-B12` rev 1 with `DEC-A08` rev 2.

---

## 5. Structured positions for every live decision

*(All 38 indexed non-unanimous decisions from `00-LIVE-ISSUES.json`, plus explicit positions on GPT's 5 rev-2 propositions and my 4 rev-2 propositions. None of the 13 `UNANIMOUS` decisions is reopened.)*

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: REJECT
Reason: Superseded by DEC-A02 rev 2 (local function-extent bounds, explicit external context obligations, trim checks in both scopes) and DEC-B02 rev 2.
Conditions: none
Related objections: OBJ-A03, OBJ-A10, OBJ-C05
```

```text
Decision: DEC-A02
Revision: 2
Proposition SHA-256: 87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca
Position: ACCEPT
Reason: Unifies FunctionMatch/RegionMatch bidirectional obligations, function-extent local bounds, explicit external context obligations, trim checks, strict raw-OMF admission, live cutover audit, and deferral of unproven CONST gap exemptions.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: REJECT
Reason: Superseded by DEC-A03 rev 2 after R2 P1/P2 proved raw fixup validation must precede deduplication and serialization deltas stay diagnostic.
Conditions: none
Related objections: OBJ-A19, OBJ-A21
```

```text
Decision: DEC-A03
Revision: 2
Proposition SHA-256: 58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda
Position: ACCEPT
Reason: Single input-bound preflight plan plus actual assemble/link/provider/hardened-compare receipts, validating raw fixup records before collapsing agreeing page-straddle duplicates and keeping serialization deltas diagnostic.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: REJECT
Reason: Superseded by DEC-A05 rev 2 (adds fallthrough adjacency, decoded width/next-IP checks, and per-object legacy fallback rejection).
Conditions: none
Related objections: OBJ-B27, OBJ-C10, OBJ-A13
```

```text
Decision: DEC-A05
Revision: 2
Proposition SHA-256: 414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5
Position: ACCEPT
Reason: Complete cross-object transfer and fallthrough rule covering all three rel8 classes, decoded endpoints/width/next-IP, both legacy paths, symbolic rel32, independent proof before any interior exports, and whole-TU preference.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: REJECT
Reason: Superseded by DEC-A07 rev 2 (adds owner source-gate authorization and validated subset record/symbol handling).
Conditions: none
Related objections: OBJ-A14, OBJ-B04, OBJ-C14
```

```text
Decision: DEC-A07
Revision: 2
Proposition SHA-256: 5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d
Position: ACCEPT
Reason: Defers general extraction and binds any narrow post-M2 pilot to owner source-gate authorization, raw-input region proof, independent code/data bounds, validated subset handling, and independent post-transform/link proof.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: REJECT
Reason: Superseded by DEC-A08 rev 2 (applies DEC-A11 paired-state equivalence immediately to current T4 witnesses independently of demand-led E6).
Conditions: none
Related objections: OBJ-A12, OBJ-B21
```

```text
Decision: DEC-A08
Revision: 2
Proposition SHA-256: 2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31
Position: ACCEPT
Reason: Immediately applies DEC-A11 paired-state equivalence to affected current T4 witnesses and gates E6 boundary/substitution/ABI/typed-pointer/audit-parity machinery strictly on demonstrated witness needs.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A12
Revision: 1
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Position: ACCEPT
Reason: Closes OBJ-C15 and OBJ-A17 with measured effective compiler-facing path limits, fail-fast toolchain errors, and parity-proved staging requirements (aligned with DEC-B22).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A13
Revision: 1
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Position: ACCEPT
Reason: Reconciles OBJ-C13 and OBJ-A15: permits independent exact Group B promotion only with commit-bound strict raw-object RegionMatch, dual-compiler checks, typed Build A comparison, and preserved cited T4 checks / owner approval.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B01
Revision: 2
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Position: ACCEPT
Reason: Principle-driven M2 admission with parallel reconstruction tracks, all demonstrated soundness/blocker fixes (incl. oldcc guard, comparator hardening, T4 symmetry), on-demand deterministic rename helper, and post-M2 deferral of B3/E4/E6/E8.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B02
Revision: 2
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Position: ACCEPT
Reason: Adopts E0 bidirectional semantics with strict raw-OMF admission, raw-byte binding, exact CONST matching at cutover, function-scoped diagnostic external obligations, and live full-population make verify gate.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B03
Revision: 2
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Position: ACCEPT
Reason: One preflight planner plan(p, regions), mandatory actual integration receipts for T3 promotion, and mode-qualified IntroOpSyncSound regression tests resolving OBJ-C11.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B04
Revision: 2
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Position: ACCEPT
Reason: Unified Build A cross-object transfer rule with exact decoded length/prefixes/next-IP, symbolic rel32 to exported entries, in-place original-length cover (DEC-B19 rev 2), piece-local expression preferred, assembled-byte/receipt checks, no M2 C-object PUBDEF mutation, and joint-TU preference.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: ACCEPT
Reason: Proof-gated multi-function TUs starting with Group B under owner AGENTS.md checkpoint and no heuristic consolidation; paired with DEC-A13 rev 1 whenever promoted before production E0 cutover.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: REJECT
Reason: Withdrawn by author; superseded by DEC-A11 (UNANIMOUS) and DEC-B18 rev 2.
Conditions: none
Related objections: OBJ-A12, OBJ-A20
```

```text
Decision: DEC-B09
Revision: 2
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Position: ACCEPT
Reason: Defers E3/E4 during M2 and codifies owner Gate-2 authorization, strict shared OMF subset, regression tests for Probe 5a/5b/5c and rev-e4-01 F1-F4, linker-tested record limits, and RFC §16 criteria.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: Demand-led E6 adoption is right, but rev 1 restricts the trigger text to "needed for M2" and omits proved entry-only edges for c_entry_hook and DEC-A08 rev 2/DEC-A11 parity.
Conditions: Admit qualified post-M2 witnesses on the same demand-led basis, require proved entry-only edges for c_entry_hook, and enforce DEC-A08 rev 2 and DEC-A11/DEC-B18 rev 2 parity.
Related objections: OBJ-A12, OBJ-B25
```

```text
Decision: DEC-B13
Revision: 2
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Position: ACCEPT
Reason: Analyst-facing premise-carrying CU constraint graph with producer premises for shared_epilogue, PARA segment-base evaluation for non_16_aligned_start, conditional shared_const_string_literal excluding shared storage/pooling, rejection of staircases/call-locality/auto-consolidation, and M3 deferral of compilation_units.toml.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Maintain 3/3 REJECT (withdrawn; incomplete 1/5 scope and conflated probe diagnosis with verified inventory status; superseded by DEC-B18 rev 2).
Conditions: none
Related objections: OBJ-A15, OBJ-A20, OBJ-C12
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: Maintain 3/3 REJECT (rejects selective OMF extraction as an M2 strategy; post-M2 deferral in DEC-A07/DEC-B09 rev 2).
Conditions: none
Related objections: OBJ-A14, OBJ-B04, OBJ-C14
```

```text
Decision: DEC-B18
Revision: 2
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Position: ACCEPT
Reason: Complete paired starting state (CPU regs, EFLAGS, segments, ESP, all mapped memory covering host+guest writes, allocator, declared/reset stub state), separate from compared effects, audited, applied across all T4 tests with pre-landing full-suite check and owner review before any status/xfail change.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B19
Revision: 2
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Position: ACCEPT
Reason: Enforces plan-level rejection of fixed-displacement spans over either global --legacy or per-object Unplaceable fallback, plus physical adjacency for every cross-piece ASM fallthrough.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: CONDITIONAL
Reason: Changed from R2 ACCEPT on new evidence GPT R2 P1 & R2 P2: baseline parity measurement completed (typed semantics and loader attributes agree; raw fixup order and 1B last-page size differ), and LE.fixups_unique first-wins collapse masks conflicting duplicates.
Conditions: Validate all raw physical fixup occurrences before deduplicating agreeing page-straddle copies (OBJ-A21) and enforce normalized typed fixups + measured-identical loader attributes while keeping raw order and 1B last-page length diagnostic unless loader relevance is shown (OBJ-A19).
Related objections: OBJ-A19, OBJ-A21
```

```text
Decision: DEC-B21
Revision: 2
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Position: CONDITIONAL
Reason: Exact CONST matching, rejection of shape-based V4, and independent extent/ownership/access-proof preconditions are right, but normalizing CONST pad bytes inside authoritative "proof-cache digests" conflicts with DEC-B02 rev 2's raw-byte proof binding and exact CONST matching.
Conditions: (1) Restrict CONST pad-byte normalization strictly to non-authoritative research/candidate-grouping digests—never authoritative proof keys, which must bind exact raw object bytes; (2) note cross-session environment sensitivity (Gemini R2-Probe 1) alongside path sensitivity.
Related objections: OBJ-A11, OBJ-B22, OBJ-B30, OBJ-C09
```

```text
Decision: DEC-B22
Revision: 1
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Position: ACCEPT
Reason: Closes OBJ-C15 and OBJ-A17 with a measured compiler-facing path guard failing fast on exit-78 toolchain error and parity-proved optional staging (aligned with DEC-A12).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: REJECT
Reason: Superseded by DEC-C01 rev 2 (separates BuildAPlacementPlan preflight from actual integration receipts per OBJ-A09 and clarifies typed consumer boundaries).
Conditions: none
Related objections: OBJ-A09
```

```text
Decision: DEC-C01
Revision: 2
Proposition SHA-256: 9d4022c2b6e59f6bcd9d2bbd83d318609299120b33cd3aaaf173d4124e5240ec
Position: ACCEPT
Reason: Retains three-level separation with actual assemble/link/provider/hardened-compare receipts as the sole Build A acceptance boundary across all 6 pipeline tools using typed results without owning proof logic.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: REJECT
Reason: Withdrawn by author as redundant and superseded by DEC-B02 rev 2 and DEC-A02 rev 2.
Conditions: none
Related objections: OBJ-A03, OBJ-A10, OBJ-B20
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: Maintain 3/3 REJECT (withdrawn in R2; refuted by GPT R1 Q2; superseded by DEC-B02 rev 2, DEC-A06, and DEC-B21).
Conditions: none
Related objections: OBJ-A11, OBJ-B20, OBJ-B22, OBJ-B30
```

```text
Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: REJECT
Reason: Withdrawn by author as obsolete/superseded (R3 landed at EV-3 17733f9; measured oldcc path protection carried by DEC-A12 and DEC-B22).
Conditions: none
Related objections: OBJ-A17, OBJ-C15
```

```text
Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: REJECT
Reason: Withdrawn by author as superseded by DEC-B03 rev 2, DEC-B04 rev 2, DEC-B05 (UNANIMOUS), DEC-B19 rev 2, and DEC-A05 rev 2.
Conditions: none
Related objections: OBJ-A09, OBJ-A13, OBJ-B23, OBJ-B27, OBJ-C10
```

```text
Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: REJECT
Reason: Withdrawn by author as redundant and superseded by DEC-B06 rev 1, DEC-A13 rev 1, DEC-A05 rev 2, and DEC-B04 rev 2.
Conditions: none
Related objections: OBJ-A15, OBJ-A16, OBJ-C13
```

```text
Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: Withdrawn by author (now 3/3 REJECT; superseded by DEC-A01 and DEC-B01 rev 2 with parallel reconstruction tracks).
Conditions: none
Related objections: OBJ-A15, OBJ-B18, OBJ-B24, OBJ-B29
```

```text
Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: REJECT
Reason: Withdrawn by author to eliminate sign ambiguity and superseded by DEC-B09 rev 2, DEC-A07 rev 2, and DEC-B17 rev 1.
Conditions: none
Related objections: OBJ-A14, OBJ-A18, OBJ-C14
```

```text
Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: REJECT
Reason: Superseded by DEC-C09 rev 2 (strict OMF32 subset for post-M2 B3/extraction with linker-tested limits instead of fixed 64-fixup cap).
Conditions: none
Related objections: OBJ-A18, OBJ-C14
```

```text
Decision: DEC-C09
Revision: 2
Proposition SHA-256: c56d3bf32c4008225933ad3823b12dd61eb3101e511d484de021aef1b9e0492c
Position: ACCEPT
Reason: Binds post-M2 Fix B3 and any later selective extraction pilot to one shared strict OMF32 subset codec with persistent THREAD, explicit FRAME, and linker-tested record limits without rewriting unrelated permissive readers or delaying M2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: REJECT
Reason: Withdrawn by author as superseded by DEC-A06 (UNANIMOUS), DEC-B08 (UNANIMOUS), DEC-B21, and DEC-C09 rev 2.
Conditions: none
Related objections: OBJ-A11, OBJ-B22, OBJ-B30, OBJ-C09
```

```text
Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: Withdrawn by author (now 3/3 REJECT; superseded by DEC-A11, DEC-B18 rev 2, DEC-A08 rev 2, and DEC-B12).
Conditions: none
Related objections: OBJ-A12, OBJ-B21, OBJ-B25, OBJ-B28
```

```text
Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: REJECT
Reason: Withdrawn by author to remove sign ambiguity and premature cu_hypotheses.toml storage; superseded by DEC-B13 rev 2 and DEC-A10 (UNANIMOUS).
Conditions: none
Related objections: OBJ-A16, OBJ-B26
```

```text
Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: REJECT
Reason: Superseded by DEC-C13 rev 2 (scopes PARA to measured modes, keeps -4r default, frames -5r strictly as candidate search family with no historical-flag claim).
Conditions: none
Related objections: OBJ-A16, OBJ-B26
```

```text
Decision: DEC-C13
Revision: 2
Proposition SHA-256: 8b17fb93b1562ea17877185226d4e2ea7b99c4073ba6773598a80dc8a7a46517
Position: ACCEPT
Reason: Replaces RFC §2.2.5's incorrect alignment table with E2's verified matrix, keeps -4r default, positions -5r as candidate search family for 4B multi-function TUs, and schedules EXP-2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: REJECT
Reason: Superseded by DEC-C15 rev 2 on new evidence GPT R2 P1 & R2 P2 (raw physical fixup validation before deduplication per OBJ-A21; normalized typed semantics with diagnostic serialization deltas per OBJ-A19).
Conditions: none
Related objections: OBJ-A19, OBJ-A21
```

```text
Decision: DEC-C15
Revision: 2
Proposition SHA-256: a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc
Position: ACCEPT
Reason: Unifies Stage-0 strict raw-OMF subset admission (bound to exact raw bytes) with post-measurement hardened wc1.compare validation of all raw physical fixup occurrences before deduplicating page-straddle copies, normalized typed fixup and loader-attribute equality, diagnostic serialization deltas, and owner escalation on genuine mismatches.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C16
Revision: 1
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Position: REJECT
Reason: Withdrawn by author as superseded by DEC-A11 (UNANIMOUS) and DEC-B18 rev 2 (complete starting state including CPU/EFLAGS, all mapped memory covering host+guest writes, allocator, and declared stub state, with status updates gated on post-landing pytest runs under owner review).
Conditions: none
Related objections: OBJ-A12, OBJ-A15, OBJ-A20
```

*(Durable copy written to [CONSILIUM-R03-DELIBERATION.md](file:///mnt/data/projects/warcraft-1-decompile-wt/cons-c/CONSILIUM-R03-DELIBERATION.md).)*
