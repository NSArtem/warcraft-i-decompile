# Build & Codegen Infrastructure — Architecture Consilium
## Round 4 — Architect A convergence position

I retain the agreed EV-3 architecture and propose consolidating overlapping decisions without transferring approvals across revisions. My remaining conditions concern LE serialization equality, the distinction between T4 observations and cause or credit, and the named-witness exception in the M2 roadmap. The recorded conditions on Group B, placement and exact-data B3 are satisfied at the architecture level. Their production checks remain gates.

EV-3 means production `17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`, with experiments pinned at `e6150b856106ae113bb023300b956fff318da7ef`. The Secretary’s exact EV-3 verification is the baseline: 534 files matched, zero round-trip instruction mismatches, Build A IDENTICAL, and 2505 tests passed, 11 skipped and 5 xfailed. I read the four delivered files and verified their sizes and hashes. This round used one private LE probe. I ran neither `make verify` nor the full test suite.

## 1. Canonical mapping

The classifications below map the current revision of every indexed decision. “Compatible” means I support the exact combined RFC wording below, with the source decisions and their revision-specific positions retained. It is a mapping of obligations. It does not supersede another Architect's decision or constitute assent from another Architect. Prior revisions of the same decision remain historical. I do not reopen any unanimous acceptance or rejection.

| Indexed decision | Mapping | Canonical destination and boundary |
| --- | --- | --- |
| DEC-A01 r1 | Canonical | Finish line, separate conversion count and owner authority for T5. |
| DEC-A02 r2 | Canonical | Scoped verifier. DEC-C02 and DEC-B15 supply cutover and production implementation details in **Verifier**. |
| DEC-A03 r2 | Canonical | Placement and integration evidence plus supported loader comparison. See **Planner and LE**. |
| DEC-A04 r1 | Canonical | B1 affine base and leading region proof. See **Physical placement**. |
| DEC-A05 r2 | Canonical | B2 transfers and fallthrough. DEC-B19 and DEC-C05 are compatible companions subject to the same proof. |
| DEC-A06 r1 | Canonical | Storage and provider separation and exact whole-segment-first B3. See **Data and extraction**. |
| DEC-A07 r2 | Canonical | Narrow extraction policy and owner authorization. See **Data and extraction**. |
| DEC-A08 r2 | Canonical | Demand-led E6 and cited-witness boundary. See **E6**. |
| DEC-A09 r1 | Canonical | Additive presets and scoped search and scheduling evidence. |
| DEC-A10 r1 | Canonical | Premise-carrying CU evidence kept outside scope and build. |
| DEC-A11 r1 | Canonical | Equivalent per-side T4 case input and fail-closed policy. DEC-A16 is its proposed rollout and audit companion. |
| DEC-A12 r1 | Canonical | Measured effective compiler paths, including staging parity and output isolation. |
| DEC-A13 r1 | Canonical | Independent exact Group B promotion path. See **Whole-TU promotion**. |
| DEC-A14 r1 | Canonical candidate | Raw authority for verification and integration reuse. I accept r1. Two peer positions are missing. |
| DEC-B01 r2 | Superseded | Author withdrawal retained. DEC-A01 and proposed DEC-A15, with conditional DEC-C07 pending replacement wording. |
| DEC-B02 r2 | Superseded | Author withdrawal retained. DEC-A02 and DEC-C02. |
| DEC-B03 r2 | Superseded | Author withdrawal retained. DEC-A03 plus **Planner and LE** and the mode-qualified tests in **Physical placement**. |
| DEC-B04 r2 | Superseded | Author withdrawal retained. DEC-A05, DEC-B19 and DEC-C05. |
| DEC-B05 r1 | Compatible | Consolidate with DEC-A04 in **Physical placement**, preserving the leading relocation and overlap checks. |
| DEC-B06 r1 | Compatible | Consolidate with DEC-A13 and DEC-C06 in **Whole-TU promotion**. Accept r1 on the combined scope. |
| DEC-B07 r1 | Superseded | Withdrawn and rejected. DEC-A11 rather than memory-only reset. |
| DEC-B08 r1 | Compatible | Consolidate with DEC-A06 in **Data and extraction**, retaining the named early-case rule and RFC §8.2 constraints. |
| DEC-B09 r2 | Superseded | Author withdrawal retained. DEC-A07 and DEC-C08. |
| DEC-B10 r1 | Canonical | Measured Watcom/OW2 alignment and segment distinction. |
| DEC-B11 r1 | Compatible | Consolidate with DEC-A09 and DEC-B10 in **Compiler and CU evidence**, retaining the declared default. |
| DEC-B12 r1 | Superseded | Author withdrawal retained. DEC-A08 and DEC-C11. |
| DEC-B13 r2 | Superseded | Author withdrawal retained. DEC-A10 and DEC-C12. |
| DEC-B14 r1 | Canonical | Minimal entity set and deferred persistent storage. |
| DEC-B15 r1 | Canonical | Port supported proofs and controls without production imports from experiments. |
| DEC-B16 r1 | Superseded | Withdrawn and rejected. DEC-A13 covers the joint-TU route, and DEC-A11 with proposed DEC-A16 governs witness diagnosis and status. |
| DEC-B17 r1 | Superseded alternative | Retain rejection of selective extraction as the M2 strategy. DEC-A07 and DEC-C08 carry the accepted limits. |
| DEC-B18 r2 | Superseded | Author withdrawal retained. DEC-A11 plus proposed DEC-A16. DEC-C16 presently inherits a disputed diagnosis. |
| DEC-B19 r2 | Compatible | Consolidate with DEC-A05 in **Physical placement**. Keep both legacy modes explicit and retain exact fallthrough adjacency. |
| DEC-B20 r1 | Superseded | Author withdrawal retained. DEC-A03 carries measured semantic comparison, with DEC-C15 details conditional. |
| DEC-B21 r2 | Superseded | Author withdrawal retained. DEC-A02 and DEC-C10 cover data proof, and DEC-A14 covers authority reuse. |
| DEC-B22 r1 | Superseded | Author withdrawal retained. DEC-A12 and DEC-C04. |
| DEC-C01 r2 conflict | Compatible, identity pending | Consolidate under DEC-A03 and DEC-B14 in **Planner and LE**. Prefer the original r2 identity below. |
| DEC-C02 r2 | Compatible | Consolidate with DEC-A02 and DEC-B15 in **Verifier**, retaining all 55 E0 controls. |
| DEC-C03 r1 | Superseded | Withdrawn and rejected. DEC-A02 and DEC-A06 govern exact admission. No shape-only pad exception. |
| DEC-C04 r2 | Compatible | Consolidate with DEC-A12 in **Paths**. Retain C04’s effective environment arguments and verification of staging, plus the EV-3 R3 audit work already delivered. |
| DEC-C05 r2 | Compatible | Consolidate with DEC-A04, DEC-B05, DEC-A05, DEC-B19 and DEC-A03 in **Physical placement**. Accept r2 with those existing obligations. |
| DEC-C06 r2 | Compatible | Consolidate with DEC-A13 and DEC-A05 in **Whole-TU promotion**, retaining full gate and owner checkpoints. |
| DEC-C07 r2 | Compatible after correction | Use proposed DEC-A15 plus DEC-A01. I remain conditional on current r2 because of its diagnosis and E6 deferral clauses. |
| DEC-C08 r2 | Compatible | Consolidate with DEC-A07 in **Data and extraction**. Preserve the post-M2 boundary and named controls. |
| DEC-C09 r2 conflict | Canonical candidate, identity pending | One strict supported codec for admitted B3 and a post-M2 extraction pilot. Prefer original r2, with details in **Data and extraction**. |
| DEC-C10 r2 | Compatible | Consolidate with DEC-A06, DEC-B08 and DEC-A14 in **Data and extraction**. Accept r2 without importing withdrawn DEC-B21's cache rule. |
| DEC-C11 r2 | Compatible | Consolidate with DEC-A08 and DEC-A11 in **E6**. Preserve the demand trigger and pre-restore ABI checks. |
| DEC-C12 r2 | Compatible | Consolidate with DEC-A10 in **Compiler and CU evidence**. Retain the qualified individual signals as analyst guidance. |
| DEC-C13 r2 conflict | Compatible, identity pending | Consolidate with DEC-B10, DEC-B11 and DEC-A09. Prefer the original r2 text and keep additional sweeps optional. |
| DEC-C14 r1 | Canonical | Clean module boundaries and data contracts, with general frameworks excluded. |
| DEC-C15 r2 | Compatible after correction | Use DEC-A02 and DEC-A03 in **Verifier** and **Planner and LE**. Conditional r2 on removing unsupported serialization equality. |
| DEC-C16 r2 | Compatible after correction | Use DEC-A11 and proposed DEC-A16. Conditional r2 on changing the diagnostic and inventory clause. |

### Exact consolidated wording

These are proposed exact RFC clauses for the compatible mappings. The hash in each heading covers the clause text alone. The clauses carry forward the accepted boundaries, including where a companion decision is pending. Where an approval is needed, the live position is stated separately.

**Verifier** (DEC-A02 r2, DEC-C02 r2 and DEC-B15 r1)  
SHA-256 `9c0abc49957e453181f64f749007d2756af0096d34614d2ddf24b6abb8571f0c`

Use one bidirectional obligation engine for FunctionMatch and RegionMatch, with function-local bounds, explicit independently proved external obligations, trim-target checks in both scopes, and no placement authority from the local result. Admit the supported raw OMF subset using bounded records, nonzero checksum verification, a single MODEND, a record allow-list, persistent THREAD state and preserved FRAME encodings. Fail closed for malformed or unsupported inputs and compare local data exactly at cutover. Reimplement the supported logic in tools/wc1 without importing from experiments/. Port E0's 55 controls into production, add strict-raw and boundary negatives, and admit the cutover only after every live declared T3 and the existing file gate pass.

**Planner and LE** (DEC-A03 r2 and DEC-B14 r1, with the DEC-C01 identity and DEC-C15 issue recorded below)  
SHA-256 `32cfb4481eb0391e56cd737d5d81bdef3a6e9b85718b9564ca74eb99c563c0ff`

Use matcher-minted immutable VerifiedRegion, a single input-bound derived PlacementPlan with a provider for each original loaded byte, and a distinct integration result from actual assembly, link, provider evidence and comparison. Preflight callers and the emitter consume the same plan, and other tools consume typed outcomes without duplicating proof logic. Preserve all existing Build A comparison requirements. For supported LE input, validate bounds, page coverage, record structure, source-field widths and applicable ordering, and reject conflicting physical copies or unsupported overlaps before collapsing only agreeing page-straddle occurrences. Compare loaded bytes, supported object and module flags, mapped page semantics and geometry, entry and stack object-plus-offset descriptors and normalized typed fixups. Treat raw grouping, fixup-page offsets, serialization order and file padding as diagnostics unless independent loader evidence makes them semantic. Escalate genuine loader-semantic baseline differences to the owner.

**Physical placement** (DEC-A04 r1, DEC-B05 r1, DEC-A05 r2, DEC-B19 r2 and DEC-C05 r2)  
SHA-256 `6cd29942e9d0086d59c7183778973515c95917a44c42dd9fda3b3fd36ca87018`

Derive the B1 contribution base from the verified public binding minus its object offset after verifying the leading region and its relocations. Use the physical cut start and reject overlaps and unproved entries. Treat verified leading fixups into the same contribution as internal. For a cross-piece transfer verify the decoded instruction length, next instruction address, field width and original target identity, including a verified instruction boundary within VerifiedRegion for interior C targets. Keep existing valid symbolic rel32 bindings. For a fixed edge prove the in-place span, exact emitted bytes and zero relocation intersecting the displacement. Prefer a checked ASM piece-local expression, with original-byte fallback only under the same proof. Verify physical adjacency for every live cross-piece fallthrough. Exclude dependence on either global or per-object legacy placement, reject unsupported outgoing compiled-slice rel8, and require actual typed link evidence. Record fixed-layout debt. Test standalone Sync with the bridge off, legacy, the proved in-place bridge and the joint Group B TU. Introduce no M2 interior-export transform without a demonstrated blocker and separate proof.

**Whole-TU promotion** (DEC-A13 r1 and DEC-C06 r2, covering DEC-B06 r1)  
SHA-256 `2082398ed3ee5a486577c29bb7e8b45be801355315fa1d9b0cd429c2011cf0f7`

Prefer an exact whole-TU reconstruction for shared tails. Admit multi-function TUs only with whole-object RegionMatch and actual Build A integration evidence. Group B may proceed independently of general B1, B2 and matcher rollout with a commit-bound strict proof of the exact raw object, typed in-place Build A comparison, both compiler checks and the existing full gate. Preserve cited T4 checks and obtain owner resolution for any change to their meaning or the applicable source ground rule. Do not infer consolidation authority from CU heuristics.

**Data and extraction** (DEC-A06 r1, DEC-B08 r1, DEC-C10 r2, DEC-A07 r2, DEC-C08 r2, and the proposed resolution of DEC-C09)  
SHA-256 `6bf6398517cb61325b90e071092073b18e348c89c29a230902765b99051a04a5`

Keep canonical storage and alias evidence separate from physical providers. B3 starts with exact verified whole segments after M2, or earlier only for a named in-scope function that is not DONE, retaining the RFC section 8.2 and E5 aliasing and mutability constraints. A later CONST exclusion needs independent extent and access proof covering computed or overlapping reads, identical treatment in matcher and placement, explicit receipt disclosure and ASM as Build A physical provider. Do not adopt selective extraction during M2 or as the default consolidation path. A justified post-M2 pilot needs owner authorization for changed source-gate semantics, exact raw identity, independently checked code/data bounds and targets, a supported strict OMF subset shared with admitted transforms, regressions for the confirmed THREAD, mixed-public and typed table defects plus rev-e4-01 F1–F4, tested linker bounds and independent transformed-object and actual link proof. Unsupported constructs fail closed.

**E6** (DEC-A08 r2, DEC-A11 r1 and DEC-C11 r2, with DEC-A16 proposed for T4 operation)  
SHA-256 `1a335592d072b36924a5b30f8ec91c8e9a7bfb71c4d51dc761552486b7853b10`

Require paired initial-state equivalence for all T4 tests independently of E6. Add E6 only when a named M2 or post-M2 witness requires additional execution or substitution machinery. Prove per-side execution and dependency edges, symmetric substitutions, any exercised callback ABI before restoration (ebx/ecx/edx/esi/edi/ebp and esp for the tested Watcom contract), typed pointer identity and production audit parity. Use symbol-aware relocation for declared dependencies and an entry hook as defense in depth where entry-only reachability is proved, and add switch-table or CONST-pointer support only when the witness requires it.

**Paths** (DEC-A12 r1 and DEC-C04 r2, covering withdrawn DEC-B22 r1)  
SHA-256 `ddf2a22441d28d38d790ea15e27e58dc7f2ac3c44b5b732bf0796b4bef5bd580`

Measure safe effective Watcom 10.0a paths, including compiler-facing Windows source, include, output, working directory and relevant environment paths. Reject unsupported invocations as toolchain errors before launch. Use short staging only when it preserves source identity, include resolution, flags and output attribution, with isolated temporary outputs per compile.

**Compiler and CU evidence** (DEC-A09 r1, DEC-A10 r1, DEC-B10 r1, DEC-B11 r1 and DEC-C12 r2, with the proposed resolution of DEC-C13)  
SHA-256 `4293a12853f4051c07a9235721cdf29aa86cf909ee575be3e37e7b0808de7f6f`

Record E2's measured in-object spacing and separate segment alignment: Watcom 10.0a -4r -ot spaces at 16 bytes, -3r or -5r -ot at 4, and tested -os and -od at byte spacing. The tested -ot segments are paragraph aligned while the tested -os and -od segments are byte aligned. OW2's tested -4r and -5r -ot modes space at 16 bytes. Preserve the -4r default and additive declared presets, with -5r a context-specific candidate. Record S(f) with its measured TU context and coverage. Shared tails constrain merging only with verified compiler and linker premises, non-16 alignment is assessed at the actual contribution base under a PARA premise, and literal sharing requires exclusion of explicit shared storage and linker pooling. Filenames, zero16, none16, style change and S(f)-disjointness only generate competing hypotheses. Do not split on empty S(f), data staircases or call locality, apply weighted boundary scores, infer historical flags or automatically change source grouping or build inputs.

### New decisions completing two mappings

**DEC-A15 r1 · PROPOSE — Admit M2 infrastructure by demonstrated need**  
SHA-256 `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44`

Prioritize M2 by newly satisfied DONE obligations under DEC-A01. Run eligible reconstruction, owner evidence packets and verification hardening on independent tracks. Admit M2 production infrastructure for a demonstrated verification or toolchain defect or a documented blocker to a named in-scope function that is not DONE, including a scoped rename or routing helper when reconstruction is otherwise ready. Keep general B3, selective extraction, E6 beyond a named witness, persistent proof stores and CU databases off the M2 critical path, subject to their own adoption boundaries. M3 Build B does not require optional Build A consolidation.

Consolidates the continued sequencing content of withdrawn DEC-B01 r2 and conditional DEC-C07 r2 without incorporating probe diagnoses or changing the finish line. [tools/wc1/m2_inventory.py@17733f9, docs/GOAL.md@17733f9]

**DEC-A16 r1 · PROPOSE — Implement and audit paired state before reclassification**  
SHA-256 `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785`

Implement DEC-A11 for current T4 pairs using independent equivalent initialization or a certified checkpoint. Account for CPU context including EFLAGS, mapped regions and permissions and their contents, host and guest writes, allocator state, and declared mutable host and stub dependencies. Report unsupported cases when equivalence cannot be established. Preserve existing output assertions and record the initial-state method and evidence in the production T4 audit. Before landing, run the full existing T4 suite once with the rule enabled and present any changes to existing test meaning or expected status to the owner. Record the five EV-3 witness outcomes as observations, establish attribution separately, and change inventory or DONE status only on current authorized verification evidence.

Consolidates the operational and audit obligations of withdrawn DEC-B18 r2 and conditional DEC-C16 r2. Keeps DEC-A11 unchanged. [tools/wc1/cemu.py@17733f9, tools/wc1/emu.py@17733f9, tools/wc1/t4spec.py@17733f9, CONSILIUM-R03-DELIBERATION.md@6b4743669ccb2f966a97b6875a78cbfc3a3e83ed299cb8153b7e9d0863c44279]

## 2. Revision identities and the eleven withdrawals

### Revision 2 identities

For all three conflicts I select the originally published Round 2 text for the canonical mapping. I would accept those exact identities once C confirms them. I leave all three conflict records out of my delta because only the author can settle the two published identities, and a position against an undefined live revision would be ambiguous.

| Decision | My preferred r2 SHA-256 | Other published r2 SHA-256 | Reason |
|---|---|---|---|
| DEC-C01 | `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de` | `9d4022c2b6e59f6bcd9d2bbd83d318609299120b33cd3aaaf173d4124e5240ec` | Keeps all four outcomes explicit and the M2 entity set small. The typed consumer detail fits the canonical planner clause. |
| DEC-C09 | `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b` | `c56d3bf32c4008225933ad3823b12dd61eb3101e511d484de021aef1b9e0492c` | Shares the strict subset while allowing unrelated readers and M2 `omfpatch` to stay outside the migration. Actual record bounds and MODEND admission are covered by the verifier and pilot tests. |
| DEC-C13 | `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02` | `8b17fb93b1562ea17877185226d4e2ea7b99c4073ba6773598a80dc8a7a46517` | Limits PARA to the measured `-ot` settings. E2 reports byte SEGDEF for tested `-os/-od`. Additional flag sweeps are optional. DEC-B10 and DEC-B11 already carry the normative matrix and default. |

**DEC-C01 original r2**

> Maintain four explicit verification and integration outcomes: FunctionMatch (local body diagnostic with explicit external context obligations), RegionMatch -> immutable matcher-minted VerifiedRegion (closed object/region proof), PlacementPlan (single derived preflight partition plan shared by check_t3_buildable, wc1.build, wc1.emit, batch_driver, wave4a, and m2_inventory), and IntegratedResult (actual assemble, link, and hardened wc1.compare receipt). Do not add a separate CandidateRegion runtime class or persistent proof/CU metadata DB in M2.

**DEC-C09 original r2**

> Before landing Fix B3 or any future selective OMF extraction pilot (post-M2), share one tested strict OMF32 record/fixup codec (record bounds, nonzero checksums, preserved explicit FRAME encodings, persistent cross-record THREAD, format/linker-verified record-length bounds) across verification and admitted OMF transforms, while leaving permissive library-signature readers untouched and avoiding unnecessary omfpatch refactoring during M2.

**DEC-C13 original r2**

> Replace RFC §2.2.5 alignment premises with E2 empirically measured compiler behavior: Watcom 10.0a function spacing is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot (with PARA 16-byte _TEXT SEGDEF for tested -ot), and 1 byte under -os/-od; OW2 uses 16 bytes under -4r and -5r. Keep -4r as the single-file project default with additive E7 presets (DEC-B11), rank -5r as the first-tried candidate family for multi-function -ot TUs requiring 4-byte spacing without claiming it was the universal 1994 project flag, and keep EXP-2/Q-B06 (5r -d1+ -zp1 and 5r -od) as optional additive probes.

If C chooses revision 3 instead, its positions must be recorded afresh against the exact published text. None of these identity conflicts should hold up independently accepted architecture. [Ledger conflicts, C3 §2.3, E2 §A]

### Authoritative withdrawals and replacements

I confirm all eleven withdrawals. The table records my position on each replacement revision in the ledger. The corrections below retain the withdrawals while keeping independently disputed or unassigned obligations explicit.

| Author-withdrawn decision | Verified destination and my positions |
| --- | --- |
| DEC-B01 r2 | DEC-A01 r1 ACCEPT. DEC-C07 r2 CONDITIONAL. Propose DEC-A15 r1 for the parallel M2 rule. |
| DEC-B02 r2 | DEC-A02 r2 ACCEPT and DEC-C02 r2 ACCEPT. Confirm. |
| DEC-B03 r2 | DEC-A03 r2 ACCEPT and DEC-C05 r2 ACCEPT. Prefer original DEC-C01 r2 (e7c48783…), with no live vote until identity is resolved. Retain shared planner and real integration in the meantime. |
| DEC-B04 r2 | DEC-A05 r2 ACCEPT and DEC-C05 r2 ACCEPT. DEC-B19 r2 ACCEPT makes both fallback routes explicit. |
| DEC-B09 r2 | DEC-A07 r2 ACCEPT and DEC-C08 r2 ACCEPT. The codec identity remains a gate for a future pilot. |
| DEC-B12 r1 | DEC-A08 r2 ACCEPT and DEC-C11 r2 ACCEPT. A proved entry-only hook and a later witness are covered by **E6**. |
| DEC-B13 r2 | DEC-A10 r1 ACCEPT and DEC-C12 r2 ACCEPT. Confirm. |
| DEC-B18 r2 | DEC-A11 r1 ACCEPT and DEC-C16 r2 CONDITIONAL. Propose DEC-A16 r1 to carry complete state and audit without provisional attribution. |
| DEC-B20 r1 | DEC-A03 r2 ACCEPT and DEC-C15 r2 CONDITIONAL. Supported loader comparison is already covered by DEC-A03. |
| DEC-B21 r2 | DEC-A02 r2 ACCEPT and DEC-C10 r2 ACCEPT. Add DEC-A14 r1 ACCEPT for exact receipt reuse. Do not import withdrawn normalization. |
| DEC-B22 r1 | DEC-A12 r1 ACCEPT and DEC-C04 r2 ACCEPT. Confirm. |

## 3. Objection dispositions

I record 57 indexed objections as RESOLVED, seven as OPEN, and one as DEFERRED. OBJ-A24 is new and open. RESOLVED is my closing position on the architectural objection. It establishes neither closure by the other two Architects nor a passed implementation gate. OPEN preserves a current objection. DEFERRED keeps the remaining factual detail outside the production contract. The snapshot also records C’s authoritative withdrawal of OBJ-C13. My RESOLVED disposition preserves that history and confirms the exact Group B route addresses the underlying objection.

| Objection IDs | My disposition | Anchor | Basis |
| --- | --- | --- | --- |
| OBJ-A01, OBJ-A09, OBJ-B11 | RESOLVED | DEC-A03 | The shared Build A preflight cannot mint promotion credit before actual assembly, link, provider evidence and comparison. |
| OBJ-A02, OBJ-B19 | RESOLVED | DEC-A03 | Existing compare remains, and its demonstrated flag and type gaps are covered by the supported typed comparison. |
| OBJ-A03, OBJ-A10, OBJ-B10, OBJ-B20, OBJ-C05 | RESOLVED | DEC-A02 | Strict raw input, scoped local diagnostics with external obligations and trim guards, and a live cutover audit replace prototype or cohort assumptions. |
| OBJ-A04, OBJ-B05 | RESOLVED | DEC-A06 | B3 is whole-segment-first and need-driven; a speculative general M2 rollout is excluded. |
| OBJ-A05, OBJ-B01, OBJ-C13 | RESOLVED | DEC-A13 | An exact whole-TU Group B proof may proceed independently with the existing gates and preserved tests or owner approval. |
| OBJ-A06, OBJ-B07, OBJ-C06 | RESOLVED | DEC-B10 | Measured spacing is distinct from segment alignment and historical flag inference; evaluate PARA constraints at the actual contribution base. |
| OBJ-A07, OBJ-A14, OBJ-A18, OBJ-B04, OBJ-C03, OBJ-C14 | RESOLVED | DEC-A07 | A justified later extraction pilot needs canonical source-gate authorization when applicable, strict raw binding, supported records, empirically bounded linker limits and independent transformed-artifact/link proof. |
| OBJ-A08, OBJ-B25 | RESOLVED | DEC-A08 | Cited E6 use is demand-led with proved per-side boundaries and audit parity, independent of file count or M2 timing. |
| OBJ-A11, OBJ-B30, OBJ-C01, OBJ-C09 | RESOLVED | DEC-A02 | Exact cutover data obligations remain and shape-only V4 is retired; a later gap treatment needs independent extent and access evidence. |
| OBJ-A12, OBJ-B06, OBJ-B18, OBJ-B21, OBJ-B28, OBJ-C12 | RESOLVED | DEC-A11 | Current pairs require equivalent inputs now, and the five-case evidence defeats both the five-bug and one-reset-sensitive accounts without granting credit. |
| OBJ-A13, OBJ-B02, OBJ-B03, OBJ-B23, OBJ-B27, OBJ-C02, OBJ-C10, OBJ-C11 | RESOLVED | DEC-A05 | Decoded edges, actual in-place cover, no displacement fixups, adjacency, mode-qualified fixtures and link evidence govern B2; there is no mandatory M2 interior-export transform. |
| OBJ-A15, OBJ-B29, OBJ-C04, OBJ-C16 | OPEN | DEC-A15 | DEC-A15 preserves parallel reconstruction and the need-driven admission rule lost if withdrawn DEC-B01 is replaced by DEC-C07 without qualification. |
| OBJ-A16, OBJ-B12, OBJ-B26, OBJ-C07 | RESOLVED | DEC-C12 | Analyst-only CU inference carries producer, base and storage premises, with no automated consolidation or inferred default compiler flags. |
| OBJ-A17, OBJ-C08, OBJ-C15 | RESOLVED | DEC-A12 | EV-3 delivered the separate provenance fixes; measured effective compiler-facing paths and staging parity govern oldcc, and strict raw binding stays a verifier obligation. |
| OBJ-A19 | RESOLVED | DEC-A03 | Supported LE semantics govern equality and the measured raw-order and last-page differences stay diagnostic; OBJ-A24 addresses a distinct raw-grouping requirement. |
| OBJ-A20, OBJ-A23 | OPEN | DEC-A16 | The state-equivalence principle is accepted; the remaining dispute is over source attribution and inventory status in DEC-C16 and DEC-C07. |
| OBJ-A21 | RESOLVED | DEC-A03 | Validate raw physical occurrences before collapsing agreeing page-straddle copies; the first-wins projection is insufficient. |
| OBJ-A22 | OPEN | DEC-A14 | The unsafe normalization clause is withdrawn; exact authority reuse still needs explicit positions from B and C. |
| OBJ-B08 | RESOLVED | DEC-A05 | The RFC correction attributes the observed external rel8 failure to the deployed NASM OBJ backend; other OMF/linker encodings remain unverified. |
| OBJ-B09, OBJ-B13 | RESOLVED | DEC-B14 | Keep the minimal entity set and defer a separate M2 provenance or CU database until a consumer exists. |
| OBJ-B22 | DEFERRED | DEC-A02 | The precise cause of cross-path or cross-session CONST padding variance does not gate exact cutover; investigate only if a named need makes it consequential. |
| OBJ-B24 | RESOLVED | DEC-A01 | The 61 placeholder rows still need semantic work and C; tool availability or a worklist upper bound earns no DONE credit. |
| OBJ-A24 | OPEN | DEC-C15 | DEC-C15 r2 would require equality of raw grouping and fixup-page offsets despite R4 P1 showing an equivalent supported typed representation under the parser. |

## 4. Surviving disagreements and conditions satisfied

- **DEC-B06 r1 is now ACCEPT.** DEC-A13 r1 and DEC-C06 r2 supply the exact early-proof and existing-gate conditions. The phrase “production RegionMatch” remains the general rule. DEC-A13 is the bounded case that permits an independently equivalent proof on the exact Group B artifact before general deployment. The owner ground-rule and cited-test checkpoints survive. B's Group B link is evidence of feasibility. This round ran no production Group B admission or owner check. [E1, B3 §1 and R0 P3, A13]
- **DEC-C05 r2 is now ACCEPT.** DEC-A05 r2, DEC-B19 r2 and DEC-A03 r2 already require verified target identity, zero intersecting displacement relocation, actual adjacency, per-object legacy detection and a linked receipt. Apply C05 as an implementation companion under all those obligations. A literal fallback is subject to the same decoded and linked proof as a piece-local expression. R3 P2 demonstrated one standalone Sync link on a private EV-3 export. Stock NASM rejected the two external rel8 sites. Two piece-local expressions emitted 7493 and 7589 with zero fixups over their fields. The patched link placed all 535 C files in sequence with zero legacy and passed typed comparison. Generic B2 still needs both legacy negatives, the prefixed instruction, cross-piece fallthrough and combined B1/B2 coverage. [A3 R3 P2, P-Build, A05/B19]
- **DEC-C10 r2 is now ACCEPT.** B withdrew the unconditional normalization rule. The prospective gap provision in C10 carries its own extent, access and provider obligations and grants no proof-cache exception. DEC-A02 and DEC-A03 still require exact input binding. DEC-A14 governs any later reuse. No gap exception is required for initial exact whole-segment B3. C09's identity and B3 proof remain implementation prerequisites. [B3 §2.2, A1 Q2, E5, P-Build]

The three surviving substantive disagreements are below. Each quoted proposition is from the frozen ledger. The two missing peer positions on DEC-A14 are a distinct decision-status gap.

### DEC-C07 r2 — CONDITIONAL

> Prioritize genuine M2 completion (98 remaining not-DONE on EV-3 main@17733f9) via parallel tracks: (a) Stage 0/1 verification hardening, single planner, B1/B2, Group B pilot, and T4 paired-state symmetry (DEC-A11/DEC-B18/DEC-C16, immediately addressing 3 of 5 xfailed PLAYFLIC tests while 0x23530 and 0x2fcfc remain genuine ref-C bugfixes); (b) routine area reconstruction (BULLET.C and the 61+7 name/C backlog, supported by lightweight deterministic rename/Wave 3R enablers, reporting reconstruction yield as an upper bound rather than a deterministic guarantee); and (c) owner evidence packets for the 8 scope/discovery items. Defer Fix B3, selective extraction (E3/E4), demand-led E6 Group machinery, and CU hypothesis databases to the post-M2/M3 track; decouple M3 Build B from optional Build A consolidation paths.

The five functions concern four PLAYFLIC tests and EndScreen. Reset-sensitive passes do not demonstrate that every original failure had one cause. Two persistent differences also do not isolate the C source from fixture, bridge, ABI or reference-side causes. Blanket post-M2 E6 would block a named current witness that needs an intra-TU substitution or callback. Remove the diagnosis and temporal exclusion and I will accept the narrowly stated roadmap. Otherwise an implementation could reclassify outstanding work or serialize a real M2 blocker. [R3 P1, B3 §2.1, P-T4, DEC-A01 r1, DEC-A08 r2.]

**Condition.** Replace the factual and sequencing clauses with the scope of DEC-A15 r1 and use the observation and attribution separation in DEC-A16 r1.

### DEC-C15 r2 — CONDITIONAL

> In Stage 0, enforce strict raw-OMF admission over the supported subset before production verification (record bounds, checksum when nonzero, single MODEND, record-type allow-list, persistent cross-record THREAD state, preserved explicit FRAME encodings, bound to the exact raw object bytes consumed by the build), and harden tools/wc1/compare.py to validate all raw physical fixup occurrences for typed agreement, supported placement/ordering, and page coverage before deduplicating agreeing page-straddle copies, then enforce equality on the measured-identical LE loader attributes (object flags, entry/stack, module flags, page size/count, page map, fixup page offsets, raw grouping multiset) and normalized typed fixups (src_type and target), keeping measured serialization-only deltas (raw fixup serialization order and 1-byte last-page file size) diagnostic unless loader relevance is established and escalating any genuine mismatch to the owner.

The three R2 mutants justify raw validation and typed comparison. R4 P1 shows distinct raw grouping and offset tables with equal typed physical occurrences and loaded image under the parser. An encoding can therefore fail C15 before any demonstrated semantic divergence. Let independent loader evidence decide a specific field. The cheapest follow-up is to inspect the two validated encodings against the pinned loader or exercise both with the same load base and compare the affected relocated values. Exclude the alternate encoding if it is unsupported. Do not make table-byte equality a generic compatibility gate on baseline coincidence. [P-LE, A2 P1/P2, R4 P1, OBJ-A24.]

**Condition.** Use DEC-A02 r2 for OMF and DEC-A03 r2 for LE. Require structural validation of all raw occurrences, then equality on supported loader semantics. Keep raw groupings, offset tables and other serialization differences diagnostic unless loader relevance is independently established.

### DEC-C16 r2 — CONDITIONAL

> Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per identical independent results of R1-Probe 2 and Claude R1-P4 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). Adopt full paired initial-state equivalence in tools/wc1/cemu.py::run_pair (combining DEC-A11 and DEC-B18, subject to Q-B05 full T4 suite verification and owner approval for test-meaning/xfail changes): initialize or restore identical per-side CPU/flags (including EFLAGS/CF), all mapped writable memory, and declared/stateless host-stub state; keep restoration strictly separate from watch output assertions; and record restored regions and unwatched global writes in WC1_T4_AUDIT_LOG.

My R3 P1 witness pairs used independent initialization and compared CPU including EFLAGS, mapped contents and allocator state. B independently checked initial CPU and memory and used stateless witness stubs. Both report passing IntroOpWaitSound, IntroRunScript and IntroPlay with the reset treatment. The first persistent differences were IntroOpStartCredits at 0x59eb9 (01 vs 00) and EndScreen at 0x80054c (70 vs 50) in my fixtures. Neither probe certified production audit parity or causality. The next check is the production pair mechanism with complete state, controlled reset-on/off or targeted causal traces, and the current T4 suite before landing. Remove the reclassification instruction as an immediate operation and I will accept the operational contract. Do not credit a witness until production verification and any necessary owner approval. [A1 Q1, A3 R3 P1, B3 §2.1, P-T4, DEC-A11 r1, DEC-A16 proposed.]

**Condition.** Recast the inventory clause as diagnostic observations. Preserve CPU including EFLAGS, permissions and mapped bytes, host and guest accounting, allocator and declared mutable stub state. Apply DEC-A11 and the operational scope proposed in DEC-A16. Require production-equivalent audit and owner review before status or test-meaning changes.

### DEC-A14 r1 — Missing peer positions

**ACCEPT** on `bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7`. B's withdrawal and C3's qualification of B21 support the distinction in prose. Neither supplies an explicit position on A14 r1. The exact raw object or transformed artifact and the verified context must be bound to any receipt used for authority. A normalized fingerprint can identify a set of candidates for fresh verification. It cannot substitute for raw identity if an earlier proof is reused. This rule requires no persistent cache. [A1 Q2, B3 §2.2, C3 §2.1, DEC-A02 r2, DEC-A03 r2]

### OBJ-A24 — Unsupported raw equality in DEC-C15 r2

This is a correctness-verification objection to C15 r2's inclusion of “fixup page offsets, raw grouping multiset” among fields that must be equal. The equal baseline values are observations. R4 P1 shows a source-list record can encode the same independent fixups under the supported parser while changing both fields. Comparing raw grouping would reject that representation before any evidence of a changed loader obligation. Require strict occurrence and coverage validation first, then compare supported loader semantics. A concrete loader requirement that differentiates the representations would justify keeping that specific equality. Until then the objection remains open. [P-LE, R4 P1]

## 5. Production sequencing and deferrals

EV-3 has **912/1010 DONE** and **98 outstanding**. The 539 T3 functions, compiled from 534 files in baseline Build A, are one component of DONE. A conversion of an already valid T4 to T3 earns no additional DONE.

| Track | Scope now | Return condition for deferred work |
|---|---|---|
| Verification soundness | Strict raw OMF and scoped obligations with a live cutover audit. Bound receipts to inputs and actual integration. Validate LE occurrences before typed comparison. Repair complete paired state for current T4 witnesses independently of E6. | A new supported record, state channel or loader attribute must bring a concrete proof obligation and controls. Changes to gate or test meaning remain owner decisions. |
| Named M2 blockers | B1 by verified leading region and physical base. B2 by checked transfers and adjacency for specific cuts. The Group B TU can seek strict case-specific admission without waiting for general rollout. Oldcc guard closes an observed toolchain issue, with staging conditioned on parity. | A new physical encoding or interior export needs a named blocker and independent link, binding and frame proof. |
| Routine reconstruction | Run eligible area work independently under the current gates. The 61 placeholder rows need naming and C reconstruction, and seven low-confidence items need evidence. Use a deterministic migration or routing helper only for a real batch need. Submit separate owner evidence packets for the eight scope and discovery items. | Tooling becomes a dependency only for a specific batch that cannot safely advance with current tools. |
| M3 Build B and consolidation | Plan source-owned storage and alias evidence once justified. Start B3 with exact whole segments. Use a shared strict OMF subset for admitted transforms. No M3 prerequisite is inferred from optional Build A consolidation. | B3 may be considered before M2 completion only under DEC-B08 for a named outstanding function. Later gap handling requires independent access and extent proof. Post-M2 extraction requires a concrete canonical benefit, owner source-gate decision where applicable and strict transform checks. |
| Optional extensions | E6 features, CU storage, a persistent proof store, other flag sweeps, and a generalized format framework are outside default delivery. Research grouping remains harmless when it carries no authority. The exact cause of variable CONST padding is deferred. | A cited witness can trigger only the needed E6 feature, including during M2. A durable store needs a real consumer. A compiler sweep or padding study needs a decision it can discriminate. There is no accepted generalized framework. |

[EV-3, P-Goal, E2, E5–E8, A13, A15 proposed]

## 6. Acceptance criteria and execution status

“Recorded” means the test obligation appears in accepted text. “Proposed detail” means I recommend the specified implementation check and do not infer peer approval of every fixture. Executed controls and baselines are stated separately. Architecture acceptance does not mark the implementation complete.

| Canonical anchor and architecture status | Future acceptance criterion | Executed evidence and limit |
|---|---|---|
| DEC-A01 r1 accepted. DEC-A15 r1 proposed. | Recorded existing scope, tiers and gates. Proposed trace each infrastructure unit to a demonstrated defect or named blocker, keep routine work independent, and report newly DONE separately from conversions. | EV-3 progress and the Secretary’s full verify ran. Gate 1 remains short by 98. No future roadmap is executed by this round. |
| DEC-A02 r2, DEC-C02 r2 and DEC-B15 r1 accepted. | Recorded live declared-T3 and file-gate cutover, 55 ported E0 controls and production isolation from experiments. Add checksum, FRAME, unsupported record, non-contiguous function, external-edge and trim negatives. | E0 controls and earlier 539-function audit exist. The strict cutover implementation has not run. |
| DEC-A03 r2 and DEC-B14 r1 accepted. DEC-C01 identity pending and DEC-C15 conditional. | Recorded single input-bound plan, actual assemble/link/provider/comparison and raw-occurrence validation. Proposed baseline LE positive, the three R2 mutants as negatives, and alternative grouping with equivalent typed records as a control for the supported subset. Enforce byte/loader semantics and preserve current gates. | R2 P1 measured baseline parity and serialization deltas. R2 P2 demonstrated the flag, source-type and conflicting-copy gaps in the old comparator. R4 P1 corroborates grouping differences under the parser. The hardened comparator has not run. |
| DEC-A04 r1 and DEC-B05 r1 accepted. | Recorded verified prefix, internal fixups and no overlap at the affine base. Proposed prefix/no-prefix pair with wrong-base, out-of-extent and overlap negatives. | B R0 P6 reported an actual ChooseCampaignDialog link. The generic B1 integration test remains. |
| DEC-A05 r2 and DEC-B19 r2 accepted. My DEC-C05 r2 condition is satisfied in architecture. | Recorded decoded edges, actual adjacency and link evidence. Run the mode-qualified Sync tests, both legacy modes, prefixed rel8, B1 prefix and MissionDefeat fallthrough. Verify emitted field and absence of intersecting OMF fixups independently. | R3 P2 linked the specific standalone Sync in place with typed equality and recorded the stock NASM negative. It did not exercise generic fallback or combined cuts. |
| DEC-A06 r1, DEC-B08 r1 accepted. I accept DEC-C10 r2. DEC-C09 identity pending. | Recorded exact whole-segment-first proof, RFC §8.2 and E5 alias/mutability safety, strict supported codec and transformation/link checks. A future gap rule needs proved no access, including computed or overlapping reads, and an identical policy in matcher and placement. | E5 has supported subset feasibility and A1 Q2 refutes shape-only gaps. No production B3 cutover. |
| DEC-A07 r2 and DEC-C08 r2 accepted. DEC-C09 identity pending. | Recorded named need, owner source-gate authorization if needed, supported raw proof, transformed-proof replay and real link. Include THREAD, mixed-public, typed tables, F1–F4 and actual linker bounds. | Prototype faults and the 256-fixup supported record were checked. No later production pilot was admitted. |
| DEC-A08 r2 and DEC-C11 r2 accepted. | Recorded only the needed E6 capabilities. Use the cited witness, asymmetric substitution, interior escape, wrong callback ABI and wrong-target negatives as applicable. Require production T4 audit parity. | E6 fixture feasibility exists. No generalized E6 production boundary is certified. |
| DEC-A09 r1, DEC-B10 r1 and DEC-B11 r1 accepted. DEC-C13 identity pending. | Recorded preserve additive presets and declared context. Verify the RFC table against E2's tested compiler/flags, including BYTE SEGDEF in the tested `-os/-od` cases. Optional EXP-2 only if useful. | E2 alignment matrix executed and E7 presets already merged. EV-3 revalidation found 0/202 historical improved-T4 records fresh for Wave 4B. The optional extra sweeps were not run here. |
| DEC-A10 r1 and DEC-C12 r2 accepted. | Recorded analyst-facing evidence and explicit premises. Proposed shared-literal and leading-table counterexamples and review that a hypothesis cannot mutate build or scope. | E8 corpora measured signal limits. Those results neither prove game-wide precision nor freeze a storage schema. |
| DEC-A11 r1 accepted. DEC-A16 r1 proposed. DEC-C16 r2 conditional. | Recorded equivalent input state and fixed output assertion meaning. Proposed nonce-bound audit plus independent-world, reverse-order, carry, host-write, allocator and stub-state regressions. Once the production mechanism is ready, run the current T4 suite and obtain owner disposition for changed checks/status. | A1 Q1 exposes carry and host-write channels. A3 R3 P1 and B R3-P1 reproduce three reset-sensitive passes and two persistent differences. Neither was the production audit or full suite. |
| DEC-A12 r1 and DEC-C04 r2 accepted. | Recorded measured effective argument envelope, isolated outputs and staging parity. Sweep shallow/deep source, output, include, working directory and environment paths with the same warmed prefix. Verify correct dependency and artifact identity. | EV-3 path failure was observed. An enforceable envelope and parity of staging remain unmeasured. |
| DEC-A13 r1 and DEC-C06 r2 accepted. I accept DEC-B06 r1. | Recorded run strict exact-object RegionMatch, all existing gates including both compiler checks, typed Build A and cited T4 checks or owner approval for changes. Preserve the source-ground-rule checkpoint. | E1 and B R0 P3 supply joint-TU feasibility. This is not the exact proposed production gate run. |
| DEC-A14 r1 ACCEPT from A. B and C positions missing. | Proposed normalize two candidate digests to the same key, mutate a raw byte covered by the exact proof and demand an authority miss and fresh verdict. Also change only the verified context. | A1 Q2 provides a semantic gap negative. No production authority-cache implementation or audit was run. |
| DEC-C14 r1 accepted. | Recorded clean module/data contracts. Review the production dependency graph for unused abstraction or a framework without an admitted consumer. | Architecture rule. No generic framework test or implementation is proposed. |

## 7. Reproduction and source index

### R4 P1 — Equivalent typed fields under different raw grouping

The script read the original through my private EV-3 export and wrote a disposable patched LE under my runtime. It replaced two disjoint same-page OFF32 records with one source-list record to the same target and updated subsequent fixup-page offsets. It checked the sorted typed physical occurrences and the loaded image under EV-3's parser. Commands ran from my worktree:

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r2e" PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$WC1_ROOT/tools"
r=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt
python3 "$r/r04-regroup.py" "$r" "$WC1_ROOT/original/install/war.exe" | tee "$r/r04-regroup.log"'
```

```text
page=1 sources=0xadb,0xad2 records=0700db0a024085,0700d20a024085 -> 270002024085db0ad20a
fixup bytes removed=4 physical typed occurrences=8773 unique=8770
typed physical occurrences equal; loaded images equal; raw grouping and page offsets differ
wc1.compare exit=0: IDENTICAL (loaded image, entry, stack, fixups)
```

Exit 0. Disposable LE `r04-regroup.exe` and script/log are in my private runtime. Script SHA-256 `a29224e51d5fab58f2c4ef94c394335e13978f0241f0e6820bb91a4d892c998c`. Log SHA-256 `47f75153dd9a40bd9579b2aa82e069889e7bc2dcd5d554be30e37c9f39e455a2`. The probe did not execute DOS/4GW or establish which additional encodings a historical linker emits. It establishes that raw grouping and fixup-page offsets are stronger than equality of the parsed typed representation. No tracked source, original binary or other worktree changed.

| Key | Source |
|---|---|
| EV-3, P-Goal | EV-3 exact verification and progress notices. `AGENTS.md@17733f9`, `docs/GOAL.md@17733f9`, `Makefile@17733f9`, `tools/wc1/m2_inventory.py@17733f9` and `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md@17733f9`. |
| P-Build | `tools/wc1/build.py@17733f9`, `tools/wc1/emit.py@17733f9`, `tools/wc1/match.py@17733f9` and `tools/wc1/omf.py@17733f9`. The fallback and placement flow are in `build.py:305–353`. |
| P-LE | `tools/wc1/le.py@17733f9`, especially the source-list and first-wins paths in `_parse_fixups`, and `tools/wc1/compare.py@17733f9`. |
| P-T4 | `tools/wc1/cemu.py@17733f9`, `tools/wc1/emu.py@17733f9`, `tools/wc1/t4spec.py@17733f9`, `tests/test_playflic_t4.py@17733f9` and `tests/test_mod_2efd0_t4.py@17733f9`. |
| E0–E8 | `docs/research/build-codegen/summary.md@e6150b8` and the pinned individual reports, contracts and results. E2 matrix is in `E2-compilation-context.md@e6150b8` §A. E4 findings are in `experiments/build_codegen/e4/omf_extract.py@e6150b8` and the frozen review. |
| A1, A2, A3 | Own frozen Round 1, 2 and 3 reports and their probe logs. A1 Q1/Q2, A2 P1/P2 and A3 R3 P1/P2 are the controls cited here. |
| B3, C3, Ledger | `r04-inbox/01-architect-claude-response.md`, `r04-inbox/02-architect-gemini-response.md`, `r04-inbox/00-LIVE-ISSUES-v2.json` at the delivered SHA-256 digests. Stock and changed-state observations attributed to B are from B3 §2.1. |

## 8. Exact positions in this round

The delta also carries unchanged ACCEPT records where a mapping or objection disposition needs them. The delta was validated against this response and contains 29 decision records. The following table shows all changed, newly stated and unresolved positions from me. The three undefined C identities are dealt with in §2. No position here carries across a revised proposition.

| Decision | SHA-256 | Position |
| --- | --- | --- |
| DEC-A14 r1 | `bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7` | ACCEPT |
| DEC-A15 r1 | `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44` | PROPOSE |
| DEC-A16 r1 | `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785` | PROPOSE |
| DEC-B06 r1 | `22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc` | ACCEPT |
| DEC-C05 r2 | `0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d` | ACCEPT |
| DEC-C07 r2 | `f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999` | CONDITIONAL |
| DEC-C10 r2 | `b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f` | ACCEPT |
| DEC-C15 r2 | `a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc` | CONDITIONAL |
| DEC-C16 r2 | `06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95` | CONDITIONAL |
