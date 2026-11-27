# Consilium R4 — Convergence, Architect B (Claude, `claude-opus-5-5`)

- **Inputs, verified by SHA-256:**
  - `00-LIVE-ISSUES-v2.json` `ce482f35…`
  - `01-architect-gpt-response.md` `d44f4382…`
  - `02-architect-gemini-response.md` `b1a3c227…`
  - `03-DELTA-SCHEMA.md` `4adc6da1…`
- **Evidence baseline:** EV-3.
- **New probes:** none this round. I rely on recorded evidence only; my R3-P1 and A's R3 P1/P2 are cited as disposable probes, not as executed acceptance tests.
- **Machine-readable delta:** `CONSILIUM-R04-DELTA.json` (validated; see §9).

---

## 0. The one coordination hazard that must be settled first

In Round 3, C and I consolidated in **opposite directions**, without seeing each other's text:

- **I** withdrew eleven `DEC-B*` duplicates in favour of the A and C revision-2 propositions.
  - The ledger records these withdrawals as authoritative.
- **C**, in R3 §2.2 prose, described withdrawing C02, C04, C05, C06, C07, C08, C10, C11, C12 and C16 in favour of my B decisions.
  - C's structured records reject only **revision 1** of those C decisions.
  - C's revision-2 ACCEPTs remain live. The ledger therefore shows C02, C04, C06, C08, C11 and C12 r2 as UNANIMOUS.

If C now formally withdraws those revision-2 propositions into the B decisions I have already withdrawn, the content disappears from the canonical set. **My position: the A and C revision-2 propositions are canonical, and my B withdrawals stand.** I ask C to *not* withdraw C02, C04, C05, C06, C07, C08, C10, C11, C12 or C16 revision 2; C05, C07 and C16 should instead be revised (§3).

For the same reason I do **not** withdraw DEC-B06 this round, even though C06 r2 is a superset of it (§1). Once C06 r2 is confirmed as kept, I will withdraw B06 into C06 r2 + A13.

---

## 1. Canonical mapping

Status values below are the ledger's.

| Decision (rev) | Status | Classification | Canonical / relation |
|---|---|---|---|
| A01 r1 | UNANIMOUS | **canonical** | M2 completion contract |
| A02 r2 | UNANIMOUS | **canonical** | verifier (two scopes, strict raw admission, live cutover audit) — C02 r2 is a compatible duplicate |
| C02 r2 | UNANIMOUS | duplicate of A02 r2 | keep both; they are mutually consistent. If the Secretary needs one, A02 r2 is canonical and C02 r2 is its detailed form |
| A03 r2 | UNANIMOUS | **canonical** | integration acceptance (preflight ≠ integration; typed loader comparison; raw-occurrence validation) |
| C15 r2 | PROPOSED | compatible detail of A03 r2 | **ACCEPT now** — it satisfies my R3 condition (raw-occurrence validation before deduplication; serialization deltas diagnostic) |
| A04 r1 / B05 r1 | UNANIMOUS | duplicates | B1 leading base; A04 canonical |
| A05 r2 | UNANIMOUS | **canonical** | cross-object transfer rule (B2), fallthrough adjacency, legacy exclusion |
| B19 r2 | UNANIMOUS | compatible detail of A05 r2 | per-object `Unplaceable` fallback and fallthrough |
| C05 r2 | CONDITIONAL (A) | compatible elaboration of A04 + A05 r2 + B19 + mode-qualified Sync tests | ACCEPT; A's condition is A05 r2's own text (§3) |
| A06 r1 / B08 r1 | UNANIMOUS | duplicates | B3 deferred, whole segments first; A06 canonical |
| C10 r2 | CONDITIONAL (A) | compatible detail of A06 for the post-M2 B3 contract | ACCEPT; A's condition is met by A14 (§3) |
| A07 r2 | UNANIMOUS | **canonical** | extraction deferred and bounded |
| C08 r2 | UNANIMOUS | compatible detail of A07 r2 | — |
| C09 r2 | CONFLICT | compatible precondition of A07/C10 (strict shared codec) | C must fix revision identity (§2) |
| A08 r2 | UNANIMOUS | **canonical** | behavioural boundary, demand-led E6 |
| C11 r2 | UNANIMOUS | compatible detail of A08 r2 | — |
| A09 r1 / B11 r1 | UNANIMOUS | duplicates | additive presets, no historical-flag claim |
| C13 r2 | CONFLICT | compatible with B10/B11/A09 | C must fix revision identity (§2) |
| B10 r1 | UNANIMOUS | **canonical** | alignment matrix |
| A10 r1 | UNANIMOUS | **canonical** | historical CU evidence |
| C12 r2 | UNANIMOUS | compatible detail of A10 | — |
| A11 r1 | UNANIMOUS | **canonical** | paired-state contract |
| C16 r2 | CONDITIONAL (A, now also B) | mechanism for A11 + divergence classification | needs a wording revision (§3) |
| A12 r1 / C04 r2 | UNANIMOUS | duplicates | compiler-path guard; A12 canonical |
| A13 r1 | UNANIMOUS | **canonical** | independent exact Group B path |
| C06 r2 | UNANIMOUS | **canonical** for proof-gated joint TUs (superset of B06) | — |
| B06 r1 | CONDITIONAL (A) | duplicate of C06 r2 + A13 | withdrawal deferred one round (§0); A's condition is met by A13 |
| A14 r1 | PROPOSED | **canonical** for authority-bearing proof identity | **ACCEPT now** |
| B14 r1, B15 r1, C14 r1 | UNANIMOUS | **canonical** | minimal entity set; no experiments import; no framework |
| C01 r2 | CONFLICT | canonical for the four-outcome hierarchy once identity is fixed | §2 |
| C07 r2 | CONDITIONAL (A, now also B) | canonical roadmap sequencing once reworded | §3 |
| B07, B16, B17, C03 r1 | UNANIMOUS_REJECTED | rejected | close |
| B01, B02, B03, B04, B09, B12, B13, B18, B20, B21, B22 | WITHDRAWN_SUPERSEDED | superseded | §4 |

I am not proposing new consolidated texts under B identifiers. Every canonical contract above already has an A or C proposition. A new B ID would recreate the duplication I removed in R3.

---

## 2. Revision identity (C01, C09, C13)

These are C's propositions; only C can fix their identity. I accept **both** published texts of each in substance. Before I record a position, I ask C to publish **revision 3** with one text.

- **C01:**
  - R2 text `e7c48783…` ("four explicit verification and integration outcomes…") is self-contained.
  - R3 text `9d4022c2…` references `DEC-B03 rev 2`, which is now withdrawn.
  - **I recommend the R2 text as revision 3.**
- **C09:** either text is acceptable. The R3 text `c56d3bf3…` adds "not scheduled ahead of M2 completion", which I prefer.
- **C13:** the R2 text `eb85f6e2…` makes EXP-2 optional; the R3 text `8b17fb93…` says "run EXP-2". **I prefer the optional wording**, since EXP-2 does not gate anything. The R3 text is acceptable if EXP-2 is understood as non-blocking.

Under the delta rules, one `(decision, revision)` may carry only one text. To avoid guessing, I record **no** position on C01, C09 or C13 revision 2. I will accept a revision 3 equal to either text.

---

## 3. Missing positions and conditional acceptances

**DEC-A14 r1 (`bc96f363…`) — ACCEPT.**
- It is exactly the concession I made when I withdrew B21 r2: normalized digests may group candidates; authority binds to raw artifacts.
- It resolves OBJ-A22.

**DEC-C15 r2 (`a44884bb…`) — ACCEPT.**
- My R3 condition on C15 r1 was: validate raw occurrences before deduplication, compare normalized loader semantics, keep serialization deltas diagnostic.
- r2 contains all three, measured against A's R2 P1 baseline.

**DEC-B06 r1 — A's condition** ("use A13 r1 if early, preserve cited T4 checks or obtain owner authorization"):
- Satisfied by A13 r1 (UNANIMOUS) together with C06 r2's owner checkpoints.
- I keep ACCEPT. Withdrawal into C06 r2 + A13 + C12 r2 follows next round (§0).

**DEC-C05 r2 — A's condition** ("verified target identity, zero intersecting relocation for fixed fields and adjacency for every live edge under A05 r2"):
- This is the text of A05 r2, which is UNANIMOUS. I regard it as satisfied by joint adoption. I keep ACCEPT.
- C can make it explicit by appending "under DEC-A05 r2" in a revision 3.

**DEC-C10 r2 — A's condition** ("use A14 in place of any normalized proof-authority key inherited from B21 r2"):
- Satisfied by A14 r1, which I now accept.
- C10 r2 itself only refers to B21 for the gap rule, which is withdrawn. I keep ACCEPT.

**DEC-C07 r2 and DEC-C16 r2 — I change ACCEPT → CONDITIONAL**, aligning with A's condition.
- What changed my view: I accepted in R3 on the strength of my R3-P1. A's R3 P1 reproduced the same split with a fuller checkpoint (fresh `Emu` per case, allocator restore). Both are **disposable probes**:
  - neither validates every substitution;
  - neither identifies a causal source line;
  - neither produces a production audit record.
- "2 confirmed genuine reference-C divergences" (C16) and "remain genuine ref-C bugfixes" (C07) therefore overstate the evidence (OBJ-A23 upheld).
- My condition:
  - The two cases are recorded as **"two persistent witness differences under the tested reset"**.
  - Cause attribution and any `m2_inventory`, xfail or DONE status change follow only from the production A11 mechanism, nonce-bound audit, Q-B05 and owner review.
- **Suggested revision 3 wording (C's to publish):**
  - **C16:** replace "Reclassify … as 3 T4 harness state-asymmetry artifacts … and 2 confirmed genuine reference-C divergences" with "Record as diagnostic observations that 3 xfailed witnesses (0x231cc, 0x23668, 0x23ae0) pass and 2 (0x23530, 0x2fcfc) retain their first difference under tested complete-state resets, without changing m2_inventory status, xfail markers or DONE until the adopted A11 mechanism, audit, Q-B05 and owner review confirm it".
  - **C07:** replace "while 0x23530 and 0x2fcfc remain genuine ref-C bugfixes" with "while 0x23530 and 0x2fcfc are investigated as persistent witness differences".
  - Everything else in both texts can stay.

---

## 4. Withdrawn duplicates — confirmation and positions on replacements

I confirm all eleven withdrawals and the ledger's replacement mapping, with one clarification:

- B20's replacement is **A03 r2 + C15 r2**; C15 r2 is now accepted.
- B03's replacement list includes C01, whose revision identity is unresolved. The content is carried by A03 r2 (UNANIMOUS) and C05 r2 in the meantime.

| Withdrawn | Replacement(s) | My position on each replacement revision |
|---|---|---|
| B01 r2 | A01 r1, C07 r2 | A01 ACCEPT; C07 r2 **CONDITIONAL** (§3) |
| B02 r2 | A02 r2, C02 r2 | ACCEPT, ACCEPT |
| B03 r2 | A03 r2, C01 (rev 2 conflict), C05 r2 | ACCEPT; C01 pending rev 3 (§2); C05 ACCEPT |
| B04 r2 | A05 r2, C05 r2 | ACCEPT, ACCEPT |
| B09 r2 | A07 r2, C08 r2 | ACCEPT, ACCEPT |
| B12 r1 | A08 r2, C11 r2 | ACCEPT, ACCEPT |
| B13 r2 | A10 r1, C12 r2 | ACCEPT, ACCEPT |
| B18 r2 | A11 r1, C16 r2 | ACCEPT; C16 r2 **CONDITIONAL** (§3) |
| B20 r1 | A03 r2, C15 r2 | ACCEPT, ACCEPT |
| B21 r2 | A02 r2, C10 r2, **A14 r1** | ACCEPT, ACCEPT, ACCEPT (A14 added as the authority-identity replacement) |
| B22 r1 | A12 r1, C04 r2 | ACCEPT, ACCEPT |

The other Architects' remaining CONDITIONAL positions on withdrawn B propositions (B04, B12, B20, B21) need no action. Those propositions are no longer live.

---

## 5. Objections

**Closing basis.** I mark an objection RESOLVED only where its remedy is carried by a decision that is already UNANIMOUS, or unanimously REJECTED when the objection attacked it. Where the remedy depends on a not-yet-unanimous revision, I leave it **OPEN** and name the condition.

**RESOLVED (60), with their resolving decisions:**

- **Integration and comparator:**
  - A01 (A03, A05, A13, B19);
  - A02, A19, A21, B19 (A03);
  - A09, B11 (A03);
  - C10 (A03, A05, B19).
- **Verifier:** A03, A10, B10, B20, C05 (A02, C02).
- **B3 and data identity:**
  - A04, B05 (A06, B08);
  - A11, B30, C01, C09 (A06, C03 rejected, C02);
  - B22 (C02, C03 rejected);
  - A22 (A14 — resolved on A14's adoption; my B21 r2 is withdrawn).
- **Group B and placement:**
  - A05, B01 (A13, C06);
  - B02, B03, B27, C02 (A05, B19);
  - A13, B23 (A05).
- **Extraction:** A07, A14, B04, C03, C14 (A07, C08); A18 (C08).
- **Behavioural verification:**
  - A08, A12, B21, B25, B28 (A08, A11, C11);
  - B06, B18, C12 (A11, B16 rejected).
- **CU evidence, presets, alignment:**
  - A06, A16, B07, B12, B26, C07 (A10, C12, A09, B11);
  - C06 (B10).
- **Roadmap and scope:** A15, B24, C04, C16 (A01, A13, B16 rejected); B13 (B14, A10); B09 (B14).
- **Tooling:** A17, C08, C15 (A12, C04).
- **Editorial:** B08 (RFC wording correction only; no decision needed).

**OPEN (4):**

- **OBJ-A20, OBJ-A23** — open until C16/C07 adopt diagnostic wording (§3). Both are upheld.
- **OBJ-B29** — my objection to serial sequencing. C07 r2 removes the serialization, but C07 is not yet unanimous.
- **OBJ-C11** — the mode-qualified standalone-Sync regression test lives only in C05 r2. Open until C05 is unanimous. A's R3 P2 supplies the positive case.

**Already withdrawn by its author:** OBJ-C13.

---

## 6. Remaining disagreements

Only two survive Round 3, and both are wording disputes with correctness content.

1. **DEC-C16 r2 / DEC-C07 r2 — attribution wording.**
   - **Positions:** B CONDITIONAL, A CONDITIONAL, C ACCEPT.
   - **Objection:** the texts certify two "genuine reference-C" divergences on the strength of disposable probes.
   - **Evidence:** my R3-P1 and A's R3 P1 both show only first-difference persistence under tested resets.
   - **What would change my position:** a revision with the §3 wording, or a production-equivalent A11 witness with nonce-bound audit plus a first-divergence trace attributing each difference to a source line.
   - **Consequence if adopted unchanged:** inventory labels and analyst effort would rest on unproven attribution. That is the same error class B16 committed in the other direction.
2. **C01, C09 and C13 — revision identity.** Not a substantive disagreement. It is resolved the moment C publishes revision 3 (§2).

There are no other surviving disagreements. A05 r2 vs C05 r2 on interior exports ("only under independent proof" vs "none in M2") is compatible: both forbid an unproven export. I classify it as a **design preference**, not a contract difference.

---

## 7. Deferred questions (agreed boundaries)

| Deferred | Boundary keeping it out of accepted production decisions | Condition that brings it back |
|---|---|---|
| Fix B3 (E5) | A06/B08/C10: post-M2, whole segments, strict codec (C09) | a named not-done function or an M3 consolidation demonstrably needing multi-anchor data (Q-B08) |
| Selective extraction (E3/E4) | A07/C08: no M2 use; owner gate-2 decision first | a justified canonical-TU candidate plus an owner decision on `match --all` semantics |
| CONST gap exemption | A14 + C10: none without independent extent/access proof | a real natural-literal candidate with computed-read negatives (A's test D) |
| Full E6 Group/Integrated | A08/C11: per witness need | a witness requiring substitution, callbacks or pointer identity |
| CU hypothesis storage | A10/C12/B14: analyst-only, no store in M2 | the M3 consolidation start |
| EXP-2 / Q-B06 (5r OD, `-zp1`) | B11/A09: presets additive, no default change | a concrete search need |
| Synthesized interior PUBDEF | A05/C05: not in M2 without independent proof | a required edge that piece-local or literal encoding cannot serve |
| wlink LOBYTE fixups | editorial (OBJ-B08) | Build B needs symbolic rel8 |

---

## 8. Roadmap classification and acceptance criteria

The three columns keep architecture agreement, the agreed future acceptance test, and actual execution separate:

- **(i)** agreement on the architecture: yes for all rows, given the canonical decisions above;
- **(ii)** the agreed future acceptance test;
- **(iii)** what has actually been executed.

**Nothing below has passed an acceptance test.** Probes are disposable evidence, not (iii).

| Class | Canonical decision(s) | (ii) Acceptance test | (iii) Executed? |
|---|---|---|---|
| Verification soundness (now) | A02 r2 / C02 r2 | port the 55 E0 controls plus raw checksum/FRAME/non-contiguous/trim-target negatives; every live declared T3 MATCH at the cutover commit under `make verify` | **No.** Only the prototype E0 audit on 539 T3s (my R0 P1) |
| Verification soundness (now) | A03 r2 / C15 r2 | strengthened comparator rejects A's three R2 P2 mutants (no-exec flag, src_type change, conflicting duplicate occurrence) and accepts the live Build A | **No.** A's R2 P1 baseline measurement only |
| Verification soundness (now) | A11 + C16 mechanism (after rewording) | production `run_pair` restores CPU/EFLAGS, mapped memory, allocator and declared stub state; carry-only, host-write and mutable-stub negatives fail; Q-B05 full T4 suite once; any outcome change to the owner | **No.** Disposable probes only |
| Verification soundness (now) | A14 | cache negative: a gap-only mutant sharing a normalized key forces reverification | **No** |
| Toolchain reliability | A12 / C04 r2 | measured shallow/deep effective-path compile with include and output parity; controlled failure outside the envelope | **No** |
| Named M2 blockers | A04/B05 (B1) | ChooseCampaignDialog strict leading-table proof; corrupted-table negative; actual Build A | **No.** My R0 P6 probe link only |
| Named M2 blockers | A05 r2 + B19 + C05 (B2) | standalone Sync (A's R3 P2 is the demonstrated positive, not yet a production test), MissionDefeat with conditional fallthrough, a prefixed rel8, global and per-object legacy negatives, integration receipt | **No.** Probes only (R0 P5, A R3 P2) |
| Named M2 blockers | A13 + C06 (Group B) | strict exact-object RegionMatch, both compiler checks, file gate, typed Build A, cited PLAYFLIC tests unchanged or owner-approved | **No.** R0 P3 probe only |
| Routine reconstruction | A01, C07 (after rewording) | progress counts by DONE obligations; T4→T3 conversions reported separately | ongoing; not a test |
| M3 consolidation | A06/C10/C09 (B3), A10/C12 (CU), A07/C08 (extraction), A08/C11 (E6) | per their deferral triggers | not started |
| Optional | C13 EXP-2, B10/B11 | none required | — |

---

## 9. Delta and validation

`CONSILIUM-R04-DELTA.json` records:

- **New ACCEPTs:** A14 r1 and C15 r2, each with exact text and hash.
- **Changed positions:** CONDITIONAL on C07 r2 and C16 r2, each with exact text, hash and stated condition.
- **Re-affirmed ACCEPTs:** C05 r2, C10 r2 and B06 r1 (exact text), plus ACCEPTs on the replacement revisions listed in §4 (no text, revision-anchored).
- **Objection dispositions:** all 64 non-withdrawn objections, nested in the decision records.
- **Deliberately omitted:** no positions on C01, C09 or C13 revision 2 (§2), and no new withdrawals (§0).

The validator command from `03-DELTA-SCHEMA.md` was run after this response was frozen; its result is reported in the final message. I do not claim consensus.
