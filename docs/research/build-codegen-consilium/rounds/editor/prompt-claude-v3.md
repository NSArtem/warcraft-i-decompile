# Build & Codegen Infrastructure — RFC Editor, draft revision 3

You are **Architect B — Claude**, serving as **RFC Editor**. Draft revision 2 was
delivered to final approval. Architect C approved it; Architects A and B returned
`REQUEST_CHANGES`.

Your worktree is `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`. Your draft
is at `CONSILIUM-DRAFT/`.

## 1. Inputs

Read both request texts completely. They are in your inbox with their hashes:

1. `00-REQUEST-CHANGES-gpt.md` — Architect A: four numbered required changes.
2. `01-REQUEST-CHANGES-claude.md` — Architect B: C-1, C-2, C-3, plus optional items.
3. `02-APPROVE-gemini.md` — Architect C's approval of revision 2 (context only;
   it does not carry over to revision 3).
4. `03-DRAFT-V2-MANIFEST.json` — the frozen hashes of revision 2.

## 2. Task

Produce **draft revision 3** by applying the two request lists.

Rules:

- Apply every required change that is stated as a required change. Apply optional
  items only where they are purely factual or editorial and clearly improve
  accuracy; say in the report which optional items you applied and which you did
  not, with the reason.
- Do not change any decision, proposition, revision, status, position or objection
  disposition. Do not narrow or weaken any gate. If a requested change would
  require an architectural decision, stop and report instead of making it.
- If the two lists conflict anywhere, stop and report the conflict; do not choose.
- Where a requested change corrects a factual claim, verify the claim against the
  pinned artifacts yourself before changing the text, and record what you checked.
- Keep `decision-ledger.json` byte-identical to `00-CANONICAL-LEDGER-v2.json`
  (hash `dc6bda93ea7f3cf2b1506f481600b12af6a357c3fa9a84beb8208bbb39b4e97a`).

## 3. Outputs

1. The revised files in `CONSILIUM-DRAFT/`.
2. `CONSILIUM-DRAFT/CHANGELOG-v3.md` — one entry per requested change: the id
   (A1–A4, C-1–C-3, optional), the file and section touched, the before/after
   substance in one or two sentences, and your verification of any factual claim.
3. `CONSILIUM-EDITOR-REPORT.md` — updated with the new file hashes, the change
   log summary, and an explicit statement of which files are unchanged from
   revision 2 (with their revision-2 hashes).

## 4. Response of record

Return the updated report as your final message. Do not modify production code,
`main`, branches or shared files. Do not run `make verify`.

Begin now.
