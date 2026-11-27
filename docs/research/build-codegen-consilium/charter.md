# Architecture Consilium — Charter

## 1. Purpose

This consilium reconsiders the existing Build & Codegen Infrastructure RFC in
light of the completed E0–E8 experimental campaign and the subsequent
production work (E7 compiler presets, M2 mechanical cleanup). It is an
architectural discussion, not an implementation campaign.

The consilium's objective is to produce:

1. A technically rigorous interpretation of E0–E8.
2. A revised architecture.
3. An updated RFC.
4. A dependency-aware production implementation roadmap.
5. Explicitly documented remaining uncertainties and necessary experiments.
6. Unanimous approval of substantive architectural decisions, where achievable.

The architecture must support:

- Completion of M2 under existing verification guarantees.
- Subsequent M3 development.
- Progressive reconstruction of original compilation units.
- Stronger verification and placement infrastructure.
- Reliable large-scale automated reconstruction.
- Potential application to substantially larger reverse-engineering projects.

## 2. Participants and authority

The three Architects are equal in authority.

| Participant | Intended model | Reasoning effort | Harness |
|---|---|---|---|
| Architect A — GPT | GPT-6.2 Sol (`gpt-6.2-sol`) | High | Codex CLI |
| Architect B — Claude | Claude Opus 5.5 (`claude-opus-5-5`) | High | Claude Code CLI |
| Architect C — Gemini | Gemini 4 Neon (`gemini-4-neon-high`) | High (encoded in model id) | AGY CLI |

The Secretary is DeepSeek V4.1 Flash through OpenCode2, provider OpenCode Go
(`opencode-go/deepseek-v4.1-flash`). The Secretary has no vote and does not
participate in the architectural discussion.

Verified harness versions at campaign start:

- `codex-cli 0.172.0`
- Claude Code `2.1.332`
- `agy 1.5.17`

Model identifiers were verified from local metadata and/or an actual session:
Codex `~/.codex/models_cache.json`; Claude result `modelUsage` canonical id
`claude-opus-5-5`; AGY `init.model` event `gemini-4-neon-high`.

## 3. Secretary responsibilities and prohibitions

The Secretary is responsible exclusively for administrative, procedural and
technical orchestration:

- Creating and maintaining isolated worktrees.
- Launching and maintaining Architect sessions.
- Delivering discussion messages without alteration.
- Preserving complete discussion records with content hashes.
- Collecting telemetry and accounting for resource budgets.
- Maintaining the decision and objection ledgers mechanically.
- Committing discussion artifacts atomically.
- Preserving resumable campaign state.

The Secretary must not:

- Formulate architectural recommendations.
- Interpret experimental results on behalf of Architects.
- Resolve substantive disagreements.
- Rank arguments by correctness.
- Select a winning architectural position.
- Summarize arguments instead of delivering their complete original text.
- Rewrite an Architect's arguments.
- Make architectural decisions to save time or tokens.
- Announce consensus without explicit agreement from all three Architects.
- Substitute another model for an Architect.
- Declare a decision accepted from silence, tone, or partial similarity.

## 4. Scope and prohibitions for Architects

Architects may inspect code, execute read-only analysis, reproduce experimental
evidence, and perform narrowly scoped disposable technical probes.

Architects must not implement production changes. They must not:

- Modify `main` or merge the consilium branch into `main`.
- Alter verification gates or project scope.
- Modify the primary checkout at `/mnt/data/projects/warcraft-1-decompile`.
- Modify shared original binaries, compiler installations, or other campaigns'
  worktrees.
- Create, switch, merge or delete branches outside their own worktree.
- Run repository-wide cleanup or garbage collection.
- Terminate unrelated Wine, compiler, CLI or orchestration processes.

All Architect activity occurs in the assigned worktree and private runtime
directories described in the protocol.

## 5. Decision rule

There is no majority voting. Agreement by two Architects does not overrule the
third. A substantive objection must be addressed by evidence, architectural
revision, or explicit unanimous agreement to defer the issue.

Consensus means agreement on substantive decisions, not identical personal
preferences or writing style.

## 6. Terminal states

### CONSENSUS_ACHIEVED

All three Architects approve the same substantive RFC and roadmap revision.
Required artifacts: complete transcript, decision ledger, objection history,
experimental interpretation, revised RFC, implementation roadmap, explicitly
deferred questions, three matching final approvals, resource report, and
reproduction instructions for technical probes.

### PAUSED_AWAITING_OWNER

Used when authorized resources are exhausted or another agreed stopping
condition prevents further discussion. Required artifacts: complete discussion
history, latest agreed decisions, latest position of every Architect,
outstanding disagreements, exact propositions under dispute, supporting
evidence, latest RFC draft, progress and convergence metrics, resource
consumption, native session IDs, worktree paths, pending messages, exact next
round, and resume instructions.

## 7. Governance

- The finish line, verification gates and project scope are fixed by the owner.
- The Secretary does not decide whether an unfinished consilium should receive
  additional resources.
- In the absence of consensus, the consilium produces a pause handoff rather
  than a forced resolution.
