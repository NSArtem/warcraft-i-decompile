```text
Draft revision: 2
RFC_SHA256: 44490954fff4d66c005b8996d80d74e980ca1207f06b00289df8dda772cabeef
ROADMAP_SHA256: e6470713736f5ed0ba629a7862dc1ea5b9aea06b4c808265ab5c03e16dd8f929
Verdict: REQUEST_CHANGES
```

# Final approval review — Architect B (Claude, `claude-opus-5-5`)

**Disclosure.** I am also the RFC Editor who produced this draft. I reviewed it as an Architect against the ledger, the frozen discussion and the evidence, and I hold my own text to the same standard as anyone else's.

**Verdict in short.** Every change I request is factual or editorial. **None touches a decision, a proposition, a revision, a status, an objection disposition or a gate. I have no architectural disagreement with this revision.** I nevertheless cannot approve it as it stands, for two reasons:

- It contains one factual statement about the E0 prototype that the code contradicts.
- It contains one statement about the identity of the package's own ledger that is no longer true.

The consilium's output should not carry known false statements, least of all in the appendix whose purpose is to separate facts from interpretation.

## 1. Verification performed

- **File identity.** All seven files in `approval-inbox/` match their stated SHA-256 values. They are byte-identical to `CONSILIUM-DRAFT/` revision 2 (`cmp`).
- **Ledger identity.** `draft-decision-ledger.json` is `dc6bda93…`, the v2 canonical ledger. Its contents: 38 UNANIMOUS, 4 UNANIMOUS_REJECTED and 12 WITHDRAWN_SUPERSEDED decisions; 64 RESOLVED and 2 WITHDRAWN objections. No objection is open, and no position carries a condition.
- **Exact text (checked by script against the delivered ledger).**
  - For every one of the 54 decisions, the proposition hashes to its recorded SHA-256.
  - Each of the 42 non-withdrawn decisions appears verbatim in `draft-revised-rfc.md`, under a header with the correct id, revision, status and hash.
  - All 54 appear verbatim, with correct headers, in `draft-decision-rationale.md`.
- **Positions.** My recorded position is ACCEPT on every UNANIMOUS decision and REJECT on every UNANIMOUS_REJECTED decision, consistent with RFC §13.
- **EV-3 figures.** RFC §1/§2 and the roadmap use 912/1010 DONE, 98 not DONE, 539 T3 in 534 C files, 2505/11/5, gate statuses, and 0 of 202 fresh E7 records. All agree with `editor-v2-inbox/03-EV-3.json` (`3d3dfa43…`).
- **E0 prototype claim.** I checked it against `tools/wc1/omf.py@e6150b856106ae113bb023300b956fff318da7ef`, which the E0 prototype uses through `from wc1 import … omf` in `experiments/build_codegen/e0/matcher_proto.py@e6150b8`. See finding C-1.

No probe, test or production verification was run.

## 2. Answers to the review questions

1. **Agreed decisions preserved at their current revision: yes.** This was mechanically verified (§1).
2. **Objections silently resolved, omitted or altered: no.** The draft closes nothing itself. RFC §11 reports 64 RESOLVED and 2 WITHDRAWN as the ledger records them. The two closures with residual questions (OBJ-A24, OBJ-B22) are tied to DQ-11 and DQ-04.
3. **Internal consistency with the ledger: yes for all normative and architectural content.** The inconsistencies are factual and editorial (C-1 to C-3 below).
4. **Gates preserved and not weakened: yes.** `make verify`, `make goal`, the tiers and the classification rules are unchanged (RFC §10 and §8). The baseline invariants are carried forward, and every new mechanism is marked "not executed".
5. **Dependency ordering tied to M2 progress and blockers: yes.**
   - Roadmap S0 → S1 follows DEC-A02/DEC-A03 before B1/B2.
   - The Group B exception (S1.3) follows DEC-A13.
   - S2 is post-M2 or on demand, per DEC-B08, DEC-C08 and DEC-A08.
   - Each stage names its need: either a demonstrated defect or a named blocker (DEC-A15).
6. **Uncertainties and required experiments stated: yes.** See DQ-01 to DQ-17, the U/Q lines in the appendix, and the (iii) column.
7. **Claims presented as fact without support: yes, one** (C-1). There is also a provenance overstatement (C-3) and a stale identity statement (C-2).

## 3. Required changes

The changes are listed in order of importance. None changes normative text.

**C-1 — `experimental-interpretation.md`, section "E0 — Matcher soundness", bullet **I**, line 41.**

- **Current text:** "The prototype does not admit raw OMF strictly: bounds, nonzero checksums, single MODEND, persistent THREAD and explicit FRAME are not enforced."
- **Why it is wrong:** the "persistent THREAD" item is contradicted by the code.
  - `tools/wc1/omf.py@e6150b8` `parse_module` initialises the THREAD table once per module (lines 105–106) and updates it in every FIXUPP record (lines 240–248). Thread state therefore *does* persist across records.
  - The cross-record THREAD defects recorded by the consilium belong to the E4 extractor (Probe 5a, DEC-C08) and to E5's rewriting, not to the matcher's parser.
- **What the same code does support:**
  - no checksum verification;
  - silent truncation instead of record-bound checks (`body = buf[p+3:p+3+rlen-1]`);
  - a return at the first MODEND, with trailing bytes ignored by `parse_object`;
  - unknown records ignored instead of an allow-list (line 289 comment);
  - FRAME method and index parsed but not kept in `Fixup` (lines 256–263; the `Fixup` record at line 288 has no frame field, see the `Fixup` class at lines 25–31).
- **Required change:** replace the sentence with: "The prototype parses raw OMF through `tools/wc1/omf.py@e6150b8`, which does not verify checksums, does not bound-check records (it truncates silently), stops at the first MODEND without rejecting trailing content, ignores unknown records instead of using an allow-list, and does not retain explicit FRAME encodings in its fixups; it does keep THREAD state across records within a module."

**C-2 — `editorial-notes.md` §2 (lines 14 and 17) and §7 (line 55).**

- **Line 14:** it says `decision-ledger.json` is "a byte-identical copy of `00-CANONICAL-LEDGER.json`". Since revision 2 it is a copy of `00-CANONICAL-LEDGER-v2.json` (`dc6bda93…`). RFC header line 6 states the identity correctly, so the package now contradicts itself on the identity of its normative source.
  - **Required change:** replace the file name with `00-CANONICAL-LEDGER-v2.json`.
- **Line 17:** replace `00a-DECISION-LEDGER-FULL.json` and `01-OBJECTION-LEDGER.json` with `01-DECISION-LEDGER-FULL-v2.json` and `02-OBJECTION-LEDGER-v2.json`.
- **Line 55:** add "EV-2 and EV-3 are included in the package as `03-EV-2.json` and `03-EV-3.json` (see RFC §12 item 4)".
- **`revised-rfc.md` header, line 11:** make the same addition, so that the header does not imply EV-3 is available only through quotations.

**C-3 — `revised-rfc.md` §10, table header (line 482).**

- **Current text:** "(ii) Agreed acceptance test (from the decision texts)".
- **Why it is wrong:** several listed tests are not in the decision texts. They come from the acceptance-criteria tables that all three Architects published in r04:
  - `12-r04-gpt-response.md` §6, `13-r04-claude-response.md` §8 and `14-r04-gemini-response.md` §7;
  - and, for the corrupted-table negative, from baseline RFC §16.
  - Examples: the three comparator mutants; the wrong-base, out-of-extent and overlap negatives for B1; the carry, host-write, allocator and stub controls; the prefixed-rel8 and MissionDefeat B2 cases.

  The content is right; the stated provenance is not. A reader could otherwise take these tests to be ledger decision text.
- **Required change:** change the header to "(ii) Agreed acceptance test (from the decision texts, the r04 acceptance-criteria tables of all three Architects, and baseline RFC §16)".
- **Roadmap, optional:** for the same reason, the sentence in `implementation-roadmap.md` §"How the roadmap is ordered", "Every 'exit criterion' below is an agreed future acceptance test (ii)", may cite the same sources. I do **not** require this; with C-3 applied to the RFC, the roadmap's reference to "(ii)" is unambiguous. If it is left untouched, ROADMAP_SHA256 stays `e6470713…`.

**Optional, not required.** The "objections referencing it" lists in `decision-rationale.md` were computed from the v1 objection ledger, as RFC §12 item 3 discloses. Regenerating them from `02-OBJECTION-LEDGER-v2.json` would make them complete. They are non-normative and disclosed, so I do not require it.

## 4. What I am not disputing

I have no substantive architectural disagreement with any proposition in the ledger or with any architectural or roadmap content of revision 2, so this verdict is not `DISPUTED`. After C-1 to C-3 are applied in a revision 3, I expect to approve it if nothing else changes. That revision needs fresh approvals from all three Architects; this verdict does not carry over.

I do not claim consensus.