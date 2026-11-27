# Build & Codegen Infrastructure — RFC Editor, draft revision 3 (reassigned)

You are **Architect A — GPT**. By explicit owner authorization the **RFC Editor
role has been reassigned from Architect B (Claude) to you**. This is an
editorial and administrative reassignment only: it changes no architectural
authority, voting right, decision, approval, objection, architect identity or the
unanimity requirement.

Draft revision 2 was delivered to final approval. Architect C (Gemini) approved
it; Architects A (you) and B (Claude) returned `REQUEST_CHANGES`. Architect B
began drafting revision 3 but exhausted its subscription window mid-task. Its
partial draft was preserved and must **not** be discarded or rewritten from
scratch. Your job is to finish it.

Your worktree is `/mnt/data/projects/warcraft-1-decompile-wt/cons-a`. The editor
package is in `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/gpt/editor-v3-inbox/`.

## 1. Inputs (all hashed in `MANIFEST.json` and `SHA256SUMS`)

1. `00-CANONICAL-LEDGER-v2.json` — 124977 bytes — SHA-256 `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` — Canonical decision ledger, byte-identical to revision 2; the Editor must preserve it byte-for-byte
2. `01-DRAFT-V2-MANIFEST.json` — 1145 bytes — SHA-256 `b1664adf1d6867e047e4918cdaf766657e786c6af452355c994c65e6e0fa19e4` — Frozen revision 2 manifest with per-file SHA-256
3. `02-DRAFT-V2-SHA256SUMS.txt` — 618 bytes — SHA-256 `32ef582e10f52539defa6208ce11cb3c563c8dcaca1d889cff95283453c6369c` — Frozen revision 2 SHA256SUMS
4. `03-ORIGINAL-ASSIGNMENT-prompt-claude-v3.md` — 2486 bytes — SHA-256 `67a410d7520b856c065942f4edbbd60bbd4226130bc879fc1ef349b7542892d8` — The original revision 3 editor assignment given to Architect B
5. `04-FAILED-ATTEMPT-01/meta.json` — 1971 bytes — SHA-256 `16cff982aceea4e9d38df728f891639ab458e0d8e1c5f89c186df03b7a1789f0` — Metadata of Architect B's failed revision 3 invocation (provider rate limit)
6. `04-FAILED-ATTEMPT-01/response.md` — 60 bytes — SHA-256 `94e0e5418fece95538e6b6d167878c2d9875af795abf4eceead0a51daa5f3dae` — Provider error text recorded for the failed invocation
7. `05-PARTIAL-DRAFT-MANIFEST.json` — 1173 bytes — SHA-256 `0120d15f4e28c5ccd83e56df44fe774ec335f57cd5443bb87109fda24f1cf544` — Hashes of Architect B's preserved partial revision 3 (seven files)
8. `approval/claude-response.md` — 8842 bytes — SHA-256 `f8790e3a09a99854be6fbb55b5a97beb5dc3baf3cab48d363df0ef041f83d6a2` — Exact revision-2 approval response of Architect B — Claude
9. `approval/gemini-response.md` — 11869 bytes — SHA-256 `b34162ed18a96baf23c409ea4dd1139821fe7a82d6e7110fa45b185a586da1b1` — Exact revision-2 approval response of Architect C — Gemini
10. `approval/gpt-response.md` — 6221 bytes — SHA-256 `fd4dfc29b6f2e7f37de7c2266d8f5c610fd6ebfa7f52b9465ea671074fd91354` — Exact revision-2 approval response of Architect A — GPT
11. `partial-v3/decision-ledger.json` — 124977 bytes — SHA-256 `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` — Architect B's preserved partial revision 3 file: decision-ledger.json (read-only)
12. `partial-v3/decision-rationale.md` — 81941 bytes — SHA-256 `324afad1dd2d3f9f576ddb054f8a7f0138b9bc15d79639b70e538edaf9c8f380` — Architect B's preserved partial revision 3 file: decision-rationale.md (read-only)
13. `partial-v3/deferred-questions.md` — 9657 bytes — SHA-256 `68b934c778a373fa2c88502c45d9c38cd6c4b6c15c021f3bc9b6a6d2801d6319` — Architect B's preserved partial revision 3 file: deferred-questions.md (read-only)
14. `partial-v3/editorial-notes.md` — 7169 bytes — SHA-256 `ac3200c6737a0e0423c57e67590a92201102560bfcfa4e7328231c3208fe0376` — Architect B's preserved partial revision 3 file: editorial-notes.md (read-only)
15. `partial-v3/experimental-interpretation.md` — 16764 bytes — SHA-256 `924e032d599e09946508a5077747b67ca7d1bd5ac66890bfe6f52bbd76a9bb39` — Architect B's preserved partial revision 3 file: experimental-interpretation.md (read-only)
16. `partial-v3/implementation-roadmap.md` — 16094 bytes — SHA-256 `3c4a25566d3d0f85b82b3d81b1ac9d64f85c80543daa71508ea51a992f648723` — Architect B's preserved partial revision 3 file: implementation-roadmap.md (read-only)
17. `partial-v3/revised-rfc.md` — 65446 bytes — SHA-256 `6f6ee07329c5c3a20ee06a4fb71503a079f7bd10b1ad6610f9c37b6c3ff2fa3e` — Architect B's preserved partial revision 3 file: revised-rfc.md (read-only)
18. `v2/decision-ledger.json` — 124977 bytes — SHA-256 `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a` — Frozen revision 2 file: decision-ledger.json
19. `v2/decision-rationale.md` — 78906 bytes — SHA-256 `db5884df73d1fddc39a4ec80a70be622e024c27bbfdbf3fbcf0356badb390576` — Frozen revision 2 file: decision-rationale.md
20. `v2/deferred-questions.md` — 9215 bytes — SHA-256 `97604eb6f17cbb025633edb500e1ec464a3b49d2845314699051ea1320bd8a18` — Frozen revision 2 file: deferred-questions.md
21. `v2/editorial-notes.md` — 6164 bytes — SHA-256 `a024c73a866a99671979cff2843e0f5ca3c69265d4d21d628821dd1cc8667ac8` — Frozen revision 2 file: editorial-notes.md
22. `v2/experimental-interpretation.md` — 13019 bytes — SHA-256 `81388b77cdaf1a9e16eff7cd8764333d5a470c4813f0950f8b448a6eb797b398` — Frozen revision 2 file: experimental-interpretation.md
23. `v2/implementation-roadmap.md` — 13545 bytes — SHA-256 `e6470713736f5ed0ba629a7862dc1ea5b9aea06b4c808265ab5c03e16dd8f929` — Frozen revision 2 file: implementation-roadmap.md
24. `v2/revised-rfc.md` — 57870 bytes — SHA-256 `44490954fff4d66c005b8996d80d74e980ca1207f06b00289df8dda772cabeef` — Frozen revision 2 file: revised-rfc.md

## 2. Task — finish the partial revision 3

1. Compare the partial revision 3 (`partial-v3/`) against frozen revision 2 (`v2/`).
2. Determine which required changes have already been implemented.
3. Verify those changes against the original review requests and the pinned evidence.
4. Complete only the missing or incorrect changes.
5. Check that no unrelated architectural or normative change was introduced.
6. Preserve the canonical decision ledger byte-for-byte
   (`00-CANONICAL-LEDGER-v2.json`, SHA-256
   `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`).
7. Produce a complete revision 3 candidate.
8. Produce a precise `CHANGELOG-v3.md`.
9. Produce an editor report with hashes and validation results.

Work on your own copy: create `CONSILIUM-DRAFT-V3/` in your worktree as a copy of
`partial-v3/`, then edit that copy. Do not modify the package files in the inbox
and do not modify Architect B's preserved partial draft.

## 3. Required changes to address

The **authoritative** texts are the two `REQUEST_CHANGES` responses in
`approval/`. The summaries below are navigational aids only, not substitutes.

### Architect A (your previous required changes)

- **A1.** Bind authority-bearing verification and integration receipts to exact
  artifacts and verified context at issuance, not only on reuse. Preserve the
  independent Group B path.
- **A2.** Extend paired-state release obligations to existing T4 execution routes
  that bypass `cemu.run_pair`, including the twelve documented hand-written
  bypass nodes and declared mutable host dependencies. Correct overstatements
  about the experimental checkpoint coverage.
- **A3.** Reconcile the normative-text rule with carried-forward baseline
  verification invariants, B3 constraints, transform admission conditions and
  existing production gates. Clearly distinguish already verified E7 production
  changes from future mechanisms.
- **A4.** Correct the experimental claims concerning E1–E4, E7–E8 and DQ-04,
  including the precise scope of demonstrated results and observed CONST padding
  variability.

### Architect B (previous required changes)

- **C-1.** Correct the E0 raw-OMF parser description. In particular, distinguish
  actual persistent cross-record THREAD handling from the parser's genuine
  admission limitations and the separate E4/E5 transformation defects.
- **C-2.** Correct stale ledger identity, package filenames and evidence revision
  references.
- **C-3.** Correct the provenance of the agreed acceptance criteria,
  distinguishing decision text from the r04 acceptance-criteria tables and the
  pinned baseline RFC.

Optional editorial changes from the partial draft may be retained only when they
are accurate, useful, non-substantive and explicitly documented. Do not seek new
optional improvements.

## 4. Constraints

Do **not**:

- rewrite the architecture;
- change any proposition, decision revision, decision status or objection status;
- introduce new implementation requirements beyond accepted decisions and
  requested gate clarifications;
- remove or weaken existing verification gates;
- introduce new experiments;
- run broad production verification;
- change production code;
- optimize the document merely for stylistic preference.

Factual corrections must be checked against the relevant pinned evidence. If a
requested change cannot be implemented without altering an accepted architectural
decision, report that specific conflict; do not silently resolve it. Reuse the
already completed work and read only the targeted evidence needed; do not reread
the entire historical transcript.

## 5. Outputs

1. The revised files in `CONSILIUM-DRAFT-V3/`:
   `revised-rfc.md`, `implementation-roadmap.md`,
   `experimental-interpretation.md`, `decision-rationale.md`,
   `decision-ledger.json`, `deferred-questions.md`, `editorial-notes.md`.
2. `CONSILIUM-DRAFT-V3/CHANGELOG-v3.md` — one entry per requested change: the id
   (A1–A4, C-1–C-3, optional), the file and section touched, the before/after
   substance in one or two sentences, and your verification of any factual claim.
3. `CONSILIUM-EDITOR-REPORT-V3.md` — the new file hashes, the change-log summary,
   the exact ledger identity, which files are unchanged from revision 2 (with
   their revision-2 hashes), and your validation results.

## 6. Response of record

Return the editor report as your final message. Do not modify production code,
`main`, branches or shared files. Do not run `make verify`.

Begin now.
