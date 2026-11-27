Draft revision: 3
RFC_SHA256: 1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b
ROADMAP_SHA256: 40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5
Verdict: APPROVE

# Final Approval Review (Draft Revision 3) — Architect C (Gemini)

- **Architect:** Architect C — Gemini (`gemini-4-neon-high`, high reasoning effort, harness `agy 1.5.17`)
- **Draft revision reviewed:** `3` (fresh independent verdict; revision-2 approval not carried over)
- **Draft manifest SHA-256:** `548a15714b23554223d085600bce76ff5c749d816238a170fa4f1f0bc6a3acfc`
- **Evidence baseline:** `EV-1` (`e6150b856106ae113bb023300b956fff318da7ef`, `main@a21772b8140b4b07012cde8da7da18ad3f6d56b6`), with supplemental committed evidence notices `EV-2` (`d5d4d2c6...`) and `EV-3` (`main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`)

---

## 1. Immutable Artifact Verification

Every delivered draft file and prior evidence file in `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/approval-3-inbox/` was read completely and independently SHA-256 verified against the delivery manifest:

| File | Bytes | Verified SHA-256 |
| --- | ---: | --- |
| `draft-revised-rfc.md` | 65,748 | `1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b` |
| `draft-implementation-roadmap.md` | 16,132 | `40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5` |
| `draft-decision-ledger.json` | 124,977 | `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` |
| `draft-decision-rationale.md` | 82,114 | `e4b86d24d8b8b23dc2892d350327cfec6f2c18e0cdc71a3bae23486b7cbfddcb` |
| `draft-experimental-interpretation.md` | 17,620 | `1eaa7877a98e80ecbea946733c5ed0ae31519f918820ecaa0db5ad5d5957a2ec` |
| `draft-deferred-questions.md` | 9,657 | `68b934c778a373fa2c88502c45d9c38cd6c4b6c15c021f3bc9b6a6d2801d6319` |
| `draft-editorial-notes.md` | 7,179 | `66c9564170e67989e5ec910457ada3ee1c68e0ceef4d1d001217a7fc44421c3b` |
| `draft-CHANGELOG-v3.md` | 5,657 | `c9b29ac0cc49b8950dd9fc05dc45bcdfa0335e90665c9e5f736f641b7dfa695e` |
| `prior/00-NOTE.md` | 221 | `b6fe4f59ea87e0e39a4170ca61a034c1919104008ccb391a793bedb68dad7f52` |
| `prior/01-EVIDENCE-MANIFEST.json` | 21,862 | `c2d059d32c50e0eccc3bb5c4b66a56fe27e7ee040b965547225abafe24c4c7eb` |
| `prior/02-EV-2.json` | 1,330 | `0f546837c2de8c09154d145c2d1a24c81c4036ec511d97b953d2fbf5759d721f` |
| `prior/03-EV-3.json` | 4,245 | `3d3dfa43f79ad4a890f65f9b04be9c911a0f38293290e817a49e14f0ad6bd537` |

---

## 2. Verification Against All Seven Review Criteria

### Criterion 1 — Preserves every agreed decision at its current revision

**PASS (mechanically verified byte-for-byte).**

- `draft-decision-ledger.json` is byte-identical (`dc6bda93...`) to the final canonical v2 ledger: **38 `UNANIMOUS`**, **4 `UNANIMOUS_REJECTED`**, **12 `WITHDRAWN_SUPERSEDED`**, **0 `CONDITIONAL` / `PROPOSED` / `CONFLICT`** across all 54 decisions. No decision was reopened or modified.
- In `draft-revised-rfc.md`:
  - §4 indexes all **54** decisions with **0** mismatches in ID, revision, or status.
  - §5 and §6 reproduce all **42** active and rejected propositions (38 `UNANIMOUS` + 4 `UNANIMOUS_REJECTED`) with **0** byte-for-byte mismatches in revision, status, 64-hex SHA-256, or proposition text.
  - §7 lists all **12** `WITHDRAWN_SUPERSEDED` decisions with exact revisions, origins, and replacements (**0** mismatches).
- In `draft-decision-rationale.md`, all **54** quoted propositions match `draft-decision-ledger.json` byte-for-byte (**0** mismatches).
- Editorial titles remain explicitly tagged `[editorial title]`, and `draft-editorial-notes.md` §2 confirms non-voted consolidated clauses were not substituted for verbatim ledger propositions.

### Criterion 2 — Does not silently resolve, omit, or alter any outstanding objection

**PASS (mechanically verified against canonical v2 objection ledger).**

- All **66** objections remain closed (**64 `RESOLVED`**, **2 `WITHDRAWN`**: `OBJ-C09`, `OBJ-C13`; **0 `OPEN`**).
- Revision 3 improves companion fidelity (`O-B1`): `draft-decision-rationale.md` now references all **66** objections across all **54** decisions with **0** mismatches against `draft-decision-ledger.json` (all 278 decision–objection pairs match the canonical v2 projection).
- `draft-revised-rfc.md` §11 continues to highlight `OBJ-A24` (r06) and `OBJ-B22` (r07) explicitly, and §12 item 3 documents the revision-3 update from v1 to v2 cross-references.
- Every `DEC-*` and `OBJ-*` citation across all seven markdown files resolves to a valid canonical ledger entry (**0** invalid or invented IDs).

### Criterion 3 — Internal consistency across experimental interpretation, revised RFC, roadmap, deferred questions, and ledger

**PASS (substantially improved over revision 2).**

- **Normative source consistency (`A3`):** Revision 3 eliminates the revision-2 tension between ledger-only normativity and baseline carry-forward by defining exactly two normative sources in `draft-revised-rfc.md` §0 (1. verbatim accepted ledger propositions; 2. pinned baseline RFC provisions `B-1..B-7` incorporated by reference at `6f319ac8...` in §8, with governing accepted decisions explicitly named per row where overridden), mirrored consistently in `draft-editorial-notes.md` §§2 and 6.
- **Receipt-binding consistency (`A1`):** `DEC-A14 r1` raw-artifact and verified-context binding is now enforced **at issuance** of every authority-bearing verification or integration receipt (as well as on reuse) across `draft-revised-rfc.md` §10 and `draft-implementation-roadmap.md` (`S0.2`, `S0.3`, `S0.4`, `S1.3`), with Group B (`S1.3`) meeting the contract locally without requiring a cache or waiting on `S0.2–S0.4` (consistent with `DEC-A13 r1`).
- **T4 coverage consistency (`A2`):** `draft-revised-rfc.md` §10 and `draft-implementation-roadmap.md` `S0.5` consistently cover both `cemu.run_pair` and the 12 documented hand-written T4 bypass nodes (`docs/ANALYST_GUIDE.md@17733f9`), account for declared mutable host dependencies, preserve existing output assertions, and require owner review (`O-2`) for any change in test meaning or expected status.
- **Roadmap and deferred-question alignment:** `draft-implementation-roadmap.md` cites 37 of 38 `UNANIMOUS` decisions (omitting only `DEC-C14`, the framework exclusion recorded in RFC §5.11 and §8 B-7), cites **0** `UNANIMOUS_REJECTED` or `WITHDRAWN_SUPERSEDED` decisions as active requirements, and aligns cleanly with `DQ-01..DQ-17` and owner checkpoints `O-1..O-4`.
- **Editorial governance (`§13`, `editorial-notes.md` §9):** The owner's reassignment of draft revision 3 to Architect A is transparently disclosed alongside both Architect A's and Architect B's recorded positions, leaving unanimity and ledger authority intact.

### Criterion 4 — Acceptance and verification gates preserved and not weakened

**PASS.**

- `make verify`, `make goal` (gates 1–3), tier definitions, `wc1.progress` classification rules, dual-compiler (`10.0a` + `OW2`) compilation, Build A `IDENTICAL`, and owner-only authority over scope/gates/`AGENTS.md` are fully preserved.
- `draft-implementation-roadmap.md` ("Admission gate for every stage") explicitly requires `make verify` green at admission for **every** newly adopted production mechanism, including stages with no prior-stage dependency (`S0.1`, `S0.5`, `S1.3`), with stage-specific exit criteria strictly additive.
- The three-way separation **(i)** architectural agreement vs **(ii)** agreed future acceptance test vs **(iii)** executed status is rigorously maintained across `draft-revised-rfc.md` §0 & §10, `draft-implementation-roadmap.md`, `draft-experimental-interpretation.md`, and `draft-decision-rationale.md`. Revision 3 properly credits all three sources of `(ii)` acceptance criteria (decision texts, all three Architects' Round 4 criteria tables, and incorporated baseline RFC §16; `C-3`/`O-B2`) and accurately distinguishes the already-merged E7 presets (`3123a47`, verified as ancestor of both EV-1 `main@a21772b` and EV-3 `main@17733f9`) from all unexecuted mechanisms (`(iii) = No`).

### Criterion 5 — Implementation stages dependency-ordered and tied to actual M2 progress and blockers

**PASS.**

- Grounded on EV-3 (`main@17733f9`: `912/1010 DONE`, `98` not DONE, `539` T3, `2505 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`), with parallel Track `(b)` routine reconstruction (`BULLET.C`, `61+7`) and Track `(c)` owner packets (`8` scope/discovery items + `O-1..O-4`) never serialized behind Track `(a)` infrastructure.
- Track `(a)` dependencies accurately reflect the ledger: `S0.1` path guard, `S0.4` receipt binding at issuance/reuse landing with `S0.2` verifier cutover and `S0.3` single planner + integration receipt + hardened LE comparator, feeding `S1.1` (B1) and `S1.2` (B2); `S0.5` paired T4 state (including the 12 bypass nodes -> `Q-B05` -> `O-2`) independent; `S1.3` Group B whole TU independent of `S0.2/S1.x` with local raw-artifact binding and `O-1`/`O-2` checkpoints.
- Post-M2 / M3 and on-demand stages (`S2.1` strict OMF32 codec -> `S2.2` Fix B3 & `S2.3` extraction pilot; `S2.4` E6 on demand; `S3` CU evidence/storage, Build B, T5) stay off the M2 critical path.

### Criterion 6 — Remaining uncertainties and required experiments stated explicitly

**PASS.**

- Uncertainties, deferrals, and reopening conditions are explicitly bounded in `draft-deferred-questions.md` (`DQ-01..DQ-17`, plus `O-1..O-4` and mapping of baseline §17 items 1–12), `draft-experimental-interpretation.md` (`U` and `Q` entries for `E0..E8`), `draft-revised-rfc.md` §10, and `draft-implementation-roadmap.md`.
- `DQ-04` accurately scopes observed CONST pad-byte variance (path-dependent in B's probes; repeatable within a session and varying across sessions at a fixed path in C's R2 probe as recorded in Round 3 `OBJ-B22`; varying across same-recipe builds in E8 Corpus A) while keeping its causal determinant explicitly undetermined and its architectural boundary closed.

### Criterion 7 — No claim presented as fact without supporting evidence

**PASS (independently spot-checked against pinned repository commits).**

- **OMF THREAD / FRAME facts (`C-1`):** Directly verified against pinned `e6150b8` sources:
  - `tools/wc1/omf.py@e6150b8` (`parse_module`, lines 99–117, 236–297; `Fixup`, lines 25–31) indeed maintains persistent `threads` across FIXUPP records within a module while lacking strict record-length bounds checks, checksum checks, trailing-after-MODEND checks, record allow-listing, and explicit `FRAME` preservation on `Fixup`.
  - `experiments/build_codegen/e4/omf_extract.py@e6150b8` (lines 245–262, specifically line 258 `Threads().parse(...)`) indeed resets `Threads` per FIXUPP record.
  - `experiments/build_codegen/e5/omf_b3.py@e6150b8` (lines 280 and 318–326) indeed uses a persistent `Threads()` decoder across records, including dropped data's thread definitions.
- **Experiment scope clarifications (`A4`, `A2`):** `E1` isolated candidate-plus-ASM links and 4 standalone `IntroOpSyncSound` NASM rejections; `E2` 0/96 normalized same-flags diagnostic vs 83/96 strict FunctionMatch vs 0/3 full-area RegionMatch; `E3`/`E4` modified `ScoreTickIncome` fixture (`sum = delta + score;`); `E6` distinction between B R3-P1 (did not separately restore `Emu._heap`) and A R3 P1 (restored allocator/bookkeeping and also tested fresh `Emu` per case), with neither certifying arbitrary Python state or production audit parity; `E7` `c01`/`c06` 417-match paired control and `3123a47` ancestry of both `a21772b` and `17733f9`; and `E8` explicit `shared_epilogue` producer/partition/linker premises — all are stated accurately without overclaiming.
- **Provenance accuracy (`C-2`):** Ledger filenames, SHA-256 prefixes, and the distinction between the EV-1 campaign manifest and the EV-2/EV-3 supplemental notices are accurately recorded.

---

## 3. Closing Note

Draft revision `3` resolves every substantive and technical precision item documented in `draft-CHANGELOG-v3.md` while keeping the canonical ledger byte-identical, preserving all gates and owner checkpoints intact, and maintaining strict separation between architectural agreement, future acceptance tests, and unexecuted production verification.

I approve **Draft revision `3`** (`revised-rfc.md` `1f88bfa35a2e1d4654a4c75df681919f1ec92e03211b5456945308c1745d1c8b`, `implementation-roadmap.md` `40600cffb77c775acba94c436b3213ea5e883ca2d0637f11d8b004fac7f5c6b5`).

I do **not** claim consensus; the Secretary verifies all three Architects' independent verdicts against the same immutable draft hashes.
