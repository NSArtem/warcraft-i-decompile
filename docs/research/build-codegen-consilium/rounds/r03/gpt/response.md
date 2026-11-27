# Build & Codegen Infrastructure — Architecture Consilium
## Round 3 — Architect A targeted deliberation

EV-3 pins production evidence at `17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`. The experimental baseline remains `e6150b856106ae113bb023300b956fff318da7ef`. The index contains 38 non-unanimous records, 63 open objections and 13 decisions marked unanimous. I reviewed all three frozen files. I address each indexed item and record separate positions on the 18 current revisions printed in the frozen responses but absent from the index. Responses to superseded text do not carry approval to new versions. I leave the 13 decisions marked unanimous undisturbed.

## Live issues

Decision positions in the competing column appear in A/B/C order. A = ACCEPT, R = REJECT, C = CONDITIONAL, P = PROPOSE and — = no indexed position on that revision. For objections, the competing column records the author of the challenge and source-round dispositions when present. An unreported disposition makes no claim about an Architect’s view. Objections have no indexed revision or proposition hash. Their resolution references the exact revision of the decision that would resolve them.

The last column gives classification, direction and a test or review from §4. CV = correctness-verification, BA = blocking architectural, UF = unsupported factual claim, IR = implementation risk, M = maintainability, E = editorial. ↓ = narrowing and → = stable. The cited change test defines the condition under which I would reconsider the issue. Source keys are resolved in §1.

The exact proposition column quotes the contested sentence where the full decision contains several. The hash covers the full frozen proposition.

### Indexed decisions

| Issue, your position, proposition SHA-256 | Exact proposition under dispute | Competing A/B/C | Supporting evidence, failure mode and assumptions | Practical consequence and proposed resolution | Classification, convergence and change test |
| --- | --- | --- | --- | --- | --- |
| DEC-A02 r1 · REJECT<br>`20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417` | Implement two scopes of one bidirectional verifier, using strict raw-record admission for production proofs. | R/A/A | E0–E3. Retire in favor of A02 r2. E2 Cause B and E3 trim checks need explicit bounds and obligations. Assumes same proof families as rev 1, with independently established bounds. | Verifier can diagnose local bodies without granting placement. → A02 r2 | CV ↓ V |
| DEC-A03 r1 · REJECT<br>`f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b` | Require actual assembly, link, existing comparison and explicit loader-relevant identity and provider evidence for Build A acceptance. | R/A/A | A2 P1–P2. Retire in favor of A03 r2. The legacy parser hides contradictory fixup copies. Assumes the comparator admits the supported LE subset. | Build acceptance checks real output and rejects contradictions. → A03 r2 | CV ↓ L |
| DEC-A05 r1 · REJECT<br>`aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43` | Allow an original ASM piece-local relative expression only where source, target and intervening fixed cover are proved and emitted bytes and final link agree. | R/A/A | P:build; A2 P3; R3 P2. Retire in favor of A05 r2. Fixed displacement does not cover fallthrough or automatic fallback by itself. Assumes the physical cut yields changed providers. | A checked partition has both edge and adjacency obligations. → A05 r2 | CV ↓ B |
| DEC-A07 r1 · REJECT<br>`9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846` | Admit a narrow pilot only for a proven canonical-TU benefit, a region proof bound to the object, independently identified targets, and a verified post-transform artifact and link. | R/C/C | G; E4. Retire in favor of A07 r2. A valid slice can leave the canonical source failing the file-wide gate. Assumes the pilot would claim canonical src credit. | No shortcut for partial source credit. → A07 r2 | BA ↓ X |
| DEC-A08 r1 · REJECT<br>`652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883` | Require per-side execution boundaries, symmetric declared substitutions, real callback/ABI checks, typed pointer identity and production audit parity before using multi-function T4 for a cited proof. | R/A/C | A1 Q1; R3 P1. Retire in favor of A08 r2. Current single-function proofs can see different flags or RAM. Assumes original and C currently can share state. | Repair current input symmetry independently of E6. → A08 r2 | CV ↓ T |
| DEC-A12 r1 · ACCEPT<br>`40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37` | Stage or reject effective Watcom 10.0a paths before launch. | A/—/— | W. A measured guard or verified staging can address path failures while preserving include identity. Assumes effective arguments can be measured before launch. | Fail before opaque compiler crashes. Add staging after parity. → A12 r1; B22 r1 | IR ↓ W |
| DEC-A13 r1 · ACCEPT<br>`c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c` | Permit the exact Group B whole-TU promotion independently of general B1, B2 and matcher rollout only with a commit-bound strict raw-object RegionMatch equivalent to the intended production rules, ordinary file and dual-compiler checks, actual in-place Build A with typed loader comparison, and preserved cited T4 checks or explicit owner approval for changes. | A/—/— | E1; B R0 P3; A2 P1. A case-specific strict proof can cover the exact Group B artifact without a generic rollout. Assumes the strict shadow proof is independently reproducible. | Start an independent pilot, credit only after the current artifact and gates pass. → A13 r1 | CV ↓ J |
| DEC-B01 r2 · ACCEPT<br>`3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390` | Until gate 1 passes, a production infrastructure change is admitted only if it removes an observed blocker of named not-done in-scope functions or closes a demonstrated verification or toolchain soundness defect; routine reconstruction work proceeds in parallel and is not serialized behind infrastructure stages. | —/A/— | I; G. The revised admission criterion allows named blockers, demonstrated defects and concurrent ordinary work. Assumes unchanged gates and scope govern current admission. | Eligible work proceeds while independently justified tooling lands. → B01 r2 | BA ↓ I |
| DEC-B02 r2 · ACCEPT<br>`e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed` | Production admission additionally requires strict raw-OMF input checks (record bounds, checksum when nonzero, single MODEND, record-type allow-list, cross-record THREAD state, explicit FRAME preserved) with unsupported input reported as UNSUPPORTED, and the proof is bound to the raw bytes of the exact object later consumed by the build. | —/A/— | E0–E3; P:omf,build. The strict input verifier and exact-data cutover address prior gaps. Match original compiler output as transform input, then check any transformed output independently. Assumes strict raw validation applies before any transform. | Live T3 and file gates stay intact. No CONST exemption blocks the cutover. → B02 r2 with A02 r2 scoped checks | CV ↓ V |
| DEC-B03 r2 · ACCEPT<br>`8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680` | A clean plan is a preflight result only: a function is promoted (src wiring for T3) only with an integration receipt recording the actual assembly, link and comparison (including the checks added by DEC-B20) of the exact plan. | —/A/— | P:build,emit; A0 Q2; R3 P2. Actual materialization replaces preflight-only approval. R3 P2 demonstrates the specific enabled Sync fixture. Assumes the integration receipt binds the exact materialization. | A disabled bridge rejects standalone Sync. An enabled verified bridge can incur only the declared debt. → B03 r2 with A03 r2 | CV ↓ B |
| DEC-B04 r2 · CONDITIONAL<br>`445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0` | Otherwise it is admitted only if (a) every byte between source and target is supplied by in-place objects of original length (DEC-B19), (b) a target inside a C object lies within that object's VerifiedRegion at an instruction boundary, and it is encoded preferably as a piece-local label expression (assembler-checked range) or else as the original instruction bytes, (c) the assembled field equals the original bytes, and (d) the integration receipt is IDENTICAL. | —/A/— | A1 Q3; A2 P3; B R0 P5; R3 P2. The typed decode and emitted-byte check settle representation. Fixed fields also need zero intersecting relocation and verified original target identity under A05 r2. Assumes the endpoint is the verified original instruction, including for ASM. | A literal fallback is an encoding choice once it passes the same proof as an expression. → Adopt B04 r2 subject to A05 r2; test raw, prefixed and no-fixup paths. | CV ↓ B |
| DEC-B06 r1 · CONDITIONAL<br>`22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc` | A ReconstructedTU may contain several functions when the whole compiled object passes production RegionMatch (all publics MATCH, original spacing) and Build A is IDENTICAL. | C/A/A | E1; B R0 P3; G. Accept the whole-TU target and tested flags. Before production cutover require an exact, independently checked A13 proof and preserve cited T4 checks. Assumes the same subject object passes strict RegionMatch. | The pilot can run early. Landing remains gated. → Apply A13 r1 and owner review of any check change. | CV ↓ J |
| DEC-B07 r1 · REJECT<br>`2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b` | cemu.run_pair (or t4spec) restores, before the C run, all memory written during the original run (by code or stubs), or fails closed when a stub writes outside the restored set. | C/R/C | P:cemu,emu; A1 Q1. Withdrawn by B. A memory-only reset leaves CPU and host-state contamination. Assumes a stateful call can affect CPU and host state. | Use one complete-state contract. → A11 r1 and B18 r2 | CV ↓ T |
| DEC-B09 r2 · ACCEPT<br>`da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb` | Any later adoption first requires an owner decision on gate-2 semantics for src files containing mismatching publics (match --all currently fails them); then implementation over a strict shared OMF record/fixup subset with regression tests for the confirmed prototype defects (per-record THREAD reset, non-_TEXT PUBDEF/LPUBDEF rebasing, linear decode across tables) and rev-e4-01 F1-F4; record-size limits tested against the actual linker; then the RFC §16 criteria. | —/A/— | G; E4; A1 Q3–Q4. The strict subset, owner gate and tested record limits address the production pilot risks. Assumes the transform subset is bounded and existing gate authority applies. | Diagnostic region matching remains useful. Partial canonical source credit requires the stated gate disposition. → B09 r2 alongside A07 r2 | BA ↓ X |
| DEC-B12 r1 · CONDITIONAL<br>`7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3` | Production cemu adopts symbol_aware_reloc for declared out-of-boundary dependencies, and VerificationBoundary/callback execution, only when a T4 needed for M2 requires Group mode with intra-TU calls or callbacks. | C/A/C | P:cemu; E6. The M2-only literal trigger leaves justified later witnesses outside the rule. Entry hooks cannot intercept arbitrary interior edges. Assumes the feature is required by a cited witness. | Apply the same demand test in M2 and M3, with the narrowest supported mechanism. → C11 r2 and A08 r2; preserve entry-only guard. | CV ↓ F |
| DEC-B13 r2 · ACCEPT<br>`74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3` | shared_epilogue is a proven one-directional merge constraint only under stated producer premises (both functions compiler-generated by wcc386, correct block partition, no link-time tail merging or hand-written bridge). | —/A/— | E8; E1–E2. The premises qualify shared tails and literals and place PARA at the contribution base. Assumes producer, actual base and shared storage premises are independent. | Analysts retain competing hypotheses without mutating scope or sources. → B13 r2 | UF ↓ H |
| DEC-B16 r1 · REJECT<br>`ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c` | wc1.m2_inventory reclassifies 0x2315c/0x23170/0x231cc as "joint-TU T3 available (DEC-B06)", 0x1e380/0x2e96c/0x2efd0/0x2f73c as "fixed-displacement cross-object branches (DEC-B04)", and the IntroOpWaitSound divergence as "T4 harness state asymmetry (DEC-B07)". | R/R/R | B R0 P3/P5; R3 P1. Withdrawn by B. Integration candidates and scenario diagnoses are evidence classes, not inventory credit. Assumes feasibility probes are separate from promotion tests. | Count WaitSound once after its actual proof passes. → A13 r1 for the TU; A11 r1 and B18 r2 for T4 | CV ↓ T |
| DEC-B17 r1 · REJECT<br>`0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1` | Selective OMF extraction is adopted in production as the mechanism for advancing M2. | R/R/R | I; G; E4. The indexed positive proposition adopts extraction as the M2 strategy. It has no demonstrated M2 need and current canonical sibling rules block the path. Assumes no named M2 obligation requires extraction on EV-3. | Defer that strategy. A later narrow pilot is separate. → A07 r2; B09 r2; C08 r2 | BA → X |
| DEC-B18 r2 · ACCEPT<br>`eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2` | Each T4 pair runs both sides from an equivalent complete starting state: CPU context (general registers, EFLAGS, segment registers and ESP), the full set of mapped memory regions and their contents (covering host and guest writes), emulator allocator state, and declared mutable stub state. | —/A/— | P:emu,cemu,t4spec; A1 Q1; R3 P1. The revised general contract covers CPU context, mappings, allocator and declared host state, with existing effects and owner review. Assumes declared mutable dependency state accounts for dependencies allowed by the witness. | Certified checkpoint and independent initialization are both viable mechanisms. → B18 r2 implements A11 r1; run the targeted T4 regression suite before landing. | CV ↓ T |
| DEC-B19 r2 · ACCEPT<br>`5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d` | The placement planner rejects any fixed-displacement cross-object transfer whose source-to-target span includes an object placed in legacy layout, whether by the global --legacy flag or the automatic per-object Unplaceable fallback, and records an adjacency obligation for every ASM piece that falls through into the next object, rejecting the plan if that successor is not the original in-place object. | —/A/— | P:build; A2 P3. Legacy exclusion must use actual layout and fallthrough must preserve the original next address. Original successor means the verified contribution at that address. Assumes the actual physical layout, including fallback, is known. | The required adjacency can be satisfied by an exact C replacement at the original successor address. → B19 r2; A05 r2 covers all live fallthrough. | CV ↓ B |
| DEC-B20 r1 · CONDITIONAL<br>`9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a` | If they agree, extend wc1.compare to compare them (strengthen-only). | C/A/A | A2 P1–P2; P:le,compare. Typed fixups and flags agree. Raw fixup order and last-page lengths differ, so compare validated loader semantics and report serialization differences. Assumes the meaning of normalized fields is in the supported LE subset. | Strengthen the current oracle without rejecting healthy serialization or accepting conflicting duplicates. → A03 r2 with B20 measurement; owner disposition for loader-significant baseline differences. | CV ↓ L |
| DEC-B21 r2 · CONDITIONAL<br>`fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f` | Watcom 10.0a CONST inter-literal pad bytes are environment-dependent (they vary with compile-input paths and are stable for fixed inputs in our probes) and are excluded from proof-cache digests by normalization. | —/A/— | A1 Q2; B/C R2 P1; P:build. Independent access proof and identical matching/placement policy are right. Unconditional normalization of proof-cache digests conflicts with B02 raw-object binding and the exact-data cutover. Assumes a proof cache can be consumed without rerunning all exact checks. | Normalized candidate reuse can help triage. Authority reuse must preserve proof inputs. → A14 r1 for fingerprints; C10 r2 for data admission. | CV ↓ D |
| DEC-B22 r1 · ACCEPT<br>`1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c` | wc1.oldcc fails fast with a toolchain error (exit 78 path) when any compiler-facing argument (source, -fo output, -i= include, working directory) exceeds a measured safe Windows-path length, the limit being set from a measured envelope of the installed Watcom 10.0a under Wine rather than a fixed guess; a staging scheme to keep paths short may follow if it is proven to leave compiled bytes and include resolution unchanged. | —/A/— | W; P:oldcc. An early toolchain diagnostic helps even before staging is proven. The measured envelope covers effective paths, including translated environment inputs when read. Assumes safe envelopes are measurable for each effective path class. | Automation distinguishes tool failure from source failure. Staging remains conditional. → B22 r1 with A12 r1 | IR ↓ W |
| DEC-C01 r1 · REJECT<br>`89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a` | Retain the separation between `FunctionMatch` (local diagnostic), `RegionMatch` -> immutable `VerifiedRegion` (closed object/region proof), and `BuildAPlacementPlan` (integrated Build A admissibility), and require all pipeline tools (`wc1.match`, `wc1.build`, `wc1.t3_audit`, `wc1.m2_inventory`, `wc1.overnight`, `wc1.wave4`) to distinguish these three levels explicitly. | C/A/P | P:build,emit; A0 Q2. Superseded by C01 r2. Its fourth outcome records actual integration. Assumes actual output differs in claim kind from a plan. | A clean planner does not authorize source wiring. → C01 r2 and A03 r2 | CV ↓ B |
| DEC-C02 r1 · REJECT<br>`32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b` | Replace `tools/wc1/match.py`'s one-directional matcher with E0's bidirectional Normalized Addressing Obligation engine in Stage 0, fixing E2 Cause B (`FunctionMatch` MUST check branch closure against `[orig_fn.start, orig_fn.start + fn_len)`, NOT the first public's linear region) and preserving `trimmed_branch_target` checks across all modes (fixing E3 `partial_matcher.py:206`). | C/C/P | E0–E3. Superseded by C02 r2. Bounded branches still need explicit external context and strict raw admission. Assumes some later publics are not contiguous in original layout. | Fixes conservative false rejection while retaining independent placement proof. → C02 r2 and A02 r2 | CV ↓ V |
| DEC-C03 r1 · REJECT<br>`2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896` | In both E0 `RegionMatch` and Stage-3 Fix B3, explicitly exempt 1..3-byte alignment padding gaps in `CONST` **if and only if** all 5 conditions hold: (1) segment is `CONST` (never `_DATA`/`_BSS`/`_TEXT`), (2) `1 <= len(gap) <= 3` ending at `align4(gap.start)`, (3) immediately preceded by `0x00` terminating a byte-identical verified literal, (4) zero object fixups and zero `war.exe` fixups/references target any byte in `gap`, and (5) `VerifiedRegion` records `const_pad_exempted = True` and forces `physical_provider = ASM` in Build A. | R/R/R | A1 Q2; E5. Withdrawn by C. The five predicates admit a computed read of a nonmatching gap. Assumes a computed effective address can enter an apparent gap. | The initial verifier retains exact data matching. → C10 r2 plus A14 r1 | CV ↓ D |
| DEC-C04 r1 · REJECT<br>`6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b` | Immediately implement Watcom 10.0a short-path staging/length guard (`<= 48` char staging path + fail-fast `[TOOLCHAIN ERROR]` before ~129-char crash) in `tools/wc1/oldcc.py`, and fix the 3 `R3` provenance defects in `tools/wc1/t3_audit.py@a21772b` (checkout-rooted `_default_system_headers(repo_root)`, live `tool_sig` comparison, fail-closed `_git()`). | C/C/P | W; EV-3. Superseded by C04 r2. EV-3 already handled R3 audit defects, and the proposed fixed directory cap does not bound effective arguments. Assumes changes are scoped to EV-3. | Scope remaining work to measured toolchain reliability. → A12 r1; B22 r1; C04 r2 | IR ↓ W |
| DEC-C05 r1 · REJECT<br>`16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9` | Introduce non-forgeable `VerifiedRegion` (V5) and `BuildAPlacementPlan` in Stage 1, unifying `build.check_t3_buildable` with `BuildAPlacementPlan`, implementing Fix B1 (`LeadingJumpTableSpec` widened cut `[table_start, fn_end)`), and implementing **Unified Fix B2** handling ALL three cross-piece `rel8` classes (interior, cut-entry, cut-spanning) plus cross-piece fallthrough via NASM piece-boundary local-label offset expressions strictly in `in_place` mode (unconditionally forbidden under `--legacy`), plus `omfpatch` interior `_loc_<addr>` `PUBDEF` for cross-piece `rel32`. | C/C/P | A1 Q3; B R0 P5; P:build; R3 P2. Superseded by C05 r2. An M2 interior-PUBDEF transform lacks a demonstrated dependency, and both legacy routes need checks. Assumes the original contribution's physical base controls B2. | Select the narrow fixed-layout bridge with actual link proof. → A05 r2; C05 r2 subject to no relocation over fixed fields. | CV ↓ B |
| DEC-C06 r1 · REJECT<br>`3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a` | Where all functions in a shared-epilogue cluster have C sources, prefer co-compiling them into a single contiguous multi-function `VerifiedRegion` under `-5r` / `-oa -5r` (starting with E1 Group B: `IntroOpPlaySound` `0x2315c` + `IntroOpSyncSound` `0x23170` + `IntroOpWaitSound` `0x231cc`), using Unified Fix B2 strictly as the incremental bridge while siblings remain ASM. | C/A/P | E1; B R0 P3. Superseded by C06 r2. Scope the flags to the exact verified candidate and include gate and owner prerequisites. Assumes source availability alone does not establish exact output. | Promote independently when the actual proof is ready. → C06 r2 and A13 r1 | CV ↓ J |
| DEC-C07 r1 · REJECT<br>`9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f` | Sequence Stage 2 (deterministic atomic cross-module symbol renamer `wc1.symbol_migrate`, Wave 3R `upgrade-existing` + `low`-conf admission, `BULLET.C`, remaining 4–5 ref-C bugfixes, and user governance proposal on the 8 discovery/scope artifacts) immediately after Stage 1, and defer B3 (E5), multi-function T4 (E6), CU advisor (E8), and selective extraction (E4) to Stage 3 (post-M2). | R/R/P | I; R3 P1. Eligible work exists before placement changes. RAM-sensitive witness cases need diagnosis, and names alone do not supply C. Assumes names and source obligations are distinct. | Keep reconstruction and verification tracks concurrent. → B01 r2; C07 r2 subject to observational wording. | IR ↓ I |
| DEC-C08 r1 · REJECT<br>`ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3` | Selective OMF extraction may only be introduced conditionally in Stage 3 if irreducible mismatching siblings remain after `-5r`/Wave 4B, and ONLY after rebuilding it over a unified OMF32 codec fixing all 8 defects (Probe 5 Bugs 5a–5d + `rev-e4-01` F1–F4). | C/A/R | G; E4; A1 Q3–Q4. Superseded by C08 r2. The 64-fixup limit and exhaustive sweep are unsupported prerequisites, and partial source credit needs owner disposition. Assumes evidence for selective extraction must follow Gate 2. | A scoped pilot can prove a supported subset after M2. → A07 r2; B09 r2; C08 r2 | BA ↓ X |
| DEC-C09 r1 · REJECT<br>`dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b` | Before landing Fix B3 (Stage 3B) or any optional OMF extraction (Stage 3E), consolidate OMF32 parsing, persistent cross-record `THREAD` tracking, 64-fixup `FIXUPP32` chunking, and record emission into one tested module (`tools/wc1/omf.py`), removing duplicate ad-hoc OMF serializers. | C/C/P | A1 Q3; E4. Superseded by C09 r2. The deployed linker accepted 256 disjoint off32 fixups in one record. Assumes the test uses the deployed OW2 linker. | Limit the shared codec to proof and adopted transforms. → C09 r2 | M ↓ X |
| DEC-C10 r1 · REJECT<br>`0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a` | Adopt E5's data-anchor decoupling (`semantic_owner = C`, `physical_provider = ASM` in Build A) in Stage 3B over the unified OMF32 codec, strictly conditioned on implementing Invariant V4 (1..3B unreachable `CONST` alignment-gap verification), passing **EXP-1** on `SaveSlotPath` (`0x14740`), and enforcing `rev-e5-02` `_DATA` mutability/aliasing guards. | C/C/P | E5; A1 Q2. Superseded by C10 r2. Mandatory shape-based V4 fails the computed-read control. Assumes exact storage validates only the admitted subset. | Begin with exact whole-segment data when needed. → C10 r2; A14 r1 | CV ↓ D |
| DEC-C11 r1 · REJECT<br>`7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b` | Adopt E6's multi-function T4 architecture (`Isolated`/`Group`/`Integrated` modes, contiguous `VerificationBoundary`, 3-mechanism `DependencySubstitutionPolicy`, generator callbacks with pre-restore `watcall` ABI checks, R2 typed `LogicalFnPtr` extended with `LogicalConstDataPtr` and proven intra-function switch tables) in Stage 3C as a **hard prerequisite before consolidating any T4 function into a multi-function `.c` file**, while keeping single-function `wc1.cemu` unchanged during M2. | R/R/P | P-T4; A1 Q1. Superseded by C11 r2. Existing multi-function TU witnesses and the current carry leak defeat both old clauses. Assumes file layout and effective execution boundary can differ. | Repair current boundaries and extend E6 only for a real witness. → A08 r2; A11 r1; C11 r2 | CV ↓ F |
| DEC-C12 r1 · REJECT<br>`9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139` | Adopt instead an analyst-only **premise-carrying CU constraint graph** (`analysis/cu_hypotheses.toml` in Stage 3D) distinguishing Class 1 hard merges (`shared_epilogue`, `shared_const_string_literal`), Class 2 premise-dependent one-directional merges (`non_16_aligned_start` under `SEGDEF=PARA`), and Class 3 soft anchors (filenames, `zero16`), explicitly preserving competing hypotheses. | C/C/R | E8; E2. Superseded by C12 r2. Shared literals and alignment signals need producer/storage premises. Assumes assembler/compiler producers and linker pooling are alternatives. | The historical graph remains analyst-owned and separate from build. → A10 r1; B13 r2; C12 r2 | UF ↓ H |
| DEC-C13 r1 · REJECT<br>`29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969` | Replace RFC §2.2.5's incorrect "10.0a always aligns to 4B" premise with E2's empirically verified matrix (`10.0a -4r -ot = 16B`, `-5r/-3r -ot = 4B`, `-os/-od = 1B`, `SEGDEF = PARA 16B`; `OW2 -4r/-5r = 16B`), codify `-5r` as the primary Watcom 10.0a default family for contiguous CU reconstruction, and run **EXP-2** to evaluate `-5r -d1+ -zp1` and `-od -5r`. | C/C/P | E2; E7. Superseded by C13 r2. Sampled 4-byte spacing does not identify the historical flag or change the default. Assumes tested context and historical compile flags differ. | Keep additive context search and flag ranking only for suitable candidates. → C13 r2; B10/B11 r1 | UF ↓ H |
| DEC-C15 r1 · CONDITIONAL<br>`a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8` | In Stage 0 (alongside E0 matcher cutover and wc1.oldcc short-path protection), enforce strict raw-OMF admission before production verification (validating record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, and preserved explicit FRAME encodings) and harden tools/wc1/compare.py to verify loader-relevant LE object flags, entry/stack object+offset, and fixup src_type alongside loaded bytes and fixup targets, after validating attribute parity on baseline Build A (EXP-A03). | C/C/A | A2 P1–P2; P:le. The measured baseline supports the typed additions. Checking only types after first-wins deduplication misses the duplicate mutant. Assumes supported LE copies can be checked before canonicalizing. | Validate raw occurrences and compare normalized loader data. → C15 r1 subject to A03 r2. | CV ↓ L |
| DEC-C16 r1 · REJECT<br>`d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5` | Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per R1-Probe 2 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). | R/C/P | A1 Q1; R3 P1. Superseded by C16 r2. Memory rollback and guest hooks do not cover the shown CPU and host paths. Assumes the stock harness shares mutable input state. | Log diagnoses as observations and keep proof flags separate. → A11 r1; B18 r2; C16 r2 subject to the diagnostic conditions below. | CV ↓ T |

### Indexed objections — Architect A

| Issue and your position | Exact proposition challenged | Competing positions | Supporting evidence, failure mode and practical consequence | Necessary assumption and proposed resolution | Classification, convergence and change test |
| --- | --- | --- | --- | --- | --- |
| OBJ-A01 · UPHOLD | Challenge the iff claim in production `check_placed_plan` and the older M2 roadmap’s unconditional Sync wiring. | A objects | A0 Q2; P:emit,build; R3 P2. Sync edges cross retained pieces, and NASM rejects despite clean preflight. | Standalone cut splits the printed pieces. → A05 r2 and B03 r2 | CV ↓ B |
| OBJ-A02 · UPHOLD | Challenge using `wc1.compare` success alone as the new placement oracle (RFC §§7.2, 13, 16). | A objects | A2 P1–P2; P:compare. Execute/type mutants pass legacy compare. Standalone success cannot authorize placement. | The admitted LE loader attributes matter. → A03 r2 | CV ↓ L |
| OBJ-A03 · UPHOLD | Challenge adopting E0 directly as a complete authoritative object validator (campaign D1). | A objects | A0 Q3; P:omf. Checksum/FRAME projection can conflate different artifacts. Verify raw inputs before authority. | Linker consumes raw OMF. → A02 r2; B02 r2 | CV ↓ V |
| OBJ-A04 · UPHOLD | Challenge the claim in campaign D4 that E5 unblocks arbitrary multi-function consolidation. | A objects | E5; I. SaveErrorDialog's native literal stride remains wrong. Anchor-order fixes alone cannot promote broad TUs. | A candidate must first prove address and byte obligations. → A06 r1; C10 r2 | UF → D |
| OBJ-A05 · UPHOLD | Challenge the RFC §18 Phase D universal dependency on B3, extraction and E6 for consolidation pilots. | A objects | E1; B R0 P3; R; R3 P2. E1 can close the shared tail without B3, E4 or E6. Universal ordering stalls a viable pilot. | Existing data layout and preserved cited tests suffice. → A13 r1; B01 r2 | BA ↓ J |
| OBJ-A06 · UPHOLD | Challenge treating `-3r/-5r` as defeating paragraph alignment in the E8 interpretation. | A objects | E2; E8; B R0 P6. 4-byte entry spacing coexists with PARA; a leading table can separate base from first public. | The prospective segment base is independently found. → B13 r2; C13 r2 | UF ↓ H |
| OBJ-A07 · UPHOLD | Challenge production extractor admission on the `VerifiedRegion` type check alone. | A objects | E4; A1 Q4. A type tag cannot rule out stale bytes or transformed DATA rebasing. Bind and reverify. | Objects may be rebuilt or transformed after a proof. → A07 r2; A14 r1 | CV ↓ X |
| OBJ-A08 · UPHOLD | Challenge treating E6 Integrated as a direct production T4 audit replacement. | A objects | E6; P-T4. A blanket Integrated run can exercise original code outside the intended C boundary and evade audit. | An E6 witness will be cited for production credit. → A08 r2; C11 r2 | IR ↓ F |
| OBJ-A09 · UPHOLD | B03/I-2 and C01/C05 place a clean plan and emitter acceptance at the integrated buildability boundary. | A objects; R2 B UPHOLD, C UPHOLD | A0 Q2; A2 P2; P:build; R3 P2. Preflight only approximates encodability and actual loader behavior. Separate promotion credit. | Assembly and link are distinct from planning. → A03 r2; B03 r2; C01 r2 | CV ↓ B |
| OBJ-A10 · UPHOLD | C02/V2 says cross-function edges force `UNSUPPORTED` in FunctionMatch, and B §3.2 I-1 restricts changes to losing matches. | A objects; R2 B UPHOLD, C UPHOLD | E1–E3. E1 context edges and E2's nine false unsupported results need scoped local diagnostics. | External target evidence is independent of the local similarity. → A02 r2; C02 r2 | CV ↓ V |
| OBJ-A11 · UPHOLD | C03 and C10 make the V4 predicates sufficient for a CONST exclusion. | A objects; R2 C UPHOLD | A1 Q2; E5. Literal shape and relocation absence admit a computed gap read with different value. | The pointer can reach beyond a directly referenced literal. → A06 r1; C10 r2; A14 r1 | CV ↓ D |
| OBJ-A12 · UPHOLD | B07’s restoration scope covers memory. C11 freezes the current harness in M2 and makes full E6 plus extensions prerequisite to any consolidation. | A objects; R2 B UPHOLD, C UPHOLD | A1 Q1; R3 P1; P-T4. CPU flags and host writes survive RAM-only guest accounting. Baseline premise fails before E6. | One engine or host state is shared between calls. → A11 r1; B18 r2; A08 r2 | CV ↓ T |
| OBJ-A13 · UPHOLD | C05’s elaboration uses `t - (ia+2)` for every rel8 and mandates interior rel32 PUBDEF. B04’s literal path leaves encoding checks implicit. | A objects; R2 B UPHOLD, C UPHOLD | A1 Q3; B R0 P5; A2 P3; R3 P2. PC+2 miscomputes prefixed jcxz; verbatim literal avoids arithmetic but still requires typed span and no intersecting fixup. | Same original encoding, origin and destination frame are proved. → A05 r2; B04 r2 with stated conditions | CV ↓ B |
| OBJ-A14 · UPHOLD | C08’s later extraction prerequisites omit owner disposition of existing `match --all` semantics for mismatching publics. | A objects; R2 C UPHOLD | G; E3–E4. Existing per-public conjunction fails the canonical source even when a slice matches. | The pilot seeks canonical src credit for mismatching siblings. → A07 r2; B09 r2; C08 r2 | BA ↓ X |
| OBJ-A15 · UPHOLD | C07 and B §8 S5 require generic placement work before the main reconstruction queue. B16 would turn probes into categorical status labels. | A objects; R2 B UPHOLD, C UPHOLD | I; B R0 P3/P5; R3 P1. Serial ordering delays eligible work. Provisional inventory evidence cannot certify DONE. | Existing gates can handle eligible area work independently. → B01 r2; A13 r1; C07 r2 subject to observational wording | IR ↓ I |
| OBJ-A16 · UPHOLD | C12 treats shared literals as hard merges and C13 couples the alignment correction to a default reconstruction family. B13’s hard epilogue rule also needs verified producer premises. | A objects; R2 B UPHOLD, C UPHOLD | E1–E2; E7–E8. Pooled/explicit extern literals and a leading prefix defeat unconditional CU conclusions. | Historical producer and storage premises must be independently known. → A10 r1; B13 r2; C12/C13 r2 | UF ↓ H |
| OBJ-A17 · UPHOLD | C04 bundles obsolete audit changes with a hard copy/staging limit, and B02/C02 do not by themselves ensure non-lossy raw binding. | A objects; R2 B UPHOLD, C UPHOLD | EV-3; P:oldcc,omf; A0 Q3. Old audit work is delivered. A short staging root leaves translated includes and output paths long; raw proof identity is a separate concern. | Invocation and includes can vary by checkout. → A12 r1; B22 r1; C04 r2; A02 r2 | IR ↓ W |
| OBJ-A18 · UPHOLD | C08/C09 treat missing 64-fixup chunking as an established production-blocking overflow and require broad serializer consolidation. | A objects; R2 C UPHOLD | A1 Q3–Q4; E4. The deployed linker admits 256 disjoint fixups in one record. A different confirmed PUBDEF bug remains. | Limit claim must name the canonical emitted subset and linker. → C09 r2; A07 r2 | UF ↓ X |
| OBJ-A19 · UPHOLD | B20 calls for equality checks over object flags, page/fixup records and types when the baseline agrees. | A objects | A2 P1; P:le. Raw record ordering and last-page file length differ at baseline. Literal equality rejects a valid control. | Only normalized admitted loader semantics enter acceptance. → A03 r2; B20 r1 only with semantic comparison | CV → L |
| OBJ-A20 · UPHOLD | B18 claims every mapped region restored makes the two runs start in identical complete state. C16 prescribes RAM restoration or dirty-page hooks and definitive five-row classifications. | A objects | A1 Q1; P-T4; R3 P1. RAM alone misses CPU/host state. New checkpoint reproduces the 3/2 observations but does not attribute all root causes. | Affected original and C executions share controlled setup. → A11 r1; B18 r2; reword C16 r2 | CV ↓ T |
| OBJ-A21 · UPHOLD | The minimal reading of C15 would add types from `fixups_unique` to the comparator. | A objects | A2 P2; P:le. Conflicting second occurrence leaves the entire unique typed projection unchanged. Typed equality after dedup is too late. | LE supported subset must reject contradictory page-straddle records. → A03 r2; C15 r1 conditional | CV → L |

### Indexed objections — Architect B

| Issue and your position | Exact proposition challenged | Competing positions | Supporting evidence, failure mode and practical consequence | Necessary assumption and proposed resolution | Classification, convergence and change test |
| --- | --- | --- | --- | --- | --- |
| OBJ-B01 · UPHOLD | Group B (IntroOpPlaySound/IntroOpSyncSound) requires "cut-boundary relative branch emission in wc1.emit/wc1.build". The m2 inventory (`DG-03`) and `e1a4178` say so, and `summary.md` §18.9 PR2 counts Group A and B under "+5–6 more T3s via E1" without stating that no infrastructure is needed. | B objects | E1; B R0 P3. The exact joint object removes the standalone cut. Generic B2 is a separate dependency. | Exact Group B proof and current owner gates can be met. → A13 r1; C06 r2 | UF ↓ J |
| OBJ-B02 · UPHOLD | The campaign roadmap (`summary.md` §18.9; `decisions.md`) presents E0–E8 as covering the RFC's production mechanisms. Fix B2 (RFC §7.2) was never tested; `grep` finds no B2 implementation or test in `experiments/`. | B objects | R; E1; B R0 P5; I. E1 joint-object feasibility leaves production cross-object edges unproven; B3/E4 need a consumer. | M2 credit is through current gates, without a promised yield. → B01 r2; separate A05 r2 pilot | BA ↓ B |
| OBJ-B03 · UPHOLD | RFC §7.2 Fix B2 covers "ASM instruction in `piece_k` branches into a verified interior address `t`". | B objects | P:emit; A0 Q2; B R0 P5; R3 P2. Retained-to-retained and cut-entry edges escape an interior-only diagnostic. | The source and target are in different physical objects. → A05 r2; B19 r2 | CV ↓ B |
| OBJ-B04 · UPHOLD | D5 "ADOPT (SCOPED)" and D6 "ADOPT (CONDITIONAL)" (`decisions.md@e6150b8`). | B objects | G; E3–E4. A mismatching public keeps an existing `src` file from passing. Owner disposition precedes any semantic change. | Partial canonical promotion, rather than a private diagnostic, is sought. → A07 r2; B09 r2 | BA ↓ X |
| OBJ-B05 · UPHOLD | D4 "ADOPT" Fix B3, and roadmap PR3 placed before the multi-function T4 and extraction work. | B objects | E5; I. The demonstrated real case is already DONE. Prioritizing B3 would spend M2 time without a named obligation it closes. | A later case could justify B3. → A06 r1; B08 r1 | IR → D |
| OBJ-B06 · UPHOLD | "5 ref-C behavioural divergences … fix real behavioural bug in reference C" (`m2_inventory` DG-04; AGENTS.md next step 2 calls them "real ref-C divergences"). | B objects | R3 P1; A1 Q1; P-T4. Three reference witnesses flip under checkpoint with unchanged C. Rewriting C first wastes effort and leaves false-pass risk. | The reported cases preserve existing output checks. → A11 r1; B18 r2; audit before credit. | CV ↓ T |
| OBJ-B07 · UPHOLD | `summary.md` §18.1: "single biggest discovery … unifying root cause … `-5r`". | B objects | E2; E7. 51 only_4r under sampled options and -3r spacing leave multiple histories. Do not promote -5r to a default. | S(f) is contextual and finite. → A09 r1; C13 r2 | UF ↓ H |
| OBJ-B08 · UPHOLD | RFC §2.2.4: "Формат OMF не поддерживает внешние 8-битные релокации". | B objects | R §2.2.4; A0 Q2. The observed limit is NASM OBJ external rel8. OMF LOBYTE does not prove self-relative support in deployed wlink. | No production rule relies on LOBYTE. → Correct RFC language; retain A05 r2. | E → B |
| OBJ-B09 · UPHOLD | RFC §16 row "CodeRegion + Fix B1 + Fix B2" requires a "strict type/state separation CandidateRegion → VerifiedRegion → PlacementPlan" before B1/B2. | B objects | B R0 P5/P6; A0 Q2. A separate CandidateRegion class brings no additional assurance; actual proof binding and materialization do. | Only the current M2 consumers are in scope. → B14 r1; C01 r2 | M ↓ B |
| OBJ-B10 · UPHOLD | `summary.md` §18.9 PR1: "Zero T3 regressions guaranteed (519/519)". | B objects | E0; B R0 P1. 519 and 539 are cohort observations. They cannot guarantee cutover or exercise absent branch/data cases. | The cutover changes the verifier and possibly the live cohort. → A02 r2; rerun the actual declared population. | UF ↓ V |
| OBJ-B11 · UPHOLD | E7 "13 buildable T3 opportunities" as a production metric. It uses `check_t3_buildable` (E7 "Inputs"). | B objects | E7; A0 Q2; P:build. Prefilter counts opportunity, while the E7 combined link supports its reported positives. Separate future preflight from credit. | Actual candidate compiles and links are available for promotion. → B03 r2; A03 r2 | CV ↓ B |
| OBJ-B12 · UPHOLD | E8 precision figures used as general classification of game-CU signals (RFC §9.2 re-mapping). | B objects | E8. Synthetic/library precision cannot be inferred for original game CUs. Keep guidance analyst-facing. | A and B1 are test corpora with distinct mixes. → A10 r1; B13 r2; C12 r2 | UF ↓ H |
| OBJ-B13 · UPHOLD | RFC §4.2/§9.1 `analysis/compilation_units.toml` and §10.2's 13-field provenance as near-term deliverables. | B objects | R §§4,9–10; I. A second persistent database has no M2 reader. Proof inputs and receipts still need lineage. | A derived receipt satisfies current consumers. → B14 r1; C01 r2 | M → I |
| OBJ-B18 · UPHOLD | "5 real ref-C behavioural divergences" (C §1, §8.0 item 5, DEC-C07; inventory DG-04; A §8 "repair the five"). | B objects; R2 C UPHOLD | B R1 P4; C R1 P2; R3 P1. Only two first failures persist under the tested restore. Source fault and status await adjudication. | The five frozen test cases are separate from all other scenarios. → A11 r1; B18 r2; revise C16 outcome language. | CV ↓ T |
| OBJ-B19 · UPHOLD | my own R0 I-3(c)/I-6 and the RFC §13.1 framing that Build A IDENTICAL is a complete Build A check. | B objects; R2 A UPHOLD | A2 P1–P2; P:compare. Mutants survive legacy compare. This affects new placement proof obligations. | Object flags and typed applied fixups matter in the admitted LE model. → A03 r2; C15 conditional | CV ↓ L |
| OBJ-B20 · UPHOLD | C DEC-C02's dependency structure (matcher landing depends on DEC-C03/EXP-1). | B objects; R2 C UPHOLD | P:build; E0; A1 Q2. V4 would delay a safe strict E0 cutover and is unsound as a shape exemption. | Current cohort can use exact bytes or extern literals. → A02 r2; C02 r2 | IR ↓ V |
| OBJ-B21 · UPHOLD | A DEC-A08 and C DEC-C11 placing paired-state reset only within multi-function T4 adoption. | B objects; R2 A UPHOLD, C UPHOLD | P-T4; R3 P1. Current single-function tests already have the defect, so E6 scheduling cannot gate repair. | Preserve current assertions and owner approval for changes. → A11 r1; A08 r2; B18 r2 | CV ↓ T |
| OBJ-B22 · UPHOLD in part | C OBJ-C01 and DEC-C03 "non-deterministic … flaky across runs" and V4 as Stage 0. | B objects | B/C R2 P1. Same-session stability and same-path cross-session variation are compatible. Exact trigger is unisolated and irrelevant to authority. | Report the measured configurations and avoid a universal determinism claim. → Drop V4 cutover dependency. Use A14 r1 for cache policy. | UF ↓ D |
| OBJ-B23 · UPHOLD | C DEC-C05's `omfpatch` `_loc_<addr>` PUBDEF synthesis for cross-piece rel32 into cut interiors. | B objects; R2 C UPHOLD | B R0 P5; A1 Q3. One real interior rel32 linked without patching PUBDEF. No demonstrated necessity for M2. | The supported cases can preserve fixed displacement under exact layout. → A05 r2; no general interior export in M2. | IR ↓ B |
| OBJ-B24 · UPHOLD | C "68 blocked by atomic cross-module symbol migration" and "1002/1010" (DEC-C07, OBJ-C04, Stage 2). | B objects; R2 A REBUT | I. All 61 placeholder rows also need C. Rename availability cannot imply the projected yield. | Classification confidence is evidence-based. → B01 r2; scoped workflow pilot only. | UF ↓ I |
| OBJ-B25 · UPHOLD | C DEC-C11 "hard prerequisite before consolidating any T4 function into a multi-function `.c`"; "Multi-function T4 without E6 leaks intra-TU sibling calls". | B objects; R2 C UPHOLD | E6; P-T4. Physical multi-function layout alone does not determine whether a substitution is bypassed. | Only executed declared boundary obligations trigger extensions. → A08 r2; C11 r2 | CV ↓ F |
| OBJ-B26 · UPHOLD | C §2.8 "[FACT] predominantly `-5r`", §2.9/§7.1 "`non_16_aligned_start` 100% precision", DEC-C13 "-5r primary default". | B objects; R2 C UPHOLD | E7–E8. Only_4r and measured non-16 precision contradict default/100% claims; alignment premises may still give valid implications. | The true base and producer flags are independent evidence. → B13 r2; C12/C13 r2 | UF ↓ H |
| OBJ-B27 · UPHOLD | all three roadmaps forbidding B2 only under the global `--legacy` flag. | B objects; R2 C UPHOLD | P:build; A2 P3. Automatic Unplaceable fallback can move a provider even without global legacy. Span and adjacency use actual layout. | Fixed layout depends on every relevant contribution. → A05 r2; B19 r2 | CV ↓ B |
| OBJ-B28 · UPHOLD | DEC-C11 rev 1, "while keeping single-function `wc1.cemu` unchanged during M2". | B objects | P-T4; A1 Q1; R3 P1. Freezing current cemu leaves a proved false-pass channel and three avoidable divergences. | Affected single-function runs share CPU and RAM today. → A11 r1; B18 r2; C11 r2 | CV ↓ T |
| OBJ-B29 · UPHOLD | DEC-C07 rev 1, Stage 2 "immediately after Stage 1" as a serial dependency. | B objects | I; B R0 P3. Existing eligible candidates can proceed before B1/B2. Serial sequencing blocks immediate work. | Normal verification remains available. → B01 r2, C07 r2 subject to diagnostic wording | IR ↓ I |
| OBJ-B30 · UPHOLD | DEC-C03 rev 1's five V4 conditions as sufficient. | B objects | A1 Q2. The computed byte read defeats five shape predicates and could change behavior if C supplies storage. | No proof excludes overlapping/computed access. → C03 remains withdrawn; C10 r2 | CV ↓ D |

### Indexed objections — Architect C

| Issue and your position | Exact proposition challenged | Competing positions | Supporting evidence, failure mode and practical consequence | Necessary assumption and proposed resolution | Classification, convergence and change test |
| --- | --- | --- | --- | --- | --- |
| OBJ-C01 · REBUT the cutover blocker | That E0 `RegionMatch` (`experiments/build_codegen/e0/matcher_proto.py:333@e6150b8`) and E5 Fix B3 (`experiments/build_codegen/e5/omf_b3.py:172-173@e6150b8`, `decisions.md@e6150b8` D1/D5) can verify real multi-string Watcom 10.0a `-ot` `CONST` segments via whole-segment byte equality or zero-gap `per_symbol` checking. | C objects; R2 C UPHOLD | C R2 P1; E0; A1 Q2. Pads may differ, so a strict verifier loses completeness for some future candidates. Shape alone cannot certify a gap. | Any exemption would require a concrete candidate and independent access bounds. → A02 r2 now; C10 r2 if a case needs it. | CV ↓ D |
| OBJ-C02 · UPHOLD | RFC §7.2 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) and `tools/wc1/emit.py:45-84@a21772b` (`replaced_interior_refs`) modeling Fix B2 solely as branches targeting the *interior* of a replaced cut (`s < t < e`, `t not in entries`). | C objects | A0 Q2; A2 P3; P:emit; R3 P2. Cut-spanning and cut-entry rel8 escape an interior filter. Match all physical edges. | The retained ASM pieces are separate link objects. → A05 r2; B19 r2 | CV ↓ B |
| OBJ-C03 · UPHOLD in part | `docs/research/build-codegen/decisions.md@e6150b8` (Decision D6) and `E4-omf-extraction.md@e6150b8` treating `experiments/build_codegen/e4/omf_extract.py` as ready for near-term production adoption pending only minor `rev-e4-01` polish. | C objects | E4; A1 Q3–Q4; B/C R1. THREAD reset, DATA-public rebasing and untyped linear decode are valid defects. Missing fixed 64-fixup chunking is not established. | A supported subset may reject other records and typed layouts. → A07 r2; C08/C09 r2 | CV ↓ X |
| OBJ-C04 · UPHOLD the priority | `docs/research/build-codegen/summary.md@e6150b8` and `decisions.md@e6150b8` (§18.9 rollout priority) sequencing B3 (E5) and multi-function T4 (E6) ahead of or on the M2 completion critical path without accounting for the actual 98-function M2 blocker distribution on `main@a21772b`. | C objects; R2 C UPHOLD | I; E5; R3 P1. General B3/E6/E4 lack an immediate demonstrated consumer. The 68 require judgment, and five xfails are not five established C repairs. | Keep independently eligible work moving under existing gates. → B01 r2; revise C07 r2's factual clauses. | BA ↓ I |
| OBJ-C05 · UPHOLD | E0 `matcher_proto.py:358-359@e6150b8` validating `FunctionMatch` branch closure against `[first_pub_base, first_pub_base + len(_TEXT))` instead of the target function's own `[base, base + fn_len)`. | C objects | E2 Cause B; E3 rev-e3-01. First-public window creates nine conservative false unsupported results. Local scope also needs explicit external obligations. | Some diagnostic TUs are non-contiguous in the original. → A02 r2; C02 r2 | CV ↓ V |
| OBJ-C06 · UPHOLD with correction | RFC §2.2.5 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) asserting that Watcom 10.0a always aligns functions to 4 bytes while OW2 aligns to 16 bytes. | C objects | E2 alignment matrix. -4r -ot disproves 'always 4'. PARA claim is limited to tested -ot. -3r and -5r both reach tested 4-byte spacing. | In-object public spacing and SEGDEF alignment are different facts. → C13 r2; B10 r1 | UF ↓ H |
| OBJ-C07 · UPHOLD | RFC §9.3 (`docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`) proposing `_DATA`/`_BSS` staircases and `call_locality_drop` as primary CU boundary recovery signals. | C objects | R §9.3; E8. Poor corpus precision makes these unsuitable for automatic boundaries. Corpus measures do not estimate game-wide rates. | Historical boundaries lack oracle coverage in the game. → A10 r1; B13 and C12 r2 | UF ↓ H |
| OBJ-C08 · UPHOLD the remaining path issue | Production `tools/wc1/t3_audit.py@a21772b` claiming checkout-portable, fail-closed improved-T4 audit provenance, and `tools/wc1/oldcc.py@a21772b` omitting E7 D9 short-path protection. | C objects | EV-3; P:oldcc,t3_audit. R3 provenance issues repaired at EV-3. Effective path crash risk remains. | Long translated paths can reach the installed compiler. → A12 r1; B22 r1; C04 r2 | IR ↓ W |
| OBJ-C09 · REBUT the exemption requirement | `DEC-A06` (GPT: *"Admit B3 initially for fully verified whole segments only"*), `DEC-B02` (Claude: adopting E0 matcher semantics as-is), and `DEC-B08` (Claude: RFC §8.2 constraints 1–5 as-is for B3) omitting explicit handling of Watcom 10.0a's non-deterministic uninitialized 1..3-byte `CONST` alignment padding. | C objects; R2 A REBUT, B REBUT | A1 Q2; B/C R2 P1. Exact first admission tolerates fewer cases, preserving soundness. Variability does not make a gap proof-irrelevant. | Re-adopt a gap rule only when independently bounded and needed. → A06 r1; C10 r2 + A14 r1 | CV ↓ D |
| OBJ-C10 · UPHOLD in part | `DEC-B04` (Claude) emitting cross-object `rel32` to cut interiors and cross-object `rel8` as raw literal bytes (`db`) while relying on unhardened `wc1.compare` as "a complete check", and both `DEC-B04` and `DEC-A05` omitting explicit cross-piece fallthrough guards. | C objects; R2 A UPHOLD, B UPHOLD | A2 P3; A1 Q3; B R0 P5; R3 P2. Guard displacement, fallthrough and legacy. No synthesized PUBDEF is needed on measured cases. In the serial example the relevant fallthrough is 0x202bb to 0x202bc. | Piece-local or literal form uses the same typed verified edge. → A05 r2; B04/C05 conditional; B19 r2 | CV ↓ B |
| OBJ-C11 · UPHOLD | Internal contradiction between `DEC-B03` (*"Regression tests: IntroOpSyncSound standalone is rejected; Group B is accepted"*) and `DEC-B04` (admitting fixed-layout in-place cross-object `rel8` branches spanning a cut). | C objects; R2 A UPHOLD, B UPHOLD | A0 Q2; B03/B04 r2; R3 P2. Bridge-off rejection and proved bridge-on integration are distinct. Prove the bridge-on candidate before credit. | Tests use mode-qualified fixtures. → B03 r2; A03/A05 r2 | CV ↓ B |
| OBJ-C12 · UPHOLD the incomplete diagnosis challenge | `DEC-B16` (Claude) reclassifying only `IntroOpWaitSound` as T4 harness state asymmetry and estimating S4 as `"up to +4"` DONE. | C objects; R2 A UPHOLD, B UPHOLD | B R1 P4; C R1 P2; R3 P1. Two additional scenarios now pass under checkpoint. Two persistence observations are not categorical C diagnoses. | Credit requires an owner-approved witnessed result. → Withdraw B16 r1; revise C16 r2 accordingly. | UF ↓ T |
| OBJ-C13 · REBUT the universal dependency | Architect B's Stage S1 (`DEC-B06`) merging the first multi-function `src =` TU (Group B) into production **before** Stage S2 (`DEC-B02` production E0 `RegionMatch`). | C objects; R2 A UPHOLD, B REBUT | E1; B R0 P3; G. C withdrew the objection in R2. Early production rollout isn't needed with equivalent exact proof; older E1 evidence alone cannot certify a new artifact. | Bind the proof to the current private pilot object. → A13 r1; C06 r2 | IR ↓ J |
| OBJ-C14 · UPHOLD in part | `DEC-A07` (GPT) and `DEC-B09` (Claude) specifying E4 pilot prerequisites without including all four Probe-5 defects in `e4/omf_extract.py` (and `DEC-A07` omitting Claude's Gate-2 governance prerequisite). | C objects; R2 A UPHOLD | G; E4; A1 Q3–Q4. Canonical gate, THREAD, rebasing and code/data typing matter. An arbitrary input scope or 64-fixup bound adds unsupported requirements. | Future pilot is restricted to a supported subset. → A07 r2; B09/C08/C09 r2 | BA ↓ X |
| OBJ-C15 · UPHOLD | Omission of Watcom 10.0a short-path staging/guard (`tools/wc1/oldcc.py`, E7 Decision D9) from both Architect A's and Architect B's Stage 0 / M2 roadmaps. | C objects; R2 A UPHOLD, B UPHOLD | EV-3; B/C R2 reports; P:oldcc. EV-3 records rc=5 during deep-path compile. Path is not proved to explain every rc=-11. | Measure effective arguments with same tool chain and warmed prefix. → A12 r1; B22 r1; C04 r2 | IR ↓ W |
| OBJ-C16 · UPHOLD the open admission criterion | `DEC-B01` (Claude) restricting M2 tooling strictly to E0/planner/B1/B2/joint-TUs/T4-state and assigning the remaining 78 functions to `"existing drivers"` (S5). | C objects; R2 B UPHOLD | I; P:oldcc. Closed list misses enablers, though 61 need more than migration. A bottleneck-specific helper can help without delaying ready work. | A ready batch currently encountering that obstacle can be named. → B01 r2; pilot transactional edits only as justified. | IR ↓ I |

## 1. New evidence and source index

### R3 P1 — Five T4 witnesses with a fuller checkpoint

I ran the actual five EV-3 test functions against the unchanged reference C in the private `build/r2e` export. The final invocation was:

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r2e"
export PYTHONPATH="$WC1_ROOT/tools"
export PYTHONDONTWRITEBYTECODE=1
export WINEPREFIX="$PWD/build/oldcc/wineprefix"
export TMPDIR=.
unset WC1_T4_AUDIT_LOG WC1_T4_AUDIT_NONCE
r=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt
cd "$WC1_ROOT"
python3 "$r/r03-t4.py" "$WC1_ROOT" | tee "$r/r03-t4.log"'
```

The script calls the five test functions directly. Its checkpoint wrapper retains `cemu.run_pair` for the actual comparisons, saves Unicorn CPU context and all mapped bytes before the original call, checks that mapping permissions and stub assignments did not change, restores changed mapped bytes and CPU context before the C call, and restores allocator and selected emulator bookkeeping. A third mode starts a fresh `Emu` for every existing case before applying the pair checkpoint. For the selected fixtures, custom callbacks use emulator memory or immutable captured values, and their logs live in emulator memory. The initial driver stopped on the first expected stock assertion because it matched the wrong diagnostic phrase. I corrected the driver filter from `"diff(s)"` to `" failed on "`; the complete rerun exited 0.

| Witness | Stock first difference | Checkpoint | Fresh case + checkpoint |
|---|---|---|---|
| WaitSound `0x231cc` | `cnt3-a0`: `0x801130 30 != 0c` | 4/4 pass | 4/4 pass |
| IntroRunScript `0x23668` | `b0-lim2-ab0-fo0`: `0x801130 68 != 50` | 16/16 pass | 16/16 pass |
| IntroPlay `0x23ae0` | `digffff-req1-ab0-m0`: `0x801130 74 != 68` | 12/12 pass | 12/12 pass |
| StartCredits `0x23530` | `d5-idxffff`: `0x59eb9 01 != 00` | Same first difference | Same first difference |
| EndScreen `0x2fcfc` | `win race0`: `0x80054c 70 != 50` | Same first difference | Same first difference |

The driver stops a failing witness at its first assertion. It does not compare unwatched effects, reset arbitrary Python objects, reverse per-side call order, or produce a production audit record. The results strengthen the three-flip/two-persistent observation without certifying either root cause or changing inventory status. The script SHA-256 is `bb70846e9c1e83a1f710c50ec047d4c0cbe36af7e65fc8815a0880aac2039c6c`. The log SHA-256 is `e279f232307ea541c56d7dc4110b532f2ef052a0b03f7a4b0e05b9a8ac97581c`.

### R3 P2 — Real Build A link of standalone Sync

I used a fresh private EV-3 export. The driver adds only the existing `IntroOpSyncSound` source assignment in memory and uses current compilation, placement, assembly and link. It runs unmodified NASM on the affected generated piece as a negative control, then changes only its two branch operands to piece-local expressions anchored at the actual right-piece start. No production files or experiment implementations were changed.

```bash
nix develop -c bash -c '
set -eu
set -o pipefail
probe_repo="$PWD/build/r3s"
test ! -e "$probe_repo"
mkdir "$probe_repo"
git archive 17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9 | tar -x -C "$probe_repo"
ln -s "$PWD/original" "$probe_repo/original"
export WINEPREFIX="$PWD/build/oldcc/wineprefix"
export WC1_ROOT="$probe_repo"
export PYTHONPATH="$probe_repo/tools"
export PYTHONDONTWRITEBYTECODE=1
unset WC1_CFLAGS
r=/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt
cd "$probe_repo"
export TMPDIR=.
timeout 180s python3 "$r/r03-sync.py" 2>&1 | tee "$r/r03-sync.log"'
```

The actual right ASM piece was `[0x231ca,0x2322c)`. Stock NASM exited 1 at `piece_295.asm:19,21` with `OBJ format can only handle 16- or 32-byte relocations`. The two expressions emitted `7493` and `7589` with zero intersecting fixups. The link exited 0 and placed 540 functions from 535 C files, all 535 in sequence and zero legacy. It reported `IDENTICAL (loaded image, entry, stack, fixups)`. I also checked equal loaded bytes, object flags, entry/stack descriptors and typed physical fixup occurrences, with no conflicting duplicate. The stock matcher on the same private source returned `MATCH IntroOpSyncSound_` under this command.

```bash
nix develop -c bash -c '
set -eo pipefail
export WC1_ROOT="$PWD/build/r3s" WINEPREFIX="$PWD/build/oldcc/wineprefix" PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$WC1_ROOT/tools"
cd "$WC1_ROOT"
export TMPDIR=.
python3 -m wc1.match src/playflic/intro_op_sync_sound.c'
```

This establishes the specific standalone in-place bridge. The driver does not implement a generic planner or strict RegionMatch, and did not exercise global/automatic legacy or other branch forms. The script SHA-256 is `0ea6142873154c24803dd96481e8067ca4d7d33d557aa512cc9d902fd3307379`. The log SHA-256 is `2af95eccb26bd5703cc88f0190c137149fc4fd7de32ee7259968c9bbffdf1661`.

All probe commands used the worktree’s Nix shell, warmed private Wine prefix and private export paths. I ran neither `make verify` nor the full test suite. The three frozen files matched the supplied sizes and SHA-256 digests. I recomputed the 38 indexed proposition hashes and the 18 omitted revision hashes from the exact texts. The absent revisions are A02/A03/A05/A07/A08 r2 and C01/C02/C04–C13/C16 r2. I did not inspect another Architect’s workspace.

| Key | Pinned evidence |
|---|---|
| EV-3, W | EV-3 notice, `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/{report.md,e7_snapshot_revalidation.json}@17733f9` and `tools/wc1/oldcc.py@17733f9`. |
| G, I | `AGENTS.md`, `Makefile`, `docs/{GOAL,METHODOLOGY}.md`, `tools/wc1/{match,m2_inventory,progress}.py@17733f9`, and `docs/telemetry/campaigns/2026-11-27-m2-mechanical-cleanup/candidate_ledger.json@a21772b`. |
| P, P-T4 | `tools/wc1/{build,emit,match,omf,omfpatch,compare,le,cemu,emu,t4spec}.py@17733f9`. Especially `build.py:94–104,305–353`, `le.py:_parse_fixups`, `cemu.py:344–415`, and `emu.py:188–240`. Fixture files are `tests/test_playflic_t4.py@17733f9` and `tests/test_mod_2efd0_t4.py@17733f9`. |
| R, E0–E8 | `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac`; experiment reports under `docs/research/build-codegen/@e6150b8` and `results/{e0/controls.json,e0/t3_reaudit.json,e1/results.json,e2/results.json,e3/results.json,e4/results.json,e5/results.json,e6/results.json,e7/calibration_matrix.json,e8/metrics.json}`; `experiments/build_codegen/{e0/matcher_proto.py,e4/omf_extract.py,e5/omf_b3.py,e6/mf_cemu.py}@e6150b8`. |
| A0, A1, A2 | `CONSILIUM-R00-POSITION.md`, `CONSILIUM-R01-CROSSREVIEW.md`, `CONSILIUM-R02-RESPONSE.md`, with the logged probes at their stated pins. |
| B, C | Frozen `r03-inbox/01-architect-claude-response.md` and `02-architect-gemini-response.md`. Prior-round probes reported there are attributed to their authors. |

## 2. Position changes

I retain my five r2 propositions and do not increment any existing A revision. I now reject B07 r1 because B withdrew it in favor of the complete paired-state contract. For C01, C02, C04, C05, C06, C08, C09, C10, C12 and C13, my former conditional positions on r1 become rejections of superseded text. I record new positions separately on the exact r2 propositions. I accept B18 r2. The new checkpoint results strengthen my conditions on C07 and C16 r2 because they show what persists under controlled state, while leaving attribution and production audit as distinct obligations. I retain A05 r2 after R3 P2. The tested expressions resolve one technical uncertainty without changing its general rule.

## 3. New objections and decision

**OBJ-A22 — Correctness-verification.** B21 r2 retains the clause “are excluded from proof-cache digests by normalization” after B02 r2 requires exact data verification and raw-object binding. With two input artifacts differing only in a gap, a normalized key can collide even when exact RegionMatch would reject one. A1 Q2 demonstrates a semantic gap read as well. If the cache only groups work, the objection is satisfied. Otherwise require A14. A cache negative under test D would demonstrate why the distinction matters. [A1 Q2, B02/B21 r2, `build.py:94–104@17733f9`]

**OBJ-A23 — Unsupported factual claim.** C07 r2 says StartCredits and EndScreen “remain genuine ref-C bugfixes”, while C16 r2 would make the corresponding inventory reclassification. The five cases include four PLAYFLIC tests and EndScreen. R3 P1 confirms their first differences with a stronger checkpoint and fresh cases. It does not independently validate every substitution or identify the causal source line. Use “two persistent witness differences under the tested reset” and distinguish diagnosis from DONE. An equivalent-input run with independently validated substitutions and a first-divergence trace could justify more specific labels. [R3 P1, `tests/test_playflic_t4.py@17733f9`, `tests/test_mod_2efd0_t4.py@17733f9`]

```text
Decision: DEC-A14
Title: Bind verification reuse to raw artifacts
Proposition: Bind each authority-bearing verification or integration receipt to the exact raw artifacts and the verified context used in its claim. A normalized CONST digest may group candidates but shall never substitute for raw identity on authority reuse; reverify before accepting any different raw artifact.
Revision: 1
Position: PROPOSE
Reason: The strict verifier checks exact data before any independently justified exception. A normalized lookup alone cannot identify the object consumed by the build.
Evidence: A1 Q2; B02 r2; B21 r2; tools/wc1/build.py:94–104@17733f9
Assumptions: Only a consumer reusing verification or integration results needs this rule. It requires no new persistent store.
Dependencies: DEC-A02 r2 and DEC-A03 r2
```

## 4. Convergence assessment and change tests

The direction of each issue is in §Live issues. Group B sequencing is an implementation preference once the exact artifact meets A13. File-gate authority, proof identity, fallthrough and verified input state are substantive obligations. The RFC wording about OMF and NASM is editorial if the supported path remains the tested fixed-layout path. Parallel M2 work is a roadmap decision supported by visible eligible work. The tested Sync bridge and five-witness checkpoint reduce factual uncertainty; neither settles generic release admission.

| Test | Cheapest decisive check and the result that would change my position |
|---|---|
| V — Verifier | Audit all live declared T3s at cutover and add raw checksum/FRAME, non-contiguous local, external-context and trimmed-target controls. An accepted invalid artifact or failed live control blocks the cutover. |
| B — Partition edges | R3 P2 closes the specific Sync positive and stock NASM negative. Next use one MissionDefeat cut with conditional fallthrough, a leading-prefix variant, a prefixed rel8 and both legacy negatives. Wrong emitted field, a relocation intersecting a fixed field, moved successor, or a claimed positive that fails the link blocks that rule. A real unmet M2 edge with an independently validated symbolic export would reopen the export choice. |
| J — Exact group | Run actual Group B with a strict exact-object proof, both compiler checks, existing file gate, typed Build A and cited test checks. A verified fit supports early admission; absent strict evidence or changed check meaning requires the specified checkpoint. |
| L — LE | R2 P1 already measured flags, entry/stack and types. Add all three R2 P2 mutants to a strict comparator and keep the real baseline as positive control. A bad acceptance or good rejection changes the implementation; a loader-significant baseline difference goes to the owner. |
| D — CONST and reuse | Compile the same source at one controlled path across sessions, then vary one input. Separately seed a proof for one raw object and retry with a gap-only mutant sharing the normalized key. A raw mismatch must trigger reverification. Admit a future gap exclusion only with independently proved bounds and computed-read and changed-literal negatives. |
| T — Paired state and diagnosis | R3 P1 confirms the five witness observations. Add original-first/C-first and independent-world controls for CPU, heap/mappings, host/guest writes and host mutable dependencies. Run the cited scenarios with nonce-bound audit and regress the affected T4 suite once under the adopted mechanism. Order dependence, a false audit pass or an unjustified xfail change blocks rollout. Trace the two persistent first differences to attribute cause. |
| X — Extraction | Start only with a justified candidate and owner source-gate decision if needed. Test cross-record THREAD, mixed publics at nonzero slice, typed tables, actual linker record bounds and transform/link receipts. A changed retained obligation or invalid link blocks the subset. |
| W — Compiler paths | Measure real source, include, output, CWD and compiler-read environment paths independently with one warmed private prefix and a shallow control. A wrong include or compiled-output attribution blocks staging; a controlled failure inside the proposed envelope blocks that guard. |
| F — Behavioral boundary | Use one witness needing a real substitution, callback or pointer identity. Try interior escape, wrong ABI, wrong target and original-only execution negatives, then require audit parity. A passing negative blocks that extension. |
| H — Historical inference | Challenge the proposed merge with an independently known legal producer/linker partition or shared-storage alternative. Test true PARA bases with a leading prefix and extend flag searches only as useful. A measured alternative defeats a hard inference or default, without changing existing presets. |
| I — Roadmap | Run an already-eligible candidate under current gates and a ready batch that demonstrably encounters migration. A precise failure that only a capability removes can move it earlier. A missing name/body or unexplained result does not establish tool yield. |

## 5. Structured positions

These entries cover every non-unanimous indexed decision, the omitted current revisions and the new proposition. I carry forward the indexed unanimous positions without reopening them.

### Architect A

```text
Decision: DEC-A02
Revision: 1
Proposition SHA-256: 20349fbc30ce2eba38b56f88990e4f40f3777cb92c9af489e809a95abe525417
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-B20, OBJ-A03, OBJ-C01, OBJ-C05, OBJ-C09

Decision: DEC-A02
Revision: 2
Proposition SHA-256: 87a63b4cd4658b1d7e03e377aab0100a096d996f6416aaf90cae6eabb13866ca
Position: ACCEPT
Reason: Scoped local and whole-region checks, strict raw input, and live file-gate audit.
Conditions: none
Related objections: OBJ-A03, OBJ-A10

Decision: DEC-A03
Revision: 1
Proposition SHA-256: f48dd625f3fd34b6cee6a01ae6f9616fce969d705868f8df9fa2f7ba5881c32b
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-B19, OBJ-A02, OBJ-A19, OBJ-A21

Decision: DEC-A03
Revision: 2
Proposition SHA-256: 58e7c0dd039eca33389f5687af38366d392357c6102a752407af6944ab5d1fda
Position: ACCEPT
Reason: Actual materialization and validated raw fixup occurrences precede loader equivalence.
Conditions: none
Related objections: OBJ-A19, OBJ-A21

Decision: DEC-A05
Revision: 1
Proposition SHA-256: aa4d747deed87bb671bbf98cacd3a06dee04c312e3dd749c5b69905937ee1e43
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-C02, OBJ-C10, OBJ-B27

Decision: DEC-A05
Revision: 2
Proposition SHA-256: 414da43a537e7ef898d23fcb6536e2e18f55026e216ff241f6aed39dac601fa5
Position: ACCEPT
Reason: R3 P2 links the Sync bridge. Actual adjacency and no-fixup proofs still cover every new cut.
Conditions: none
Related objections: OBJ-C10, OBJ-B27

Decision: DEC-A07
Revision: 1
Proposition SHA-256: 9c28c5b2f073471389239eb6fb44da4e48a6da55224cd95ea91d05e994d2d846
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A14, OBJ-B04, OBJ-C03, OBJ-C14

Decision: DEC-A07
Revision: 2
Proposition SHA-256: 5d8aa99eec7ea3f4e32fe146ca5ad05040695c2d489b05ab6b57865109b2898d
Position: ACCEPT
Reason: Owner source-gate disposition and independently verified transform and link.
Conditions: none
Related objections: OBJ-B04, OBJ-C14

Decision: DEC-A08
Revision: 1
Proposition SHA-256: 652a1d04c4a5bc9febc03fae9a6637469f55698981699a3f995554e59c70a883
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A12, OBJ-B21, OBJ-B06, OBJ-C12, OBJ-A20

Decision: DEC-A08
Revision: 2
Proposition SHA-256: 2be94ebaca45a667115e4d3afe3935dcd6515528f4fcd42e82cf946f536b2e31
Position: ACCEPT
Reason: Present input symmetry is distinct from demand-led witness boundaries.
Conditions: none
Related objections: OBJ-A12, OBJ-A20

Decision: DEC-A12
Revision: 1
Proposition SHA-256: 40569d572c9a4641aa40a42e9385ab97985b12e5080193d43c558b9dd4c38c37
Position: ACCEPT
Reason: Protect effective paths and preserve compiler semantics.
Conditions: none
Related objections: OBJ-C15

Decision: DEC-A13
Revision: 1
Proposition SHA-256: c2358d2447d36c8f78ee4eacc974d9e21e4b4e1a3d52e3f3ce7e7eac5fd3e46c
Position: ACCEPT
Reason: Certify the exact Group B object independently of general rollout.
Conditions: none
Related objections: OBJ-C13

Decision: DEC-A14
Revision: 1
Proposition SHA-256: bc96f36311c7f296bcff8b35d52be636ff94f57bda8bcc46dac4459c99686ae7
Position: ACCEPT
Reason: Raw receipt identity and normalized scheduling serve different claims.
Conditions: none
Related objections: OBJ-A22

```

### Architect B

```text
Decision: DEC-B01
Revision: 2
Proposition SHA-256: 3bf6d12ea2777317ef8e60bcd9c6428eca51d015f63a02d34e867b16c5c01390
Position: ACCEPT
Reason: Parallel work and observed-blocker admission.
Conditions: none
Related objections: OBJ-A15, OBJ-A02, OBJ-A03, OBJ-C15, OBJ-C16

Decision: DEC-B02
Revision: 2
Proposition SHA-256: e3dcf170f78bb48740ab7e0575ddb253cffea0e1ff0b9fff43adc2c69ef74fed
Position: ACCEPT
Reason: Strict raw admission and exact-data cutover.
Conditions: none
Related objections: OBJ-A10, OBJ-A17, OBJ-A03, OBJ-C01, OBJ-C05, OBJ-C09, OBJ-B20, OBJ-B30

Decision: DEC-B03
Revision: 2
Proposition SHA-256: 8055745b4eb77009a7b67fbd3af3bdf07c753926b05389138f50ca0d12d17680
Position: ACCEPT
Reason: Shared preflight plus real integration evidence.
Conditions: none
Related objections: OBJ-A09, OBJ-A13, OBJ-C11

Decision: DEC-B04
Revision: 2
Proposition SHA-256: 445c252ed6fa757985217f7dd84bd6245756b0899274c4974d7f494f7e1c24c0
Position: CONDITIONAL
Reason: Fixed encodings require the same complete physical proof.
Conditions: Require identical instruction and target identity plus zero intersecting fixup and physical span/adjacency under A05 r2.
Related objections: OBJ-A13, OBJ-A02, OBJ-C10, OBJ-C11, OBJ-B27, OBJ-B19

Decision: DEC-B06
Revision: 1
Proposition SHA-256: 22cad9b6a92aa93eae83f22e57bc498f9cb9262eb72c66b68182f04360f506dc
Position: CONDITIONAL
Reason: Keep independent Group B pilot under exact current proof.
Conditions: Use A13 r1 if early, and preserve cited T4 checks or obtain owner authorization for a change.
Related objections: OBJ-A15, OBJ-C13

Decision: DEC-B07
Revision: 1
Proposition SHA-256: 2bfe76f44dbbb025a814b65c7e860923fe87972f35dfe6bdf5d86cbc5ac2104b
Position: REJECT
Reason: Withdrawn and superseded by complete paired state.
Conditions: none
Related objections: OBJ-A12, OBJ-C12, OBJ-B21, OBJ-A20

Decision: DEC-B09
Revision: 2
Proposition SHA-256: da8923449d98d336b828858026a24fbb4ac844c0340f937869a9454dec1489bb
Position: ACCEPT
Reason: A bounded post-M2 pilot preserves the source gate.
Conditions: none
Related objections: OBJ-A14, OBJ-C03, OBJ-C14, OBJ-B04, OBJ-A18

Decision: DEC-B12
Revision: 1
Proposition SHA-256: 7fe4e53785e07c33c212c6b5fc1e9b20f1ac087f8ab0a21aee6563e54ef5ddd3
Position: CONDITIONAL
Reason: Witness-specific extension must remain usable after M2.
Conditions: Apply the trigger to justified post-M2 witnesses, prove entry-only edges for an entry hook, and require A08 r2.
Related objections: OBJ-A12, OBJ-B25

Decision: DEC-B13
Revision: 2
Proposition SHA-256: 74e56068c80a8c6a55f5524bc58003d130052633e5966f5d80460a288b9128f3
Position: ACCEPT
Reason: Verified premises qualify analyst-facing CU constraints.
Conditions: none
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-B16
Revision: 1
Proposition SHA-256: ba07a05ddd54e66408d68f654387aeecfee06aa9b9f5e84ba5724764215c339c
Position: REJECT
Reason: Withdrawn. Probe observations do not change status.
Conditions: none
Related objections: OBJ-A15, OBJ-C12, OBJ-A20, OBJ-B18

Decision: DEC-B17
Revision: 1
Proposition SHA-256: 0ebcbdfd1442a8d5431012977688f911d68821ceca5bf59f6c70d4c8ee4b6ed1
Position: REJECT
Reason: General extraction lacks a demonstrated M2 need.
Conditions: none
Related objections: OBJ-A14, OBJ-B04, OBJ-C14

Decision: DEC-B18
Revision: 2
Proposition SHA-256: eea41a0ae22168be8fe937044df924cbac29930301347029277b16ced87ecec2
Position: ACCEPT
Reason: Complete paired-state and owner-approved test changes.
Conditions: none
Related objections: OBJ-A20, OBJ-B21, OBJ-A12, OBJ-B28

Decision: DEC-B19
Revision: 2
Proposition SHA-256: 5efd2b5a5855cbd9b4eb8370ecfdbfabb69d59b85ea44de5fe73bc3295c41b8d
Position: ACCEPT
Reason: Check actual placement and fallthrough.
Conditions: none
Related objections: OBJ-B27, OBJ-C10

Decision: DEC-B20
Revision: 1
Proposition SHA-256: 9827f9478582739191aef8fc7f845090e364d72add8893b812ea869bba1ed89a
Position: CONDITIONAL
Reason: Measured semantic parity differs from raw serialization parity.
Conditions: Use A03 r2. Validate all raw occurrences, compare normalized typed loader semantics, and present loader-relevant deltas to the owner.
Related objections: OBJ-A19, OBJ-A21, OBJ-A02, OBJ-B19

Decision: DEC-B21
Revision: 2
Proposition SHA-256: fe41a9239ce8fb17051566078783e6220138ba464d064535a1092f09844f7b6f
Position: CONDITIONAL
Reason: Independent access proof is necessary. Normalized authority remains unsafe.
Conditions: Use A14 r1 for authority cache binding. Limit normalized digests to grouping and scheduling.
Related objections: OBJ-A11, OBJ-C09, OBJ-B30

Decision: DEC-B22
Revision: 1
Proposition SHA-256: 1deaeb25012d2c931c08902359bcd561b466217c514b8eb868a97ea931cd6d1c
Position: ACCEPT
Reason: Measured early path errors improve reliability.
Conditions: none
Related objections: OBJ-C15, OBJ-A17

```

### Architect C

```text
Decision: DEC-C01
Revision: 1
Proposition SHA-256: 89590ee50b1609f5e5ad7e4ef98a560dd7cf5d5471e6e6850d8aa5fa0a7c6c3a
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A09

Decision: DEC-C01
Revision: 2
Proposition SHA-256: e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de
Position: ACCEPT
Reason: Four distinct outcomes, with one derived plan and no speculative durable store.
Conditions: none
Related objections: OBJ-A09

Decision: DEC-C02
Revision: 1
Proposition SHA-256: 32bdbb10f84f604d9b33aa2388b5dd07c842fea749a9408695e6c52c4d9c967b
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A10, OBJ-A11, OBJ-B22, OBJ-A03, OBJ-B20

Decision: DEC-C02
Revision: 2
Proposition SHA-256: 8f73dfdc9e753c1ac2127883b3ec1880895adc497ea11560adf6844ec25cb25b
Position: ACCEPT
Reason: The narrow verifier preserves raw semantics, local bounds, trim guards and existing gate behavior.
Conditions: none
Related objections: OBJ-A03, OBJ-A10, OBJ-B20

Decision: DEC-C03
Revision: 1
Proposition SHA-256: 2e96264a171ef72dea16c558f344f5e6d44e38ea367f1645f4ff4f3b7a572896
Position: REJECT
Reason: Withdrawn. A computed read defeats gap predicates.
Conditions: none
Related objections: OBJ-A11, OBJ-B22, OBJ-C09, OBJ-B30, OBJ-B20

Decision: DEC-C04
Revision: 1
Proposition SHA-256: 6110ad1cd89c84ed999125906beec1c44830a88c230244bb8a10dada43eb2c2b
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A17, OBJ-C15

Decision: DEC-C04
Revision: 2
Proposition SHA-256: 083f8ccd09b23d76e98d1e064d2b6f0faa61f405dcd0fdbff6062f094c657f37
Position: ACCEPT
Reason: Effective-path measurement and compile/include parity address the active EV-3 fault class.
Conditions: none
Related objections: OBJ-A17, OBJ-C15

Decision: DEC-C05
Revision: 1
Proposition SHA-256: 16a616ad8b0e5a2e1f6fffa070f8ca251cc5cf83ccc187092c1b2b6cebf78cd9
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A09, OBJ-A13, OBJ-B23, OBJ-B27, OBJ-C10

Decision: DEC-C05
Revision: 2
Proposition SHA-256: 0fa438f046f1b4530042fe24e4a888d7d3105556fcba5a6bf8828e2d3f3c512d
Position: CONDITIONAL
Reason: R3 P2 validates the Sync instance. Exact encoding and actual layout are the right basis.
Conditions: Require verified target identity, zero intersecting relocation for fixed fields and adjacency for every live edge under A05 r2.
Related objections: OBJ-A13, OBJ-C10

Decision: DEC-C06
Revision: 1
Proposition SHA-256: 3bd8b1d5e90aa8cadc8158702ddbd8c16b0f3e5d72fb04fcde4dece5ab40c12a
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A15, OBJ-A16, OBJ-C13

Decision: DEC-C06
Revision: 2
Proposition SHA-256: ae897988ef4e49b930a51202ed26ca800a03ac6a623a085235a6b3b1306b1f23
Position: ACCEPT
Reason: An exact whole-TU proof, actual Build A and normal owner/test checks suffice independently.
Conditions: none
Related objections: OBJ-C13

Decision: DEC-C07
Revision: 1
Proposition SHA-256: 9be785e085ddec89659f364826c1f2c63175dd42918f8cc48f4936926f067b6f
Position: REJECT
Reason: Serial staging delays eligible work.
Conditions: none
Related objections: OBJ-A12, OBJ-A15, OBJ-B18, OBJ-B24, OBJ-A20, OBJ-B29

Decision: DEC-C07
Revision: 2
Proposition SHA-256: f92f2bc0a42e324e7de41a67f398e1ada6d68bcd94414a8f73f8b65ceebfe999
Position: CONDITIONAL
Reason: Parallel M2 tracks and M3 independence are sound; diagnosed input differences must remain scenario-specific.
Conditions: Replace 'genuine ref-C bugfixes' with two persistent witness differences under R3 P1. Allow E6 earlier only for a named necessary witness. Do not count new DONE yet.
Related objections: OBJ-A20, OBJ-A23, OBJ-B29

Decision: DEC-C08
Revision: 1
Proposition SHA-256: ee55d25043dd8f9fe0658e47dda212dd5ab018901fd44d367154bb19d23031f3
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A14, OBJ-A18, OBJ-C14

Decision: DEC-C08
Revision: 2
Proposition SHA-256: 6d614771ea47701e9b769af7e137755df151d7e4d05c6c4cc063d2fb76cb8a00
Position: ACCEPT
Reason: Demand-led post-M2 extraction with the owner and supported-record tests.
Conditions: none
Related objections: OBJ-A14, OBJ-C14

Decision: DEC-C09
Revision: 1
Proposition SHA-256: dfab7c569dd76b8c399ab8dc5b66f513f079201a7e15f82b60a85f34f4bb801b
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A18, OBJ-C14

Decision: DEC-C09
Revision: 2
Proposition SHA-256: 802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b
Position: ACCEPT
Reason: Share the strict supported parser/transform subset and measure deployed linker bounds.
Conditions: none
Related objections: OBJ-A18

Decision: DEC-C10
Revision: 1
Proposition SHA-256: 0755146f59113b38bcc854a65ec97728b37cc79daacb0c966fac0f725422b10a
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A11, OBJ-B22, OBJ-C09, OBJ-B30

Decision: DEC-C10
Revision: 2
Proposition SHA-256: b609b22870c7f38845c3c2e49ae3d2e329a747bbc6168387d06e935890c5668f
Position: CONDITIONAL
Reason: Exact whole-segment B3 and independent access evidence for later exclusions are sound.
Conditions: Use A14 r1 in place of any unconditional normalized proof-authority key inherited from B21 r2.
Related objections: OBJ-A11, OBJ-A22

Decision: DEC-C11
Revision: 1
Proposition SHA-256: 7a204425544c260b6b818b7daa21215e2318042fecc764b89da96c9aab06ad9b
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A12, OBJ-B25, OBJ-B21, OBJ-B28

Decision: DEC-C11
Revision: 2
Proposition SHA-256: 46e66a775e59a9b1b2eb8310febc5ec293a7db9351392abb354772ee9f918090
Position: ACCEPT
Reason: Pair input equivalence is immediate. Boundary machinery serves the obligations a witness exercises.
Conditions: none
Related objections: OBJ-A12, OBJ-B28

Decision: DEC-C12
Revision: 1
Proposition SHA-256: 9f75f979df9121edb96c8730e7c1f05854f8c57fdbcdfc0dea7933f8854c6139
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-C12
Revision: 2
Proposition SHA-256: 7009936a27e239c6860b5f313428f5a703e6b354e36347d6cd7110e490a504fa
Position: ACCEPT
Reason: Producer, storage and actual base premises qualify analyst-facing CU evidence.
Conditions: none
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-C13
Revision: 1
Proposition SHA-256: 29bf51dbcb0ca81f41d2b70321882bd2bd68fdf37eb643eb6cd87acd28ecd969
Position: REJECT
Reason: Superseded by revision 2.
Conditions: none
Related objections: OBJ-A16, OBJ-B26

Decision: DEC-C13
Revision: 2
Proposition SHA-256: eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02
Position: ACCEPT
Reason: Measured alignment, unchanged default, additive -5r candidate ranking.
Conditions: none
Related objections: OBJ-B26

Decision: DEC-C15
Revision: 1
Proposition SHA-256: a20c0a7209411459354c45afe883de502ead216a0699c3e50aff1037b2300aa8
Position: CONDITIONAL
Reason: Harden the oracle without hiding conflicting record copies.
Conditions: Use supported strict records and nonzero checksum checks. Validate fixup occurrences before deduplication as in A03 r2.
Related objections: OBJ-A02, OBJ-A03, OBJ-A19, OBJ-A21

Decision: DEC-C16
Revision: 1
Proposition SHA-256: d2738595f1aaee71a72b7cc7421e45d62df957a5b56c4b7dfb614a88d4a46eb5
Position: REJECT
Reason: Superseded. RAM-only restoration misses CPU and host state.
Conditions: none
Related objections: OBJ-A12, OBJ-A20, OBJ-A15

Decision: DEC-C16
Revision: 2
Proposition SHA-256: 06d885d45b91ba5fe58d284a066c34392ae32be1e8938d8de5173db79afb3d95
Position: CONDITIONAL
Reason: R3 P1 confirms the three flips and two persistent differences even with CPU/allocator restoration and fresh cases.
Conditions: Record diagnostic observations first. Attribute cause and change status only after the production-equivalent witness, audit and owner review. Apply A11 and B18 r2.
Related objections: OBJ-A20, OBJ-A23

```

### Exact resolution texts for revisions absent from the index

**DEC-A02 r2.** Use one bidirectional obligation engine for FunctionMatch and RegionMatch. Bound local branch checks to the independently verified function extent and carry independently proven external context as explicit obligations. Check trim targets in both scopes. Admit only the strictly decoded raw OMF subset of the actual declared compiler output, and cut over only after the existing file gate and every live declared T3 pass. Defer unproven CONST gap exemptions.

**DEC-A03 r2.** For a new in-place Build A path, derive one input-bound partition plan with one physical provider per original loaded byte. Treat plan success as preflight. Accept integration only from actual assembly and link, materialized provider evidence, the existing comparison, and an expanded comparison of supported LE loader attributes and normalized typed fixups. Validate raw fixup records before collapsing agreeing page-straddle duplicates. Keep serialization differences diagnostic unless shown to be loader-relevant.

**DEC-A05 r2.** Prefer a verified whole-TU shared-tail group. For each cross-piece fallthrough prove physical adjacency. For each fixed relative branch prove decoded endpoints, field width, next instruction address, in-place cover, exact emitted bytes, and zero relocation over its displacement. Cover interior, entry and cut-spanning rel8 using checked piece-local expressions for supported ASM encodings. Reject edges whose proof depends on global or per-object legacy placement. Use existing valid symbolic rel32 bindings and require independent proof before adding interior exports. Require final link evidence and reject unsupported outgoing compiled-slice rel8.

**DEC-A07 r2.** Defer general extraction. Permit a narrowly justified pilot only with owner authorization for any source-gate semantics change, a region proof bound to the raw input object, independently established code and data bounds and targets, record and symbol handling validated for the admitted subset, and independent proof of the transformed artifact and actual link. Reject unsupported inputs.

**DEC-A08 r2.** Apply certified paired-state equivalence to affected current T4 witnesses. Before a new cited witness relies on a multi-function or substitution boundary, prove the allowed per-side execution and dependency edges, symmetric declared substitutions, exercised callback ABI and typed pointer identity, and production t4spec audit parity. Add boundary machinery only for demonstrated witness requirements.

**DEC-C01 r2.** Maintain four explicit verification and integration outcomes: FunctionMatch (local body diagnostic with explicit external context obligations), RegionMatch -> immutable matcher-minted VerifiedRegion (closed object/region proof), PlacementPlan (single derived preflight partition plan shared by check_t3_buildable, wc1.build, wc1.emit, batch_driver, wave4a, and m2_inventory), and IntegratedResult (actual assemble, link, and hardened wc1.compare receipt). Do not add a separate CandidateRegion runtime class or persistent proof/CU metadata DB in M2.

**DEC-C02 r2.** Reimplement E0 bidirectional Normalized Addressing Obligation verification in tools/wc1/match.py (importing nothing from experiments/) with strict raw-OMF admission (record bounds, nonzero checksums, single MODEND, persistent cross-record THREAD, preserved explicit FRAME encodings) and all 55 controls as production tests, audited over every live declared T3 at cutover. Evaluate FunctionMatch intra-function branch closure against [orig_fn.start, orig_fn.start + fn_len) while attaching explicit sibling-context obligations (never minting placement permission); preserve trimmed_branch_target across all modes; fail closed on CONST pad mismatches (no Stage-0 V4 dependency).

**DEC-C04 r2.** Implement a measured compiler-facing Windows-path length guard and short-path staging policy in tools/wc1/oldcc.py checking all compiler-facing arguments (source, -fo, -i=, TMPDIR, translated Z: paths), failing fast with [TOOLCHAIN ERROR] before Watcom 10.0a path-buffer crashes while verifying unchanged compile/include semantics across checkout depths. (The three t3_audit.py R3 defects from rev 1 are delivered and closed as of EV-3 main@17733f9.)

**DEC-C05 r2.** Implement Fix B1 (leading-byte region base first_entry_addr - first_entry_off gated on E0 RegionMatch of [0,k), zero overlap/foreign entry, branch analysis using physical table_start) and Unified Fix B2 inside the single derived PlacementPlan: keep extern symbolic rel32 for exported entries; emit remaining cross-object ASM relative branches (B2-interior, B2-entry, B2-span, and rel32-interior such as 0x2f6df with zero M2 OMF PUBDEF synthesis) via NASM piece-local label expressions (preferred, using decoded next_ip = ia + insn.size and typed encodings with assembled-byte verification) or verified literal displacement fallback, strictly rejecting any span containing a global --legacy or automatic per-object Unplaceable legacy-placed object (DEC-B19), explicitly checking cross-piece fallthrough adjacency, recording Build A placement debt, and requiring IntegratedResult with hardened wc1.compare (DEC-B20/DEC-C15). Qualify IntroOpSyncSound standalone regression tests by mode: rejected under legacy or B2-disabled, accepted only with explicit B2-span debt under in-place B2, zero debt as Group B.

**DEC-C06 r2.** Admit proof-gated multi-function ReconstructedTUs when the whole compiled object passes RegionMatch and Build A IntegratedResult, preferring whole-TU co-compilation over B2 placement debt for shared-epilogue clusters. Pilot E1 Group B (IntroOpPlaySound 0x2315c, IntroOpSyncSound 0x23170, IntroOpWaitSound 0x231cc) as an independent -5r TU without waiting on generic B2, subject to owner confirmation of AGENTS.md ground-rule wording, dual-compiler checks, full make verify, and owner review of any xfailed PLAYFLIC test adjustment.

**DEC-C07 r2.** Prioritize genuine M2 completion (98 remaining not-DONE on EV-3 main@17733f9) via parallel tracks: (a) Stage 0/1 verification hardening, single planner, B1/B2, Group B pilot, and T4 paired-state symmetry (DEC-A11/DEC-B18/DEC-C16, immediately addressing 3 of 5 xfailed PLAYFLIC tests while 0x23530 and 0x2fcfc remain genuine ref-C bugfixes); (b) routine area reconstruction (BULLET.C and the 61+7 name/C backlog, supported by lightweight deterministic rename/Wave 3R enablers, reporting reconstruction yield as an upper bound rather than a deterministic guarantee); and (c) owner evidence packets for the 8 scope/discovery items. Defer Fix B3, selective extraction (E3/E4), demand-led E6 Group machinery, and CU hypothesis databases to the post-M2/M3 track; decouple M3 Build B from optional Build A consolidation paths.

**DEC-C08 r2.** REJECT adopting experiments/build_codegen/e4/omf_extract.py@e6150b8 or selective OMF extraction during M2 or as a default consolidation path. Whole-TU RegionMatch is the primary integration path. Any future narrow post-M2 extraction pilot requires: (1) explicit owner decision on Gate-2 / match --all semantics for src files with mismatching publics (DEC-B09); (2) proven canonical-TU benefit; (3) implementation over the shared strict OMF32 subset (DEC-C09) fixing confirmed Probe 5a (cross-record THREAD), Probe 5b/GPT Q4 (non-_TEXT PUBDEF corruption when lo>0), Probe 5c (typed table/code model), and rev-e4-01 F1-F4; and (4) post-transform verification and Build A IntegratedResult (without mandating unproved 64-fixup chunking or exhaustive Wave 4B).

**DEC-C09 r2.** Before landing Fix B3 or any future selective OMF extraction pilot (post-M2), share one tested strict OMF32 record/fixup codec (record bounds, nonzero checksums, preserved explicit FRAME encodings, persistent cross-record THREAD, format/linker-verified record-length bounds) across verification and admitted OMF transforms, while leaving permissive library-signature readers untouched and avoiding unnecessary omfpatch refactoring during M2.

**DEC-C10 r2.** Keep semantic_owner separate from physical_provider and defer Fix B3 to the post-M2/M3 track (triggered by justified need such as Q-B08). Admit B3 initially for strictly verified whole segments over the shared strict OMF32 subset (DEC-C09) with RFC §8.2 constraints 1-5 and rev-e5-02 mutability/aliasing guards. Any future CONST inter-literal alignment-gap rule (per DEC-B21) must additionally: apply identically in matcher and build.place(), force Build A physical_provider = ASM, be explicitly disclosed in the proof receipt, and require independent extent/access evidence ruling out computed or overlapping reads (OBJ-A11).

**DEC-C11 r2.** Keep full paired initial-state symmetry (DEC-A11/DEC-B18/DEC-C16) mandatory immediately for ALL T4 tests (single- and multi-function), independent of E6. Adopt E6 multi-function machinery (contiguous VerificationBoundary, symbol_aware_reloc primary + c_entry_hook defense in depth, generator callbacks with pre-restore ABI checks on PRESERVED_REGS ebx/ecx/edx/esi/edi/ebp plus esp, R2 typed pointer identity, and full t4spec production audit parity per DEC-A08) on demand whenever any M2 or post-M2 witness requires substituting an intra-TU sibling, executing real callbacks, or comparing logical pointer identities; treat switch-table relaxation and LogicalConstDataPtr (EXP-4) as optional extensions when needed.

**DEC-C12 r2.** Explicitly REJECT _DATA/_BSS staircase splits, call_locality_drop, none16 auto-splits, weighted CU boundary scoring, empty-S(f) auto-splitting, and any automatic mutation of analysis/modules.toml or automatic source consolidation. Maintain original CU recovery strictly as an analyst-facing premise-carrying constraint graph (storage deferred to M3): shared_epilogue as a one-directional merge constraint under verified compiler/linker provenance; non_16_aligned_start evaluated at the actual segment base under a PARA-segment premise (with measured corpus precision 0.800/0.836/0.618, never 100%); shared_const_string_literal as conditional premise-dependent evidence requiring exclusion of explicit shared externs and linker pooling; filenames, zero16, none16, style_transition, and S(f)-disjointness as candidate generators preserving competing hypotheses.

**DEC-C13 r2.** Replace RFC §2.2.5 alignment premises with E2 empirically measured compiler behavior: Watcom 10.0a function spacing is 16 bytes under -4r -ot, 4 bytes under -3r/-5r -ot (with PARA 16-byte _TEXT SEGDEF for tested -ot), and 1 byte under -os/-od; OW2 uses 16 bytes under -4r and -5r. Keep -4r as the single-file project default with additive E7 presets (DEC-B11), rank -5r as the first-tried candidate family for multi-function -ot TUs requiring 4-byte spacing without claiming it was the universal 1994 project flag, and keep EXP-2/Q-B06 (5r -d1+ -zp1 and 5r -od) as optional additive probes.

**DEC-C16 r2.** Reclassify the 5 xfailed T4 functions in wc1.m2_inventory per identical independent results of R1-Probe 2 and Claude R1-P4 as 3 T4 harness state-asymmetry artifacts (IntroOpWaitSound 0x231cc, IntroRunScript 0x23668, IntroPlay 0x23ae0) and 2 confirmed genuine reference-C divergences (IntroOpStartCredits 0x23530, EndScreen 0x2fcfc). Adopt full paired initial-state equivalence in tools/wc1/cemu.py::run_pair (combining DEC-A11 and DEC-B18, subject to Q-B05 full T4 suite verification and owner approval for test-meaning/xfail changes): initialize or restore identical per-side CPU/flags (including EFLAGS/CF), all mapped writable memory, and declared/stateless host-stub state; keep restoration strictly separate from watch output assertions; and record restored regions and unwatched global writes in WC1_T4_AUDIT_LOG.