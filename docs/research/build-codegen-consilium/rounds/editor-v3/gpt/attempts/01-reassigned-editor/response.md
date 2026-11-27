# RFC Editor report — draft revision 3

Draft revision 3 is complete and ready for fresh approval. I finished Architect B’s preserved partial draft and retained its verified changes. The seven draft files and the [change-by-change record](/mnt/data/projects/warcraft-1-decompile-wt/cons-a/CONSILIUM-DRAFT-V3/CHANGELOG-v3.md) are in `CONSILIUM-DRAFT-V3/`. The editor reassignment changes neither Architect’s recorded positions nor the unanimity requirement.

## Changes completed

- **A1–A2.** Bind authority-bearing receipts at issuance and check freshness on reuse, while preserving the independent Group B path. Cover the twelve documented T4 bypass nodes and declared mutable host dependencies in the paired-state release check. Describe the tested checkpoints and their limitations.
- **A3–A4.** Incorporate the unaffected pinned baseline provisions within their original scopes and retain `make verify` for every production admission. Distinguish the verified E7 presets from pending work. Qualify the E1–E4 and E7–E8 results and preserve the DQ-04 boundary for the unresolved cause of CONST padding variance.
- **C-1–C-3.** Distinguish E0’s permissive OMF admission and persistent THREAD state from E4’s per-record reset and E5’s controlled rewrite. Correct the ledger and evidence references and identify the sources of the acceptance criteria.
- **Retained editorial updates.** B’s refreshed objection cross-references and acceptance-criteria attribution remain in the candidate. The RFC credits B’s partial draft and preserves B’s historical disclosure.

## Validation

- All 24 inbox entries passed byte-count and SHA-256 checks. The final checksum pass confirmed that the inbox, including the preserved partial draft, was unchanged.
- The canonical ledger, frozen revision 2 ledger, preserved partial ledger, and candidate ledger are byte-identical. All 54 proposition hashes recomputed correctly. The ledger records 38 accepted, four rejected, and twelve withdrawn decisions, plus 64 resolved and two withdrawn objections.
- All 42 decision quotations in the RFC and all 54 in the rationale match revision 2 and the canonical ledger, including revision, status, and hash. All 278 rationale cross-references match the canonical objection IDs and statuses.
- I checked the corrections against the pinned baseline RFC, OMF parser and transform code, experiment reports, production guide, and targeted frozen responses cited in the changelog. The EV-2 and EV-3 notice filenames refer to the consilium evidence package. Those two notice files were outside the reassignment inbox.
- I ran no probes, tests, or `make verify`. Production files and Git state were untouched.

## Candidate SHA-256

| File | SHA-256 |
|---|---|
| `CHANGELOG-v3.md` | `c9b29ac0cc49b8950dd9fc05dc45bcdfa0335e90665c9e5f736f641b7dfa695e` |
| `decision-ledger.json` | `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` |
| `decision-rationale.md` | `e4b86d24d8b8b23dc2892d350327cfec6f2c18e0cdc71a3bae23486b7cbfddcb` |
| `deferred-questions.md` | `68b934c778a373fa2c88502c45d9c38cd6c4b6c15c021f3bc9b6a6d2801d6319` |
| `editorial-notes.md` | `66c9564170e67989e5ec910457ada3ee1c68e0ceef4d1d001217a7fc44421c3b` |
| `experimental-interpretation.md` | `1eaa7877a98e80ecbea946733c5ed0ae31519f918820ecaa0db5ad5d5957a2ec` |
| `implementation-roadmap.md` | `40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5` |
| `revised-rfc.md` | `1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b` |

## Files unchanged from revision 2

Only `decision-ledger.json` is unchanged from revision 2. Its revision-2 and canonical SHA-256 is `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`. That file and `deferred-questions.md` are also byte-identical to the preserved partial revision 3. [Durable editor report](/mnt/data/projects/warcraft-1-decompile-wt/cons-a/CONSILIUM-EDITOR-REPORT-V3.md)