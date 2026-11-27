Draft revision: 2
RFC_SHA256: 44490954fff4d66c005b8996d80d74e980ca1207f06b00289df8dda772cabeef
ROADMAP_SHA256: e6470713736f5ed0ba629a7862dc1ea5b9aea06b4c808265ab5c03e16dd8f929
Verdict: APPROVE

# Final Approval Review — Architect C (Gemini)

- **Architect:** Architect C — Gemini (`gemini-4-neon-high`, high reasoning effort, harness `agy 1.5.17`)
- **Draft revision reviewed:** `2` (RFC Editor: Architect B — Claude)
- **Draft manifest SHA-256:** `b1664adf1d6867e047e4918cdaf766657e786c6af452355c994c65e6e0fa19e4`
- **Evidence baseline:** `EV-1` (`e6150b856106ae113bb023300b956fff318da7ef`, `main@a21772b8140b4b07012cde8da7da18ad3f6d56b6`), with supplemental committed evidence notices `EV-2` and `EV-3` (`main@17733f9`)

---

## 1. Immutable Artifact Verification

Every file delivered in `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gemini/approval-inbox/` was read in full and independently SHA-256 verified against the delivery manifest:

| File | Bytes | Verified SHA-256 |
| --- | ---: | --- |
| `draft-revised-rfc.md` | 57,870 | `44490954fff4d66c005b8996d80d74e980ca1207f06b00289df8dda772cabeef` |
| `draft-implementation-roadmap.md` | 13,545 | `e6470713736f5ed0ba629a7862dc1ea5b9aea06b4c808265ab5c03e16dd8f929` |
| `draft-decision-ledger.json` | 124,977 | `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` |
| `draft-decision-rationale.md` | 78,906 | `db5884df73d1fddc39a4ec80a70be622e024c27bbfdbf3fbcf0356badb390576` |
| `draft-experimental-interpretation.md` | 13,019 | `81388b77cdaf1a9e16eff7cd8764333d5a470c4813f0950f8b448a6eb797b398` |
| `draft-deferred-questions.md` | 9,215 | `97604eb6f17cbb025633edb500e1ec464a3b49d2845314699051ea1320bd8a18` |
| `draft-editorial-notes.md` | 6,164 | `a024c73a866a99671979cff2843e0f5ca3c69265d4d21d628821dd1cc8667ac8` |

---

## 2. Verification Against All Seven Review Criteria

### Criterion 1 — Preserves every agreed decision at its current revision

**PASS (mechanically verified byte-for-byte).**

- Comparing `draft-decision-ledger.json` against the frozen Round 7 ledger (`r07-inbox/00-LIVE-ISSUES-v2.json`), the sole status transition is the expected Round 7 closure of `DEC-C05 r4` (`PROPOSED -> UNANIMOUS`, SHA-256 `5d51b22b3d2b992137dc76143311ebef8f77e127b10ba1610c54605060191751`), yielding **38 `UNANIMOUS`**, **4 `UNANIMOUS_REJECTED`**, **12 `WITHDRAWN_SUPERSEDED`**, and **0 `CONDITIONAL` / `PROPOSED` / `CONFLICT`** across all 54 decisions.
- Every `UNANIMOUS` decision records unconditional `ACCEPT` from all three Architects at its current revision; every `UNANIMOUS_REJECTED` decision records `REJECT` from all three Architects; every `WITHDRAWN_SUPERSEDED` decision points exclusively to `UNANIMOUS` replacements.
- In `draft-revised-rfc.md`:
  - §4 indexes all **54** decisions with **0** mismatches in ID, revision, or status.
  - §5 and §6 quote all **42** active and rejected propositions (38 `UNANIMOUS` + 4 `UNANIMOUS_REJECTED`) with **0** byte-for-byte mismatches in revision, status, 64-hex SHA-256, or proposition text.
  - §7 lists all **12** `WITHDRAWN_SUPERSEDED` decisions with exact revisions, origins, and `UNANIMOUS` replacements (**0** mismatches).
- In `draft-decision-rationale.md`, all **54** decision propositions match `draft-decision-ledger.json` byte-for-byte (**0** mismatches).
- Editorial titles added for readability are explicitly marked `[editorial title]`, and `draft-editorial-notes.md` §2 confirms that non-voted consolidated prose (such as Architect A's Round 5 draft clauses) was never substituted for verbatim ledger propositions.

### Criterion 2 — Does not silently resolve, omit, or alter any outstanding objection

**PASS.**

- All **66** objections in `draft-decision-ledger.json` are closed (**64 `RESOLVED`**, **2 `WITHDRAWN`**: `OBJ-C09`, `OBJ-C13`; **0 `OPEN`**), reflecting only the expected Round 7 closure of `OBJ-B22` (`OPEN -> RESOLVED`) following `DEC-C05 r4`'s unanimous acceptance.
- `draft-revised-rfc.md` §11 explicitly highlights the final two closing-round objections (`OBJ-A24` closed in r06 with `DEC-A03 r2`, and `OBJ-B22` closed in r07 with `DEC-C05 r4`) and preserves the non-normative boundary between `DEC-A03`'s single-plan scope and `DEC-C05`'s diagnostic admission/link-verification semantics.
- Every `DEC-*` and `OBJ-*` identifier cited across all six markdown files resolves to a valid entry in `draft-decision-ledger.json` (**0** dangling or invented references).

### Criterion 3 — Internal consistency across experimental interpretation, revised RFC, roadmap, deferred questions, and ledger

**PASS.**

- `draft-experimental-interpretation.md` aligns each of `E0..E8` (plus `E2/E3/E4` caveat scoping and `E6` conditional deferral) with the exact unanimous decisions (`DEC-B07..B16`, `DEC-B18`, `DEC-B19`, `DEC-C02`, `DEC-C04`, `DEC-C09`, `DEC-C10`, `DEC-C13`, `DEC-A02`, `DEC-A04`, `DEC-A07..A10`, `DEC-A12`, `DEC-A14`).
- `draft-implementation-roadmap.md` cites **37** of the 38 `UNANIMOUS` decisions directly, cites **0** `UNANIMOUS_REJECTED` and **0** `WITHDRAWN_SUPERSEDED` decisions as active requirements, and omits only `DEC-C14` (historical RFC §1 narrative errata, appropriately placed in `draft-revised-rfc.md` §8 and `draft-experimental-interpretation.md` rather than an implementation stage).
- `draft-deferred-questions.md` (`DQ-01`..`DQ-15`) cleanly separates unresolved implementation design questions, owner-authority decisions (`DQ-15`, `O-1`..`O-4`), and cross-decision boundary notes (`DQ-04`, `DQ-11`) without smuggling in unvoted architectural commitments.
- `draft-revised-rfc.md` §13 explicitly lists the Editor's own withdrawn/rejected/retained positions, honoring Editor impartiality.

### Criterion 4 — Acceptance and verification gates preserved and not weakened

**PASS.**

- `draft-revised-rfc.md` §0, §1, §5.1, §10, and §13 and `draft-implementation-roadmap.md` preserve every project gate and invariant verbatim: `make verify`, `make goal` (gates 1–3), tier definitions (`T3` / `T4`), `wc1.progress` classification rules, dual-compiler (`10.0a` + `OW2`) compilation, Build A bit-identity, and the fixed finish line (owner-only authority to change gates, scope, or `AGENTS.md` rules).
- The mandatory three-way separation between **(i)** architectural agreement in this consilium, **(ii)** agreed future acceptance tests/gates, and **(iii)** executed production test status is rigorously maintained in `draft-revised-rfc.md` §0 & §10, `draft-implementation-roadmap.md`, `draft-experimental-interpretation.md`, and `draft-decision-rationale.md`. Every production verification row explicitly records `(iii) Executed now? = No`, and every consilium probe (`A1 Q1/Q2`, `A R2 P1/P2`, `A R3 P1/P2`, `A R4 P1`, `B R0 P3/P5/P6`, `B R3-P1`) is explicitly bounded as disposable evidence rather than an executed production gate.

### Criterion 5 — Implementation stages dependency-ordered and tied to actual M2 progress and blockers

**PASS.**

- Grounded on `EV-3` (`main@17733f9`: `912/1010 DONE`, `98` not-DONE, `539` T3, `2505 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`), with explicit provenance tracking from `EV-1` (`main@a21772b`) through `EV-3`.
- Dependency ordering faithfully reflects `DEC-A01`, `DEC-A03`, `DEC-A06`, `DEC-A11..A16`, `DEC-C05`, `DEC-C07`, `DEC-C08`, `DEC-C16`:
  - **Parallel Tracks `(b)`** (routine M2 reconstruction: `BULLET.C`, `61 + 7` clean items) and **`(c)`** (owner-approval packets `O-1..O-4`) are explicitly never serialized behind Track `(a)` infrastructure work.
  - **Track `(a)` Stage 0 (`S0.1..S0.5`)** properly sequences the `cemu.py::run_pair` paired starting-state harness (`S0.1`), strict raw-OMF admission (`S0.2`), `omfpatch` hardening (`S0.3`), `compare`/`le` loader-semantic verifier (`S0.4`), and `wc1.oldcc` compile-flag plumbing (`S0.5`).
  - **Stage 1 (`S1.1..S1.3`)** gates B1 (`S1.1`, e.g., `ChooseCampaignDialog 0x157e8`) and B2 (`S1.2`, e.g., `SaveErrorDialog 0x1aca8`) on `S0.2..S0.4`, while explicitly allowing Group B (`S1.3`, `-od`/`-d1+` flags) to proceed independently of `S0.2/S1.1/S1.2` per `DEC-A13`.
  - **Post-M2 / M3 Stages (`S2.1..S2.4`, `S3`)** properly defer the strict OMF codec (`S2.1`), B3 shared-epilogue multi-function TUs (`S2.2`, gated on `O-1`), C-owned data/BSS extraction pilot (`S2.3`, gated on `DQ-15`), E6 conditional compiler plumbing (`S2.4`, on demand only), and M3 CU storage / Build B / T5 (`S3`) without blocking M2.

### Criterion 6 — Remaining uncertainties and required experiments stated explicitly

**PASS.**

- Uncertainties, deferred design choices, and required production-equivalent experiments are explicitly catalogued in `draft-deferred-questions.md` (`DQ-01`..`DQ-15`), `draft-revised-rfc.md` §10–§12, `draft-experimental-interpretation.md`, and `draft-implementation-roadmap.md`:
  - Owner-gated checkpoints `O-1` (`AGENTS.md` multi-TU rule), `O-2` (T4 inventory/DONE/xfail status updates after `S0.1` + nonce-bound `WC1_T4_AUDIT_LOG` + full T4 suite regression `Q-B05`), `O-3` (the 8 scope/discovery/runtime packets), and `O-4` (any loader-semantic discrepancy against `war.exe` during `S0.4`).
  - Deferred technical questions including Gate-2 extraction semantics (`DQ-15`), strict-OMF vs `omfpatch` seam details, pre-function switch-table / sibling layout details, and `E6` trigger conditions (`DEC-B16`).

### Criterion 7 — No claim presented as fact without supporting evidence

**PASS.**

- All factual claims trace to pinned commits (`e6150b8`, `a21772b`, `17733f9`, `6f319ac`), archived experiment reports (`E0..E8`), frozen Round 0–7 responses, or explicitly scoped disposable probes.
- Witness T4 observations (`3` passing + `2` persistent failures under checkpoint restoration) are explicitly restricted to diagnostic observations per `DEC-C16 r3` and `DEC-A16 r1`, with root-cause attribution and inventory updates deferred until production-equivalent verification and owner review.
- Historical inaccuracies in the baseline RFC §1 are explicitly corrected as editorial errata (`draft-revised-rfc.md` §8, `DEC-C14 r1`).

---

## 3. Non-Blocking Observations (For Record Only)

Neither observation below affects architectural validity, completeness, or gate fidelity, and neither requires a new draft revision:

1. **V1 vs V2 objection cross-references in `draft-decision-rationale.md`:** As the Editor transparently discloses in `draft-revised-rfc.md` §12 item 3, the non-normative per-decision `"Objections referencing it"` lines in `draft-decision-rationale.md` reflect the narrower v1 objection mapping (63 distinct objection IDs referenced across entries) rather than the expanded v2 cross-reference links in `draft-decision-ledger.json` (66 objections total). Because §12.3 explicitly designates the v2 ledger as authoritative and §11 explicitly documents `OBJ-A24` and `OBJ-B22`, the package is accurate and non-misleading.
2. **Mechanical `closure_note` text on four `RESOLVED` objections in `draft-decision-ledger.json`:** In the Secretary-generated canonical ledger (`dc6bda93...`), four `RESOLVED` objections (`OBJ-A02`, `OBJ-A19`, `OBJ-A21`, `OBJ-B19`) carry a mechanical `closure_note` reading `"named resolutions are not yet unanimously resolved"` because their `referenced_decision_ids` retain withdrawn entries (`DEC-B20`, `DEC-C15`) superseded by `UNANIMOUS` replacements (`DEC-A03`, etc.). All four objections have status `RESOLVED`, all replacements are `UNANIMOUS`, and `0` objections remain open.

---

## 4. Closing Note

I approve **Draft revision `2`** (`revised-rfc.md` `44490954fff4d66c005b8996d80d74e980ca1207f06b00289df8dda772cabeef`, `implementation-roadmap.md` `e6470713736f5ed0ba629a7862dc1ea5b9aea06b4c808265ab5c03e16dd8f929`).

I do **not** claim consensus; the Secretary verifies all three Architects' independent verdicts against the same immutable draft hashes.
