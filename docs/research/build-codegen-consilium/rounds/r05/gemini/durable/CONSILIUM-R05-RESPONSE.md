# Build & Codegen Infrastructure — Consilium Round 5 Confirmation & Editor Nomination

- **Architect:** Architect C — Gemini (`gemini-4-neon-high`, high effort, `agy 1.5.17`)
- **Round:** Round 5 — Targeted confirmation, and RFC Editor nomination
- **Evidence Baseline:** `EV-3` (`research/build-codegen-experiments@e6150b856106ae113bb023300b956fff318da7ef`; RFC `docs/architecture/rfc-build-codegen-infrastructure.md@6f319ac8ff780bb45ff028d006216016fc932a13`; production `main@17733f94dc00a14cfcfcebf4b9ce2f0fee40f0d9`: `912/1010 DONE`, `98` not-done, `2505 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`)
- **Inbox Verified (SHA-256):** `00-LIVE-ISSUES-v2.json` (`05297f82...`), `01-architect-gpt-response.md` (`e6a4affd...`), `02-architect-claude-response.md` (`a9c0099e...`), `03-DELTA-SCHEMA.md` (`357e7358...`).
- **New Probes:** None this round.
- **Unanimous / Closed Decisions Untouched:** None of the `29` `UNANIMOUS`, `4` `UNANIMOUS_REJECTED`, or `11` `WITHDRAWN_SUPERSEDED` decisions in `00-LIVE-ISSUES-v2.json` is reopened.
- **Structured Delta:** Companion machine-readable delta written to `CONSILIUM-R05-DELTA.json` and validated against this exact response file via `decision_delta.py`.

---

## 1. Targeted Resolution of Unresolved Decisions

### 1.1 Republished Revisions (Byte-Identical) — `DEC-C01 r3`, `DEC-C09 r3`, `DEC-C13 r3`

Each of these three revision-3 publications carries the exact byte-identical Round 2 text (`CONFLICT` cleared in Round 4). I explicitly confirm that my approval on the identical text applies to **revision 3** (and maintain `ACCEPT` in `CONSILIUM-R05-DELTA.json`):

| Decision | Revision | Proposition SHA-256 (byte-identical to R2) | My Position |
|---|---|---|---|
| `DEC-C01` | `3` | `e7c48783a6fd1b06d03a15889e1e3b9761abc4fca001b3eda58ee77e1e5f21de` | **`ACCEPT`** (re-confirmed on rev 3; clears R3 conflict) |
| `DEC-C09` | `3` | `802a18ef20526453f67ca65085b8a3b7be3102ae0fb97c6ea02a34735e199b9b` | **`ACCEPT`** (re-confirmed on rev 3; clears R3 conflict) |
| `DEC-C13` | `3` | `eb85f6e2e75fb9c1a62cbdfc1703db8fa33a89dfdbb9fe01e116c32f195a6b02` | **`ACCEPT`** (re-confirmed on rev 3; clears R3 conflict) |

### 1.2 Changed Revisions — `DEC-C05 r3`, `DEC-C07 r3`, `DEC-C10 r3`, `DEC-C16 r3`

I authored and published all four revision-3 texts in Round 4 (explicitly superseding revision 2) to incorporate Architects A and B's stated conditions. I maintain **`ACCEPT`** on every exact revision-3 text and hash (noting on `DEC-C05 r3` that its parenthetical comparator reference `DEC-A03 r2 / DEC-C15 r2` continues cleanly via unanimous `DEC-A03 r2` after my authoritative withdrawal of `DEC-C15 r2` in §1.4 below):

| Decision | Revision | Proposition SHA-256 | My Position |
|---|---|---|---|
| `DEC-C05` | `3` | `7f518ba5aaeb07edb8b3190ab28eb5a0c1dde91c28b8dd75fa590bdc409c3a65` | **`ACCEPT`** (rev 2 superseded; incorporates `DEC-A05 r2` fixed-field/adjacency/legacy rules and mode-qualified Sync tests) |
| `DEC-C07` | `3` | `4756b13b2fde6f82475c1180e4d5c0102effb4dccda5c6936d8e93b6adf84a9f` | **`ACCEPT`** (rev 2 superseded; incorporates diagnostic-only 3/2 wording, zero premature DONE credit, and named-witness E6 exception; compatible with `DEC-A15 r1`) |
| `DEC-C10` | `3` | `a8756e094f269537ac7342f0d2c9361af01a4a63c54c1966a9c9d5fe6bea1e19` | **`ACCEPT`** (rev 2 superseded; enforces unanimous `DEC-A14 r1` raw identity and independent extent/access-proof gate) |
| `DEC-C16` | `3` | `d4fe9e9c5ce5769a66512b4f53cb098344d2bd5b7d233d64c2837f2f217fecbb` | **`ACCEPT`** (rev 2 superseded; incorporates diagnostic-only 3/2 wording, `Q-B05`, owner review, and full paired-state channels including allocator/segment/ESP/stubs; compatible with `DEC-A16 r1`) |

### 1.3 New Decisions Proposed in Round 4 — `DEC-A15 r1`, `DEC-A16 r1`

Both new decisions proposed by Architect A in Round 4 are clean, well-scoped, and fully compatible with my Round 4 revision-3 texts (`DEC-C07 r3` and `DEC-C16 r3`). I unconditionally **`ACCEPT`** both:

- **`DEC-A15` rev 1** — SHA-256 `f89aed122bc2331b2432c0a368d2a083b71121b277bc7ce199001f927d3a7f44` — **`ACCEPT`**.
  - *Basis:* Cleanly preserves parallel M2 reconstruction, owner evidence packets, verification hardening, need-driven infrastructure admission (including a scoped rename/routing helper when reconstruction is ready), post-M2 boundaries for general B3 / selective extraction / E6 beyond a named witness / persistent stores, and M3 Build B independence.
- **`DEC-A16` rev 1** — SHA-256 `750e1346bc31b346b2d1d4933d2c446373d109a33e888364b59f7e696b9d5785` — **`ACCEPT`**.
  - *Basis:* Cleanly specifies full paired starting state under unanimous `DEC-A11 r1` (including `EFLAGS`, mapped regions **and permissions** and contents, host/guest writes, allocator state, and declared mutable host/stub dependencies), `UNSUPPORTED` fail-closed behavior, full existing T4 suite regression before landing, production T4 audit logging, owner review, and observation-only status for the five EV-3 witnesses until current authorized verification evidence exists.

### 1.4 Conditional Decision — `DEC-C15 r2` (Authoritatively Withdrawn in Favour of Unanimous `DEC-A02 r2`, `DEC-C02 r2`, `DEC-A03 r2`)

- **`DEC-C15` rev 2** — SHA-256 `a44884bb09f9f7efcdd0fb760c03cf6174249af49b20f53094b55564b5d58ddc` — **`REJECT` (authoritatively withdrawn into `DEC-A02 r2`, `DEC-C02 r2`, `DEC-A03 r2`)**.
- *Technical evaluation of Architect A's condition and `OBJ-A24`:* Architect A's `R4 P1` probe (`r04-regroup.py`) is decisive. Replacing two disjoint same-page `OFF32` records on page 1 with one source-list record targeting `(2, 0x4085)` preserves all `8,773` parsed physical typed fixup occurrences (`8,770` unique) and the exact loaded image while altering `fixup page offsets` and `raw grouping multiset`. Requiring hard equality on those two fields in `DEC-C15 r2` therefore over-constrained serialization without an established loader-semantic obligation.
- *Resolution:* Architect A's condition (*"Use DEC-A02 r2 for OMF and DEC-A03 r2 for LE. Require structural validation of all raw occurrences, then equality on supported loader semantics. Keep raw groupings, offset tables and other serialization differences diagnostic unless loader relevance is independently established"*) is **100% sound and already carried by unanimous `DEC-A02 r2`, `DEC-C02 r2`, and `DEC-A03 r2`**. Rather than publishing a redundant `DEC-C15 r3`, I authoritatively withdraw `DEC-C15 r2` (`withdraws` -> `["DEC-A02", "DEC-C02", "DEC-A03"]`), confirming that Stage-0 strict raw-OMF admission lives in unanimous `DEC-A02 r2` + `DEC-C02 r2` and hardened `wc1.compare` (pre-deduplication raw physical fixup validation, equality on supported LE loader semantics — object flags, entry/stack, module flags, page size/count, page map, normalized typed fixups — while keeping `fixup page offsets`, `raw grouping multiset`, raw fixup serialization order, and 1-byte last-page file size diagnostic unless independent loader evidence establishes relevance) lives in unanimous `DEC-A03 r2`.

---

## 2. Durable Copy versus Final Message Verification (§2.5)

I confirm that my Round 4 structured delta (`CONSILIUM-R04-DELTA.json`, bound to `CONSILIUM-R04-RESPONSE.md` SHA-256 `f6a1c08481280b5e68b97534a3df7a184212ca5e4184769d09d66992e4fb5bba`) **accurately and completely describes every decision position and objection disposition in my Round 4 final message**. My Round 4 final message emitted the complete, unabbreviated text of `CONSILIUM-R04-RESPONSE.md`; any byte difference between the durable file and the captured message is purely non-substantive trailing whitespace/newline formatting. No Round 4 record requires restatement; all Round 5 updates (`DEC-A15 r1`, `DEC-A16 r1`, authoritative withdrawal of `DEC-C15 r2`, re-confirmation of `DEC-C01/C05/C07/C09/C10/C13/C16 r3`, and the 12 open-objection dispositions) are cleanly recorded in `CONSILIUM-R05-DELTA.json`.

---

## 3. Disposition of All 12 `OPEN` Objections (§2.6)

For every `OPEN` objection in `00-LIVE-ISSUES-v2.json`, the table below records my closing disposition and explicitly separates **(i) architectural agreement**, **(ii) agreed future acceptance test/gate**, and **(iii) executed test status** (none of the production acceptance tests below has been executed yet; all consilium probes remain disposable diagnostic evidence):

| Objection | Origin | My R5 Disposition | Resolving Decision(s) | One-Sentence Basis & Strict (i) / (ii) / (iii) Assertion |
|---|---|---|---|---|
| `OBJ-A01` | GPT | **`RESOLVED`** | `DEC-A03 r2`, `DEC-A05 r2`, `DEC-A13 r1`, `DEC-B06 r1`, `DEC-B19 r2` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A03 r2`, `DEC-A13 r1`, and `DEC-B06 r1` establish that preflight never grants promotion credit without actual assembly/link/provider/comparison receipts and permit exact Group B independently; production planner and Group B gates remain unexecuted. |
| `OBJ-A09` | GPT | **`RESOLVED`** | `DEC-A03 r2`, `DEC-C01 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A03 r2` (with byte-identical compatible companion `DEC-C01 r3`) establishes that the single derived placement plan is preflight-only and `IntegratedResult` is sole acceptance authority; production planner cutover remains unexecuted. |
| `OBJ-A15` | GPT | **`RESOLVED`** | `DEC-A01 r1`, `DEC-A13 r1`, `DEC-A15 r1`, `DEC-B16 r1`, `DEC-C07 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A01 r1`/`DEC-A13 r1`, rejected `DEC-B16 r1`, and accepted `DEC-A15 r1`/`DEC-C07 r3` preserve parallel M2 reconstruction, need-driven infrastructure admission, upper-bound yield framing, and zero premature DONE credit; M2 execution is ongoing. |
| `OBJ-A20` | GPT | **`RESOLVED`** | `DEC-A11 r1`, `DEC-A16 r1`, `DEC-C16 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A11 r1` plus accepted `DEC-A16 r1` and `DEC-C16 r3` keep the five EV-3 witness results strictly diagnostic until production paired-state implementation, nonce-bound audit, full T4 suite regression (`Q-B05`), and owner review execute; production execution remains pending. |
| `OBJ-A22` | GPT | **`RESOLVED`** | `DEC-A14 r1`, `DEC-C10 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A14 r1` (with withdrawn `DEC-B21 r2` and aligned `DEC-C10 r3`) binds every authority-bearing receipt to exact raw artifacts and restricts normalized `CONST` digests to candidate grouping; production cache-miss negative test remains unexecuted. |
| `OBJ-A23` | GPT | **`RESOLVED`** | `DEC-A15 r1`, `DEC-A16 r1`, `DEC-C07 r3`, `DEC-C16 r3` | **Asserting (i)+(ii), NOT (iii):** Accepted `DEC-A15 r1`, `DEC-A16 r1`, `DEC-C07 r3`, and `DEC-C16 r3` remove all premature `"genuine ref-C"` attribution and DONE credit and admit E6 early only for a named necessary witness; production verification and causal tracing remain unexecuted. |
| `OBJ-A24` | GPT | **`RESOLVED`** | `DEC-A02 r2`, `DEC-C02 r2`, `DEC-A03 r2` *(plus withdrawal of `DEC-C15 r2`)* | **Asserting (i)+(ii), NOT (iii):** Upholding `R4 P1`, I authoritatively withdraw `DEC-C15 r2` in favour of unanimous `DEC-A02 r2`, `DEC-C02 r2`, and `DEC-A03 r2`, validating all raw physical fixups before deduplication and comparing supported LE loader semantics while keeping `fixup page offsets` and `raw grouping multiset` diagnostic unless loader relevance is independently established; hardened `wc1.compare` remains unexecuted. |
| `OBJ-B22` | Claude | **`RESOLVED`** | `DEC-A02 r2`, `DEC-C02 r2`, `DEC-A14 r1`, `DEC-C03 r1` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A02 r2`, `DEC-C02 r2`, `DEC-A14 r1`, and unanimously rejected `DEC-C03 r1` resolve the architectural contract by enforcing exact raw-byte matching at cutover and retiring shape-only V4 (while the forensic root cause of Watcom 10.0a `CONST` pad variance remains deferred out of production unless a named reconstruction makes it consequential); production cutover test remains unexecuted. |
| `OBJ-B29` | Claude | **`RESOLVED`** | `DEC-A01 r1`, `DEC-A15 r1`, `DEC-C07 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A01 r1` plus accepted `DEC-A15 r1` and `DEC-C07 r3` remove serial infrastructure gating and keep eligible reconstruction, verification hardening, and owner packets on independent parallel tracks; M2 execution is ongoing. |
| `OBJ-C04` | Gemini | **`RESOLVED`** | `DEC-A01 r1`, `DEC-A15 r1`, `DEC-C07 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A01 r1` plus accepted `DEC-A15 r1` and `DEC-C07 r3` keep routine M2 reconstruction parallel with verification hardening and named-blocker infrastructure without artificial universal serialization; M2 execution is ongoing. |
| `OBJ-C11` | Gemini | **`RESOLVED`** | `DEC-A05 r2`, `DEC-B19 r2`, `DEC-C05 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A05 r2`/`DEC-B19 r2` plus accepted `DEC-C05 r3` codify mode-qualified standalone-Sync tests, zero M2 interior `PUBDEF` synthesis, and verified fixed-field/fallthrough/legacy rules; production B2 tests remain unexecuted beyond GPT's disposable `R3 P2` link probe. |
| `OBJ-C16` | Gemini | **`RESOLVED`** | `DEC-A01 r1`, `DEC-A15 r1`, `DEC-C07 r3` | **Asserting (i)+(ii), NOT (iii):** Unanimous `DEC-A01 r1` plus accepted `DEC-A15 r1` and `DEC-C07 r3` separate M2 Gate-1 closure from T4-to-T3 conversion with upper-bound yield framing and zero premature DONE credit; M2 execution is ongoing. |

---

## 4. RFC Editor Nomination

```text
Nomination: B
Consent if nominated: YES
Conditions: (1) Every normative clause in the revised RFC traces explicitly to unanimous canonical decision IDs, revisions, and SHA-256 hashes from the frozen ledger, with any non-unanimous item or deferred question marked explicitly by status and re-entry boundary rather than silently resolved; (2) the revised RFC maintains strict three-way separation between (i) architectural agreement, (ii) agreed future acceptance tests/gates, and (iii) executed test status (disposable consilium probes cited strictly as diagnostic evidence); (3) all three Architects review the complete drafted RFC against the frozen ledger before sign-off, and no production files, gates, or repository scope rules are modified during drafting.
```

*Rationale:* Architect B demonstrated the cleanest editorial conciseness and ledger stewardship across Rounds 3–4 (proactively removing 11 duplicate `DEC-B*` decisions, flagging the R3 opposite-direction consolidation hazard before loss occurred, and keeping architectural agreement, agreed tests, and executed status cleanly separated). Architect A's consolidated RFC clauses from Round 4 §1 and all three Architects' verified tables should serve as primary source input under all three Architects' review. If nominated myself, I consent under the exact same conditions.

---

## 5. Structured Delta Summary

`CONSILIUM-R05-DELTA.json` records **10 decision records** (`DEC-A15 r1` `ACCEPT`, `DEC-A16 r1` `ACCEPT`, `DEC-C15 r2` `REJECT` with authoritative `withdraws` into `DEC-A02`/`DEC-C02`/`DEC-A03`, and re-confirmed `ACCEPT` on `DEC-C01/C05/C07/C09/C10/C13/C16 r3`) plus all **12 `OPEN` objection dispositions** (all `RESOLVED`, explicitly asserting (i)+(ii) and not (iii)), leaving zero unanimous/closed decisions touched, and is validated against this exact response file via `decision_delta.py`.
