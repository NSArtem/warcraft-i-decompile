# Implementation roadmap (EDITOR DRAFT)

## How the roadmap is ordered

The order follows the ledger's dependencies and the actual M2 state at EV-3 (`main@17733f9`):

- 912/1010 DONE; 98 not DONE; 539 T3.
- Gate 1 FAIL (98), gate 2 PASS, gate 3 undefined.

The ordering rules come from the ledger:

- **DEC-A01 r1.** Order work by DONE obligations under the existing scope, tiers and gates. Count T4→T3 conversions separately.
- **DEC-A15 r1.** Admit M2 infrastructure only for a demonstrated verification or toolchain defect, or for a documented blocker to a named in-scope function that is not DONE. Run reconstruction, owner packets and hardening as independent tracks.
- **DEC-C07 r3.** The tracks are (a) hardening and named blockers, (b) routine reconstruction, (c) owner evidence packets. B3, extraction and CU databases are post-M2; E6 is earlier only for a named witness; Build B is decoupled from Build A consolidation.

No stage below changes `make verify`, `make goal`, the tier definitions or `wc1.progress` classification. A stage that would change the meaning of an existing test needs owner approval (DEC-A13, DEC-C06, DEC-A16).

**Admission gate for every stage.** Every newly adopted production mechanism lands only with the existing `make verify` green at its admission commit (gate 2, `docs/GOAL.md@17733f9` §4; DEC-B15 r1). That includes the stages with no prior-stage dependency: S0.1, S0.5 and S1.3. The stage-specific exit criteria below are additional to that gate, never a substitute for it.

**Execution status:** no stage has been started or executed. Every "exit criterion" below is an agreed future acceptance test (ii), not a result (iii). The exit criteria come from the decision texts, the r04 acceptance-criteria tables of all three Architects (`12-r04-gpt-response.md` §6, `13-r04-claude-response.md` §8, `14-r04-gemini-response.md` §7), and the baseline RFC §16 minimum admission criteria incorporated by RFC §8.

## Dependency graph (editorial)

```text
Track (b) routine reconstruction ───────────────────────────────────────────► M2 gate 1
Track (c) owner packets (8 items, O-1..O-4) ────────────────────────────────► owner decisions
Track (a):
  S0.1 path guard (A12/C04) ─┐
  S0.4 raw-artifact receipt binding (A14) — at issuance of every authority-bearing receipt and on reuse;
       lands with S0.2/S0.3 (before their first receipt); S1.3 meets it locally
  S0.2 verifier cutover (A02/C02/B15) ─┬─► S1.1 B1 (A04/B05/C05) ─┐
  S0.3 integration receipt + LE comparator (A03/C01/B14) ─┘        ├─► S1.2 B2 (A05/B19/C05)
  S0.5 paired T4 state (A11/A16/C16), run_pair and the 12 bypass nodes ── independent ─► Q-B05 suite ─► owner (O-2)
  S1.3 Group B whole TU (A13/C06/B06) — may run before S0.2/S1.x with its own strict proof
Post-M2 / M3: S2.1 strict codec (C09) ─► S2.2 B3 (A06/B08/C10); S2.3 extraction pilot (A07/C08, DQ-15)
On demand:    S2.4 E6 machinery (A08/C11) for a named witness
M3:           S3 CU evidence/storage (A10/C12/B14, DQ-06), Build B (DQ-14), T5 (DQ-13)
```

## Track (b): routine reconstruction (parallel, not gated by infrastructure)

- **Scope:** BULLET.C and the "61+7" name/C backlog (DEC-C07 r3). This is the bulk of the 98 not-DONE functions.
- **Entry:** now, under the current gates.
- **Exit:** each function DONE under the existing tier rules. Progress is reported as newly DONE, separately from T4→T3 conversions (DEC-A01). Yield projections are upper bounds, not guarantees (DEC-C07).
- **Admitted helpers:** "lightweight deterministic rename/Wave 3R enablers when demonstrably needed" (DEC-C07 r3), and "a scoped rename or routing helper when reconstruction is otherwise ready" (DEC-A15 r1).
- **Regression risk:** as for current work. `make verify` must be green per commit.
- **Reversibility:** per-commit.

## Track (c): owner evidence packets

- **Scope:** the 8 scope/discovery items (DEC-C07 r3), plus the owner checkpoints O-1 to O-4 (`deferred-questions.md`).
- **Exit:** an owner decision. No agent changes scope, gates or AGENTS.md rules (DEC-A01).

## Track (a): verification soundness and named M2 blockers

### S0.1 — Compiler-facing path guard (DEC-A12 r1, DEC-C04 r2)

- **Need:** a demonstrated toolchain defect. A Watcom 10.0a path-buffer failure was observed on EV-3 (`12-r04-gpt-response.md` §6).
- **Entry:** now.
- **Exit:**
  - The effective-path envelope is measured under the same warmed prefix, varying source, `-fo`, `-i=`, TMPDIR, the working directory and Z: translation.
  - Calls outside the envelope are rejected before launch as `[TOOLCHAIN ERROR]`.
  - Staging preserves source identity, include resolution, flags and output attribution.
  - Outputs are isolated per compile.
- **Verification prerequisite:** none.
- **Regression risk:** low. False rejections surface as toolchain errors, not silent mismatches.
- **Reversibility:** high; the change is confined to `tools/wc1/oldcc.py`.

### S0.2 — Verifier cutover (DEC-A02 r2, DEC-C02 r2, DEC-B15 r1)

- **Need:** a demonstrated verification defect (E0: three legacy gaps).
- **Entry:** now.
- **Exit:**
  - Production `tools/wc1/match.py` implements the bidirectional obligation engine, with no imports from experiments/.
  - All 55 E0 controls are production tests.
  - Strict raw-OMF negatives are covered: bounds, nonzero checksum, single MODEND, record allow-list, persistent THREAD, explicit FRAME.
  - Function-extent closure with explicit external obligations; trimmed-branch-target checks in both scopes.
  - The matcher fails closed on CONST pad mismatch.
  - **Cutover:** the existing file gate and every live declared T3 pass. The audit runs over the live set at the cutover commit, not the 519 of the experiments baseline.
  - Every authority-bearing verification receipt minted at or after cutover binds the exact raw artifacts and the verified context (S0.4; DEC-A14 r1).
- **Verification prerequisite:** `make verify` green before and after.
- **Regression risk:** **high.** A stricter matcher may reject current T3s. The baseline rule stands: no automatic downgrade, and no keeping a known-bad proof. Any reclassification follows `docs/GOAL.md` with the owner.
- **Reversibility:** medium. Cutover is one commit, but a revealed defect cannot be "un-revealed".

### S0.3 — Single plan, integration receipt, hardened LE comparator (DEC-A03 r2, DEC-C01 r3, DEC-B14 r1)

- **Need:** a demonstrated verification defect. The old comparator accepted three mutants (A R2 P2).
- **Entry:** now. It can be built alongside S0.2.
- **Exit:**
  - `check_t3_buildable`, `wc1.build`, `wc1.emit`, batch_driver, wave4a and m2_inventory consume one derived PlacementPlan (DEC-C01).
  - Promotion credit comes only from an IntegratedResult: actual assembly and link, materialized provider evidence, the existing comparison, and the expanded typed LE comparison.
  - Raw fixup occurrences are validated before agreeing page-straddle copies are deduplicated.
  - The three mutants (cleared OBJ_EXEC, changed src_type, contradictory duplicate) fail, and the live Build A passes.
  - Raw grouping, page offsets, serialization order and last-page size are reported as diagnostics (DQ-11).
  - Unsupported encodings are rejected structurally.
  - The entity set is per DEC-B14: no CandidateRegion type and no persistent store.
  - Every IntegratedResult binds, when minted, the exact raw artifacts it consumed (objects, linked image, original) and its verified context (S0.4; DEC-A14 r1).
- **Verification prerequisite:** the S0.2 verifier, for the VerifiedRegion input.
- **Regression risk:** medium. A stricter comparator may flag the current Build A. Genuine loader-semantic differences go to the owner (O-4).
- **Reversibility:** medium.

### S0.4 — Raw-artifact binding of authority-bearing receipts (DEC-A14 r1)

- **Need:** a demonstrated verification risk. CONST pad variance would let a receipt or a normalized key stand for different raw bytes.
- **Scope:** DEC-A14 binds *each* authority-bearing verification or integration receipt to the exact raw artifacts and the verified context used in its claim. The obligation therefore applies when a receipt is **minted**, not only when a verdict is reused.
- **Entry:** before each path issues its first authority-bearing receipt, including S0.2 and S0.3. The same binding applies if a later component reuses a verdict.
- **Exit:**
  - Issuance: every authority-bearing receipt records the exact raw-artifact identities and verified context it relies on. A receipt without that binding is not accepted as authority.
  - Reuse: two raw artifacts share a normalized digest, or only the verified context changes, and both cases force a fresh verdict.
- **Group B (S1.3):** the exact Group B proof meets this requirement locally. Its commit-bound strict proof and integration receipt bind the exact raw artifacts used for their claims, including the raw object, the original and linked images where compared, and the verified context. It needs no cache and does not wait for the generic S0.2–S0.4 rollout (DEC-A13 r1).
- **Regression risk:** low; the only cost is cache misses.
- **Reversibility:** high.

### S0.5 — Complete paired T4 starting state (DEC-A11 r1, DEC-A16 r1, DEC-C16 r3)

- **Need:** a demonstrated verification defect (A1 Q1). The 5 xfails are the witnesses.
- **Entry:** now. It is independent of S0.2–S0.4 and of E6 (DEC-C11).
- **Coverage:** all current T4 routes. That means `cemu.run_pair`, **and** the 12 legacy hand-written T4 nodes that bypass it (`docs/ANALYST_GUIDE.md@17733f9` §Runtime T4 audit trust boundary; list in `docs/HISTORY.md`). Each bypass node is either migrated to the audited pair mechanism or checked by an equivalent audited path. Its output assertions are preserved, and changes go to the owner (O-2).
- **Exit:**
  - Every T4 case runs from independent initialization or a certified checkpoint. The checkpoint covers:
    - CPU context, including EFLAGS, segment registers and ESP;
    - mapped regions with their permissions and contents;
    - host and guest writes;
    - allocator state;
    - declared mutable host dependencies;
    - declared mutable stub state.
  - Unsupported state is reported as UNSUPPORTED.
  - Restoration is kept separate from the compared effects, and the existing output assertions are preserved.
  - The method and the restored state are recorded in a nonce-bound `WC1_T4_AUDIT_LOG`.
  - Carry, host-write, allocator and mutable-stub negatives are covered.
  - The full existing T4 suite, including the 12 bypass nodes, runs once with the rule enabled (Q-B05). Any change in test meaning or expected status goes to the owner (O-2).
  - The five EV-3 witness outcomes are recorded as observations. Attribution comes separately (DQ-12).
- **Verification prerequisite:** none.
- **Regression risk:** **medium–high.** Existing passes may flip. That is precisely why the owner presentation is required.
- **Reversibility:** high in code. Status changes are owner decisions.

### S1.1 — B1, leading jump tables (DEC-A04 r1, DEC-B05 r1, DEC-C05 r4)

- **Need:** a named blocker, ChooseCampaignDialog `0x157e8`.
- **Entry:** S0.2, for RegionMatch over `[0,k)` and its relocations, and S0.3, for the single plan.
- **Exit:**
  - The contribution base is derived as `first_entry_addr - k` from a verified binding.
  - Leading fixups into the object's own range are internal.
  - Overlap with other cuts and foreign entries are rejected.
  - Corrupted-table, wrong-base, out-of-extent and overlap negatives are covered.
  - Actual Build A IntegratedResult.
- **Regression risk:** low–medium; it is confined to objects with k>0.
- **Reversibility:** high.

### S1.2 — B2, cross-object transfers and fallthrough (DEC-A05 r2, DEC-B19 r2, DEC-C05 r4)

- **Need:** named blockers, IntroOpSyncSound standalone and MissionDefeat entry/fallthrough.
- **Entry:** S0.2 and S0.3. It is combined with S1.1 for prefix cases.
- **Exit:**
  - Each fixed edge has decoded endpoints, field width, the next instruction address, in-place cover, the exact emitted bytes and zero relocation over the displacement.
  - Checked piece-local expressions are used, with a verified literal fallback under the same proof.
  - Every live cross-piece fallthrough has adjacency to the original in-place successor.
  - Spans over global or per-object legacy placement are rejected.
  - No M2 PUBDEF synthesis (DQ-09).
  - Placement debt is recorded.
  - Mode-qualified IntroOpSyncSound tests: rejected under legacy or B2-disabled; accepted with explicit B2-span debt in place; zero debt as Group B.
  - A prefixed rel8, the B1 combination, and an actual IntegratedResult.
- **Regression risk:** medium. A placement bug would show up only at link time, which is why the IntegratedResult is required.
- **Reversibility:** high.

### S1.3 — Group B whole TU (DEC-A13 r1, DEC-C06 r2, DEC-B06 r1)

- **Need:** named functions `0x2315c/0x23170/0x231cc` (E1; B R0 P3).
- **Entry:** now, **independently of S0.2/S1.x** (DEC-A13), if the exact object has a commit-bound strict raw-object RegionMatch equivalent to the intended production rules. It also requires owner confirmation of the AGENTS.md wording (O-1).
- **Receipt binding:** the Group B proof binds its raw artifacts and verified context locally (see S0.4). No cache is required.
- **Exit:**
  - One `-5r` TU.
  - Ordinary file gate and dual-compiler compile checks.
  - Actual in-place Build A with typed loader comparison.
  - Full `make verify`.
  - The cited PLAYFLIC T4 checks are preserved, or the owner approves changes (O-2).
- **Regression risk:** low; one file.
- **Reversibility:** high; a single revert.
- **Relation:** this case removes the need for IntroOpSyncSound's B2-span debt, but S1.2 is still required for MissionDefeat.

## Post-M2 / M3 and on-demand work (not on the M2 critical path)

| Stage | Decisions | Entry condition | Exit / acceptance (agreed, not executed) | Deferred item |
|---|---|---|---|---|
| S2.1 Shared strict OMF32 codec | DEC-C09 r3 | Before landing B3 or any extraction pilot | Record bounds, nonzero checksums, explicit FRAME, persistent THREAD, linker-verified record-length bounds; shared by verification and admitted transforms; permissive readers untouched; no unnecessary omfpatch refactor in M2 | — |
| S2.2 Fix B3 | DEC-A06 r1, DEC-B08 r1, DEC-C10 r3 | Post-M2, or earlier for a named not-DONE function; S2.1 | Exact whole segments; RFC §8.2 constraints 1–5; rev-e5-02 mutability and aliasing guards; DEC-A14 on receipts; transform and link proof | DQ-01, DQ-03 |
| S2.3 Extraction pilot | DEC-A07 r2, DEC-C08 r2 | Post-M2; owner decision DQ-15; proven benefit; S2.1 | Fixed THREAD, PUBDEF, typed-table and F1–F4 defects; raw-bound region proof; independent transform and link proof; IntegratedResult | DQ-02 |
| S2.4 E6 machinery | DEC-A08 r2, DEC-C11 r2 | A named witness requires it, in M2 or later | Only the needed feature; per-side edges, symmetric substitution, callback ABI before restoration, typed pointer identity, audit parity, negatives | DQ-05, DQ-17 |
| S3 CU evidence, storage, Build B, T5 | DEC-A10 r1, DEC-C12 r2, DEC-B14 r1, DEC-A15 r1 | M3 start | Analyst-facing constraint graph; no automatic consolidation; storage only with a consumer; Build B independent of Build A consolidation | DQ-06, DQ-07, DQ-13, DQ-14, DQ-16 |

## Documentation actions

These are small and have no gate impact:

- `docs/subsystems/compiler.md` and the RFC alignment statement (DEC-B10 r1, DEC-C13 r3).
- Preset policy: additive, `-4r` default (DEC-B11 r1, DEC-A09 r1).
- The AGENTS.md ground-rule text only after O-1.

## What the roadmap does not claim

- It does not forecast how many of the 98 not-DONE functions each stage converts. The consilium treated reconstruction yield as an upper bound (DEC-C07 r3).
- It does not schedule any stage by experiment success alone.
- It does not grant DONE credit for any probe or prototype result.
