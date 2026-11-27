# Decision rationale (EDITOR DRAFT)

This file covers all 54 ledger decisions. Each entry gives the exact proposition, the identifier, the revision, the status, the SHA-256 and the live positions, followed by an **editorial** rationale.
The rationale explains why the consilium converged and cites evidence. It does not add obligations. Where the rationale and the proposition differ, the proposition governs.

## Evidence index

- `E0..E8`: `docs/research/build-codegen/E<n>-*.md@e6150b856106ae113bb023300b956fff318da7ef`, with `summary.md` and `decisions.md` at the same commit.
- `EV-3`: production `main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`, as quoted in `12-r04-gpt-response.md` (`e6a4affd…`) and `14-r04-gemini-response.md` (`a6f2f9d7…`).
- `A1 Q1/Q2`, `A R2 P1/P2`, `A R3 P1/P2`, `A R4 P1`: Architect A's disposable probes, reported in A's frozen responses. R4 P1 is in `12-r04-gpt-response.md` §7.
- `B R0 P3/P5/P6`, `B R3-P1`: Architect B's disposable probes, reported in `CONSILIUM-R00-POSITION.md@887fad77…` and `CONSILIUM-R03-DELIBERATION.md@7bcf0f68…` (worktree `cons-b`). Their delivered final-message forms are in the Secretary's archive.
- Probes are evidence for agreement on the architecture. They are not executions of production acceptance tests.

## DEC-A01 r1 — Keep the M2 completion contract

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A05 RESOLVED (r04), OBJ-A15 RESOLVED (r05), OBJ-B29 RESOLVED (r05), OBJ-C04 RESOLVED (r05), OBJ-C16 RESOLVED (r05)

> **DEC-A01 r1** · UNANIMOUS · SHA-256 `cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31`  
> *Keep the M2 completion contract*
>
> Sequence work by remaining DONE obligations under the existing scope, tiers and gates. Count a T4-to-T3 conversion separately. Leave T5 authorization to the owner.

**Rationale (editorial).** The fixed finish line (scope, tiers, gates) stays with the owner; infrastructure is valued by the DONE obligations it satisfies, and a T4-to-T3 conversion does not change DONE. EV-3 records 912/1010 DONE with 98 outstanding.

## DEC-A02 r2 — Scoped bidirectional verifier with strict raw-OMF admission [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca`
- **Live positions:** gpt: ACCEPT (r07), claude: ACCEPT (r07), gemini: ACCEPT (r03)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A03 RESOLVED (r04), OBJ-A10 RESOLVED (r04), OBJ-B10 RESOLVED (r04), OBJ-B20 RESOLVED (r04), OBJ-C01 RESOLVED (r04), OBJ-C05 RESOLVED (r04), OBJ-C09 WITHDRAWN (r04)

> **DEC-A02 r2** · UNANIMOUS · SHA-256 `87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca`  
> *Scoped bidirectional verifier with strict raw-OMF admission [editorial title]*
>
> Use one bidirectional obligation engine for FunctionMatch and RegionMatch. Bound local branch checks to the independently verified function extent and carry independently proven external context as explicit obligations. Check trim targets in both scopes. Admit only the strictly decoded raw OMF subset of the actual declared compiler output, and cut over only after the existing file gate and every live declared T3 pass. Defer unproven CONST gap exemptions.

**Rationale (editorial).** E0 showed the three legacy matcher gaps are real and closable, but the prototype is evidence, not production: strict raw admission (checksums, THREAD, FRAME, MODEND) and a live audit of every declared T3 at cutover are required before the new engine becomes authoritative. Shape-only CONST gap exemptions were refuted (A1 Q2) and stay deferred.

## DEC-A03 r2 — Single preflight plan; integration only from actual link and comparison [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda`
- **Live positions:** gpt: ACCEPT (r06), claude: ACCEPT (r06), gemini: ACCEPT (r03)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A01 RESOLVED (r05), OBJ-A02 RESOLVED (r04), OBJ-A09 RESOLVED (r05), OBJ-A19 RESOLVED (r04), OBJ-A21 RESOLVED (r04), OBJ-B19 RESOLVED (r04), OBJ-C10 RESOLVED (r04)

> **DEC-A03 r2** · UNANIMOUS · SHA-256 `58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda`  
> *Single preflight plan; integration only from actual link and comparison [editorial title]*
>
> For a new in-place Build A path, derive one input-bound partition plan with one physical provider per original loaded byte. Treat plan success as preflight. Accept integration only from actual assembly and link, materialized provider evidence, the existing comparison, and an expanded comparison of supported LE loader attributes and normalized typed fixups. Validate raw fixup records before collapsing agreeing page-straddle duplicates. Keep serialization differences diagnostic unless shown to be loader-relevant.

**Rationale (editorial).** A placement plan is a preflight; only actual assembly, link, provider evidence and comparison establish integration. Comparator mutants (missing executable flag, changed source type, contradictory duplicate occurrence) were accepted by the old comparator (A R2 P2), so occurrence validation precedes deduplication; serialization-only deltas stay diagnostic (A R2 P1, A R4 P1).

## DEC-A04 r1 — Admit verified leading tables

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1

> **DEC-A04 r1** · UNANIMOUS · SHA-256 `5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0`  
> *Admit verified leading tables*
>
> Derive a whole contribution base from a verified public binding and object offset. Admit leading bytes only with full region bounds, ownership and checked relocation obligations.

**Rationale (editorial).** Leading jump tables (B1, e.g. ChooseCampaignDialog 0x157e8) are admitted by deriving the contribution base from a verified public binding, never by an address exception.

## DEC-A05 r2 — Cross-object transfer and fallthrough rule (B2) [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A13 RESOLVED (r04), OBJ-B02 RESOLVED (r04), OBJ-B03 RESOLVED (r04), OBJ-B23 RESOLVED (r04), OBJ-B27 RESOLVED (r04), OBJ-C02 RESOLVED (r04), OBJ-C10 RESOLVED (r04)

> **DEC-A05 r2** · UNANIMOUS · SHA-256 `414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5`  
> *Cross-object transfer and fallthrough rule (B2) [editorial title]*
>
> Prefer a verified whole-TU shared-tail group. For each cross-piece fallthrough prove physical adjacency. For each fixed relative branch prove decoded endpoints, field width, next instruction address, in-place cover, exact emitted bytes, and zero relocation over its displacement. Cover interior, entry and cut-spanning rel8 using checked piece-local expressions for supported ASM encodings. Reject edges whose proof depends on global or per-object legacy placement. Use existing valid symbolic rel32 bindings and require independent proof before adding interior exports. Require final link evidence and reject unsupported outgoing compiled-slice rel8.

**Rationale (editorial).** Cross-object short branches (B2: interior, entry, span) and fallthrough need proof per edge; NASM -f obj cannot emit 8-bit external relocations, so supported encodings use checked piece-local expressions. Probes linked the remaining B2 cases (B R0 P5; A R3 P2) but no production test exists.

## DEC-A06 r1 — Separate storage identity from provider

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A04 RESOLVED (r04), OBJ-B05 RESOLVED (r04), OBJ-C01 RESOLVED (r04), OBJ-C09 WITHDRAWN (r04)

> **DEC-A06 r1** · UNANIMOUS · SHA-256 `4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac`  
> *Separate storage identity from provider*
>
> Keep canonical storage and alias evidence independent of physical suppliers. Admit B3 initially for fully verified whole segments only, once a pilot justifies deployment and the strict transform and link tests pass.

**Rationale (editorial).** Semantic owner and physical provider are separate; B3 starts with exact whole segments because E5 is feasible only for its verified subset.

## DEC-A07 r2 — General extraction deferred; narrow pilot conditions [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A07 RESOLVED (r04), OBJ-A14 RESOLVED (r04), OBJ-B04 RESOLVED (r04), OBJ-C03 RESOLVED (r04), OBJ-C14 RESOLVED (r04)

> **DEC-A07 r2** · UNANIMOUS · SHA-256 `5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d`  
> *General extraction deferred; narrow pilot conditions [editorial title]*
>
> Defer general extraction. Permit a narrowly justified pilot only with owner authorization for any source-gate semantics change, a region proof bound to the raw input object, independently established code and data bounds and targets, record and symbol handling validated for the admitted subset, and independent proof of the transformed artifact and actual link. Reject unsupported inputs.

**Rationale (editorial).** E4's prototype had confirmed faults (cross-record THREAD, non-_TEXT PUBDEF, typed tables, rev-e4-01 F1-F4) and extraction changes source-gate semantics; a pilot therefore needs owner authorization and independent proof.

## DEC-A08 r2 — Demand-led E6 boundary machinery [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A08 RESOLVED (r04), OBJ-A12 RESOLVED (r04), OBJ-B21 RESOLVED (r04), OBJ-B25 RESOLVED (r04)

> **DEC-A08 r2** · UNANIMOUS · SHA-256 `2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31`  
> *Demand-led E6 boundary machinery [editorial title]*
>
> Apply certified paired-state equivalence to affected current T4 witnesses. Before a new cited witness relies on a multi-function or substitution boundary, prove the allowed per-side execution and dependency edges, symmetric declared substitutions, exercised callback ABI and typed pointer identity, and production t4spec audit parity. Add boundary machinery only for demonstrated witness requirements.

**Rationale (editorial).** E6 machinery is justified only by a witness that needs it; paired-state equivalence applies first to current witnesses.

## DEC-A09 r1 — Keep compiler search evidence scoped

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-B07 RESOLVED (r04), OBJ-C06 RESOLVED (r04)

> **DEC-A09 r1** · UNANIMOUS · SHA-256 `2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e`  
> *Keep compiler search evidence scoped*
>
> Keep the merged additive presets and declared compiler policy. Record S(f) with its full measured context and coverage. Treat heuristic scores and freshness snapshots as scheduling inputs only.

**Rationale (editorial).** E7 presets are merged and additive; S(f) is context-bound and scores/freshness snapshots only schedule work (EV-3: 0 of 202 historical improved-T4 records fresh for Wave 4B).

## DEC-A10 r1 — Record historical alternatives and premises

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A06 RESOLVED (r04), OBJ-B12 RESOLVED (r04), OBJ-C07 RESOLVED (r04)

> **DEC-A10 r1** · UNANIMOUS · SHA-256 `8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e`  
> *Record historical alternatives and premises*
>
> Store original CU evidence separately from scope and build inputs. Apply hard constraints only with their premises independently established. Do not drive automatic source consolidation from the measured signals.

**Rationale (editorial).** E8 measured signal precision on its corpora only; hard constraints need independently established premises and no signal drives consolidation.

## DEC-A11 r1 — Certify paired starting state independently of outputs

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r01; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A08 RESOLVED (r04), OBJ-A12 RESOLVED (r04), OBJ-A20 RESOLVED (r05), OBJ-B06 RESOLVED (r04), OBJ-B18 RESOLVED (r04), OBJ-B21 RESOLVED (r04), OBJ-B28 RESOLVED (r04), OBJ-C12 RESOLVED (r04)

> **DEC-A11 r1** · UNANIMOUS · SHA-256 `0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78`  
> *Certify paired starting state independently of outputs*
>
> A T4 pair must execute from equivalent per-side CPU, memory and declared mutable dependency state for each case. Implement independent initialization or a certified checkpoint with host- and guest-write accounting. Keep the effects compared by existing tests separate from state restoration. Report unsupported state when equivalence of inputs cannot be established. Apply this requirement to affected current witnesses before adopting multi-function extensions.

**Rationale (editorial).** cemu.run_pair restores only watch ranges and Emu.call does not reset EFLAGS (A1 Q1); under complete resets 3 of 5 xfailed witnesses pass and 2 keep a first difference (B R3-P1, A R3 P1). Equivalent per-side input state is therefore a precondition of a T4 verdict.

## DEC-A12 r1 — Protect effective Watcom 10.0a paths

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r02; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A17 RESOLVED (r04), OBJ-C08 RESOLVED (r04), OBJ-C15 RESOLVED (r04)

> **DEC-A12 r1** · UNANIMOUS · SHA-256 `40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37`  
> *Protect effective Watcom 10.0a paths*
>
> Stage or reject effective Watcom 10.0a paths before launch. Prove that staging preserves source identity, include resolution, flags and output attribution, and isolate temporary outputs per compile. Report path failures as toolchain errors. Use measured limits on effective compiler-facing paths.

**Rationale (editorial).** A Watcom 10.0a path-length failure was observed on EV-3; staging is allowed only when it preserves source identity, include resolution, flags and output attribution.

## DEC-A13 r1 — Admit an independent exact Group B proof

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r02; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A01 RESOLVED (r05), OBJ-A05 RESOLVED (r04), OBJ-A15 RESOLVED (r05), OBJ-B01 RESOLVED (r04), OBJ-C13 WITHDRAWN (r04)

> **DEC-A13 r1** · UNANIMOUS · SHA-256 `c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c`  
> *Admit an independent exact Group B proof*
>
> Permit the exact Group B whole-TU promotion independently of general B1, B2 and matcher rollout only with a commit-bound strict raw-object RegionMatch equivalent to the intended production rules, ordinary file and dual-compiler checks, actual in-place Build A with typed loader comparison, and preserved cited T4 checks or explicit owner approval for changes.

**Rationale (editorial).** E1 Group B links IDENTICAL as a joint -5r TU with current tools (E1; B R0 P3), so this exact case may proceed before generic B1/B2 rollout under an equivalent strict proof.

## DEC-A14 r1 — Bind verification reuse to raw artifacts

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r04)
- **First seen:** r03; **revisions admitted:** 1

> **DEC-A14 r1** · UNANIMOUS · SHA-256 `bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7`  
> *Bind verification reuse to raw artifacts*
>
> Bind each authority-bearing verification or integration receipt to the exact raw artifacts and the verified context used in its claim. A normalized CONST digest may group candidates but shall never substitute for raw identity on authority reuse; reverify before accepting any different raw artifact.

**Rationale (editorial).** CONST pad bytes vary with path/session (B R0, E8 rev-e8-02 normalization), so normalized digests may only group candidates; authority binds to exact raw artifacts and verified context.

## DEC-A15 r1 — Admit M2 infrastructure by demonstrated need [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r04; **revisions admitted:** 1

> **DEC-A15 r1** · UNANIMOUS · SHA-256 `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44`  
> *Admit M2 infrastructure by demonstrated need [editorial title]*
>
> Prioritize M2 by newly satisfied DONE obligations under DEC-A01. Run eligible reconstruction, owner evidence packets and verification hardening on independent tracks. Admit M2 production infrastructure for a demonstrated verification or toolchain defect or a documented blocker to a named in-scope function that is not DONE, including a scoped rename or routing helper when reconstruction is otherwise ready. Keep general B3, selective extraction, E6 beyond a named witness, persistent proof stores and CU databases off the M2 critical path, subject to their own adoption boundaries. M3 Build B does not require optional Build A consolidation.

**Rationale (editorial).** Carries the obligations of withdrawn DEC-B01 r2: independent tracks and infrastructure admitted only for a demonstrated defect or a named not-DONE blocker.

## DEC-A16 r1 — Implement and audit paired T4 state before reclassification [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gpt · **SHA-256:** `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r04; **revisions admitted:** 1

> **DEC-A16 r1** · UNANIMOUS · SHA-256 `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785`  
> *Implement and audit paired T4 state before reclassification [editorial title]*
>
> Implement DEC-A11 for current T4 pairs using independent equivalent initialization or a certified checkpoint. Account for CPU context including EFLAGS, mapped regions and permissions and their contents, host and guest writes, allocator state, and declared mutable host and stub dependencies. Report unsupported cases when equivalence cannot be established. Preserve existing output assertions and record the initial-state method and evidence in the production T4 audit. Before landing, run the full existing T4 suite once with the rule enabled and present any changes to existing test meaning or expected status to the owner. Record the five EV-3 witness outcomes as observations, establish attribution separately, and change inventory or DONE status only on current authorized verification evidence.

**Rationale (editorial).** Operational form of DEC-A11 with audit, suite run and owner presentation; the five EV-3 witness outcomes are observations, not attributions.

## DEC-B01 r2 — M2 admission principle for infrastructure work

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A15 RESOLVED (r05), OBJ-B02 RESOLVED (r04), OBJ-B05 RESOLVED (r04), OBJ-B24 RESOLVED (r04), OBJ-B29 RESOLVED (r05), OBJ-C04 RESOLVED (r05), OBJ-C15 RESOLVED (r04), OBJ-C16 RESOLVED (r05)

> **DEC-B01 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390`  
> *M2 admission principle for infrastructure work*
>
> Until gate 1 passes, a production infrastructure change is admitted only if it removes an observed blocker of named not-done in-scope functions or closes a demonstrated verification or toolchain soundness defect; routine reconstruction work proceeds in parallel and is not serialized behind infrastructure stages. On main@17733f9 the admitted items are: the E0 matcher with strict raw admission (DEC-B02), the single placement planner with integration receipts (DEC-B03), the cross-object transfer rule (DEC-B04, DEC-B19), the B1 leading-byte base (DEC-B05), proof-gated joint TUs (DEC-B06), complete T4 paired-state symmetry (DEC-B18), measured comparator strengthening (DEC-B20) and the compiler-facing path guard (DEC-B22); a deterministic rename/migration helper is admitted when a reconstruction batch demonstrably needs it. Fix B3, selective extraction, E6 Group/Integrated machinery beyond a named witness, persistent provenance stores and CU databases are scheduled on a post-M2/M3 track unless a named not-done function requires them.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A01 and DEC-C07; DEC-A15 later carried its admission rule.

## DEC-B02 r2 — Production adoption of E0 matcher semantics with strict raw admission

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A03 RESOLVED (r04), OBJ-A10 RESOLVED (r04), OBJ-A11 RESOLVED (r04), OBJ-A17 RESOLVED (r04), OBJ-B10 RESOLVED (r04), OBJ-B20 RESOLVED (r04), OBJ-B22 RESOLVED (r07), OBJ-B30 RESOLVED (r04), OBJ-C01 RESOLVED (r04), OBJ-C05 RESOLVED (r04), OBJ-C09 WITHDRAWN (r04)

> **DEC-B02 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed`  
> *Production adoption of E0 matcher semantics with strict raw admission*
>
> tools/wc1/match.py adopts E0 semantics (bidirectional normalized obligations, leading bytes, local-data pointer targets, mutually exclusive verdicts with UNSUPPORTED precedence, untruncated machine findings), reimplemented in tools/ with E0's 55 controls as production tests. Production admission additionally requires strict raw-OMF input checks (record bounds, checksum when nonzero, single MODEND, record-type allow-list, cross-record THREAD state, explicit FRAME preserved) with unsupported input reported as UNSUPPORTED, and the proof is bound to the raw bytes of the exact object later consumed by the build. Local data, including CONST pad bytes, is matched exactly at cutover. A verdict may change from non-MATCH to MATCH only through a new, independently tested proof rule with positive and negative controls, never by relaxing an existing check; function-scoped diagnostic closure may record explicit external edge obligations but never grants placement. The cutover is admitted only if the full current T3 population returns MATCH under make verify.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A02 and DEC-C02.

## DEC-B03 r2 — One planner; promotion requires an integration receipt

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A01 RESOLVED (r05), OBJ-A09 RESOLVED (r05), OBJ-B09 RESOLVED (r04), OBJ-B11 RESOLVED (r04), OBJ-C02 RESOLVED (r04), OBJ-C11 RESOLVED (r05)

> **DEC-B03 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680`  
> *One planner; promotion requires an integration receipt*
>
> wc1.build exposes one planner, plan(p, regions), that computes cuts, entries, cross-object transfer encodings, adjacency obligations and data anchors, plus errors; check_t3_buildable, batch_driver, wave4a, m2_inventory and the emitter all consume that planner. A clean plan is a preflight result only: a function is promoted (src wiring for T3) only with an integration receipt recording the actual assembly, link and comparison (including the checks added by DEC-B20) of the exact plan. Regression tests are mode-qualified: standalone IntroOpSyncSound is rejected when the cross-object transfer rule is disabled or any spanned object is legacy-placed, accepted with recorded Build A debt when the rule is enabled in place, and Group B is accepted with no debt.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A03, DEC-C01 and DEC-C05.

## DEC-B04 r2 — Unified cross-object transfer rule (Build A only)

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0`
- **Live positions:** gpt: CONDITIONAL (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A13 RESOLVED (r04), OBJ-B02 RESOLVED (r04), OBJ-B03 RESOLVED (r04), OBJ-B23 RESOLVED (r04), OBJ-C02 RESOLVED (r04), OBJ-C10 RESOLVED (r04)

> **DEC-B04 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0`  
> *Unified cross-object transfer rule (Build A only)*
>
> In Build A, an ASM relative transfer whose decoded target lies in a different link object is handled by one rule. The instruction is decoded with its exact length, prefixes and next-IP; rel32 to an exported entry stays symbolic. Otherwise it is admitted only if (a) every byte between source and target is supplied by in-place objects of original length (DEC-B19), (b) a target inside a C object lies within that object's VerifiedRegion at an instruction boundary, and it is encoded preferably as a piece-local label expression (assembler-checked range) or else as the original instruction bytes, (c) the assembled field equals the original bytes, and (d) the integration receipt is IDENTICAL. No compiled C object is transformed (no synthesized interior PUBDEF) to serve such a transfer during M2. Each such transfer is recorded as Build A placement debt. Joint TUs (DEC-B06) are preferred when available.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A05 and DEC-C05.

## DEC-B05 r1 — Fix B1 via leading-byte region base

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r03), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1

> **DEC-B05 r1** · UNANIMOUS · SHA-256 `8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac`  
> *Fix B1 via leading-byte region base*
>
> place() accepts an object whose first entry has _TEXT offset k>0 by setting base = first_entry_addr - k, only when RegionMatch (DEC-B02) has verified bytes and obligations of [0,k). Fixups from the leading bytes into the object's own range are internal. The plan must reject overlap with any other cut.

**Rationale (editorial).** Implementation form of DEC-A04 for place(); leading fixups into the object's own range are internal; overlaps are rejected.

## DEC-B06 r1 — Proof-gated multi-function TUs

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r04)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A01 RESOLVED (r05), OBJ-A05 RESOLVED (r04), OBJ-B01 RESOLVED (r04), OBJ-C13 WITHDRAWN (r04)

> **DEC-B06 r1** · UNANIMOUS · SHA-256 `22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc`  
> *Proof-gated multi-function TUs*
>
> A ReconstructedTU may contain several functions when the whole compiled object passes production RegionMatch (all publics MATCH, original spacing) and Build A is IDENTICAL. Immediately: Group B (IntroOpPlaySound, IntroOpSyncSound, IntroOpWaitSound) in one -5r TU. AGENTS.md's "one function per C object" ground rule is reworded accordingly, subject to owner approval. No consolidation is performed on the basis of heuristic CU signals.

**Rationale (editorial).** Joint compilation reproduces shared epilogues in pure C (E1); multi-function TUs are admitted only on whole-object proof and IDENTICAL Build A, with the AGENTS.md ground-rule rewording subject to owner approval.

## DEC-B07 r1 — T4 paired-execution state symmetry

- **Status:** UNANIMOUS_REJECTED (all three explicitly reject the same revision and proposition hash)
- **Origin:** claude · **SHA-256:** `2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b`
- **Live positions:** gpt: REJECT (r03), claude: REJECT (r03), gemini: REJECT (r03)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A12 RESOLVED (r04)

> **DEC-B07 r1** · UNANIMOUS_REJECTED · SHA-256 `2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b`  
> *T4 paired-execution state symmetry*
>
> cemu.run_pair (or t4spec) restores, before the C run, all memory written during the original run (by code or stubs), or fails closed when a stub writes outside the restored set. The audit log records the restored set. After adoption, every xfailed "reference-C divergence" is re-evaluated, and its blocker category is changed only by evidence.

**Rationale (editorial).** Rejected after review: restoring only memory written by the original run is insufficient (CPU/EFLAGS, allocator and stub state also matter); superseded by DEC-A11/DEC-A16/DEC-C16. Withdrawn by its author in r02.

## DEC-B08 r1 — Fix B3 deferred to the M3 track

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A04 RESOLVED (r04), OBJ-B05 RESOLVED (r04)

> **DEC-B08 r1** · UNANIMOUS · SHA-256 `dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a`  
> *Fix B3 deferred to the M3 track*
>
> E5's Fix B3 is recorded as feasible for the verified subset. Its production implementation is scheduled after M2, or earlier only if a not-done function requires it. RFC §8.2's constraints 1–5 remain binding preconditions.

**Rationale (editorial).** E5 is feasible for its verified subset; production B3 waits for post-M2 or a named not-done function, with RFC section 8.2 constraints 1-5 binding.

## DEC-B09 r2 — Region-level T3 and selective extraction deferred pending governance and codec preconditions

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A07 RESOLVED (r04), OBJ-A14 RESOLVED (r04), OBJ-A18 RESOLVED (r04), OBJ-B04 RESOLVED (r04), OBJ-C03 RESOLVED (r04), OBJ-C14 RESOLVED (r04)

> **DEC-B09 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb`  
> *Region-level T3 and selective extraction deferred pending governance and codec preconditions*
>
> E3/E4 are not adopted into production during M2. Any later adoption first requires an owner decision on gate-2 semantics for src files containing mismatching publics (match --all currently fails them); then implementation over a strict shared OMF record/fixup subset with regression tests for the confirmed prototype defects (per-record THREAD reset, non-_TEXT PUBDEF/LPUBDEF rebasing, linear decode across tables) and rev-e4-01 F1-F4; record-size limits tested against the actual linker; then the RFC §16 criteria.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A07 and DEC-C08.

## DEC-B10 r1 — Corrected Watcom 10.0a alignment model

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1

> **DEC-B10 r1** · UNANIMOUS · SHA-256 `51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0`  
> *Corrected Watcom 10.0a alignment model*
>
> The RFC and docs/subsystems/compiler.md state that 10.0a function spacing inside an object is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot, and 1 byte under -os/-od, with a PARA _TEXT SEGDEF for -ot. OW2 uses 16 bytes under -4r and -5r. This describes compiler behaviour and is not a claim about original CU flags.

**Rationale (editorial).** E2 measured the alignment matrix; the RFC's '10.0a always aligns to 4 bytes' premise was wrong. The statement is about compiler behaviour, not original flags.

## DEC-B11 r1 — Presets remain additive; no global default change

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1

> **DEC-B11 r1** · UNANIMOUS · SHA-256 `c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5`  
> *Presets remain additive; no global default change*
>
> The merged E7 presets stay additive to each file's declared flags; the project default stays -4r; S(f) is recorded per reconstructed-TU context and never promoted to a CU flag claim.

**Rationale (editorial).** Presets add to declared flags; -4r stays the default (E7: 0/417 regressions on -4r to -5r is not a historical-flag claim).

## DEC-B12 r1 — E6 adoption on demand

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3`
- **Live positions:** gpt: CONDITIONAL (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-B25 RESOLVED (r04)

> **DEC-B12 r1** · WITHDRAWN_SUPERSEDED · SHA-256 `7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3`  
> *E6 adoption on demand*
>
> Production cemu adopts symbol_aware_reloc for declared out-of-boundary dependencies, and VerificationBoundary/callback execution, only when a T4 needed for M2 requires Group mode with intra-TU calls or callbacks. Until then the existing whole-object c_stubbed rule remains. c_entry_hook is kept as defence in depth.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A08 and DEC-C11.

## DEC-B13 r2 — CU recovery is a premise-carrying constraint graph, analyst-facing only

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A06 RESOLVED (r04), OBJ-A16 RESOLVED (r04), OBJ-B12 RESOLVED (r04), OBJ-B13 RESOLVED (r04), OBJ-B26 RESOLVED (r04), OBJ-C07 RESOLVED (r04)

> **DEC-B13 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3`  
> *CU recovery is a premise-carrying constraint graph, analyst-facing only*
>
> CU recovery is analyst-facing only. shared_epilogue is a proven one-directional merge constraint only under stated producer premises (both functions compiler-generated by wcc386, correct block partition, no link-time tail merging or hand-written bridge). non_16_aligned_start is conditional on the actual segment base of a PARA-aligned next object, not on a function start that may follow leading bytes. shared_const_string_literal is conditional merge evidence that requires excluding explicit shared storage and linker pooling. zero16, none16, style_transition and S(f)-disjointness are candidate generators. Staircase breaks and call-locality drops are not used. No tool creates CU boundaries or consolidates sources automatically. compilation_units.toml is deferred to M3.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A10 and DEC-C12.

## DEC-B14 r1 — Minimal entity implementation for M2

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A07 RESOLVED (r04), OBJ-B09 RESOLVED (r04)

> **DEC-B14 r1** · UNANIMOUS · SHA-256 `18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd`  
> *Minimal entity implementation for M2*
>
> For M2 the production entity set is: VerifiedRegion (immutable, matcher-minted), the single PlacementPlan (derived), and the existing ReconstructedTU/CompiledObject. CandidateRegion is not a separate type. OriginalCUHypothesis and SemanticVerificationUnit get no new storage. Persistent evidence_digest provenance is deferred until a consumer exists.

**Rationale (editorial).** No consumer yet exists for CandidateRegion as a type, CU storage or persistent provenance; the minimal entity set avoids a second metadata store.

## DEC-B15 r1 — Experimental code is evidence, not production

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-B13 RESOLVED (r04)

> **DEC-B15 r1** · UNANIMOUS · SHA-256 `c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387`  
> *Experimental code is evidence, not production*
>
> No production module imports from experiments/. Each adopted mechanism is reimplemented in tools/wc1 at the minimum scope required, with the experiment's controls ported as tests, and is gated by make verify.

**Rationale (editorial).** Experiment code is evidence; production reimplements the minimum scope with the experiment controls ported as tests.

## DEC-B16 r1 — Inventory reclassification from probes

- **Status:** UNANIMOUS_REJECTED (all three explicitly reject the same revision and proposition hash)
- **Origin:** claude · **SHA-256:** `ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c`
- **Live positions:** gpt: REJECT (r03), claude: REJECT (r04), gemini: REJECT (r03)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A15 RESOLVED (r05), OBJ-C12 RESOLVED (r04)

> **DEC-B16 r1** · UNANIMOUS_REJECTED · SHA-256 `ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c`  
> *Inventory reclassification from probes*
>
> wc1.m2_inventory reclassifies 0x2315c/0x23170/0x231cc as "joint-TU T3 available (DEC-B06)", 0x1e380/0x2e96c/0x2efd0/0x2f73c as "fixed-displacement cross-object branches (DEC-B04)", and the IntroOpWaitSound divergence as "T4 harness state asymmetry (DEC-B07)".

**Rationale (editorial).** Rejected: reclassifying inventory from disposable probes would assign status without production verification. Withdrawn by its author in r02.

## DEC-B17 r1 — Integrated selective extraction (Approach D) as the M2 strategy

- **Status:** UNANIMOUS_REJECTED (all three explicitly reject the same revision and proposition hash)
- **Origin:** claude · **SHA-256:** `0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1`
- **Live positions:** gpt: REJECT (r03), claude: REJECT (r04), gemini: REJECT (r03)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-C03 RESOLVED (r04)

> **DEC-B17 r1** · UNANIMOUS_REJECTED · SHA-256 `0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1`  
> *Integrated selective extraction (Approach D) as the M2 strategy*
>
> Selective OMF extraction is adopted in production as the mechanism for advancing M2.

**Rationale (editorial).** Rejected: extraction as the M2 strategy conflicts with the deferral and owner-gate conditions of DEC-A07/DEC-C08.

## DEC-B18 r2 — Complete paired starting state for all T4 runs

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r01; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A12 RESOLVED (r04), OBJ-A20 RESOLVED (r05), OBJ-B06 RESOLVED (r04), OBJ-B18 RESOLVED (r04), OBJ-B21 RESOLVED (r04), OBJ-B28 RESOLVED (r04), OBJ-C12 RESOLVED (r04)

> **DEC-B18 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2`  
> *Complete paired starting state for all T4 runs*
>
> Each T4 pair runs both sides from an equivalent complete starting state: CPU context (general registers, EFLAGS, segment registers and ESP), the full set of mapped memory regions and their contents (covering host and guest writes), emulator allocator state, and declared mutable stub state. Stubs keep mutable state in emulator memory or declare a per-run reset; otherwise the case reports UNSUPPORTED. State restoration is separate from the effects each test compares, and the audit log records the restored state. The rule applies to all T4 tests. Before landing, the full T4 suite runs once with the rule enabled; any change in an existing test's outcome or xfail status is presented to the owner. Reclassification of a divergence follows only from the test result after the change.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A11 and DEC-C16; DEC-A16 later carried its operating obligations.

## DEC-B19 r2 — Plan-level exclusion of legacy-placed objects and fallthrough adjacency

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** claude · **SHA-256:** `5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r03)
- **First seen:** r01; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-B03 RESOLVED (r04), OBJ-B27 RESOLVED (r04), OBJ-C02 RESOLVED (r04), OBJ-C10 RESOLVED (r04)

> **DEC-B19 r2** · UNANIMOUS · SHA-256 `5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d`  
> *Plan-level exclusion of legacy-placed objects and fallthrough adjacency*
>
> The placement planner rejects any fixed-displacement cross-object transfer whose source-to-target span includes an object placed in legacy layout, whether by the global --legacy flag or the automatic per-object Unplaceable fallback, and records an adjacency obligation for every ASM piece that falls through into the next object, rejecting the plan if that successor is not the original in-place object.

**Rationale (editorial).** Per-object automatic legacy fallback exists (build.py Unplaceable path); a fixed displacement across a legacy-placed object would be unsound, and fallthrough requires the original successor.

## DEC-B20 r1 — Comparator coverage measured, then strengthened

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a`
- **Live positions:** gpt: CONDITIONAL (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r01; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A02 RESOLVED (r04), OBJ-A19 RESOLVED (r04), OBJ-A21 RESOLVED (r04), OBJ-B19 RESOLVED (r04)

> **DEC-B20 r1** · WITHDRAWN_SUPERSEDED · SHA-256 `9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a`  
> *Comparator coverage measured, then strengthened*
>
> Before any new placement path is admitted, measure the object flags, page/fixup records and fixup types of the current Build A against the original. If they agree, extend wc1.compare to compare them (strengthen-only). If they differ, present the difference to the owner before changing the Build A oracle.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A03 and DEC-C15 (DEC-C15 itself later withdrawn into DEC-A02/DEC-C02/DEC-A03).

## DEC-B21 r2 — CONST pad bytes are environment-dependent and exempt only on independent access proof

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f`
- **Live positions:** gpt: CONDITIONAL (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r01; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A11 RESOLVED (r04), OBJ-B22 RESOLVED (r07), OBJ-B30 RESOLVED (r04), OBJ-C01 RESOLVED (r04), OBJ-C09 WITHDRAWN (r04)

> **DEC-B21 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f`  
> *CONST pad bytes are environment-dependent and exempt only on independent access proof*
>
> Watcom 10.0a CONST inter-literal pad bytes are environment-dependent (they vary with compile-input paths and are stable for fixed inputs in our probes) and are excluded from proof-cache digests by normalization. No exemption from exact data matching is granted on the basis of literal shape or the absence of relocation targets; any future exclusion requires independent extent, ownership and access evidence covering computed reads, is applied identically by the matcher and build.place(), and keeps ASM as the Build A physical provider. Until then such objects fail closed and the extern-literal idiom remains available.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A02 and DEC-C10; normalized digests are unsound as authority keys (DEC-A14).

## DEC-B22 r1 — Measured compiler-facing path guard in wc1.oldcc

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** claude · **SHA-256:** `1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c`
- **Live positions:** gpt: ACCEPT (r03), claude: REJECT (r03), gemini: REJECT (r04)
- **First seen:** r02; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A17 RESOLVED (r04), OBJ-C08 RESOLVED (r04), OBJ-C15 RESOLVED (r04)

> **DEC-B22 r1** · WITHDRAWN_SUPERSEDED · SHA-256 `1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c`  
> *Measured compiler-facing path guard in wc1.oldcc*
>
> wc1.oldcc fails fast with a toolchain error (exit 78 path) when any compiler-facing argument (source, -fo output, -i= include, working directory) exceeds a measured safe Windows-path length, the limit being set from a measured envelope of the installed Watcom 10.0a under Wine rather than a fixed guess; a staging scheme to keep paths short may follow if it is proven to leave compiled bytes and include resolution unchanged.

**Rationale (editorial).** Withdrawn by its author (r03) into DEC-A12 and DEC-C04.

## DEC-C01 r3 — Four verification and integration outcomes [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r00; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A09 RESOLVED (r05), OBJ-B09 RESOLVED (r04), OBJ-B11 RESOLVED (r04)

> **DEC-C01 r3** · UNANIMOUS · SHA-256 `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de`  
> *Four verification and integration outcomes [editorial title]*
>
> Maintain four explicit verification and integration outcomes: FunctionMatch (local body diagnostic with explicit external context obligations), RegionMatch -> immutable matcher-minted VerifiedRegion (closed object/region proof), PlacementPlan (single derived preflight partition plan shared by check_t3_buildable, wc1.build, wc1.emit, batch_driver, wave4a, and m2_inventory), and IntegratedResult (actual assemble, link, and hardened wc1.compare receipt). Do not add a separate CandidateRegion runtime class or persistent proof/CU metadata DB in M2.

**Rationale (editorial).** Names the four outcome levels so that local diagnostics, region proof, preflight and integration cannot be confused by consumers; no CandidateRegion class or proof DB in M2 (consistent with DEC-B14).

## DEC-C02 r2 — Production E0 verifier with 55 controls and live cutover audit [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A10 RESOLVED (r04), OBJ-B20 RESOLVED (r04)

> **DEC-C02 r2** · UNANIMOUS · SHA-256 `8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b`  
> *Production E0 verifier with 55 controls and live cutover audit [editorial title]*
>
> Reimplement E0 bidirectional Normalized Addressing Obligation verification in tools/wc1/match.py (importing nothing from experiments/) with strict raw-OMF admission (record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, preserved explicit FRAME encodings) and all 55 controls as production tests, audited over every live declared T3 at cutover. Evaluate FunctionMatch intra-function branch closure against [orig_fn.start, orig_fn.start + fn_len) while attaching explicit sibling-context obligations (never minting placement permission); preserve trimmed_branch_target across all modes; fail closed on CONST pad mismatches (no Stage-0 V4 dependency).

**Rationale (editorial).** Detailed production form of DEC-A02 (controls, raw admission, function-extent closure, trimmed-branch preservation, fail-closed CONST pad).

## DEC-C03 r1 — Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (Invariant V4)

- **Status:** UNANIMOUS_REJECTED (all three explicitly reject the same revision and proposition hash)
- **Origin:** gemini · **SHA-256:** `2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896`
- **Live positions:** gpt: REJECT (r03), claude: REJECT (r04), gemini: REJECT (r03)
- **First seen:** r00; **revisions admitted:** 1
- **Objections referencing it (closing round):** OBJ-A11 RESOLVED (r04), OBJ-B20 RESOLVED (r04), OBJ-B22 RESOLVED (r07), OBJ-B30 RESOLVED (r04)

> **DEC-C03 r1** · UNANIMOUS_REJECTED · SHA-256 `2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896`  
> *Adopt Strict 5-Condition Watcom 10.0a `CONST` Uninitialized Alignment-Gap Rule (Invariant V4)*
>
> In both E0 `RegionMatch` and Stage-3 Fix B3, explicitly exempt 1..3-byte alignment padding gaps in `CONST` **if and only if** all 5 conditions hold: (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A.

**Rationale (editorial).** Rejected: a shape-only CONST gap rule admits gaps that computed or overlapping reads may observe (A1 Q2); superseded by DEC-A02/DEC-A14/DEC-C10.

## DEC-C04 r2 — Measured compiler-facing path guard in wc1.oldcc [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A17 RESOLVED (r04), OBJ-C15 RESOLVED (r04)

> **DEC-C04 r2** · UNANIMOUS · SHA-256 `083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37`  
> *Measured compiler-facing path guard in wc1.oldcc [editorial title]*
>
> Implement a measured compiler-facing Windows-path length guard and short-path staging policy in tools/wc1/oldcc.py checking all compiler-facing arguments (source, -fo, -i=, TMPDIR, translated Z: paths), failing fast with [TOOLCHAIN ERROR] before Watcom 10.0a path-buffer crashes while verifying unchanged compile/include semantics across checkout depths. (The three t3_audit.py R3 defects from rev 1 are delivered and closed as of EV-3 main@17733f9.)

**Rationale (editorial).** Detailed form of DEC-A12 for wc1.oldcc; the rev-1 t3_audit defects were delivered by EV-3.

## DEC-C05 r4 — Fix B1 and unified Fix B2 inside the single PlacementPlan [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `5d51b22bcefa20d67842a75dd643b9ee3856fd9486b15318bb977ea80b76ce68`
- **Live positions:** gpt: ACCEPT (r07), claude: ACCEPT (r07), gemini: ACCEPT (r07)
- **First seen:** r00; **revisions admitted:** 1, 2, 3, 4
- **Objections referencing it (closing round):** OBJ-A13 RESOLVED (r04), OBJ-B23 RESOLVED (r04)

> **DEC-C05 r4** · UNANIMOUS · SHA-256 `5d51b22bcefa20d67842a75dd643b9ee3856fd9486b15318bb977ea80b76ce68`  
> *Fix B1 and unified Fix B2 inside the single PlacementPlan [editorial title]*
>
> Implement Fix B1 (leading-byte region base first_entry_addr - first_entry_off gated on E0 RegionMatch of [0,k), zero overlap/foreign entry, branch analysis using physical table_start) and Unified Fix B2 inside the single derived PlacementPlan: keep extern symbolic rel32 for exported entries; emit remaining cross-object ASM relative branches (B2-interior, B2-entry, B2-span, and rel32-interior such as 0x2f6df with zero M2 OMF PUBDEF synthesis) via NASM piece-local label expressions (preferred, using decoded next_ip = ia + insn.size and typed encodings with assembled-byte verification) or verified literal displacement fallback, requiring verified original target identity, zero intersecting relocation over fixed displacement fields, and physical adjacency for every live cross-piece fallthrough per DEC-A05 r2, strictly rejecting any span containing a global --legacy or automatic per-object Unplaceable legacy-placed object (DEC-B19 r2), recording Build A placement debt, and requiring IntegratedResult with hardened wc1.compare (DEC-A03 r2). Qualify IntroOpSyncSound standalone regression tests by mode: rejected under legacy or B2-disabled, accepted only with explicit B2-span debt under in-place B2, zero debt as Group B.

**Rationale (editorial).** Detailed form of DEC-A04/DEC-B05 (B1) and DEC-A05/DEC-B19 (B2) inside the single plan, with mode-qualified IntroOpSyncSound tests; r4 removes the citation of withdrawn DEC-C15.

## DEC-C06 r2 — Proof-gated multi-function TUs; Group B pilot [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2

> **DEC-C06 r2** · UNANIMOUS · SHA-256 `ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23`  
> *Proof-gated multi-function TUs; Group B pilot [editorial title]*
>
> Admit proof-gated multi-function ReconstructedTUs when the whole compiled object passes RegionMatch and Build A IntegratedResult, preferring whole-TU co-compilation over B2 placement debt for shared-epilogue clusters. Pilot E1 Group B (IntroOpPlaySound 0x2315c, IntroOpSyncSound 0x23170, IntroOpWaitSound 0x231cc) as an independent -5r TU without waiting on generic B2, subject to owner confirmation of AGENTS.md ground-rule wording, dual-compiler checks, full make verify, and owner review of any xfailed PLAYFLIC test adjustment.

**Rationale (editorial).** Prefers whole-TU co-compilation over B2 placement debt for shared-epilogue clusters; Group B pilot with owner checkpoints.

## DEC-C07 r3 — M2 parallel tracks and deferrals (EV-3 instantiation) [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `4756b13b2fde6f82475c1180e4d5c0102effb4dccda5c6936d8e93b6adf84a9f`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r00; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A15 RESOLVED (r05), OBJ-B18 RESOLVED (r04), OBJ-B24 RESOLVED (r04), OBJ-B29 RESOLVED (r05)

> **DEC-C07 r3** · UNANIMOUS · SHA-256 `4756b13b2fde6f82475c1180e4d5c0102effb4dccda5c6936d8e93b6adf84a9f`  
> *M2 parallel tracks and deferrals (EV-3 instantiation) [editorial title]*
>
> Prioritize genuine M2 completion (98 remaining not-DONE on EV-3 main@17733f9) via parallel tracks: (a) Stage 0/1 verification hardening, single planner, B1/B2, independent Group B pilot (DEC-A13), and complete T4 paired-state symmetry (DEC-A11 / DEC-C16 r3, recording the three passing witnesses and two persistent witness differences under R3 P1 as diagnostic observations with no new DONE credit until production-equivalent verification and owner review pass); (b) routine area reconstruction (BULLET.C and the 61+7 name/C backlog, supported by lightweight deterministic rename/Wave 3R enablers when demonstrably needed, reporting reconstruction yield as an upper bound rather than a deterministic guarantee); and (c) owner evidence packets for the 8 scope/discovery items. Defer Fix B3, selective extraction (E3/E4), and CU hypothesis databases to the post-M2/M3 track; admit E6 boundary machinery earlier only for a named necessary witness; decouple M3 Build B from optional Build A consolidation paths.

**Rationale (editorial).** EV-3 instantiation of DEC-A01/DEC-A15: parallel tracks, upper-bound yield, diagnostic witness wording, deferrals, Build B decoupled.

## DEC-C08 r2 — No selective extraction in M2; post-M2 pilot preconditions [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A14 RESOLVED (r04), OBJ-A18 RESOLVED (r04)

> **DEC-C08 r2** · UNANIMOUS · SHA-256 `6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00`  
> *No selective extraction in M2; post-M2 pilot preconditions [editorial title]*
>
> REJECT adopting experiments/build_codegen/e4/omf_extract.py@e6150b8 or selective OMF extraction during M2 or as a default consolidation path. Whole-TU RegionMatch is the primary integration path. Any future narrow post-M2 extraction pilot requires: (1) explicit owner decision on Gate-2 / match --all semantics for src files with mismatching publics (DEC-B09); (2) proven canonical-TU benefit; (3) implementation over the shared strict OMF32 subset (DEC-C09) fixing confirmed Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), Probe 5c (typed table/code model), and rev-e4-01 F1-F4; and (4) post-transform verification and Build A IntegratedResult (without mandating unproved 64-fixup chunking or exhaustive Wave 4B).

**Rationale (editorial).** Detailed form of DEC-A07: whole-TU RegionMatch is primary; a post-M2 pilot needs owner gate-2 decision, proven benefit, strict codec and fixed E4 defects.

## DEC-C09 r3 — Shared strict OMF32 codec before B3 or extraction [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r00; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A18 RESOLVED (r04), OBJ-C03 RESOLVED (r04), OBJ-C14 RESOLVED (r04)

> **DEC-C09 r3** · UNANIMOUS · SHA-256 `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b`  
> *Shared strict OMF32 codec before B3 or extraction [editorial title]*
>
> Before landing Fix B3 or any future selective OMF extraction pilot (post-M2), share one tested strict OMF32 record/fixup codec (record bounds, nonzero checksums, preserved explicit FRAME encodings, persistent cross-record THREAD, format/linker-verified record-length bounds) across verification and admitted OMF transforms, while leaving permissive library-signature readers untouched and avoiding unnecessary omfpatch refactoring during M2.

**Rationale (editorial).** One strict codec prevents verification and transforms from diverging on record bounds, checksums, FRAME and THREAD; permissive readers are untouched.

## DEC-C10 r3 — Data ownership separation, post-M2 B3, raw authority [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `a8756e094f269537ac7342f0d2c9361af01a4a63c54c1966a9c9d5fe6bea1e19`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r00; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A11 RESOLVED (r04)

> **DEC-C10 r3** · UNANIMOUS · SHA-256 `a8756e094f269537ac7342f0d2c9361af01a4a63c54c1966a9c9d5fe6bea1e19`  
> *Data ownership separation, post-M2 B3, raw authority [editorial title]*
>
> Keep semantic_owner separate from physical_provider and defer Fix B3 to the post-M2/M3 track (triggered by justified need such as Q-B08). Admit B3 initially for strictly verified whole segments over the shared strict OMF32 subset (DEC-C09 r3) with RFC §8.2 constraints 1-5 and rev-e5-02 mutability/aliasing guards. Enforce DEC-A14 r1 on all authority-bearing receipts: normalized CONST digests may group candidates only and never substitute for exact raw-artifact identity on authority reuse. Any future CONST inter-literal alignment-gap rule must additionally: apply identically in matcher and build.place(), force Build A physical_provider = ASM, be explicitly disclosed in the proof receipt, and require independent extent/access evidence ruling out computed or overlapping reads (OBJ-A11).

**Rationale (editorial).** Detailed post-M2 B3 contract, binding DEC-A14 on authority-bearing receipts and constraining any future CONST gap rule.

## DEC-C11 r2 — Paired state now; E6 machinery on demand [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A12 RESOLVED (r04), OBJ-B21 RESOLVED (r04), OBJ-B25 RESOLVED (r04), OBJ-B28 RESOLVED (r04)

> **DEC-C11 r2** · UNANIMOUS · SHA-256 `46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090`  
> *Paired state now; E6 machinery on demand [editorial title]*
>
> Keep full paired initial-state symmetry (DEC-A11/DEC-B18/DEC-C16) mandatory immediately for ALL T4 tests (single- and multi-function), independent of E6. Adopt E6 multi-function machinery (contiguous VerificationBoundary, symbol_aware_reloc primary + c_entry_hook defense in depth, generator callbacks with pre-restore ABI checks on PRESERVED_REGS ebx/ecx/edx/esi/edi/ebp plus esp, R2 typed pointer identity, and full t4spec production audit parity per DEC-A08) on demand whenever any M2 or post-M2 witness requires substituting an intra-TU sibling, executing real callbacks, or comparing logical pointer identities; treat switch-table relaxation and LogicalConstDataPtr (EXP-4) as optional extensions when needed.

**Rationale (editorial).** Detailed form of DEC-A08/DEC-A11: paired state mandatory now; E6 components adopted on witness demand.

## DEC-C12 r2 — CU recovery as analyst-facing constraint graph [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa`
- **Live positions:** gpt: ACCEPT (r04), claude: ACCEPT (r04), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A16 RESOLVED (r04), OBJ-B26 RESOLVED (r04)

> **DEC-C12 r2** · UNANIMOUS · SHA-256 `7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa`  
> *CU recovery as analyst-facing constraint graph [editorial title]*
>
> Explicitly REJECT _DATA/_BSS staircase splits, call_locality_drop, none16 auto-splits, weighted CU boundary scoring, empty-S(f) auto-splitting, and any automatic mutation of analysis/modules.toml or automatic source consolidation. Maintain original CU recovery strictly as an analyst-facing premise-carrying constraint graph (storage deferred to M3): shared_epilogue as a one-directional merge constraint under verified compiler/linker provenance; non_16_aligned_start evaluated at the actual segment base under a PARA-segment premise (with measured corpus precision 0.800/0.836/0.618, never 100%); shared_const_string_literal as conditional premise-dependent evidence requiring exclusion of explicit shared externs and linker pooling; filenames, zero16, none16, style_transition, and S(f)-disjointness as candidate generators preserving competing hypotheses.

**Rationale (editorial).** E8 refuted _DATA/_BSS staircase and call-locality splits and quantified zero16 recall gaps; signals stay analyst-facing with premises.

## DEC-C13 r3 — E2 alignment matrix replaces RFC alignment premise [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r00; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A06 RESOLVED (r04), OBJ-A16 RESOLVED (r04), OBJ-B07 RESOLVED (r04), OBJ-B26 RESOLVED (r04), OBJ-C06 RESOLVED (r04)

> **DEC-C13 r3** · UNANIMOUS · SHA-256 `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02`  
> *E2 alignment matrix replaces RFC alignment premise [editorial title]*
>
> Replace RFC §2.2.5 alignment premises with E2 empirically measured compiler behavior: Watcom 10.0a function spacing is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot (with PARA 16-byte _TEXT SEGDEF for tested -ot), and 1 byte under -os/-od; OW2 uses 16 bytes under -4r and -5r. Keep -4r as the single-file project default with additive E7 presets (DEC-B11), rank -5r as the first-tried candidate family for multi-function -ot TUs requiring 4-byte spacing without claiming it was the universal 1994 project flag, and keep EXP-2/Q-B06 (5r -d1+ -zp1 and 5r -od) as optional additive probes.

**Rationale (editorial).** Detailed form of DEC-B10/DEC-B11 with -5r as a context-specific first candidate and EXP-2 optional.

## DEC-C14 r1 — Reject Premature Multi-Backend Framework Abstractions in Warcraft I

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf`
- **Live positions:** gpt: ACCEPT (r02), claude: ACCEPT (r03), gemini: ACCEPT (r02)
- **First seen:** r00; **revisions admitted:** 1

> **DEC-C14 r1** · UNANIMOUS · SHA-256 `66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf`  
> *Reject Premature Multi-Backend Framework Abstractions in Warcraft I*
>
> REJECT introducing abstract multi-backend/plugin frameworks (`ICompilerBackend`, `IObjectFormatPlugin`, generic binary-rewriting frameworks) into `tools/wc1/`. Enforce architectural portability strictly via clean module boundaries and data-oriented contracts (`omf.py`, `match.py`, `build.py`, `cemu.py`).

**Rationale (editorial).** No consumer exists for multi-backend frameworks; portability is kept through module boundaries and data contracts.

## DEC-C15 r2 — Stage-0 strict raw-OMF admission and hardened wc1.compare typed LE verification

- **Status:** WITHDRAWN_SUPERSEDED (author withdrew this revision in favour of other decisions; withdrawal does not approve the replacement propositions)
- **Origin:** gemini · **SHA-256:** `a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc`
- **Live positions:** gpt: CONDITIONAL (r05), claude: CONDITIONAL (r05), gemini: REJECT (r05)
- **First seen:** r01; **revisions admitted:** 1, 2
- **Objections referencing it (closing round):** OBJ-A02 RESOLVED (r04), OBJ-A03 RESOLVED (r04), OBJ-A19 RESOLVED (r04), OBJ-A21 RESOLVED (r04), OBJ-B19 RESOLVED (r04)

> **DEC-C15 r2** · WITHDRAWN_SUPERSEDED · SHA-256 `a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc`  
> *Stage-0 strict raw-OMF admission and hardened wc1.compare typed LE verification*
>
> In Stage 0, enforce strict raw-OMF admission over the supported subset before production verification (record bounds, checksum when nonzero, single MODEND, record-type allow-list, persistent cross-record THREAD state, preserved explicit FRAME encodings, bound to the exact raw object bytes consumed by the build), and harden tools/wc1/compare.py to validate all raw physical fixup occurrences for typed agreement, supported placement/ordering, and page coverage before deduplicating agreeing page-straddle copies, then enforce equality on the measured-identical LE loader attributes (object flags, entry/stack, module flags, page size/count, page map, fixup page offsets, raw grouping multiset) and normalized typed fixups (src_type and target), keeping measured serialization-only deltas (raw fixup serialization order and 1-byte last-page file size) diagnostic unless loader relevance is established and escalating any genuine mismatch to the owner.

**Rationale (editorial).** Withdrawn by its author (r05) into DEC-A02, DEC-C02 and DEC-A03 after OBJ-A24: hard equality on raw grouping and fixup-page offsets lacked established loader relevance (A R4 P1).

## DEC-C16 r3 — T4 witness observations and complete paired-state mechanism [editorial title]

- **Status:** UNANIMOUS (all three explicitly accept the same current revision and hash with no conditions)
- **Origin:** gemini · **SHA-256:** `d4fe9e9c5ce5769a66512b4f53cb098344d2bd5b7d233d64c2837f2f217fecbb`
- **Live positions:** gpt: ACCEPT (r05), claude: ACCEPT (r05), gemini: ACCEPT (r05)
- **First seen:** r01; **revisions admitted:** 1, 2, 3
- **Objections referencing it (closing round):** OBJ-A12 RESOLVED (r04), OBJ-A20 RESOLVED (r05), OBJ-B18 RESOLVED (r04), OBJ-C12 RESOLVED (r04)

> **DEC-C16 r3** · UNANIMOUS · SHA-256 `d4fe9e9c5ce5769a66512b4f53cb098344d2bd5b7d233d64c2837f2f217fecbb`  
> *T4 witness observations and complete paired-state mechanism [editorial title]*
>
> Record the independently observed 3-passing (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2-persistent (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc) witness results under checkpoint restoration strictly as diagnostic observations; attribute root causes and update inventory, DONE, or xfail status only after production-equivalent verification, nonce-bound WC1_T4_AUDIT_LOG evidence, full T4 suite regression (Q-B05), and owner review. Adopt complete paired starting-state equivalence (per DEC-A11) in tools/wc1/cemu.py::run_pair across all T4 tests via independent initialization or a certified checkpoint: identical per-side CPU context (general registers, EFLAGS, segment registers, ESP), full set of mapped memory regions covering both host and guest writes, emulator allocator state, and declared mutable stub state (stubs must keep mutable state in emulator memory or declare a per-run reset, else report UNSUPPORTED); keep state restoration strictly separate from compared test effects and log restored state in WC1_T4_AUDIT_LOG.

**Rationale (editorial).** Mechanism and diagnostic record for DEC-A11/DEC-A16; attribution and status changes wait for production evidence and owner review.
