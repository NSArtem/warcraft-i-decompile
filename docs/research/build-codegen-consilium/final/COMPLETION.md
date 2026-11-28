# Consilium completion record

- **Status:** `CONSENSUS_ACHIEVED`
- **Completed at (UTC):** `2026-11-28T05:27:50.669577Z` (approval round frozen)
- **Campaign:** `2026-11-27-build-codegen-consilium`
- **Branch:** `research/build-codegen-consilium`
- **Baseline:** `research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`
- **Production evidence:** EV-3, `main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`

## Approved candidate: draft revision 3

| Artifact | SHA-256 |
|---|---|
| draft manifest (`final/drafts/v3/manifest.json`) | `548a15714b23554223d085600bce76ff5c749d816238a170fa4f1f0bc6a3acfc` |
| `revised-rfc.md` | `1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b` |
| `implementation-roadmap.md` | `40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5` |
| `experimental-interpretation.md` | `1eaa7877a98e80ecbea946733c5ed0ae31519f918820ecaa0db5ad5d5957a2ec` |
| `decision-rationale.md` | `e4b86d24d8b8b23dc2892d350327cfec6f2c18e0cdc71a3bae23486b7cbfddcb` |
| `decision-ledger.json` | `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` |
| `deferred-questions.md` | `68b934c778a373fa2c88502c45d9c38cd6c4b6c15c021f3bc9b6a6d2801d6319` |
| `editorial-notes.md` | `66c9564170e67989e5ec910457ada3ee1c68e0ceef4d1d001217a7fc44421c3b` |
| `CHANGELOG-v3.md` | `c9b29ac0cc49b8950dd9fc05dc45bcdfa0335e90665c9e5f736f641b7dfa695e` |

## Approval records (round `approval-3`, frozen)

| Architect | Verdict | RFC_SHA256 quoted | ROADMAP_SHA256 quoted | Response SHA-256 |
|---|---|---|---|---|
| A - GPT (Editor, separate Architect verdict) | **APPROVE** | `1f88bfa3…` | `40600cff…` | `f00b3004744efc9bcfecbc9ee3cd925e61e1a5e7586b0e4ad18054d7c8f852fb` |
| B - Claude (independent final review) | **APPROVE** | `1f88bfa3…` | `40600cff…` | `622fc605e6db54eb4f44bac97860078345273bb9fba8c4daf6dd5f08c012d00f` |
| C - Gemini (fresh, not carried over) | **APPROVE** | `1f88bfa3…` | `40600cff…` | `f9c3fbc4077c41527ae92283b5f27f08f0bf75bd91408e7989773b163937d2e2` |

Verified mechanically by `finalize.py check --round approval-3 --dir final/drafts/v3`:
`all_approve: true`, `hashes_match: true`, `status: CONSENSUS_ACHIEVED`.

## Ledger

- Decisions: 54 - 38 `UNANIMOUS`, 4 `UNANIMOUS_REJECTED`, 12 `WITHDRAWN_SUPERSEDED`.
- Objections: 66 - 64 `RESOLVED`, 2 `WITHDRAWN`. None open.
- Canonical ledger byte-identical to revision 2 and to Architect B's preserved
  partial draft: `dc6bda93…`. No proposition, revision, status, position or
  objection disposition changed during the finalization campaign.
- All 54 proposition hashes recomputed; the canonical ledger agrees with the
  rebuilt full ledger (`decisions.json`) on every status, revision and hash.

## Editor reassignment

The owner reassigned the RFC Editor role from Architect B to Architect A during
this campaign. It was editorial and administrative only: authority, voting
rights, decisions, approvals, objections, identities and the unanimity
requirement were unchanged. Architect A completed the draft from B's preserved
partial work; B's remaining window was spent only on its independent final
review.

## Non-blocking observations (recorded, no change required)

- Architect B: RFC §13 does not list A's r04 CONDITIONAL positions on DEC-C07 r2
  and DEC-C16 r2 before accepting r3. Both revisions are superseded and no
  clause is affected.
- Architect B: `editorial-notes.md` §9 references `CONSILIUM-EDITOR-REPORT-V3.md`,
  which is outside the approved package. The reference is non-normative.

Neither observation is a defect in an approved obligation, and neither architect
requested a change.

## Scope of this completion

This record certifies architectural consensus on the approved documents. It does
**not** implement the roadmap. No production code, verification gate, project
scope or classification rule was changed; `main` was not modified or merged into.
