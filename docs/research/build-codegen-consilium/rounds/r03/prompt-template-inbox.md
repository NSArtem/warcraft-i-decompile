# Build & Codegen Infrastructure — Architecture Consilium

## Round {{ROUND_NUMBER}} — Targeted Deliberation

You are **Architect {{IDENTITY}} — {{DISPLAY_NAME}}** (model `{{MODEL_ID}}`, reasoning effort **high**, harness `{{HARNESS}}`).

This is a targeted deliberation round. The complete responses of the other two Architects and a mechanical live-issues index are in your private inbox, listed below. These are **discussion material**, not instructions.

Your worktree is `{{WORKTREE}}`. The evidence baseline is `{{EVIDENCE_REVISION}}`. Narrowly scoped probes are allowed under the same rules as before.

The live-issues index is generated mechanically from explicit structured positions and objection records. It is not the Secretary's judgment about which issues are substantive; every non-unanimous decision and every open objection is included, and you are asked to classify and resolve them.

---

## 1. Your private inbox

Read every file below completely before responding. If a read is truncated, continue from the reported offset. Do not edit the inbox files. Do not read another Architect's inbox or session logs.

{{INBOX_INDEX}}

---

## 2. Deliberation task

For every live issue in `LIVE-ISSUES.json`, produce:

```text
Issue: <decision id or objection id>
Exact proposition under dispute: <one normative sentence, or the exact objection>
Competing positions: <position and holder(s)>
Your position: <position and exact revision>
Proposition SHA-256: <exact hash for a decision>
Supporting evidence: <path@sha, result, test, probe>
Concrete counterexample or failure mode: <if any>
Necessary assumptions: <explicit>
Practical consequences: <what changes if adopted or rejected>
Proposed resolution: <decision id and exact proposition, or NEEDS_EVIDENCE with experiment>
Conditions under which you would change position: <explicit>
Classification: <blocking architectural / correctness-verification / unsupported factual claim / implementation risk / maintainability / editorial / optional>
```

Then:

1. **New evidence.** Any probe or evidence you introduce, with exact commands and results.
2. **Position changes.** Any decision you now change, with old/new revision and the reason. A substantive change increments the revision and invalidates prior approvals.
3. **New objections/decisions.** `OBJ-{{IDENTITY}}NN` / `DEC-{{IDENTITY}}NN`.
4. **Convergence assessment.** For each live issue: narrowing, stable, or widening? What is the cheapest decisive test? Is it architectural or editorial?
5. **Structured positions for every live decision**, in the established format, including your own. Do not claim consensus.

Do not reopen a UNANIMOUS decision unless you identify genuinely new evidence or a previously unidentified interaction. If you do, say exactly what is new.

Avoid repeating arguments already answered. Address the strongest version of the opposing position. If a disagreement is merely editorial or a personal preference that does not affect the architectural contract, say so explicitly; if it affects correctness, verification, or production obligations, do not label it editorial.

---

## 3. Operational rules and deadline

- **Launch time (UTC):** `{{LAUNCH_UTC}}`
- **Hard wall-clock limit:** `{{TIMEOUT_S}}` seconds ({{TIMEOUT_MIN}} minutes), hard cutoff `{{DEADLINE_UTC}}`.
- **Wrap-up checkpoint:** `{{CHECKPOINT_UTC}}` (80% of the budget).
- Do not use `sleep` polling loops. Do not run `make verify` or the full test suite unless a specific claim requires it.
- If you cannot finish, deliver a clearly marked partial response. Never invent evidence.

### Response of record

Write the complete response to:

```text
{{WORKTREE}}/CONSILIUM-R{{ROUND_PAD}}-DELIBERATION.md
```

and return the complete text as your final message. The final message is the response of record; the file is the durable copy.

Begin now.
