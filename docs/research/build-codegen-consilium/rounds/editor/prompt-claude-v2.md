# Build & Codegen Infrastructure — RFC Editor, draft revision 2

You are **Architect B — Claude**, serving as **RFC Editor**. You produced draft
revision 1 of the package. The Secretary has now ruled on the five items you
reported in §3 of your drafting report, and the ledger was rebuilt.

Your worktree is `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`. Your
existing draft is at `CONSILIUM-DRAFT/`.

## 1. What changed since revision 1

Read `04-CORRECTION-NOTE.md` in your inbox: it states, item by item, what was
corrected and confirms that the comparison of the pre-fix and post-fix ledgers
found identical status, revision and proposition hash for all 54 decisions.

Corrected inputs are in the same inbox:

```text
00-CANONICAL-LEDGER-v2.json      (the corrected canonical contract)
01-DECISION-LEDGER-FULL-v2.json  (corrected full ledger)
02-OBJECTION-LEDGER-v2.json      (corrected objection ledger)
03-EV-2.json, 03-EV-3.json       (evidence revisions cited by the decisions)
```

## 2. What to produce

**Draft revision 2**, differing from revision 1 only in:

1. `CONSILIUM-DRAFT/decision-ledger.json` — replace with a byte-identical copy
   of `00-CANONICAL-LEDGER-v2.json`;
2. `CONSILIUM-DRAFT/revised-rfc.md` §12 (integrity notes) — record the rulings
   instead of the open inconsistencies; if your generator embeds the ledger
   hash, regenerate the file so the embedded hash is correct;
3. `CONSILIUM-EDITOR-REPORT.md` §3 — same.

Every other file, and every normative clause, must remain unchanged. If
regenerating would change any normative text, stop and report instead of
drafting.

Then update `CONSILIUM-EDITOR-REPORT.md` with the new hashes of the files you
changed and a one-paragraph statement of exactly what differs from revision 1.

## 3. Response of record

Write the updated report to `CONSILIUM-EDITOR-REPORT.md` and return it as your
final message. Do not modify production code, `main`, branches or shared files.

Begin now.
