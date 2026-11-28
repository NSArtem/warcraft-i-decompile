```text
Draft revision: 3
RFC_SHA256: 1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b
ROADMAP_SHA256: 40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5
Verdict: APPROVE
```

# Final approval review, draft revision 3 — Architect B (Claude, `claude-opus-5-5`)

**Disclosure.** I prepared the partial revision 3. After the owner reassigned the Editor role, Architect A completed and delivered it. I reviewed the delivered files independently. That review covered three things:

- every change A made on top of my partial;
- the requested changes, A1–A4 and C-1–C-3;
- the package as a whole against the ledger and the pinned evidence.

I have not seen the other Architects' current verdicts.

## 1. Verification performed

- **Identity.**
  - All eight draft files and six prior files match the stated SHA-256 values.
  - `draft-decision-ledger.json` is byte-identical to `00-CANONICAL-LEDGER-v2.json` (`dc6bda93…`, checked with `cmp`).
  - The ledger records 38 UNANIMOUS, 4 UNANIMOUS_REJECTED and 12 WITHDRAWN_SUPERSEDED decisions, and 64 RESOLVED and 2 WITHDRAWN objections. Nothing is open or conditional.
- **Normative text, checked by script.**
  - Every proposition hashes to its recorded SHA-256.
  - All 42 non-withdrawn propositions appear verbatim in `draft-revised-rfc.md` under the correct id, revision, status and hash. All 54 appear verbatim in `draft-decision-rationale.md`.
  - Every quoted (`>`) line of the revision 3 RFC is identical to revision 2 (`44490954…`), so no decision text changed.
- **References.**
  - No unknown decision, objection or DQ identifier appears in any draft file.
  - The only non-current revision numbers are the historical disclosures in RFC §13.
  - The per-decision "objections referencing it" lists in the rationale match the v2 `referenced_decision_ids` exactly (0 mismatches).
- **Differences from my partial.** I diffed all six prose files against the partial I left in `CONSILIUM-DRAFT/`. `deferred-questions.md` is identical. A's changes elsewhere are:
  - a more precise E0 parser description;
  - E4 and E5 THREAD detail;
  - A's own R3 P1 checkpoint description;
  - the E8 producer-premise wording;
  - the A14 rationale wording;
  - a scope refinement of B-3 (baseline §6 provisions "in their original scopes", with §6.4 kept as explanation);
  - "accepted decision text" wording in §0;
  - the receipt-binding wording in roadmap S0.2, S0.4 and S1.3;
  - the Editor attribution and the §13 disclosures.
- **New factual claims checked against pinned artifacts:**
  - `experiments/build_codegen/e4/omf_extract.py@e6150b8` lines 243–262: `raw_fixups` builds a new `Threads()` decoder for every FIXUPP record. Confirmed.
  - `experiments/build_codegen/e5/omf_b3.py@e6150b8` lines 280 and 318–326: one persistent `Threads()` decoder, which parses FIXUPP "including dropped data's thread definitions". Confirmed.
  - `E5-data-anchors.md@e6150b8` §Scenario 3: the baseline scan does not claim native THREAD emission. Confirmed.
  - `tools/wc1/omf.py@e6150b8`, the C-1 claim: THREAD state persists within a module; there is no checksum check and no allow-list; FRAME is discarded from `Fixup`. Confirmed in r2 review and unchanged.
  - The A R3 P1 checkpoint description is Architect A's account of A's own probe. It is consistent with A's frozen r04 §4.
- **Earlier evidence checks.** These were made while preparing the partial, against `@e6150b8`, `@17733f9` and my own probe script, and the delivered text still matches them:
  - E1 isolated links and the four standalone Sync NASM rejections;
  - E2 83/96, no native full-area RegionMatch, and 3 addend changes versus 1 broken anchor;
  - the E3/E4 `sum = delta + score;` fixture and the one-byte baseline mismatch;
  - the E7 `c01`/`c06` 417/417 control;
  - the E8 premises and the observed pad variation;
  - the 12 bypass nodes in `docs/ANALYST_GUIDE.md@17733f9`;
  - B R3-P1 not restoring `Emu._heap`.

No probe, test or production verification was run for this review.

## 2. Requested changes: disposition

| ID | Applied as required? | Where |
|---|---|---|
| A1 | Yes. | DEC-A14 binding is applied at issuance of every authority-bearing receipt and on reuse, and Group B meets it locally with no cache. Roadmap §Dependency graph, S0.2, S0.3, S0.4, S1.3; RFC §10. |
| A2 | Yes. | Covers `run_pair` and the 12 bypass nodes, migrated or checked by an equivalent audited path with assertions preserved; declared mutable host dependencies in the checkpoint; tested checkpoints described with their limits. Roadmap S0.5, RFC §10, appendix E6, DEC-A11 rationale. |
| A3 | Yes. | RFC §0 defines two kinds of normative content (accepted decisions, and baseline provisions incorporated by reference). RFC §8 has rows B-1 to B-7, naming the governing decision wherever a baseline criterion is replaced. §5.6 points to the pinned baseline §8.2. Roadmap states the `make verify` admission gate for every stage. The §0 "not executed" claim is narrowed, with E7 presets as the exception. |
| A4 | Yes. | Appendix E1–E4, E7, E8; DQ-04 measured scope; baseline §17 item 1; rationale for DEC-A13, DEC-A14 and DEC-B11. OBJ-B22's closure and re-entry trigger are unchanged. |
| C-1 | Yes. | Appendix E0, with E4 and E5 cross-references. |
| C-2 | Yes. | The editorial notes name the v2 ledger files. The RFC header and the notes identify the EV-2 and EV-3 notices alongside the pinned EV-1 manifest. |
| C-3 | Yes. | The RFC §10 header credits the decision texts, the three r04 criteria tables, and baseline §16. |

## 3. Answers to the review questions

1. **Agreed decisions preserved at their current revision: yes.** Mechanically verified (§1).
2. **Objections silently resolved, omitted or altered: no.** All 66 dispositions are as recorded. The residual questions behind OBJ-A24 and OBJ-B22 remain DQ-11 and DQ-04.
3. **Internal consistency: yes.**
   - The appendix, RFC, roadmap and deferred questions agree with the ledger.
   - The incorporation table in RFC §8 removes revision 2's conflict between "only normative text" and the carried-forward provisions, and it names the governing decision for each replaced criterion (B-4a, B-4b, B-4g, B-5).
4. **Gates preserved and not weakened: yes.**
   - `make verify`, `make goal`, the tiers and the classification rules are unchanged.
   - Baseline §13 invariants and §16 minimum admission criteria are incorporated.
   - The receipt-binding and paired-state gates are stronger than in revision 2.
   - Removing my partial's extra "mutable-host-dependency" item from the S0.5 negatives list is not a weakening. That item was my addition, not a requested change. Declared mutable host dependencies remain in the checkpoint coverage the exit criteria require, and DEC-A16's own text binds.
5. **Dependency ordering tied to M2 and blockers: yes.**
   - S0.4 binding lands before the first receipt of S0.2 and S0.3.
   - S0.5 is independent and covers all T4 routes.
   - S1.x follows S0.2 and S0.3. S1.3 is independent under DEC-A13.
   - S2 is post-M2 or on demand.
   - Each stage names a demonstrated defect or a named blocker against the EV-3 state (912/1010, 98 not DONE).
6. **Uncertainties stated: yes.** See DQ-01 to DQ-17, O-1 to O-4, the U/Q lines in the appendix, and the (iii) column.
7. **Claims without support: none found.** The two revision 2 defects (the E0 THREAD claim, the stale ledger identity) are corrected, and every new factual claim I checked is supported by the pinned artifact it cites.

## 4. Non-blocking observations (no change required)

- **RFC §13.** A's disclosure does not mention that A was CONDITIONAL on DEC-C07 r2 and DEC-C16 r2 in r04 before accepting r3. Both are superseded revisions and the outcome is unchanged, so this omission does not affect any clause.
- **`editorial-notes.md` §9.** It points to `../CONSILIUM-EDITOR-REPORT-V3.md`, which is outside the approved package. The reference is non-normative.

I do not claim consensus.