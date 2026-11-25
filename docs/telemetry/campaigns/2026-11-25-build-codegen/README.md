# Campaign Telemetry: Build & Codegen Infrastructure (E0–E8)

- **Campaign ID:** `2026-11-25-build-codegen`
- **Campaign Branch:** `research/build-codegen-experiments`
- **RFC Commit:** `6f319ac8ff780bb45ff028d006216016fc932a13` (`architecture/build-codegen-rfc`)
- **Main Baseline Commit:** `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da` (`main`)

## Telemetry Discovery & Metric Provenance (Section 12.1)

| Role | Provider | Harness | Model / Effort | Token Usage | Reasoning Tokens | Reasoning Time | Quota Windows |
|---|---|---|---|---|---|---|---|
| Manager / Analyst | Google | `antigravity-cli` | Gemini 4 Neon (High) | `exact` (from `transcript.jsonl` if present, else `unavailable`) | `exact`/`unavailable` | `unavailable` | `unavailable` (not logged locally) |
| Developer | OpenAI | `codex-cli 0.172.0` | `gpt-6.1-sol` (`high`) | `exact` (rollout JSONL + `codex exec --json`) | `exact` (`reasoning_output_tokens`) | `unavailable` (not exposed by Codex) | `exact` (5h `primary` & 7d `secondary` in rollout `rate_limits`) |
| Reviewer | OpenAI | `codex-cli 0.172.0` | `gpt-6.1-sol` (`high`) | `exact` (rollout JSONL + `codex exec --json`) | `exact` (`reasoning_output_tokens`) | `unavailable` (not exposed by Codex) | `exact` (5h `primary` & 7d `secondary` in rollout `rate_limits`) |

- Per-process wall-clock durations use `time.monotonic()` (`exact`).
- Verification lock waits and execution durations are captured by `experiments/build_codegen/_infra/verify_lock.py` (`exact`).
- Concurrency safety: each worktree / agent session writes an atomic per-event JSON file to `/mnt/data/projects/warcraft-1-decompile-campaign-state/streams/` and the Manager consolidates them into tracked artifacts here.
- Raw harness JSONL logs live outside Git under `/mnt/data/projects/warcraft-1-decompile-campaign-state/raw_logs/`.
