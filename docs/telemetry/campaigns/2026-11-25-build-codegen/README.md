# Campaign Telemetry Package — `2026-11-25-build-codegen`

Machine-readable and narrative orchestration telemetry for the Build & Codegen Infrastructure experimental campaign (`E0`–`E8`).

## Files
- [`report.md`](report.md) — Section 19 orchestration telemetry report (quotas, tokens, timings, harness transitions, runner hardening before/after, hypotheses H1–H5, cross-campaign comparison).
- [`campaign.json`](campaign.json) — Consolidated campaign metadata, exact Antigravity Manager token usage, aggregate subagent totals, initial/latest quota snapshots, and terminal ledger.
- [`sessions.jsonl`](sessions.jsonl) — Per-session telemetry records for all 36 completed/timed-out subagent invocations (Codex CLI + `opencode2`).
- [`events.jsonl`](events.jsonl) — Chronological stream of manager decisions, session terminations, and serialized `make verify` events.
- [`quota_snapshots.jsonl`](quota_snapshots.jsonl) — 42 timestamped Codex 5h/7d subscription quota snapshots (capturing the `18:10–18:24Z` window rollover).
- [`experiments.csv`](experiments.csv) — Per-experiment (`E0`–`E8`) roll-up of sessions, wall time, tokens, verdicts, and integration commits.
- [`reviews.csv`](reviews.csv) — Per-review-round (`rev-*`) audit log of verdicts, tokens, wall time, and reviewed commit SHAs.
- [`prompts/`](prompts/) — Archived exact prompts dispatched to every Developer and Reviewer session.
- [`summaries/`](summaries/) — Archived final responses / review verdicts from every session.
