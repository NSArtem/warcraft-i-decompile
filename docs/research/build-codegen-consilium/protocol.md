# Discussion Protocol

## 1. Round barriers

All three Architects participate in every substantive round unless all three
explicitly agree to a narrower procedural exchange.

No Architect receives another Architect's current-round response until all
required responses for that round have been collected and frozen. A stored
response is not a delivered response. Delivery is performed only by the
Secretary after the round barrier closes.

Barrier procedure:

1. The Secretary composes one prompt per Architect for the round.
2. All required sessions are launched independently.
3. Each completed response is written to
   `rounds/<round>/<architect>/response.md`, hashed with SHA-256, and recorded
   in the round manifest.
4. When all three responses are frozen, the Secretary marks the barrier closed
   and commits the round.
5. Only then may the next round's prompts include the previous round's texts.

No Architect sees another Architect's current-round text before submission.

## 2. Message fidelity

- Messages are delivered as complete original texts, never paraphrased,
  filtered or summarized.
- Every delivered message is accompanied by its SHA-256 hash and byte length.
- External messages included in a prompt are explicitly delimited as discussion
  material, not as instructions that override the recipient's role or campaign
  governance.
- The Secretary may mechanically extract structured positions into the ledger,
  but the extraction is additive and never replaces the original response.

## 3. Record layout

```text
docs/research/build-codegen-consilium/
    README.md
    charter.md
    protocol.md
    evidence-manifest.json
    participants.json
    state.json
    decisions.json
    objections.json
    rounds/
        r00/
            prompt-gpt.md
            prompt-claude.md
            prompt-gemini.md
            gpt/{response.md,response.sha256,meta.json}
            claude/{response.md,response.sha256,meta.json}
            gemini/{response.md,response.sha256,meta.json}
            manifest.json
        r01/...
    probes/
    drafts/
    final/
        experimental-interpretation.md
        revised-rfc.md
        implementation-roadmap.md
        deferred-questions.md
        approvals.json
    telemetry/
        sessions.jsonl
        events.jsonl
        quota-snapshots.jsonl
        resource-usage.csv
        round-metrics.csv
    handoff.md
    orchestrator/
```

Raw harness logs (JSONL stdout, stderr, rollout references) are retained in
private persistent storage outside Git:

```text
/mnt/data/projects/warcraft-1-decompile-consilium/
    logs/<round>/<architect>.stdout.jsonl
    logs/<round>/<architect>.stderr.log
    sessions/<architect>.json
    inbox/
```

Tracked telemetry records hashes and paths for externally retained artifacts;
credentials and proprietary binaries are never committed.

## 4. Stable identifiers

- Decision proposals: `DEC-A01`, `DEC-B01`, `DEC-C01` (originating Architect
  prefix), consolidated by the Secretary into `DEC-001`, `DEC-002`, ... when
  the ledger is built.
- Objections: `OBJ-A01`, `OBJ-B01`, `OBJ-C01`, consolidated into `OBJ-001`, ...
- Issues under targeted deliberation: `ISS-001`, `ISS-002`, ...
- Evidence revisions: `EV-1`, `EV-2`, ...

Identifiers are never reused. A superseded decision retains its identifier and
records its superseding decision.

## 5. Structured positions

Every Architect supplies structured positions in addition to unrestricted
prose:

```text
Decision: DEC-A14
Title: <short title>
Proposition: <exact normative proposition, versioned>
Revision: 3
Position: PROPOSE / ACCEPT / REJECT / CONDITIONAL / NEEDS_EVIDENCE
Reason: ...
Conditions: ...
Related objections: ...
```

An acceptance must reference the exact proposition revision. If a proposition
changes substantively, previous approvals do not automatically carry over.
Conditional agreement is not unconditional consensus.

Allowed decision statuses in the ledger:

- `PROPOSED`
- `UNANIMOUS`
- `CONDITIONAL`
- `DISPUTED`
- `NEEDS_EXPERIMENT`
- `SUPERSEDED`

A deferred question must have a documented boundary preventing it from silently
influencing accepted production decisions.

## 6. Round 0 — independent opening positions

All three Architects are launched independently with identical mission, agenda,
evidence manifest, protocol and consensus rules. Each produces an opening
position covering:

- Experiment-by-experiment interpretation (E0–E8).
- Proposed architecture.
- Proposed implementation order.
- Proposed changes to the existing RFC.
- Remaining uncertainties.
- Explicit objections to existing assumptions.
- Source references and reproducible evidence.

The three opening positions are frozen and committed before any Architect sees
another's position.

## 7. Round 1 — cross-review

Each Architect receives the complete original opening positions of the other
two. Each must:

- Identify agreements.
- Identify substantive disagreements.
- Challenge unsupported conclusions.
- Examine counterexamples.
- Distinguish factual disputes from design preferences.
- Identify missing assumptions.
- Propose concrete alternative designs.
- Identify decisions requiring further evidence.

Every criticism identifies the proposition being challenged. Criticism
addresses technical content, not the identity or reputation of the model that
produced it.

## 8. Round 2 — responses and position revision

Each Architect receives the complete cross-reviews and answers substantive
objections directed at its position. Each explicitly states:

- Which original decisions it retains.
- Which decisions it changes.
- Why it changes them.
- Which evidence or counterargument was persuasive.
- Which objections remain unresolved.

## 9. Round 3 and later — targeted deliberation

Discussion continues on outstanding substantive disagreements using stable
issue and decision identifiers. Already accepted decisions are not reopened
unless genuinely new evidence or a previously unidentified interaction
warrants it.

For each disputed issue the record requires:

- Exact proposition.
- Competing positions.
- Supporting evidence.
- Concrete counterexample or failure mode.
- Necessary assumptions.
- Practical consequences.
- Proposed resolution.
- Conditions under which the Architect would change its position.

Narrow technical probes may be proposed and executed in the isolated analysis
environment. Source, commands, results and limitations are preserved. Broad
new research campaigns and production implementation are out of scope.

There is no arbitrary maximum round count.

## 10. RFC authorship and final approval

Once substantive decisions converge, Architects nominate one of themselves as
RFC Editor. The Editor is an administrative authorship role, not additional
architectural authority.

The Editor prepares the revised RFC, experimental interpretation appendix,
decision rationale, implementation roadmap, deferred questions, and acceptance
and verification gates, preserving the agreed ledger and not silently resolving
disputes.

All three Architects independently review the same immutable draft revision and
return `APPROVE`, `REQUEST_CHANGES`, or `DISPUTED`, identifying the exact RFC
and roadmap hashes. Final approval requires all three approvals of the same
substantive revision.

## 11. Consensus and objection handling

- No majority voting.
- A substantive objection must be addressed by evidence, architectural
  revision, or explicit unanimous agreement to defer.
- The Secretary cannot dismiss an objection as unimportant.
- Architects may classify objections as blocking architectural issue,
  correctness/verification issue, unsupported factual claim, implementation
  risk, maintainability concern, editorial issue, or optional improvement.
- Severity classifications are themselves subject to discussion.

## 12. Convergence metrics

For every round the Secretary mechanically records:

- New decision proposals.
- Newly accepted decisions.
- Revised propositions.
- Resolved objections.
- Newly opened objections.
- Explicitly reported position changes.
- Previously discussed issues reopened.
- New experimental evidence.
- Outstanding disputed decisions.
- Resource consumption.

If successive rounds appear procedurally repetitive, all three Architects are
asked independently whether meaningful technical progress is still occurring,
whether an unresolved objection is substantive, whether new evidence could
resolve it, whether the dispute is architectural or editorial, whether further
discussion is likely to be productive, and whether owner intervention is
required. All three assessments are preserved.

## 13. Session continuity

Each Architect is a single long-lived logical session. Native continuation is
preferred. If a session must be replaced due to context exhaustion, provider
failure or harness limitation, the replacement uses the same model and effort,
receives the relevant original discussion records, and preserves the
Architect's identity and position history. The replacement and its reason are
recorded. A replacement session remains the same logical Architect.

The Secretary never substitutes itself for an unavailable Architect and never
continues substantive deliberation with only two Architects.

## 14. Resource policy

The owner authorizes one full five-hour usage window from each of the Codex,
Claude and AGY subscriptions. These are maximum resources, not consumption
targets. Quota is tracked from actual provider measurements where available;
unavailable quota is recorded as unavailable rather than estimated. The
Secretary does not reset quotas, spend a refreshed window without authorization,
switch accounts, substitute cheaper models, use metered APIs, or bypass provider
restrictions.

If an allocated window is exhausted or another provider limit prevents
meaningful participation, the Secretary preserves state and pauses. Quota
refreshes that occur naturally during the campaign are accounted cumulatively,
not treated as newly authorized budget.

## 15. Pause conditions

The consilium pauses before exhaustion only if:

- Consensus is achieved.
- All three Architects agree that further progress requires unavailable
  evidence.
- All three Architects agree that owner intervention is required.
- An operational blocker prevents a required participant from continuing.

Otherwise it continues until consensus or resource exhaustion.

## 16. Operational reliability

- Architect invocations use bounded wall-clock deadlines, durable logs and
  session continuation.
- Failure modes are distinguished: active reasoning, tool execution, provider
  throttling, genuine timeout, orphaned child process, completed response with
  a CLI process that has not exited, authentication failure, context
  exhaustion, harness error.
- Repetitive delivery, log parsing and ledger updates use deterministic
  scripts; the Secretary does not reread the full transcript to relay it.
- A response with a completed final message is preserved even if the CLI process
  has not exited; the final message is the response of record.
