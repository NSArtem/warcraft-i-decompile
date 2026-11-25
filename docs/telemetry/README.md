# Agent Telemetry Archive

Sanitized, reproducible resource-usage audits for completed multi-provider engineering campaigns in `NSArtem/warcraft-i-decompile`.

## Directory Structure

```text
docs/telemetry/
  README.md
  campaigns/
    <YYYY-MM-DD>-<campaign-slug>/
      report.md           # Human-readable audit report and ROI analysis
      usage.json          # Normalized machine-readable schema (v1.0)
      sessions.csv        # One row per campaign agent session
      timeline.csv        # Chronologically ordered campaign events (UTC)
      quota_snapshots.csv # Timestamped provider quota observations (UTC)
```

## Measurement Conventions

1. **Timestamps**: All timestamps are recorded in UTC (`YYYY-MM-DDTHH:MM:SSZ`).
2. **Evidence Quality Classifications**:
   - `EXACT`: Directly recorded in local provider telemetry logs, SQLite databases, or Git metadata.
   - `DERIVED`: Calculated deterministically from recorded values (for example, elapsed minus merged tool-execution intervals, or payback ratios).
   - `ESTIMATED`: Inferred from incomplete evidence (never fabricated).
   - `UNAVAILABLE`: Insufficient local evidence; encoded as `null` in JSON and empty string in CSV.
3. **Provider-Specific Token Semantics**:
   - **Google (Antigravity / Gemini)**: `input_tokens` excludes `cache_read_tokens`. Normalized `total_prompt_tokens = input_tokens + cache_read_tokens`. `output_tokens` includes `reasoning_tokens` (thinking tokens).
   - **Anthropic (Claude CLI)**: `input_tokens` excludes `cache_creation_tokens` and `cache_read_tokens`. Normalized `total_prompt_tokens = input_tokens + cache_creation_tokens + cache_read_tokens`. `output_tokens` includes `reasoning_tokens` (thinking tokens).
   - **OpenAI (Codex CLI)**: `input_tokens` includes `cached_input_tokens` (`total_prompt_tokens == input_tokens`). `output_tokens` includes `reasoning_tokens`.
   - Cross-provider aggregates always use normalized `total_prompt_tokens` and `output_tokens` rather than summing raw `input_tokens`.
4. **Quota Accounting**:
   - Quota percentages are never combined across providers and never inferred from token counts.
   - Percentage changes are expressed in percentage points (`pp`) and account for rolling-window resets.
   - Unrelated account activity outside campaign boundaries is excluded.
5. **Privacy & Sanitization**:
   - No raw transcripts, prompts, responses, credentials, emails, absolute home-directory paths, or raw provider session UUIDs are stored here.
   - Sessions are correlated via stable campaign-local aliases (for example, `agy-orch-01`, `claude-dev-01`, `codex-review-01`).
