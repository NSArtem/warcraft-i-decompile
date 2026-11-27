# Build & Codegen Infrastructure — RFC Editor Drafting

You are **Architect B — Claude**, serving as **RFC Editor**. The Editor is an administrative authorship role held by an Architect. It carries no additional architectural authority.

The consilium has asked you to prepare the revised RFC package. Your job is to preserve the agreed decision ledger exactly, not to resolve outstanding disputes, not to introduce new architecture, and not to silently narrow or broaden any accepted decision.

Your worktree is `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`. The drafting package is in your private inbox:

1. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/00-CANONICAL-LEDGER.json` — 123172 bytes — SHA-256 `71d7a98829a2aab81d44a0c1563f74719650261aebe751c9e8e0ac1291edd027` — Canonical contract: one entry per decision and objection with status, exact proposition, hash and conditions
2. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/00a-DECISION-LEDGER-FULL.json` — 1369113 bytes — SHA-256 `05997573082b9e9292cba0d4b7702b49f1f69452b3246bdd0c9df3f1c9c5a166` — Full rebuilt decision ledger (schema 2) with every admitted proposition, revision, position and stale record
3. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/01-OBJECTION-LEDGER.json` — 343463 bytes — SHA-256 `4628a3998f024b47a5a92f29b5577cd9e9beb5cfdf37fd6c5c8a949275cba114` — Objection ledger with explicit dispositions and closure eligibility
4. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/02-EVIDENCE-MANIFEST.json` — 21862 bytes — SHA-256 `c2d059d32c50e0eccc3bb5c4b66a56fe27e7ee040b965547225abafe24c4c7eb` — Evidence manifest pinned by the campaign
5. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/03-r07-gpt-response.md` — 832 bytes — SHA-256 `40a8652f639293cc3908f57aa9141263c9c01c4044686ea316e8760813487769` — Frozen r07 response of Architect A — GPT
6. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/04-r07-claude-response.md` — 1723 bytes — SHA-256 `077a2144c55c831b07a5ddb7e62275a5e5f0e1638a35e1ff10e7351604fc23f4` — Frozen r07 response of Architect B — Claude
7. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/05-r07-gemini-response.md` — 1838 bytes — SHA-256 `d104da3569d6d25d3183fb4da8aa1fba5d12df36081c0f94b6c822f89c3b2e32` — Frozen r07 response of Architect C — Gemini
8. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/06-r06-gpt-response.md` — 2344 bytes — SHA-256 `45808e6294a7d3dc3aa09aec1a63f1a515a9faded88f7e4951d073010c143f20` — Frozen r06 response of Architect A — GPT
9. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/07-r06-claude-response.md` — 6788 bytes — SHA-256 `c9690660d0a9bf0477efdab28c80400371617178d2143ddea3b8fca868171124` — Frozen r06 response of Architect B — Claude
10. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/08-r06-gemini-response.md` — 6681 bytes — SHA-256 `e89c75f7876f327572f5a9cbde0161b114952a8f5d9045e041286dd392f0febf` — Frozen r06 response of Architect C — Gemini
11. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/09-r05-gpt-response.md` — 9451 bytes — SHA-256 `7a102c2aa9625563741bdcdce33908ff6e224ad1b966369b2a360e0ec9222bf5` — Frozen r05 response of Architect A — GPT
12. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/10-r05-claude-response.md` — 13535 bytes — SHA-256 `cfacd8fa16d7a5f7969289285fe6ee4349212225909f58bd2a0c5b98d6c8ee11` — Frozen r05 response of Architect B — Claude
13. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/11-r05-gemini-response.md` — 15303 bytes — SHA-256 `43784d48ee708cc887d30b25175d018e9ebaf694c7f5bae2a3a540a3522b4ddf` — Frozen r05 response of Architect C — Gemini
14. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/12-r04-gpt-response.md` — 49510 bytes — SHA-256 `e6a4affde01c9c2a2ca21807be25a7b730b56297cc2a419afd9c34f6ee955a45` — Frozen r04 response of Architect A — GPT
15. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/13-r04-claude-response.md` — 18805 bytes — SHA-256 `a9c0099e502a6de81a030967f26ebea09f8e1cf74ccf842c292a1a352623ec83` — Frozen r04 response of Architect B — Claude
16. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/14-r04-gemini-response.md` — 62408 bytes — SHA-256 `a6f2f9d7989c78aafcf5d0a41c7d532ecbc9a053440ae7f2db1d2d4bc2798a09` — Frozen r04 response of Architect C — Gemini
17. `/mnt/data/projects/warcraft-1-decompile-consilium/runtime/claude/editor-inbox/15-RFC-BASELINE.md` — 118979 bytes — SHA-256 `1f30d5e2bb6f651467424952ede3affd179c1c99d16cca848180ccbd81299a90` — Existing RFC at 6f319ac8ff780bb45ff028d006216016fc932a13:docs/architecture/rfc-build-codegen-infrastructure.md (unmodified baseline)

Read `00-CANONICAL-LEDGER.json`, `02-EVIDENCE-MANIFEST.json`, the closing
rounds' responses and the RFC baseline completely before drafting. The two full
ledgers (`00a-…`, `01-…`) are large reference files: query them (for example with
`jq` or `grep`) for the records you cite instead of paging through them whole. If
a read is truncated, continue from the reported offset.

---

## 1. Required outputs

Write the following files to:

```text
/mnt/data/projects/warcraft-1-decompile-wt/cons-b/CONSILIUM-DRAFT/
```

1. `revised-rfc.md` — the revised Build & Codegen Infrastructure RFC.
2. `experimental-interpretation.md` — the E0–E8 interpretation appendix, distinguishing experimental facts, architectural interpretations, engineering decisions, untested assumptions and open questions.
3. `implementation-roadmap.md` — dependency-ordered production roadmap with entry/exit criteria, verification prerequisites, regression risk, reversibility and deferred work.
4. `deferred-questions.md` — every explicitly deferred question, with its boundary and the condition that would reopen it. A deferred question must not silently influence accepted production decisions.
5. `decision-rationale.md` — rationale for each agreed decision, with its stable identifier and proposition revision.
6. `decision-ledger.json` — an exact copy of the consilium decision ledger delivered in the package. Do not edit it.

You may also add an `editorial-notes.md` listing editorial changes that do not alter architectural meaning or obligations.

---

## 2. Drafting rules

- Preserve every UNANIMOUS decision at its current revision. Do not reword a proposition in a way that changes its obligations.
- For CONDITIONAL decisions, state the exact conditions; do not present them as unconditional consensus.
- For DISPUTED or NEEDS_EXPERIMENT decisions, state the competing positions and the unresolved objection identifiers. Do not pick a winner. If the ledger records an explicit unanimous deferral, present it as deferred with its boundary.
- Preserve the objection history. Do not close an objection unless an Architect explicitly closed it in a frozen response.
- Preserve the existing acceptance and verification gates. Do not weaken them.
- Tie every roadmap stage to actual M2 progress, verified blockers and the ledger's dependencies.
- Distinguish Warcraft-specific, Watcom/OMF/LE-specific and general principles.
- Do not add a general-purpose framework merely because a larger future project might use it.
- Cite evidence as `path@sha` or a stable artifact identifier. Do not invent evidence.
- Do not modify production code, `main`, Git branches, the primary checkout, shared originals, or other campaigns' worktrees.

If the ledger is internally inconsistent, stop and report the inconsistency rather than resolving it yourself.

---

## 3. Operational rules and deadline

- **Launch time (UTC):** `2026-11-27T20:55:35Z`
- **Hard wall-clock limit:** `5400` seconds (90 minutes), hard cutoff `2026-11-27T22:25:35Z`.
- **Wrap-up checkpoint:** `2026-11-27T22:07:35Z` (80% of the budget).
- Do not use `sleep` polling loops. Do not run `make verify` or the full test suite.
- If you cannot finish, deliver the partial package and list what is incomplete. Never fabricate a decision or an approval.

### Response of record

Write the complete drafting report (what you produced, what remains, and any ledger inconsistency) to:

```text
/mnt/data/projects/warcraft-1-decompile-wt/cons-b/CONSILIUM-EDITOR-REPORT.md
```

and return it as your final message. The draft files themselves are the deliverable; the Secretary will hash and deliver them to all three Architects for final approval.

Begin now.
