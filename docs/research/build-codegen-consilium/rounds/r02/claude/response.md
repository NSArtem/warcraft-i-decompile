# Consilium R2 — Responses and Position Revision, Architect B (Claude, `claude-opus-5-5`)

- **Round:** 2. Evidence: EV-1 baseline with EV-2/EV-3; no new evidence revision.
- **Inputs read in full:**
  - `r02-inbox/00-PROPOSITION-INDEX.json` (sha `62db5e6a…`)
  - `01-architect-gpt-crossreview.md` (sha `482cbb19…`, 513 lines)
  - `02-architect-gemini-crossreview.md` (sha `aecdde79…`, 658 lines)
- **Note on what C reviewed.** Architect C's cross-review addressed my **Round 0** position. Several of C's points (B16's scope, the 3/5 split, compare completeness) I had already reached independently in my Round 1 review. I still answer each one here.
- **Hashes.** Every proposition hash below for a revised or new B decision is the SHA-256 of the exact proposition text shown. It was computed by `runtime/claude/r02/props.py`; the JSON is in `runtime/claude/r02/props.json`. For unchanged decisions I use the index hash.

---

## 1. Disposition of objections and challenges directed at me

| # | Source | Attacks | Disposition |
|---|---|---|---|
| 1 | **OBJ-A09** (A) | DEC-B03: "planner returns no error and emitter accepts" defines buildability | **UPHOLD** |
| 2 | **OBJ-A10** (A) | DEC-B02 / R0 I-1 "matcher changes may only turn MATCH into non-MATCH" | **UPHOLD (partially)** |
| 3 | **OBJ-A12** (A) | DEC-B07 / DEC-B18: memory-only restoration | **UPHOLD** |
| 4 | **OBJ-A13** (A) | DEC-B04: literal displacement leaves encoding checks implicit; prefixed `jcxz` | **UPHOLD on the requirement, REBUT on the failure claim for literal copies** |
| 5 | **OBJ-A15** (A) | DEC-B16 turns probe results into status labels; B §8 S5 serializes reconstruction behind S3 | **UPHOLD** |
| 6 | **OBJ-A16** (A) | DEC-B13: hard epilogue rule needs producer premises; PARA at segment base | **UPHOLD** |
| 7 | **OBJ-A17** (A) | DEC-B02 lacks non-lossy raw binding | **UPHOLD** |
| 8 | A on **DEC-B01** | A closed list obscures dependencies | **UPHOLD** |
| 9 | A on **DEC-B12** | Allow a later justified consumer, not only M2 | **UPHOLD** (no wording change needed; see §2) |
| 10 | **OBJ-C09** / C §2.1 (C) | DEC-B02 / DEC-B08 omit CONST-pad handling; "flaky, non-deterministic" | **REBUT** (V4 is not the remedy) / **UNRESOLVED** (the nondeterminism detail only) |
| 11 | **OBJ-C10** / C §2.2 (C) | DEC-B04: raw literal bytes; rel32-interior should be a symbolic synthesized PUBDEF; fallthrough unguarded; comparator incomplete | **UPHOLD** on piece-local encoding, fallthrough and comparator; **REBUT** on PUBDEF synthesis |
| 12 | **OBJ-C11** (C) | DEC-B03's regression test contradicts DEC-B04 | **UPHOLD** |
| 13 | **OBJ-C12** (C) | DEC-B16 reclassifies only one function; S4 "up to +4" | **UPHOLD** (already conceded in my R1) |
| 14 | **OBJ-C13** (C) | DEC-B06: Group B should land after the production E0 matcher | **REBUT** as a requirement; offered compromise |
| 15 | **OBJ-C15** (C) | The `oldcc` short-path guard is missing from my M2 set | **UPHOLD** |
| 16 | **OBJ-C16** (C) | DEC-B01 omits the symbol-migration / Wave 3R tooling | **UPHOLD (partially)** |
| 17 | C on **DEC-B02** | Add V2 function-scoped closure, `trimmed_branch_target` and V4 | **UPHOLD** V2 (in A's form) and `trimmed_branch_target`; **REBUT** V4 |
| 18 | C on **DEC-B08** | Add V4 and the unified codec | **REBUT** V4; codec covered by DEC-B09 rev 2 |
| 19 | C on **DEC-B09** | Add the E4 prototype defects | **UPHOLD** |
| 20 | C on **DEC-B12** | E6 as a hard gate before any post-M2 multi-function T4 consolidation | **REBUT** |
| 21 | C on **DEC-B13** | Retain `shared_const_string_literal` as a conditional constraint | **UPHOLD** |
| 22 | C §3.1, §4.2 (C) | "IDENTICAL is a complete check" | **UPHOLD** (already conceded in R1 as OBJ-B19) |

**Details.**

1. **OBJ-A09 — UPHOLD.**
   - A planner and emitter that agree on a plan prove *encodability under the model*. They do not prove what NASM, wlink and the loader actually do: parser errors, frames, link resolution, and loader attributes the comparator does not see (OBJ-A02).
   - My R0 design used "plan clean and emitter accepts" as the definition of buildable. That would let a consumer such as `batch_driver` promote before an artifact exists.
   - **Change:** DEC-B03 rev 2 separates the preflight (shared plan) from promotion, which requires an integration receipt from the actual assemble, link and compare of that exact plan.

2. **OBJ-A10 — UPHOLD (partially).**
   - A is right that "only MATCH→non-MATCH" is too absolute. It would forbid correcting a false rejection, such as E2 Cause B, or E1 helpers that match against an explicit sibling-context obligation.
   - What I keep: no change may *relax* an existing check.
   - **Change:** DEC-B02 rev 2. A non-MATCH→MATCH change is allowed only via a new, independently tested rule with positive and negative controls. Function-scoped diagnostic closure may record explicit external edge obligations and never grants placement.

3. **OBJ-A12 — UPHOLD.**
   - Independent check: `Emu.call` (`tools/wc1/emu.py:188-240@a21772b`, unchanged at `17733f9`) never writes EFLAGS, so the C run inherits the original run's final flags. A's carry-only false pass is therefore reachable in production.
   - My R1-P4 snapshot restored all mapped memory contents, which covers host writes because it is a content snapshot, not a write journal. It did not restore the CPU context, allocator state or Python-closure stub state. C's crossreview §2.3 independently names the closure channel.
   - **Change:** DEC-B18 rev 2 (complete starting state) and ACCEPT of DEC-A11.

4. **OBJ-A13 — UPHOLD on the requirement, REBUT on the failure claim.**
   - My P5 emitted the *original instruction bytes verbatim*. No displacement was computed, so the `jcxz` next-IP error A demonstrates (the `PC+2` formula) cannot occur in that encoding. The literal displacement is correct exactly when the layout between source and target is identical in place.
   - A's general point stands, though. The span, the endpoints and the instruction-boundary target all need a typed decode (exact length, prefixes, next-IP). Assembler-checked piece-local expressions are safer than raw `db` because NASM checks the range.
   - **Change:** DEC-B04 rev 2 requires the typed decode, prefers the piece-local expression, uses original bytes only as a fallback, and checks the assembled field equals the original bytes.

5. **OBJ-A15 — UPHOLD.**
   - B16 put probe outcomes into inventory status labels. Diagnosis and status are different: status changes only through tests under the governance rule. I withdraw DEC-B16.
   - My R0 roadmap S5 had "entry: S3". That serialization is not justified. Routine reconstruction uses existing gates, and `make verify` catches any unbuildable promotion.
   - **Change:** DEC-B01 rev 2 states parallel tracks.

6. **OBJ-A16 — UPHOLD.** DEC-B13 rev 2 states the producer premises for `shared_epilogue`, ties PARA reasoning to the actual segment base, and keeps shared literals conditional.

7. **OBJ-A17 — UPHOLD.** The parsed module loses FRAME distinctions (A0 Q3; C R1-Probe 3 confirms `omf.py` has no checksum check). DEC-B02 rev 2 adds strict raw admission and binds the proof to the raw bytes of the object the build consumes.

8. **A on DEC-B01 — UPHOLD.** The closed list is replaced by the admission principle plus the current instances (DEC-B01 rev 2).

9. **A on DEC-B12 — UPHOLD in substance.** The DEC-B12 rev 1 trigger already names a needed T4. A's extension, a later justified consumer, is compatible. I keep rev 1 because its scope is "during M2"; the post-M2 use is demand-led as well.

10. **OBJ-C09 — REBUT (remedy) / UNRESOLVED (nondeterminism detail).**
    - *Factual premise:* accepted that the original has pad residue (my R1-P3) and that compiled pads differ from it.
    - *"Non-deterministic across consecutive runs":* not reproduced. In R2-P1 I compiled five times at a fixed path, with `wineserver -k` before each compile, and got byte-identical CONST every time. In R1-P2 the pads changed only when the source path changed. The bytes are environment-dependent. C's two differing runs plausibly used different staging paths, which is unresolved until C runs fixed-input controls (§5).
    - *V4 as the remedy:* A's Q2 shows the five V4 conditions do not exclude a computed (indexed) read of a gap byte. With only literal-start relocations present, an indexed read returned `0x8d` vs `0x73`. V4's predicates are therefore not sufficient for an exemption.
    - Production also already avoids local multi-literal CONST through the extern-literal idiom (`src/mod_13f60/save_slot_path.c@a21772b`). So rejecting such objects at cutover is fail-closed and costs no current T3.
    - **Change:** DEC-B21 rev 2 forbids shape-based exemptions and requires independent extent, ownership and access evidence for any future exclusion, applied in both matcher and `place()`.

11. **OBJ-C10 — split.**
    - **UPHOLD** the piece-local expression as the preferred encoding (DEC-B04 rev 2).
    - **UPHOLD** the fallthrough adjacency check (DEC-B19 rev 2). An ASM piece ending without an unconditional transfer, such as `EndCheckSurvive` ending at `0x2f73a jge`, must be followed by its original in-place successor.
    - **UPHOLD** the comparator incompleteness (DEC-B20).
    - **REBUT** synthesizing `_loc_<addr>` PUBDEFs on compiled C objects. P5 built `0x2f6df` (rel32 into MissionDefeat's interior) IDENTICAL with no object transform. A piece-local expression works for rel32 exactly as for rel8: the target is a fixed offset from a label in the same NASM piece. A synthesized public would add a post-codegen transform and binding/frame semantics to the M2 path (A's R1 also challenges it, OBJ-A13). C's stated falsifier ("evidence that synthesizing breaks wlink") is not the right test. The question is whether the transform is *needed*, and P5 shows it is not.
    - The other eight rel32-interior sites C lists are not on current B2 cuts. They are handled by the same rule if they become relevant.

12. **OBJ-C11 — UPHOLD.** The contradiction is real once DEC-B04 is enabled. DEC-B03 rev 2 states mode-qualified expectations.

13. **OBJ-C12 — UPHOLD.** I reached the same 3/5 result in R1-P4 (`probe_q1.py`). DEC-B16 is withdrawn. I accept DEC-C16 conditionally (diagnosis vs status, and complete state per DEC-A11).

14. **OBJ-C13 — REBUT as a requirement.**
    - The risk C names is "a multi-function `src =` precedent under the legacy matcher". But:
      - the legacy matcher already checks every public of the file;
      - Build A compares every byte and fixup of that object;
      - Group B has no leading bytes and no local data (the gaps that only E0 closes);
      - E1 already ran E0's RegionMatch on this exact object and got MATCH.
    - "Landing E0 first costs zero delay" is not true. The E0 cutover is a substantial engineering unit (strict admission, 55 controls ported, cutover audit). Group B is one source file plus TOML wiring.
    - **Compromise I would accept:** the Group B promotion commit cites the E0 prototype RegionMatch of the exact object as evidence, and the object is re-audited at the S2 cutover like every T3. DEC-B06's proposition is unchanged; sequencing is a roadmap choice.
    - This is a design preference, not a soundness dispute. A also favours early Group B.

15. **OBJ-C15 — UPHOLD.** The EV-3 report records "pytest tmp paths ~130 chars and a Watcom-under-Wine compile in `test_t4spec` failed with rc=5" (`docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md:64@17733f9`). New DEC-B22 follows A's caution (OBJ-A17) that the limit must be measured over all compiler-facing arguments, not fixed at 48.

16. **OBJ-C16 — UPHOLD (partially).**
    - All 61 placeholder rows are `missing=[name,C]` with `requires_llm=True`, so reconstruction is the binding constraint, not renaming.
    - But C is right that a deterministic rename helper is a legitimate M2 enabler under my own admission rule, and none exists (`git ls-tree 17733f9 tools/wc1`).
    - DEC-B01 rev 2 admits it when a reconstruction batch demonstrably needs it.

17. **C on DEC-B02.**
    - V2 accepted in A's form: function-scoped closure with explicit edge obligations.
    - `trimmed_branch_target` preserved: accepted, as an E0 control port.
    - V4: REBUT (see 10).

18. **C on DEC-B08 — REBUT V4.** The strict codec precondition is covered for E4 by DEC-B09 rev 2. For B3 it is a natural precondition, already implied by RFC §8.2 constraint 3 (full FIXUPP/THREAD handling), which DEC-B08 keeps binding.

19. **C on DEC-B09 — UPHOLD.** I confirmed two of the defects in code (R1-P6) and A confirmed the PUBDEF corruption from output (A Q4). DEC-B09 rev 2 adds them.
    - The 64-fixup chunking is *not* adopted as a mandatory fix. A's Q3 links 256 off32 fixups in one 1,280-byte FIXUPP32 record on the installed linker.
    - Instead, record-size limits are tested against the actual linker.

20. **C on DEC-B12 — REBUT.** A universal "E6 before any multi-function T4 consolidation" gate is already contradicted by the status quo. `player_reference.c` is a 20-function reference TU with cited T4s. The required capability depends on what a witness needs: substituting an intra-TU sibling, callbacks, or pointer identity. A's R1 position (reject C11 for the same reason) concurs.

21. **C on DEC-B13 — UPHOLD** (in DEC-B13 rev 2).

22. **C §3.1 / §4.2 — UPHOLD**, conceded in R1 (OBJ-B19). DEC-B04 rev 2 no longer calls IDENTICAL complete. DEC-B20 strengthens the comparator after measurement.

---

## 2. Retained decisions

| Decision | Rev | Proposition SHA-256 | Note |
|---|---|---|---|
| DEC-B05 | 1 | `8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac` | All three Architects ACCEPT/align |
| DEC-B06 | 1 | `22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc` | Sequencing relative to S2 is a roadmap choice (§1 item 14) |
| DEC-B08 | 1 | `dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a` | V4 condition rebutted (§1 items 10, 18) |
| DEC-B10 | 1 | `51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0` | |
| DEC-B11 | 1 | `c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5` | |
| DEC-B12 | 1 | `7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3` | |
| DEC-B14 | 1 | `18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd` | |
| DEC-B15 | 1 | `c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387` | |
| DEC-B17 | 1 | `0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1` | Position REJECT (the proposition is a rejected option) |
| DEC-B20 | 1 | `9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a` | |

---

## 3. Changed decisions

Approvals of revision 1 do not carry over to revision 2.

### DEC-B01 → revision 2

- **Old (rev 1, `2e0072df…`):** a closed list of admitted items, with "Fix B3, selective extraction, the full E6 Group/Integrated machinery, persistent provenance and CU databases" deferred.
- **New:**

```text
Decision: DEC-B01
Title: M2 admission principle for infrastructure work
Proposition: Until gate 1 passes, a production infrastructure change is admitted only if it removes an observed blocker of named not-done in-scope functions or closes a demonstrated verification or toolchain soundness defect; routine reconstruction work proceeds in parallel and is not serialized behind infrastructure stages. On main@17733f9 the admitted items are: the E0 matcher with strict raw admission (DEC-B02), the single placement planner with integration receipts (DEC-B03), the cross-object transfer rule (DEC-B04, DEC-B19), the B1 leading-byte base (DEC-B05), proof-gated joint TUs (DEC-B06), complete T4 paired-state symmetry (DEC-B18), measured comparator strengthening (DEC-B20) and the compiler-facing path guard (DEC-B22); a deterministic rename/migration helper is admitted when a reconstruction batch demonstrably needs it. Fix B3, selective extraction, E6 Group/Integrated machinery beyond a named witness, persistent provenance stores and CU databases are scheduled on a post-M2/M3 track unless a named not-done function requires them.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
```

- **Persuaded by:** A's condition on DEC-B01 (a closed list obscures dependencies; reconstruction must not wait), OBJ-A15, OBJ-C15/OBJ-C16, and the EV-3 path-crash record.
- **Consequences:** it depends on DEC-B02 r2, DEC-B03 r2, DEC-B04 r2, DEC-B18 r2, DEC-B19 r2 and DEC-B22. The roadmap changes: S5 (reconstruction) runs from now in parallel with S1–S4.

### DEC-B02 → revision 2

- **Old (rev 1, `52e9b26d…`):** E0 semantics plus the full-population MATCH requirement.
- **New:**

```text
Decision: DEC-B02
Title: Production adoption of E0 matcher semantics with strict raw admission
Proposition: tools/wc1/match.py adopts E0 semantics (bidirectional normalized obligations, leading bytes, local-data pointer targets, mutually exclusive verdicts with UNSUPPORTED precedence, untruncated machine findings), reimplemented in tools/ with E0's 55 controls as production tests. Production admission additionally requires strict raw-OMF input checks (record bounds, checksum when nonzero, single MODEND, record-type allow-list, cross-record THREAD state, explicit FRAME preserved) with unsupported input reported as UNSUPPORTED, and the proof is bound to the raw bytes of the exact object later consumed by the build. Local data, including CONST pad bytes, is matched exactly at cutover. A verdict may change from non-MATCH to MATCH only through a new, independently tested proof rule with positive and negative controls, never by relaxing an existing check; function-scoped diagnostic closure may record explicit external edge obligations but never grants placement. The cutover is admitted only if the full current T3 population returns MATCH under make verify.
Revision: 2
Position: PROPOSE
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
```

- **Persuaded by:** OBJ-A10 (correcting false rejections), OBJ-A17/OBJ-A03 (raw binding), C's `trimmed_branch_target` and V2 points (via A's explicit edge obligation form), and A's Q2 (computed CONST read). The last is why exact matching, not V4, holds at cutover.
- **Consequences:** DEC-B05 still depends on this decision. DEC-B21 r2 is consistent with it.

### DEC-B03 → revision 2

- **Old (rev 1, `e4227a07…`):** "buildable only if the planner returns no error and the emitter accepts", with unqualified regression tests.
- **New:**

```text
Decision: DEC-B03
Title: One planner; promotion requires an integration receipt
Proposition: wc1.build exposes one planner, plan(p, regions), that computes cuts, entries, cross-object transfer encodings, adjacency obligations and data anchors, plus errors; check_t3_buildable, batch_driver, wave4a, m2_inventory and the emitter all consume that planner. A clean plan is a preflight result only: a function is promoted (src wiring for T3) only with an integration receipt recording the actual assembly, link and comparison (including the checks added by DEC-B20) of the exact plan. Regression tests are mode-qualified: standalone IntroOpSyncSound is rejected when the cross-object transfer rule is disabled or any spanned object is legacy-placed, accepted with recorded Build A debt when the rule is enabled in place, and Group B is accepted with no debt.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
```

- **Persuaded by:** OBJ-A09 and OBJ-C11.
- **Consequences:** DEC-B04 r2 refers to the integration receipt; DEC-B20 supplies the strengthened comparator for it.

### DEC-B04 → revision 2

- **Old (rev 1, `10f99b1c…`):** original literal displacement, with IDENTICAL as the final check.
- **New:**

```text
Decision: DEC-B04
Title: Unified cross-object transfer rule (Build A only)
Proposition: In Build A, an ASM relative transfer whose decoded target lies in a different link object is handled by one rule. The instruction is decoded with its exact length, prefixes and next-IP; rel32 to an exported entry stays symbolic. Otherwise it is admitted only if (a) every byte between source and target is supplied by in-place objects of original length (DEC-B19), (b) a target inside a C object lies within that object's VerifiedRegion at an instruction boundary, and it is encoded preferably as a piece-local label expression (assembler-checked range) or else as the original instruction bytes, (c) the assembled field equals the original bytes, and (d) the integration receipt is IDENTICAL. No compiled C object is transformed (no synthesized interior PUBDEF) to serve such a transfer during M2. Each such transfer is recorded as Build A placement debt. Joint TUs (DEC-B06) are preferred when available.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
```

- **Persuaded by:**
  - OBJ-A13: typed decode, exact next-IP, emitted-byte check;
  - OBJ-C10: piece-local encoding preferred, fallthrough;
  - OBJ-A02/OBJ-B19: IDENTICAL is not complete;
  - A's and my objection to synthesized exports (no C object transform).
- **Consequences:** it depends on DEC-B03 r2 and DEC-B19 r2.

### DEC-B09 → revision 2

- **Old (rev 1, `00ff7874…`):** owner gate-2 decision, then rev-e4-01 F1–F4, then the RFC §16 criteria.
- **New:**

```text
Decision: DEC-B09
Title: Region-level T3 and selective extraction deferred pending governance and codec preconditions
Proposition: E3/E4 are not adopted into production during M2. Any later adoption first requires an owner decision on gate-2 semantics for src files containing mismatching publics (match --all currently fails them); then implementation over a strict shared OMF record/fixup subset with regression tests for the confirmed prototype defects (per-record THREAD reset, non-_TEXT PUBDEF/LPUBDEF rebasing, linear decode across tables) and rev-e4-01 F1-F4; record-size limits tested against the actual linker; then the RFC §16 criteria.
Revision: 2
Position: PROPOSE
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
```

- **Persuaded by:** C §2.6/OBJ-C14 (defects), A Q4 (PUBDEF corruption from output), and A Q3 / OBJ-A18 (256-fixup record links, so record limits are measured rather than assumed to be 64).

### DEC-B13 → revision 2

- **Old (rev 1, `84a9be5c…`).**
- **New:**

```text
Decision: DEC-B13
Title: CU recovery is a premise-carrying constraint graph, analyst-facing only
Proposition: CU recovery is analyst-facing only. shared_epilogue is a proven one-directional merge constraint only under stated producer premises (both functions compiler-generated by wcc386, correct block partition, no link-time tail merging or hand-written bridge). non_16_aligned_start is conditional on the actual segment base of a PARA-aligned next object, not on a function start that may follow leading bytes. shared_const_string_literal is conditional merge evidence that requires excluding explicit shared storage and linker pooling. zero16, none16, style_transition and S(f)-disjointness are candidate generators. Staircase breaks and call-locality drops are not used. No tool creates CU boundaries or consolidates sources automatically. compilation_units.toml is deferred to M3.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
```

- **Persuaded by:** OBJ-A16, C's condition on DEC-B13, and my own R1 objection OBJ-B26 (the PARA premise).

### DEC-B18 → revision 2

- **Old (rev 1, `ac26e81c…`):** snapshot and restore all mapped memory.
- **New:**

```text
Decision: DEC-B18
Title: Complete paired starting state for all T4 runs
Proposition: Each T4 pair runs both sides from an equivalent complete starting state: CPU context (general registers, EFLAGS, segment registers and ESP), the full set of mapped memory regions and their contents (covering host and guest writes), emulator allocator state, and declared mutable stub state. Stubs keep mutable state in emulator memory or declare a per-run reset; otherwise the case reports UNSUPPORTED. State restoration is separate from the effects each test compares, and the audit log records the restored state. The rule applies to all T4 tests. Before landing, the full T4 suite runs once with the rule enabled; any change in an existing test's outcome or xfail status is presented to the owner. Reclassification of a divergence follows only from the test result after the change.
Revision: 2
Position: PROPOSE
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
```

- **Persuaded by:**
  - OBJ-A12 / DEC-A11: carry leak; independent confirmation that `Emu.call` never writes EFLAGS;
  - C §2.3 (Python-closure stub state; logging unwatched writes is compatible as an audit field).
- **Consequences:** it supersedes DEC-B07 and is the concrete mechanism I propose for DEC-A11.

### DEC-B19 → revision 2

- **Old (rev 1, `2b1f46b7…`):** legacy exclusion only.
- **New:**

```text
Decision: DEC-B19
Title: Plan-level exclusion of legacy-placed objects and fallthrough adjacency
Proposition: The placement planner rejects any fixed-displacement cross-object transfer whose source-to-target span includes an object placed in legacy layout, whether by the global --legacy flag or the automatic per-object Unplaceable fallback, and records an adjacency obligation for every ASM piece that falls through into the next object, rejecting the plan if that successor is not the original in-place object.
Revision: 2
Position: PROPOSE
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
```

- **Persuaded by:** OBJ-C10 (fallthrough).

### DEC-B21 → revision 2

- **Old (rev 1, `adec6bc4…`):** "never required to equal the original in any future V4 rule, and V4 (when adopted) is applied identically by the matcher and build.place()".
- **New:**

```text
Decision: DEC-B21
Title: CONST pad bytes are environment-dependent and exempt only on independent access proof
Proposition: Watcom 10.0a CONST inter-literal pad bytes are environment-dependent (they vary with compile-input paths and are stable for fixed inputs in our probes) and are excluded from proof-cache digests by normalization. No exemption from exact data matching is granted on the basis of literal shape or the absence of relocation targets; any future exclusion requires independent extent, ownership and access evidence covering computed reads, is applied identically by the matcher and build.place(), and keeps ASM as the Build A physical provider. Until then such objects fail closed and the extern-literal idiom remains available.
Revision: 2
Position: PROPOSE
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
```

- **Persuaded by:** A's Q2 (a computed read of a qualifying gap byte). My rev 1 implicitly accepted V4 as the future rule; that is withdrawn.

---

## 4. Withdrawn or superseded decisions

- **DEC-B07 rev 1 (`2bfe76f4…`).** Withdrawn, superseded by DEC-B18 rev 2, which is broader: CPU, allocator and stub state as well as memory.
- **DEC-B16 rev 1 (`ba07a05d…`).** Withdrawn. It mixed diagnosis with inventory status (OBJ-A15) and was incomplete in scope (OBJ-C12). It is replaced by my CONDITIONAL acceptance of DEC-C16: the diagnosis is recorded, and the status changes only by test results after DEC-B18/DEC-A11 lands with owner approval.

---

## 5. Unresolved objections

1. **CONST-pad nondeterminism detail (C OBJ-C01/OBJ-C09).**
   - Mine: deterministic at a fixed path across 5 compiles, each with a fresh `wineserver` (R2-P1); path-dependent (R1-P2).
   - C's: two different outputs from two runs.
   - **Resolves when** C reruns the same source at the *same absolute path* N≥3 times with the probe recording the exact compiler argv. If outputs differ, C's claim stands (and I would add "run-dependent" to DEC-B21). If not, the difference is the path.
   - Architecturally, this does not change any decision: both readings make the pad proof-irrelevant and digest-normalized.
2. **Synthesized interior PUBDEF (C).**
   - **Resolves when** someone shows a transfer that the in-place piece-local or original-byte encoding cannot serve. Until then, the extra transform is unjustified for M2.
3. **Group B before or after the production E0 cutover (C OBJ-C13).** A design preference; the compromise is in §1 item 14. The owner can choose.
4. **Universal E6 gate (C on DEC-B12, DEC-C11).**
   - **Resolves when** someone gives a concrete multi-function T4 consolidation whose witness needs no substitution, callback or pointer identity, yet would be unsound without E6. I know of none: such a witness is a Group test that current `cemu` already runs (compiled siblings on the C side).

---

## 6. New objections and decisions

**OBJ-B28**
- **Proposition challenged:** DEC-C11 rev 1, "while keeping single-function `wc1.cemu` unchanged during M2".
- **Evidence:**
  - `tools/wc1/emu.py:188-240@a21772b` (EFLAGS not reset between runs);
  - `cemu.run_pair` restores only `watch` ranges;
  - R1-P4 (3/5 xfails pass under full state);
  - A's Q1 (carry-only false pass).
- **Failure mode:** current single-function T4 proofs keep running on asymmetric inputs, including the false-pass direction.
- **Severity:** correctness/verification.

**OBJ-B29**
- **Proposition challenged:** DEC-C07 rev 1, Stage 2 "immediately after Stage 1" as a serial dependency.
- **Evidence:** reconstruction uses existing gates; Group B builds with current tools (R0 P3); the inventory shows 14 functions eligible now.
- **Failure mode:** reconstruction capacity idles behind planner work.
- **Severity:** implementation risk.
- **Note:** this changes my position from R1 CONDITIONAL to REJECT for the rev 1 wording, aligning with A.

**OBJ-B30**
- **Proposition challenged:** DEC-C03 rev 1's five V4 conditions as sufficient.
- **Evidence:** A's Q2 (indexed read of a gap byte while relocation targets sit only at literal starts; `0x8d` vs `0x73`).
- **Failure mode:** certified data that behaves differently when the provider changes (Build B).
- **Severity:** correctness/verification.
- **Note:** this changes my position from R1 CONDITIONAL to REJECT.

**DEC-B22 (new):**

```text
Decision: DEC-B22
Title: Measured compiler-facing path guard in wc1.oldcc
Proposition: wc1.oldcc fails fast with a toolchain error (exit 78 path) when any compiler-facing argument (source, -fo output, -i= include, working directory) exceeds a measured safe Windows-path length, the limit being set from a measured envelope of the installed Watcom 10.0a under Wine rather than a fixed guess; a staging scheme to keep paths short may follow if it is proven to leave compiled bytes and include resolution unchanged.
Revision: 1
Position: PROPOSE
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
```

---

## 7. Convergence assessment

**Agreed in substance across all three, judging from the R1 texts:**
- M2 priority (reconstruction dominates; B3, E4 and CU tooling go post-M2);
- one shared planner;
- the three-class B2 taxonomy plus fallthrough;
- Group B as a joint TU;
- B1 via the leading base;
- E4 deferred, with the owner's gate-2 decision first;
- the alignment matrix;
- additive presets;
- analyst-only CU recovery;
- no framework;
- matcher-minted VerifiedRegion without a Candidate type;
- the comparator gap;
- strict raw admission;
- the T4 paired-state defect being on the M2 path;
- the 3/5 divergence split.

**Remaining disputes:**

| Dispute | Kind | Cheapest decisive experiment |
|---|---|---|
| CONST pad run-to-run nondeterminism | factual (no decision depends on it) | C reruns at a fixed path N≥3 with argv logged |
| V4 sufficiency | factual, settled by A's Q2 counterexample unless C shows Q2's access pattern is impossible for Watcom output | A real SaveSlotPath-style natural-literal object plus a computed-index negative (A's §7 row) |
| Synthesized interior PUBDEF vs piece-local rel32 | design / implementation risk | Full Build A link of MissionDefeat with a piece-local rel32 expression (expected IDENTICAL, as with my literal P5) |
| Group B before or after the E0 cutover | design preference | none (owner choice) |
| E6 as universal gate vs per witness | architectural | none; the counterexample is the existing `player_reference.c` practice |
| Serial vs parallel M2 tracks (C07) | architectural | none; the inventory shows eligible work now |
| Exact paired-state mechanism (full snapshot vs dirty-page plus CPU) | implementation | Q-B05: run the full T4 suite once under DEC-B18 r2; any outcome change goes to the owner |
| Comparator attribute parity | factual | EXP-A03 / DEC-B20 measurement: dump flags, page and fixup types for the original vs the current Build A |

---

## 8. Structured positions for every live decision

### 8.1 Architect A

```text
Decision: DEC-A01
Revision: 1
Proposition SHA-256: cca3a6138a5467434a850794ca1632d592272c79ef8fefc172443aeb4d3acb31
Position: ACCEPT
Reason: Sequencing by remaining DONE obligations under fixed scope, tiers and gates; T4->T3 counted separately; T5 with the owner.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: ACCEPT
Reason: Two scopes of one bidirectional verifier with strict raw admission and a cutover audit; matches DEC-B02 rev 2 (539/539 MATCH under E0 on main already, R0 P1).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: ACCEPT
Reason: Whole-image single-provider plan plus actual assembly/link/compare and loader/provider evidence for acceptance; its stated assumption (attribute policy validated on the real link first) is exactly DEC-B20's measure-then-enforce order.
Conditions: none
Related objections: OBJ-A02, OBJ-B19
```

```text
Decision: DEC-A04
Revision: 1
Proposition SHA-256: 5cee3197ac45be6a908180d33ecbaf69b7d9a8d0fc63b90aa8e1ec4d5a2b05c0
Position: ACCEPT
Reason: Same as DEC-B05; R0 P6 links ChooseCampaignDialog IDENTICAL with the affine base.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: ACCEPT
Reason: Whole-TU preference plus a piece-local bridge under proved fixed cover and emitted-byte agreement; consistent with DEC-B04 rev 2 and DEC-B19 rev 2 (fallthrough adjacency handled there).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A06
Revision: 1
Proposition SHA-256: 4900412ecbb7c67e9cc2863355109fe0079721a11249e03301438bef82173aac
Position: ACCEPT
Reason: Storage identity separate from provider; B3 whole-segment-only and need-driven; consistent with DEC-B08 and DEC-B21 rev 2 (no shape-based pad exemption).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: CONDITIONAL
Reason: Narrow, need-driven extraction pilot only.
Conditions: Any pilot also requires the owner gate-2 decision and the confirmed prototype-defect regression tests (DEC-B09 rev 2); A has stated it will add the former.
Related objections: OBJ-B04
```

```text
Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: ACCEPT
Reason: Boundary, substitution, callback/ABI, typed-pointer and audit-parity rules for cited multi-function proofs; the missing state-symmetry element is supplied by DEC-A11, which I accept.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A09
Revision: 1
Proposition SHA-256: 2cdd42c65d7906d4de19a4bf102f91b13f05dd02422a41c0cbefc24b20e1c95e
Position: ACCEPT
Reason: Additive presets, context-scoped S(f), snapshots as scheduling inputs only (EV-3: 0/202 fresh).
Conditions: none
Related objections: none
```

```text
Decision: DEC-A10
Revision: 1
Proposition SHA-256: 8dbab62c19ae9b44695421aa9fa6e1e1d79ea54a32d25ad68e6970be6505875e
Position: ACCEPT
Reason: Matches DEC-B13 rev 2.
Conditions: none
Related objections: none
```

```text
Decision: DEC-A11
Revision: 1
Proposition SHA-256: 0ab0ab6c66256e2fdcfaffe5c3ead99dad270892b175e965f186bbef38067c78
Position: ACCEPT
Reason: Complete equivalent per-side starting state (CPU, memory, declared mutable dependency state) is required; Emu.call does not reset EFLAGS (R2-P2), so memory-only restoration is insufficient. DEC-B18 rev 2 is my concrete mechanism for it.
Conditions: none
Related objections: OBJ-A12, OBJ-B28
```

### 8.2 Architect B (own)

```text
Decision: DEC-B01
Revision: 2
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Position: ACCEPT
Reason: Revised per OBJ-A15, A's DEC-B01 condition, OBJ-C15, OBJ-C16.
Conditions: none
Related objections: OBJ-A15, OBJ-C15, OBJ-C16
```

```text
Decision: DEC-B02
Revision: 2
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Position: ACCEPT
Reason: Revised per OBJ-A10, OBJ-A17, A Q2.
Conditions: none
Related objections: OBJ-A10, OBJ-A17, OBJ-B30
```

```text
Decision: DEC-B03
Revision: 2
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Position: ACCEPT
Reason: Revised per OBJ-A09, OBJ-C11.
Conditions: none
Related objections: OBJ-A09, OBJ-C11
```

```text
Decision: DEC-B04
Revision: 2
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Position: ACCEPT
Reason: Revised per OBJ-A13, OBJ-C10, OBJ-B19.
Conditions: none
Related objections: OBJ-A13, OBJ-C10
```

```text
Decision: DEC-B05
Revision: 1
Proposition SHA-256: 8828176e620e43e047b46537392ce4aff3b216c8279fd24a16640923f9c54cac
Position: ACCEPT
Reason: Retained; supported by all three positions and R0 P6.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: ACCEPT
Reason: Retained; R0 P3 shows MATCH and IDENTICAL with current tools. Sequencing relative to the E0 cutover is a roadmap choice (§1 item 14).
Conditions: none
Related objections: OBJ-C13
```

```text
Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: REJECT
Reason: Withdrawn by its author; superseded by DEC-B18 rev 2 (complete starting state, not memory only).
Conditions: none
Related objections: OBJ-A12
```

```text
Decision: DEC-B08
Revision: 1
Proposition SHA-256: dee50bd4bf4f77cb35715e5d52443e45c1b272a8494b73e2d2f37fa0af92cc6a
Position: ACCEPT
Reason: Retained; B3 has no M2 DONE effect. The V4 condition proposed by C is rebutted (A Q2).
Conditions: none
Related objections: OBJ-B30
```

```text
Decision: DEC-B09
Revision: 2
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Position: ACCEPT
Reason: Revised per C §2.6/OBJ-C14 and A Q3/Q4.
Conditions: none
Related objections: OBJ-C14, OBJ-A18
```

```text
Decision: DEC-B10
Revision: 1
Proposition SHA-256: 51f20c385768fb71e7fb3cf508ea5af7698f37d186b31446d2afffefa58bb2f0
Position: ACCEPT
Reason: Retained.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B11
Revision: 1
Proposition SHA-256: c69f7826fc8bc4658669790ec9230aceceb213dc3c28983ee609f729193c83d5
Position: ACCEPT
Reason: Retained.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: ACCEPT
Reason: Retained; demand-led E6 adoption per witness need; compatible with A's 'later justified consumer'.
Conditions: none
Related objections: OBJ-A12
```

```text
Decision: DEC-B13
Revision: 2
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Position: ACCEPT
Reason: Revised per OBJ-A16 and C's DEC-B13 condition.
Conditions: none
Related objections: OBJ-A16
```

```text
Decision: DEC-B14
Revision: 1
Proposition SHA-256: 18bb35e7b982d5235cead676e56710994a4389c95488804eb59091cff7b994bd
Position: ACCEPT
Reason: Retained; accepted by A and C.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B15
Revision: 1
Proposition SHA-256: c145c45e9e3a5349dcefcb79359314cb5247764a2c37d6e43d6b3c7cd0930387
Position: ACCEPT
Reason: Retained; accepted by A and C.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Withdrawn by its author: it mixed diagnosis with status labels (OBJ-A15) and was incomplete (OBJ-C12); replaced by conditional acceptance of DEC-C16.
Conditions: none
Related objections: OBJ-A15, OBJ-C12
```

```text
Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: Retained as written; the proposition states the rejected option (extraction as the M2 strategy), and my position is to reject it.
Conditions: none
Related objections: none
```

```text
Decision: DEC-B18
Revision: 2
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Position: ACCEPT
Reason: Revised per OBJ-A12, DEC-A11, C §2.3; R2-P2 confirms the EFLAGS leak channel.
Conditions: none
Related objections: OBJ-A12, OBJ-B28
```

```text
Decision: DEC-B19
Revision: 2
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Position: ACCEPT
Reason: Revised per OBJ-C10 (fallthrough adjacency).
Conditions: none
Related objections: OBJ-C10, OBJ-B27
```

```text
Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: ACCEPT
Reason: Retained; equivalent in substance to DEC-C15's comparator part and DEC-A03's assumption.
Conditions: none
Related objections: OBJ-A02, OBJ-B19
```

```text
Decision: DEC-B21
Revision: 2
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Position: ACCEPT
Reason: Revised per A Q2 (computed read of a qualifying gap).
Conditions: none
Related objections: OBJ-B30
```

```text
Decision: DEC-B22
Revision: 1
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Position: ACCEPT
Reason: New; per OBJ-C15 and the EV-3 rc=5 record, with A's OBJ-A17 caution on measured limits.
Conditions: none
Related objections: OBJ-C15, OBJ-A17
```

### 8.3 Architect C

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: ACCEPT
Reason: The three-level distinction (local, region, integrated) is agreed; integrated buildability is evidenced by an actual integration receipt (DEC-B03 rev 2).
Conditions: none
Related objections: none
```

```text
Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: CONDITIONAL
Reason: Landing E0 bidirectional obligations with V1-V3 is right.
Conditions: Remove the dependency on DEC-C03; keep exact data matching at cutover; V2 records explicit external edge obligations (A's form) and never grants placement.
Related objections: OBJ-B20, OBJ-A10
```

```text
Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: Changed from my R1 CONDITIONAL: A's Q2 shows the five conditions do not exclude a computed read of a qualifying gap byte (0x8d vs 0x73), so they are insufficient for an exemption; M2 does not need it (extern-literal idiom).
Conditions: none
Related objections: OBJ-B30, OBJ-A11
```

```text
Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: CONDITIONAL
Reason: The oldcc guard is needed (EV-3 rc=5 at ~130-char paths); the t3_audit R3 part is already delivered at 17733f9.
Conditions: Drop the t3_audit clause; replace the fixed <=48 limit with a measured envelope over all compiler-facing arguments (DEC-B22).
Related objections: OBJ-A17
```

```text
Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: CONDITIONAL
Reason: Single planner, B1 and the three-class B2 with in-place-only use are right and demonstrated (R0 P5/P6).
Conditions: No synthesized interior PUBDEF on C objects during M2 (piece-local or original-byte encoding instead, DEC-B04 rev 2); a typed decode with exact next-IP; promotion only with an integration receipt; per-object legacy and fallthrough adjacency enforced (DEC-B19 rev 2).
Related objections: OBJ-B23, OBJ-A13, OBJ-A09
```

```text
Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: ACCEPT
Reason: Same as DEC-B06; R0 P3 MATCH and IDENTICAL.
Conditions: none
Related objections: OBJ-C13
```

```text
Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: Changed from my R1 CONDITIONAL: the rev 1 wording makes reconstruction a serial successor of Stage 1, and its 'ref-C bug fixing' premise is 3/5 wrong; I agree with the M2-first priority, which DEC-B01 rev 2 and DEC-A01 carry.
Conditions: none
Related objections: OBJ-B29, OBJ-B24, OBJ-A15
```

```text
Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: ACCEPT
Reason: Reject near-term or default E4 rollout.
Conditions: none
Related objections: OBJ-A14
```

```text
Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: CONDITIONAL
Reason: A shared strict codec before B3/E4 is right.
Conditions: Scope to the supported subset; record-size limits tested against the actual linker (A Q3: 256 fixups/record links), not a fixed 64; not an M2 task.
Related objections: OBJ-A18
```

```text
Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: CONDITIONAL
Reason: Post-M2 need-driven B3 over a strict codec is right.
Conditions: Replace the V4 precondition with independent extent, ownership and access evidence for any excluded byte (DEC-B21 rev 2); otherwise strict whole-segment matching.
Related objections: OBJ-B30
```

```text
Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: Changed from my R1 CONDITIONAL: rev 1 freezes single-function cemu during M2, which contradicts the paired-state fix now agreed by all three (DEC-A11/DEC-B18), and imposes a universal E6 gate contradicted by existing multi-function reference TUs.
Conditions: none
Related objections: OBJ-B28, OBJ-B25
```

```text
Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: CONDITIONAL
Reason: The rejections of staircases, call-locality, weighted scoring and auto-splitting are right.
Conditions: shared_const_string_literal conditional (excluding explicit shared storage and pooling); non_16_aligned_start evaluated at actual segment bases with its measured precision, not '100%'.
Related objections: OBJ-B26, OBJ-A16
```

```text
Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: CONDITIONAL
Reason: The alignment matrix is right.
Conditions: -5r is a first-tried search family for multi-function TUs needing 4-byte spacing, with no claim about original flags or the project default (C has stated it will revise accordingly).
Related objections: OBJ-B26
```

```text
Decision: DEC-C14
Revision: 1
Proposition SHA-256: 66419eaf72495cb7686afc137a391f7c8c6360ab605c5bd10d6d1ff5894f04cf
Position: ACCEPT
Reason: No multi-backend framework.
Conditions: none
Related objections: none
```

```text
Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: CONDITIONAL
Reason: Strict raw-OMF admission and comparator hardening after parity measurement are right; equivalent to DEC-B02 rev 2's admission and DEC-B20.
Conditions: Checksum validation applies when the checksum byte is nonzero; the comparator is strengthened only after the EXP-A03/DEC-B20 parity measurement, and any genuine mismatch goes to the owner.
Related objections: OBJ-A02, OBJ-A03
```

```text
Decision: DEC-C16
Revision: 1
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Position: CONDITIONAL
Reason: The 3/5 split matches my R1-P4 and is the right diagnosis; the run_pair hardening is right.
Conditions: (1) Record it as a diagnosis; m2_inventory status and xfail markers change only after the hardened harness lands (owner approval) and the tests pass under pytest. (2) Restore CPU context (EFLAGS etc.) and allocator state as well as RAM (DEC-A11/DEC-B18 rev 2). (3) Q-B05 runs the full T4 suite first.
Related objections: OBJ-A15, OBJ-A12
```

---

## 9. Probe log and source index (Round 2)

**R2-P1 — CONST pad determinism with a fresh wineserver per compile.**
- Script: `runtime/claude/probes/scripts/run3.py`. Command: `cd /tmp/opencode/cn-claude/m && WINEPREFIX=…/cons-b/build/oldcc/wineprefix TMPDIR=/tmp/opencode/cn-claude/t nix develop -c python3 /tmp/opencode/cn-claude/t/cp/run3.py`.
- The script calls `oldcc.kill_wineserver(env)` before each of 5 compiles of `/tmp/opencode/cn-claude/t/cp/c2.c` with `-q -zl -zld -bt=dos -s -ot -ol -5r -zp2`.
- Output: all 5 runs give `2e6e6574006100742e7361760057004973617665256400`.
- **Limitation:** one source, one prefix; it does not reproduce C's exact environment.

**R2-P2 — EFLAGS handling.**
- Command: `sed -n 188,240p tools/wc1/emu.py` and `grep -n -i eflags tools/wc1/{emu,cemu}.py` on the `a21772b` export.
- Output: the only EFLAGS mention is the interrupt return frame; `Emu.call` never initializes EFLAGS.
- `emu.py`/`cemu.py` are unchanged at `17733f9` (EV-3 diff).

**R2-P3 — EV-3 path crash.**
- `git show 17733f9:docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md`, line 64: "Long verify labels made pytest tmp paths ~130 chars and a Watcom-under-Wine compile in `test_t4spec` failed with rc=5; short labels (`/tmp/wc1-vfy-a6`) pass."

**R2-P4 — proposition hashes.**
- `python3 runtime/claude/r02/props.py` writes `runtime/claude/r02/props.json` (the SHA-256 of each exact revised or new proposition).
- I also confirmed the index's hash method against the DEC-B01 rev 1 text: SHA-256 of the exact UTF-8 proposition, which matches.

No `make verify` or full test suite was run; none of the claims needed it.

**Sources:**
- **Inbox:** `r02-inbox/{00-PROPOSITION-INDEX.json, 01-architect-gpt-crossreview.md, 02-architect-gemini-crossreview.md}`.
  - A: OBJ-A09..A18, Q1–Q4, DEC-A11.
  - C: OBJ-C09..C16, R1-Probes 1–4, DEC-C15/C16.
- **Production tools:**
  - `tools/wc1/emu.py:188-240@a21772b`
  - `tools/wc1/cemu.py:344-391@a21772b`
  - `tools/wc1/compare.py@a21772b`
  - `tools/wc1/build.py:94-104,300-316@a21772b`
  - `tools/wc1/oldcc.py:123-125,188-203@17733f9`
- **Production sources:** `src/mod_13f60/save_slot_path.c@a21772b`; `src/playflic/player_reference.c@a21772b`.
- **EV-3 report:** `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md:64@17733f9`.
- **Experiment code:** `experiments/build_codegen/e4/omf_extract.py:258,798-807,823@e6150b8`.
- **My earlier probes:** R0 P3–P6 and R1-P2/P4/P6 (`runtime/claude/probes/`).