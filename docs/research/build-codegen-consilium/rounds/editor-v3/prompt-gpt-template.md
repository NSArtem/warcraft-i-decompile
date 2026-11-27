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
package is in `{{RUNTIME_DIR}}/editor-v3-inbox/`.

## 1. Inputs (all hashed in `MANIFEST.json` and `SHA256SUMS`)

{{PACKAGE_INDEX}}

## 2. Task — finish the partial revision 3

1. Compare the partial revision 3 (`partial-v3/`) against frozen revision 2 (`v2/`).
2. Determine which required changes have already been implemented.
3. Verify those changes against the original review requests and the pinned evidence.
4. Complete only the missing or incorrect changes.
5. Check that no unrelated architectural or normative change was introduced.
6. Preserve the canonical decision ledger byte-for-byte
   (`00-CANONICAL-LEDGER-v2.json`, SHA-256
   `{{LEDGER_SHA256}}`).
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
