# Build & Codegen Architecture Consilium

Three independent Architects (GPT-6.2 Sol / Claude Opus 5.5 / Gemini 4 Neon,
all at high reasoning effort) reconsider the Build & Codegen Infrastructure RFC
in light of the completed E0–E8 experimental campaign and the subsequent E7 and
M2 production work.

The Secretary (DeepSeek V4.1 Flash, OpenCode Go) provides isolated worktrees,
prompt delivery, complete transcript preservation, telemetry and accounting.
The Secretary has no vote and does not interpret evidence or resolve disputes.

## Baseline

- Consilium branch: `research/build-codegen-consilium`
- Pinned baseline: `research/build-codegen-experiments` @
  `e6150b856106ae113bb023300b956fff318da7ef`
- Production evidence: `main` @ `a21772b8140b4b07012cde8da7da18ad3f6d56b6`
- Evidence manifest revision: `EV-1` (`evidence-manifest.json`)

The primary checkout is used by another orchestration campaign and is never
modified, switched or treated as a stable baseline.

## Layout

| Path | Contents |
|---|---|
| `charter.md` | Mission, participants, authority, prohibitions, terminal states |
| `protocol.md` | Round barriers, message fidelity, ledger rules, consensus, sessions |
| `evidence-manifest.json` | Immutable pinned evidence inventory (`EV-1`) |
| `participants.json` | Verified harness/model identifiers and quota at start |
| `state.json` | Resumable campaign state |
| `decisions.json` / `objections.json` | Structured ledgers |
| `rounds/rNN/` | Prompts, frozen responses, per-round manifests |
| `probes/` | Accepted technical probes with commands and results |
| `drafts/` / `final/` | RFC drafts and final approved artifacts |
| `telemetry/` | Sessions, events, quota snapshots, resource and round metrics |
| `orchestrator/` | Deterministic delivery and telemetry scripts |

Raw harness logs and session state live in private persistent storage at
`/mnt/data/projects/warcraft-1-decompile-consilium/`; tracked telemetry records
their hashes and paths.

## Status

See `state.json` and `handoff.md`. Terminal states are `CONSENSUS_ACHIEVED` and
`PAUSED_AWAITING_OWNER`.

## Reproduction

The orchestrator is deterministic and records exact commands, session IDs,
prompt hashes and raw logs. See `orchestrator/README.md`.
