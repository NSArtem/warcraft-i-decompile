# Round 6 — Architect A targeted confirmation

## DEC-C05 cross-reference

**DEC-C05 r3 · CONDITIONAL**  
Proposition SHA-256 `7f518ba5aaeb07edb8b3190ab28eb5a0c1dde91c28b8dd75fa590bdc409c3a65`

The Round 5 ledger contains only revision 3 as the live text. C's withdrawal of DEC-C15 r2 removes its raw equality requirements from the architecture. Revision 3 still contains the citation, so my exact-text condition remains unmet:

> The IntegratedResult comparator requirement must mean DEC-A03 r2. Remove the reference to DEC-C15 r2 or replace it with an agreed revision that keeps raw grouping and fixup-page offsets diagnostic unless their loader relevance is independently established.

I would accept the revision whose sole change from revision 3 is replacing `(DEC-A03 r2 / DEC-C15 r2)` with `(DEC-A03 r2)`. It has SHA-256 `5d51b22bcefa20d67842a75dd643b9ee3856fd9486b15318bb977ea80b76ce68`. This identifies the exact text I support for C to publish. My delta records the position on the published revision 3. [Round 6 inbox ledger, DEC-C05 and DEC-C15 records, Gemini Round 5 §§1.2, 1.4]

## Objections

| Objection | Disposition | Basis |
|---|---|---|
| OBJ-A24 | **RESOLVED** | C's authoritative withdrawal of DEC-C15 r2 removes the raw equality gates; DEC-A03 r2 requires validating raw occurrences before deduplication and keeps serialization differences diagnostic unless shown to be loader-relevant. |
| OBJ-B22 | **DEFERRED** | DEC-A02 r2 and DEC-C02 r2 keep exact cutover independent of the cause of CONST padding variation, and DEC-A14 r1 bars normalized proof authority; reopen the investigation only when padding variance blocks a named exact reconstruction or its cause is needed for a justified B3 or CONST gap decision. |

For OBJ-B22 I align with B's disposition on the remaining research question. The exact-match policy and the rejection of the shape-only gap rule stand. Both dispositions concern architecture and scope. The hardened comparator and production cutover checks remain unexecuted. No new probes or tests ran in this round. [DEC-A02 r2, DEC-C02 r2, DEC-A03 r2, DEC-A14 r1, DEC-C03 r1, Claude Round 5 §6, R4 P1]

## RFC Editor

```text
Nomination: B
Consent if nominated: YES
Conditions: none
```

I consent to serve as RFC Editor if B declines.
