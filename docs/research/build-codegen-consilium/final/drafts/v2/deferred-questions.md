# Deferred questions (EDITOR DRAFT)

## How to read this file

**What qualifies.** Each item was explicitly deferred:

- by a ledger decision, or
- by a closing disposition in a frozen response.

The source column names both. No item here may influence an accepted production decision. If a question is reopened, it needs a new decision. The **boundary** column states what keeps the question out of current production.

**Sources** (frozen responses in the editor inbox):

- `13-r04-claude-response.md` §7
- `12-r04-gpt-response.md` §5
- `14-r04-gemini-response.md` §6 (D1–D8)
- `06/07/08-r06-*` and `03/04/05-r07-*` for DQ-04

The baseline RFC's open questions (§17, items 1–12) are mapped at the end.

## Deferred questions

| ID | Question | Boundary (why it cannot enter current production) | Reopening condition | Source |
|---|---|---|---|---|
| DQ-01 | **Production Fix B3**, data-anchor decoupling | DEC-B08 r1 schedules it after M2. DEC-A06 r1 and DEC-C10 r3 admit only exact verified whole segments. RFC §8.2 constraints 1–5 are binding. DEC-C09 r3 requires the strict codec first. | A named in-scope not-DONE function demonstrably requires multi-anchor data (DEC-B08 exception; Q-B08), **or** M2 completes and an M3 consolidation needs it. | DEC-A06, DEC-B08, DEC-C10, DEC-C09; R4 B §7, A §5, C D1 |
| DQ-02 | **Selective OMF extraction** (E3/E4) | Not in M2 and not a default consolidation path (DEC-A07 r2, DEC-C08 r2). Rejected as the M2 strategy (DEC-B17 r1). | Post-M2 only. A justified canonical-TU candidate where whole-TU promotion cannot serve, **plus** the owner decision of DQ-15, the shared strict codec (DEC-C09), the fixed E4 defects and independent transform and link proof. | DEC-A07, DEC-C08, DEC-B17; C D3 |
| DQ-03 | **CONST inter-literal alignment-gap exemption** | The shape-only rule is rejected (DEC-C03 r1). Unproven exemptions are deferred and the matcher fails closed on pad mismatch (DEC-A02 r2, DEC-C02 r2). | A real natural-literal candidate, with independent extent and access proof that rules out computed or overlapping reads, identical matcher and `place()` treatment, ASM as the Build A provider and disclosure in the receipt (DEC-C10 r3). | DEC-A02, DEC-C02, DEC-C03, DEC-C10; C D2 |
| DQ-04 | **Root cause of CONST pad-byte variance** (path- or session-dependent, stable for fixed inputs) | It cannot enter any proof: exact raw-byte cutover (DEC-A02, DEC-C02) and raw-artifact authority (DEC-A14). OBJ-B22 is RESOLVED as an architectural matter. | The variance blocks a named exact reconstruction, or its cause is needed for a justified B3 or CONST-gap decision. | OBJ-B22 r07 (A, B, C); `03/04/05-r07-*` |
| DQ-05 | **E6 multi-function machinery** (VerificationBoundary, symbol-aware relocation, entry hook, callbacks, typed pointers) | Built only on demand (DEC-A08 r2, DEC-C11 r2). Paired state (DEC-A11) applies now, independently. | A named M2 or post-M2 witness needs intra-TU sibling substitution, real callbacks or logical pointer identity. The feature ships with t4spec audit parity and negative controls. | DEC-A08, DEC-C11; C D4 |
| DQ-06 | **CU hypothesis storage** (`analysis/compilation_units.toml` or similar) | No new storage in M2 (DEC-B14 r1). CU evidence is analyst-facing only (DEC-A10 r1, DEC-C12 r2). | M3 consolidation starts, with a consumer that a derived, in-memory representation cannot serve. | DEC-B14, DEC-A10, DEC-C12; C D5 |
| DQ-07 | **Persistent provenance / evidence_digest store; CandidateRegion type** | Deferred until a consumer exists (DEC-B14 r1). No CandidateRegion class or proof DB in M2 (DEC-C01 r3). Reuse authority binds to raw artifacts (DEC-A14 r1). | A real consumer, such as a cache whose correctness depends on persisted provenance, together with the DEC-A14 negative test. | DEC-B14, DEC-C01, DEC-A14; C D5 |
| DQ-08 | **EXP-2 / Q-B06 compiler probes** (`-5r -d1+ -zp1`, `-5r -od`) | Optional and non-blocking (DEC-C13 r3). Presets stay additive and the default does not change (DEC-B11 r1, DEC-A09 r1). | A concrete multi-function TU fails the existing presets in a way the probe could discriminate. | DEC-C13, DEC-B11; C D6 |
| DQ-09 | **Synthesized interior exports (OMF PUBDEF) for cross-object branches** | Requires independent proof before it is added (DEC-A05 r2). Zero M2 PUBDEF synthesis (DEC-C05 r4). | A required edge that neither piece-local nor literal encoding can serve, with independent link, binding and frame proof. | DEC-A05, DEC-C05; R4 B §7 |
| DQ-10 | **Symbolic rel8 (wlink LOBYTE-style fixups)** for Build B | Build A uses piece-local or literal encodings (DEC-A05, DEC-C05). OBJ-B08 was resolved by attributing the observed failure to NASM's OBJ backend; the other OMF and linker encodings remain unverified. | Build B needs symbolic rel8 across objects. | OBJ-B08 (RESOLVED); R4 B §7 |
| DQ-11 | **Loader relevance of raw LE fixup grouping, fixup-page offsets, serialization order and last-page size** | Diagnostic unless shown to be loader-relevant (DEC-A03 r2). Unsupported encodings are excluded at structural admission. OBJ-A24 RESOLVED; DEC-C15 withdrawn. | Independent loader evidence that a valid difference in one of these fields changes loader behaviour. Equality of that specific field can then be required. | DEC-A03; OBJ-A24 r06; A R4 P1 |
| DQ-12 | **Attribution of the two persistent T4 witness differences** (`0x23530` StartCredits, `0x2fcfc` EndScreen) | Recorded as diagnostic observations only. No inventory, xfail or DONE change before production-equivalent verification, nonce-bound audit, Q-B05 and owner review (DEC-C16 r3, DEC-A16 r1). | The production DEC-A11 mechanism is landed. Then reset on/off controls or causal traces identify the source of each difference. | DEC-A16, DEC-C16; OBJ-A20, OBJ-A23 |
| DQ-13 | **T5 scenario set (gate 3)** | Owner authority (DEC-A01 r1). Defining it is a proposal to the owner. | M3 starts and the owner requests it. | DEC-A01; baseline §17 item 12; C D7 |
| DQ-14 | **Build B data layout: `physical_provider = C`, `analysis/data_layout.toml`, splitting ASM data into `_DATA`/`CONST`/`_BSS`, auditing layout-dependent idioms (I16)** | M3 track. Build B does not require optional Build A consolidation (DEC-A15 r1, DEC-C07 r3). | M2 completes and M3 starts. | baseline §17 items 9 and 11; DEC-A15, DEC-C07 |
| DQ-15 | **Owner decision on gate-2 / `match --all` semantics for source files with mismatching publics** | Required before any extraction pilot (DEC-C08 r2, DEC-A07 r2). Gates are owner-controlled (DEC-A01). | A proposed extraction pilot (DQ-02). | DEC-C08, DEC-A07 |
| DQ-16 | **Consolidating existing sources into original-CU-shaped TUs** | No consolidation on heuristic CU signals (DEC-B06 r1, DEC-A10 r1, DEC-C12 r2). Multi-function TUs only on whole-object proof (DEC-C06 r2). Baseline §18/§19.2 exclude mass reorganisation. | A specific cluster with whole-object RegionMatch and IntegratedResult, such as a shared-tail group, or the M3 consolidation start. | DEC-B06, DEC-C06, DEC-A10, DEC-C12; baseline §17 items 6 and 10 |
| DQ-17 | **Optional E6 extensions** (switch-table relaxation, LogicalConstDataPtr / EXP-4) | Optional (DEC-C11 r2), added only when a witness requires them (DEC-A08 r2). | A cited witness requires the extension. | DEC-C11, DEC-A08 |

## Pending owner decisions (not deferred questions)

These are recorded owner checkpoints inside accepted decisions. They are listed so that the roadmap does not treat them as settled:

- **O-1:** the AGENTS.md "one function per C object" ground-rule wording for proof-gated multi-function TUs (DEC-B06, DEC-C06).
- **O-2:** any change to the meaning or expected status of an existing T4 test or xfail, including after the Q-B05 run (DEC-A13, DEC-C06, DEC-A16, DEC-C16).
- **O-3:** the 8 scope/discovery evidence packets (DEC-C07 r3, track c).
- **O-4:** escalation of any genuine loader-semantic baseline mismatch found by the hardened comparator (DEC-A03 r2; also stated in the withdrawn DEC-C15 r2).

## Mapping of the baseline RFC §17 open questions

| Baseline §17 item | Disposition |
|---|---|
| 1. Frequency of compilation-context effects on existing T3 (E2) | Answered for the measured population by E2: 0/96 body changes, 23/23 `-5r` runs. Not generalised; see DQ-16. |
| 2. Supported OMF relocation-transform subset for extraction (E4) | DQ-02, DQ-15 |
| 3. Per-symbol versus whole-segment data mapping (E3/E4/E5) | DQ-01 (whole segments first), DQ-03 |
| 4. Timing of Fix B3 versus M2 (E5) | Decided: post-M2 unless a named function needs it (DEC-B08). Remaining part: DQ-01 |
| 5. Timing of selective extraction versus M2 (E1/E4) | Decided: not in M2 (DEC-C08, DEC-B17). Remaining part: DQ-02 |
| 6. Timing of source consolidation (E2/E4/E6) | DQ-16 |
| 7. Production presets and the role of `-5r` (E7) | Decided: additive, `-4r` default, `-5r` a context-specific candidate (DEC-B11, DEC-A09, DEC-C13). Remaining part: DQ-08 |
| 8. Limits of Isolated mode in multi-function T4 (E6) | DQ-05, DQ-17 |
| 9. `physical_provider` ASM→C, data_layout.toml | DQ-14 |
| 10. Mass consolidation into the original file structure | DQ-16 |
| 11. Layout-dependent idioms (I16) for Build B | DQ-14 |
| 12. T5 scenario set | DQ-13 |
