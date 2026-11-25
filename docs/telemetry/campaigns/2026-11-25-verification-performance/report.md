# Retrospective Telemetry Audit: Verification Performance Optimization Campaign

- **Campaign ID**: `2026-11-25-verification-performance`
- **Repository**: `NSArtem/warcraft-i-decompile`
- **Git Boundaries**: baseline `5677541`, implementation `5677541..4a21a87` (**33** atomic commits), merge `eebe586`, handoff `8b00a78` / `52b53aa`
- **Campaign Window (UTC)**: `2026-11-24T22:17:21Z` to `2026-11-25T04:54:05Z`

---

## 1. Executive Summary

Across **7 implementation/review iterations**, a multi-provider agent team (Google Antigravity orchestrator, Anthropic Claude Opus 5.5 developer for Iterations 1–4 and aborted Iteration 5 attempt, and OpenAI Codex GPT-6.2 Sol for all 7 independent review rounds plus developer Iterations 5–7) reduced `make verify` wall-clock time from **192.56 s to 52.56 s median (3.66× speedup, -140.0 s/run)** and verification user CPU from **2,233.54 s to 349.64 s (-84.3%)**, while expanding passing tests from **1,719 to 2,238** with Build A **IDENTICAL**.

| Metric | Value | Evidence Quality |
|---|---:|---|
| Total campaign elapsed wall time | **6h 36m 44s** (`23804 s`) | `EXACT` |
| Confirmed infrastructure/quota interruption | **1h 10m 54s** (`4254 s`) | `EXACT` |
| Net campaign wall time (excl. interruption) | **5h 25m 50s** (`19550 s`) | `DERIVED` |
| Non-overlapping active model API time | **2h 01m 54s** (`7313.9 s`) | `DERIVED` |
| Total campaign agent sessions | **29** (1 orchestrator, 6 wrappers, 8 developer, 8 main reviewer, 6 guardian) | `EXACT` |
| Total model requests | **616** (0 context compactions) | `EXACT` |
| Total normalized prompt tokens | **75,449,797** (95.4% cache-read) | `EXACT` |
| Total output tokens (incl. reasoning) | **579,190** (reasoning: **229,722**) | `EXACT` |
| OpenAI Codex quota consumed | **+56.0 pp** (5h window) / **+9.0 pp** (7d window) | `EXACT` |
| Anthropic Claude quota consumed | 5h window reached **100%** at `02:55:04Z` (reset `03:50:00Z`); weekly numeric % unavailable | `EXACT` (5h) / `UNAVAILABLE` (7d) |
| Google Antigravity quota consumed | Historical quota % not logged locally | `UNAVAILABLE` |
| Verification payback point (wall time) | **170.0** runs (total wall) / **139.6** runs (net wall) / **52.2** runs (active API time) | `DERIVED` |

---

## 2. Subscription Quota Consumption

Provider quota percentages are reported independently per provider and never combined. Full timestamped observations are in [`quota_snapshots.csv`](quota_snapshots.csv).

### 2.1 OpenAI (Codex CLI — `codex` pool)

- **Pre-campaign last observation** (`2026-11-24T17:09:03Z`, end of prior Wave 4A Run 2): 5h window **10.0%** (reset `2026-11-24T20:58:04Z`), 7d window **57.0%** (reset `2026-11-29T06:40:07Z`) (`EXACT`).
- **Campaign start** (`2026-11-25T00:52:53Z`, `codex-review-01` start): 5h window **0.0%** (reset after `20:58:04Z`), 7d window **60.0%** (`EXACT`).
  - *Attribution note*: The `+3.0 pp` 7d increase between `17:09:03Z` and `00:52:53Z` occurred with 0 local Codex threads in that interval and is **not** attributed to this campaign.
- **Reviewer-only phase (Iterations 1–4, `00:52:53Z` to `02:49:23Z`)**:
  - 5h window: `0.0% -> 27.0%` (**+27.0 pp**) (`EXACT`).
  - 7d window: `60.0% -> 64.0%` (**+4.0 pp**) (`EXACT`).
- **Combined Developer + Reviewer phase (Iterations 5–7, `04:07:25Z` to `04:48:01Z`)**:
  - 5h window: `27.0% -> 56.0%` (**+29.0 pp**) (`EXACT`).
  - 7d window: `64.0% -> 69.0%` (**+5.0 pp**) (`EXACT`).
- **Total campaign-attributable OpenAI consumption**: **+56.0 pp** on the 5h window and **+9.0 pp** on the 7d window (all within the same 5h window resetting `2026-11-25T05:52:49Z` and 7d window resetting `2026-11-29T06:40:07Z`; confirmed unchanged at `69.0%` 7d after the 5h reset at `07:42:09Z`).

### 2.2 Anthropic (Claude CLI — `claude_subscription` pool)

- **5-hour rolling window**: Starting percentage is `UNAVAILABLE` locally. At **`2026-11-25T02:55:04Z`**, `claude-dev-05-aborted` hit **100%** (`EXACT`) with a synthetic limit message stating the window reset at `2026-11-25T03:50:00Z` (`07:50 +04:00`).
- **7-day weekly window**: Exact pre- and post-campaign percentages are `UNAVAILABLE` in local Claude CLI logs. At `2026-11-25T04:06:06Z`, the user qualitatively observed that weekly quota was nearly exhausted and directed switching the Developer role to Codex.
- **Hypothetical API-equivalent cost** (from Claude CLI `cost-state` records using API list pricing; **not** actual subscription expenditure): **$19.8836** across the 5 campaign developer sessions (`claude-dev-01` $7.4904, `claude-dev-02` $4.7588, `claude-dev-03` $4.0291, `claude-dev-04` $2.3531, `claude-dev-05-aborted` $1.2522).

### 2.3 Google (Antigravity — Gemini 4 pools)

- Historical Google/Antigravity quota percentages and reset timestamps are **`UNAVAILABLE`** in local logs, state files, and SQLite databases. Exact per-request token usage and latencies were recovered from `transcript.jsonl` and conversation SQLite `gen_metadata` records.

---

## 3. Token Usage by Provider, Model, and Role

### Accounting Semantics Preserved

- **Google (Antigravity)**: `input_tokens` excludes `cache_read_tokens`; `total_prompt_tokens = input_tokens + cache_read_tokens`; `output_tokens` includes `reasoning_tokens` (thinking).
- **Anthropic (Claude CLI)**: `input_tokens` excludes `cache_creation_tokens` and `cache_read_tokens`; `total_prompt_tokens = input_tokens + cache_creation_tokens + cache_read_tokens`; `output_tokens` includes `reasoning_tokens` (thinking).
- **OpenAI (Codex CLI)**: `input_tokens` includes `cached_input_tokens` (`total_prompt_tokens == input_tokens`); `output_tokens` includes `reasoning_tokens`.

### 3.1 By Provider

| Provider | Sessions | Requests | Tool Calls | Normalized Prompt Tokens | Cache Read / Cached | Cache Creation | Output Tokens | Reasoning Tokens | Active API Time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Google | 7 | 123 | 211 | 23,105,787 | 21,813,936 | — | 135,133 | 62,397 | 26m 08s (`EXACT`) |
| Anthropic | 5 | 176 | 227 | 30,658,446 | 29,730,521 | 927,573 | 325,771 | 118,086 | 46m 07s (`EXACT`) |
| OpenAI | 17 | 317 | 262 | 21,685,564 | 20,401,920 | 0 | 118,286 | 49,239 | 1h 05m 59s (`DERIVED`) |
| **Total (Normalized)** | **29** | **616** | **700** | **75,449,797** | **71,946,377** | — | **579,190** | **229,722** | **2h 01m 54s** (non-overlapping) |

### 3.2 By Model

| Model | Provider | Sessions | Requests | Normalized Prompt Tokens | Output Tokens | Reasoning Tokens |
|---|---|---:|---:|---:|---:|---:|
| `Gemini 4 Neon` (High) | Google | 1 | 93 | 22,767,854 | 128,085 | 60,567 |
| `Gemini 4 Hydrogen` (High, `codex-session` wrappers) | Google | 6 | 30 | 337,933 | 7,048 | 1,830 |
| `claude-opus-5-5` (High) | Anthropic | 5 | 176 | 30,658,446 | 325,771 | 118,086 |
| `gpt-6.2-sol` (High) | OpenAI | 11 | 272 | 20,709,643 | 112,771 | 46,526 |
| `codex-auto-review` (Low, guardian subagent) | OpenAI | 6 | 45 | 975,921 | 5,515 | 2,713 |

### 3.3 By Agent Role (Separating Codex Developer vs. Reviewer)

| Role | Sessions | Requests | Elapsed Sum | Active API Time | Normalized Prompt Tokens | Output Tokens | Reasoning Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| Analyst / Orchestrator (Gemini 4 Neon) | 1 | 93 | 6h 36m 44s* | 24m 43s | 22,767,854 | 128,085 | 60,567 |
| Orchestrator Wrappers (Gemini 4 Hydrogen, Iter 5–7) | 6 | 30 | 38m 48s* | 1m 24s | 337,933 | 7,048 | 1,830 |
| Developer — Anthropic (Iter 1–4 + aborted Iter 5) | 5 | 176 | 3h 35m 51s | 46m 07s | 30,658,446 | 325,771 | 118,086 |
| Developer — OpenAI (Iter 5–7) | 3 | 124 | 26m 28s | 16m 59s | 9,200,221 | 38,575 | 17,948 |
| Reviewer — OpenAI Main (`gpt-6.2-sol`, 7 rounds + 1 retry) | 8 | 148 | 35m 46s | 32m 40s | 11,509,422 | 74,196 | 28,578 |
| Reviewer — OpenAI Guardian (`codex-auto-review`) | 6 | 45 | 16m 19s* | 16m 19s* | 975,921 | 5,515 | 2,713 |

*\*Overlapping parent/child elapsed times (orchestrator, wrappers, and guardian subagents) are never summed into campaign wall time.*

*Note on adjacent human session*: During the infrastructure pause (`2026-11-25T03:56:48Z`–`04:02:43Z`), after Anthropic's 5h window reset at `03:50:00Z`, the user ran one interactive Claude session (`claude-infra-cleanup`, 12 requests, 944,239 prompt tokens, 13,810 output tokens, 5m 55s) to analyze `/mnt/data` usage and free space. It is recorded under `adjacent_human_sessions` in `usage.json` and excluded from campaign agent totals.

---

## 4. Campaign Execution Timeline

All 48 timestamped milestones are stored in [`timeline.csv`](timeline.csv). Key phases (UTC):

1. **Initial Investigation & Baseline (`2026-11-24T22:17:21Z` – `22:32:09Z`, 14m 48s)**: Orchestrator profiled verification stages, ran baseline `make verify` (`22:27:43Z`–`22:30:46Z`, 183 s), and drafted the Iteration 1 assignment.
2. **Initial Approval Wait (`22:32:09Z` – `22:44:30Z`, 12m 21s)**: Human approval wait before the first unsandboxed `claude` developer task started.
3. **Phase A — Claude Developer + Codex Reviewer (`22:44:30Z` – `2026-11-25T02:55:04Z`, 4h 10m 34s)**:
   - Iterations 1–4 produced **28** accepted commits (`f0e886c..8d3f654`), each followed by an independent Codex review round (`REJECT` on Rounds 1–4).
   - `/mnt/data` hit 100% capacity (`4.1 MiB` free at `02:24:39Z`, `1.6 MiB` free by `02:43:58Z`). Review Round 4 attempt 1 (`codex-review-04a`) exited with code 1 after 101.1 s and was retried as `codex-review-04b`.
   - Claude Iteration 5 attempt 1 (`claude-dev-05-aborted`) started at `02:50:26Z` and hit Anthropic's 5-hour limit at `02:55:04Z` (resets `03:50:00Z`).
4. **Confirmed Infrastructure & Quota Interruption (`02:55:12Z` – `04:06:06Z`, 1h 10m 54s / 4,254 s)**:
   - Orchestrator paused citing dual blockers (Claude 5h limit + `/mnt/data` 100% full).
   - User freed disk space (assisted by `claude-infra-cleanup`, `03:56:48Z`–`04:02:43Z`) and resumed the orchestrator at `04:06:06Z` with instructions to switch the Developer role to Codex GPT-6.2 Sol via `codex-session` subagents.
5. **Phase B — Codex Developer + Codex Reviewer (`04:07:09Z` – `04:48:12Z`, 41m 03s)**:
   - Iterations 5–7 produced the final **5** hardening commits (`4696eb8..4a21a87`), culminating in Review Round 7 **`APPROVE` (0 Must Fix, 0 Should Fix, 0 Optional)** at `04:48:01Z`.
6. **Merge, Post-Merge Verification & Handoff (`04:48:28Z` – `04:54:05Z`, 5m 37s)**:
   - Merged `feature/verification-performance` at `eebe586` (`04:48:28Z`), ran 3× post-merge `make verify` + stage/pytest profiling (`04:48:53Z`–`04:52:25Z`), committed handoff `8b00a78` / `52b53aa` (`04:53:56Z`), and delivered final summary (`04:54:05Z`).

---

## 5. Iteration-Level Breakdown

> **Important methodological caveat**: Claude (Iterations 1–4) and Codex (Iterations 5–7) performed fundamentally different engineering work at different stages of the campaign (major architectural rewrites and 28 commits vs. targeted late-stage hardening and 5 commits). These figures are **not** a controlled model benchmark.

### 5.1 By Iteration

| Iter | Accepted Commits | Dev Provider | Dev Elapsed | Dev Prompt Tokens | Dev Output | Rev Elapsed (Main) | Rev Prompt Tokens (Incl. Guardian) | Rev Output | Verdict |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | Anthropic | 2h 07m 16s | 15,888,241 | 98,762 | 5m 19s | 1,921,048 | 11,919 | REJECT (2M/3S/1O) |
| 2 | 8 | Anthropic | 37m 35s | 7,140,119 | 76,586 | 5m 59s | 2,519,470 | 14,273 | REJECT (2M/4S/2O) |
| 3 | 7 | Anthropic | 30m 10s | 4,794,563 | 78,079 | 7m 10s | 2,266,391 | 14,498 | REJECT (2M/1S/5O) |
| 4 | 3 | Anthropic | 16m 13s | 2,358,278 | 46,148 | 6m 44s | 2,257,644 | 15,283 | REJECT (2M/2S/3O; 1 failed retry) |
| 5 | 2 | Anthropic (aborted) -> OpenAI | 22m 17s | 5,999,759 | 48,444 | 3m 58s | 1,102,289 | 9,336 | REJECT (1M/1S/3O) |
| 6 | 2 | OpenAI | 6m 27s | 2,471,918 | 12,895 | 4m 07s | 1,672,668 | 8,706 | REJECT (1M/1S/3O) |
| 7 | 1 | OpenAI | 2m 22s | 1,205,789 | 3,432 | 2m 30s | 745,833 | 5,696 | APPROVE (0M/0S/0O) |

- **Multi-session iterations**:
  - **Review Round 4**: Required 2 main sessions (`codex-review-04a` failed exit 1 under disk exhaustion; retried as `codex-review-04b`).
  - **Iteration 5 Developer**: Required 2 sessions (`claude-dev-05-aborted` hit Anthropic 5h limit after 278.1 s with 0 commits; re-executed on Codex as `codex-dev-05`).
- **Review overhead**: Independent review (including `codex-auto-review` guardian subagents) accounted for **16.5%** of total normalized prompt tokens (12,485,343), **13.8%** of total output tokens (79,711), and **31.3%** of all model requests (193/616).
- **Per accepted commit (33 commits)**: **2,286,357.5** prompt tokens, **17,551.2** output tokens, **18.67** model requests.
- **Compactions & restarts**: **0** context compactions across all 29 sessions; **2** aborted/failed sessions requiring retry (`codex-review-04a`, `claude-dev-05-aborted`).

### 5.2 Per-Session Ledger (29 Campaign Sessions)

| Alias | Iter | Role | Provider | Model | Effort | Start (UTC) | End (UTC) | Elapsed | Input (raw) | Cached | Output | Reasoning | Reqs | Outcome |
|---|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `agy-orch-01` | all | analyst_orchestrator | google | Gemini 4 Neon | high | 2026-11-24T22:17:21Z | 2026-11-25T04:54:05Z | 6h 36m 44s | 1,162,259 | 21,605,595 | 128,085 | 60,567 | 93 | COMPLETED (33 commits merged at eebe586, handoff 52b53aa) |
| `claude-dev-01` | 1 | developer | anthropic | claude-opus-5-5 | high | 2026-11-24T22:44:30Z | 2026-11-25T00:51:45Z | 2h 07m 16s | 150 | 15,588,481 | 98,762 | 31,362 | 75 | COMPLETED (10 commits) |
| `codex-review-01` | 1 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T00:52:43Z | 2026-11-25T00:58:02Z | 5m 19s | 1,921,048 | 1,791,488 | 11,919 | 4,493 | 20 | REJECT (2 Must Fix, 3 Should Fix, 1 Optional) |
| `claude-dev-02` | 2 | developer | anthropic | claude-opus-5-5 | high | 2026-11-25T01:00:58Z | 2026-11-25T01:38:33Z | 37m 35s | 80 | 6,909,435 | 76,586 | 25,611 | 40 | COMPLETED (8 commits) |
| `codex-review-02` | 2 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T01:39:19Z | 2026-11-25T01:45:18Z | 5m 59s | 2,519,470 | 2,366,080 | 14,273 | 5,070 | 25 | REJECT (2 Must Fix, 4 Should Fix, 2 Optional) |
| `claude-dev-03` | 3 | developer | anthropic | claude-opus-5-5 | high | 2026-11-25T01:46:24Z | 2026-11-25T02:16:34Z | 30m 10s | 62 | 4,601,125 | 78,079 | 33,026 | 31 | COMPLETED (7 commits) |
| `codex-review-03` | 3 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T02:17:24Z | 2026-11-25T02:24:34Z | 7m 10s | 2,176,975 | 2,061,696 | 13,951 | 6,811 | 25 | REJECT (2 Must Fix, 1 Should Fix, 5 Optional) |
| `codex-guardian-03` | 3 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T02:20:03Z | 2026-11-25T02:22:46Z | 2m 43s | 89,416 | 61,568 | 547 | 350 | 3 | COMPLETED (auto-review subagent for codex-review-03) |
| `claude-dev-04` | 4 | developer | anthropic | claude-opus-5-5 | high | 2026-11-25T02:25:28Z | 2026-11-25T02:41:41Z | 16m 13s | 46 | 2,235,370 | 46,148 | 14,925 | 23 | COMPLETED (3 commits) |
| `codex-review-04a` | 4 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T02:42:11Z | 2026-11-25T02:43:52Z | 1m 41s | 610,724 | 516,992 | 3,244 | 1,118 | 10 | FAILED (exit 1; retried as codex-review-04b) |
| `codex-guardian-04a` | 4 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T02:43:06Z | 2026-11-25T02:43:11Z | 5.2s | 20,023 | 5,888 | 260 | 197 | 1 | COMPLETED (auto-review subagent for codex-review-04a) |
| `codex-review-04b` | 4 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T02:44:20Z | 2026-11-25T02:49:23Z | 5m 03s | 1,322,548 | 1,233,664 | 10,526 | 3,867 | 19 | REJECT (2 Must Fix, 2 Should Fix, 3 Optional) |
| `codex-guardian-04b` | 4 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T02:44:32Z | 2026-11-25T02:49:04Z | 4m 32s | 304,349 | 250,112 | 1,253 | 437 | 13 | COMPLETED (auto-review subagent for codex-review-04b) |
| `claude-dev-05-aborted` | 5 | developer | anthropic | claude-opus-5-5 | high | 2026-11-25T02:50:26Z | 2026-11-25T02:55:04Z | 4m 38s | 14 | 396,110 | 26,196 | 13,162 | 7 | ABORTED (5h rate limit hit at 02:55:04Z; 0 commits) |
| `agy-wrap-dev-05` | 5 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:07:09Z | 2026-11-25T04:25:13Z | 18m 04s | 29,279 | 27,000 | 1,414 | 260 | 5 | COMPLETED (invoked codex-dev-05) |
| `codex-dev-05` | 5 | developer | openai | gpt-6.2-sol | high | 2026-11-25T04:07:25Z | 2026-11-25T04:25:05Z | 17m 39s | 5,522,514 | 5,399,424 | 22,248 | 10,635 | 68 | COMPLETED (2 commits) |
| `agy-wrap-rev-05` | 5 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:25:52Z | 2026-11-25T04:30:04Z | 4m 12s | 20,085 | 37,837 | 1,603 | 498 | 5 | COMPLETED (invoked codex-review-05) |
| `codex-review-05` | 5 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T04:25:59Z | 2026-11-25T04:29:57Z | 3m 58s | 896,228 | 814,592 | 8,139 | 2,859 | 14 | REJECT (1 Must Fix, 1 Should Fix, 3 Optional) |
| `codex-guardian-05` | 5 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T04:26:09Z | 2026-11-25T04:29:32Z | 3m 23s | 206,061 | 168,704 | 1,197 | 560 | 10 | COMPLETED (auto-review subagent for codex-review-05) |
| `agy-wrap-dev-06` | 6 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:30:51Z | 2026-11-25T04:37:35Z | 6m 44s | 19,974 | 35,978 | 1,056 | 354 | 5 | COMPLETED (invoked codex-dev-06) |
| `codex-dev-06` | 6 | developer | openai | gpt-6.2-sol | high | 2026-11-25T04:31:00Z | 2026-11-25T04:37:26Z | 6m 27s | 2,471,918 | 2,384,512 | 12,895 | 6,862 | 33 | COMPLETED (2 commits) |
| `agy-wrap-rev-06` | 6 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:37:48Z | 2026-11-25T04:42:11Z | 4m 23s | 20,316 | 36,456 | 1,270 | 249 | 5 | COMPLETED (invoked codex-review-06) |
| `codex-review-06` | 6 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T04:37:54Z | 2026-11-25T04:42:01Z | 4m 07s | 1,487,946 | 1,405,056 | 7,542 | 3,247 | 23 | REJECT (1 Must Fix, 1 Should Fix, 3 Optional) |
| `codex-guardian-06` | 6 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T04:38:11Z | 2026-11-25T04:41:44Z | 3m 33s | 184,722 | 153,472 | 1,164 | 625 | 9 | COMPLETED (auto-review subagent for codex-review-06) |
| `agy-wrap-dev-07` | 7 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:42:34Z | 2026-11-25T04:45:13Z | 2m 39s | 20,050 | 35,299 | 805 | 255 | 5 | COMPLETED (invoked codex-dev-07) |
| `codex-dev-07` | 7 | developer | openai | gpt-6.2-sol | high | 2026-11-25T04:42:43Z | 2026-11-25T04:45:05Z | 2m 22s | 1,205,789 | 1,142,784 | 3,432 | 451 | 23 | COMPLETED (1 commit) |
| `agy-wrap-rev-07` | 7 | orchestrator_wrapper | google | Gemini 4 Hydrogen | high | 2026-11-25T04:45:26Z | 2026-11-25T04:48:12Z | 2m 46s | 19,888 | 35,771 | 900 | 214 | 5 | COMPLETED (invoked codex-review-07) |
| `codex-review-07` | 7 | reviewer | openai | gpt-6.2-sol | high | 2026-11-25T04:45:31Z | 2026-11-25T04:48:01Z | 2m 30s | 574,483 | 498,432 | 4,602 | 1,113 | 12 | APPROVE (0 Must Fix, 0 Should Fix, 0 Optional) |
| `codex-guardian-07` | 7 | reviewer_guardian | openai | codex-auto-review | low | 2026-11-25T04:45:41Z | 2026-11-25T04:47:45Z | 2m 04s | 171,350 | 147,456 | 1,094 | 544 | 9 | COMPLETED (auto-review subagent for codex-review-07) |

---

## 6. Infrastructure Interruption and Provider Switch

- **Root causes**: Dual external blockers converged at `2026-11-25T02:55:12Z`:
  1. `/mnt/data` (1.4 TiB partition) reached 100% usage (`4.1 MiB` free at `02:24:39Z`, dropping to `1.6 MiB` by `02:43:58Z`), forcing Review Rounds 3–4 outputs to `/tmp` and coinciding with `codex-review-04a` exiting with code 1.
  2. Anthropic's 5-hour subscription window hit 100% during `claude-dev-05-aborted` (`02:55:04Z`, resetting `03:50:00Z`), and the user observed Anthropic weekly quota was nearly exhausted.
- **Confirmed downtime**: **4,254 s (70.9 min / 1h 10m 54s)** from `02:55:12Z` to `04:06:06Z` (17.9% of total campaign wall time).
- **Before vs. after provider switch**:
  - **Before switch (Iterations 1–4 + aborted Iter 5)**: 28 commits; Anthropic Developer consumed 30,658,446 prompt tokens / 325,771 output tokens (176 reqs, 3h 35m 51s elapsed); OpenAI Reviewer consumed +27.0 pp (5h) / +4.0 pp (7d).
  - **After switch (Iterations 5–7)**: 5 commits; OpenAI Developer consumed 9,200,221 prompt tokens / 38,575 output tokens (124 reqs, 26m 28s elapsed); OpenAI combined Dev + Reviewer consumed +29.0 pp (5h) / +5.0 pp (7d); Google `Gemini 4 Hydrogen` `codex-session` wrappers added 30 requests (337,933 prompt tokens, 7,048 output tokens, 84.3 s active API time).

---

## 7. Engineering Return on Investment

| Verification Metric | Baseline (`5677541`) | Post-Merge (`eebe586`) | Delta / Speedup |
|---|---:|---:|---:|
| Full `make verify` wall time | 192.56 s | **52.56 s** (median) | **-140.00 s/run (3.66×)** |
| Full `pytest -n auto` wall time | 166.81 s | **40.11 s** (median) | **-126.70 s/run (4.16×)** |
| Verification user CPU time | 2,233.54 s | **349.64 s** (median) | **-1,883.90 s/run (-84.3%)** |
| Passing tests | 1,719 | **2,238** | **+519 regression tests** |
| Build A / reconstruction progress | IDENTICAL / 510 T3 | **IDENTICAL / 510 T3** | **Unchanged** |

### Payback & Projected Savings (`DERIVED`)

- **Payback point (total campaign elapsed wall time, 23,804 s)**: **170.0 verifications**.
- **Payback point (net wall time excl. 4,254 s interruption, 19,550 s)**: **139.6 verifications**.
- **Payback point (non-overlapping active model API time, 7,313.9 s)**: **52.2 verifications**.

| Subsequent `make verify` Runs | Wall-Clock Time Saved | User CPU Time Saved |
|---:|---:|---:|
| 100 runs | **3.89 h** | **52.33 h** |
| 500 runs | **19.44 h** | **261.65 h** |
| 1,000 runs | **38.89 h** | **523.31 h** |
| 10,000 runs | **388.89 h** | **5233.06 h** |

---

## 8. Evidence Limitations

1. **Google quota (`UNAVAILABLE`)**: No local Antigravity log or database stores historical Google subscription quota percentages or reset timestamps.
2. **Anthropic weekly quota (`UNAVAILABLE`)**: Local Claude CLI logs record the exact 5-hour limit hit (`100%` at `02:55:04Z`, reset `03:50:00Z`) and exact per-request tokens/durations/hypothetical API cost, but do not log numeric 5-hour starting % or 7-day weekly %.
3. **OpenAI pre-campaign 7d gap**: OpenAI 7d quota moved from `57.0%` (`2026-11-24T17:09:03Z`) to `60.0%` (`2026-11-25T00:52:53Z`) with 0 local Codex threads in between; this `+3.0 pp` is attributed to non-campaign activity and excluded from campaign totals.
4. **OpenAI active API time (`DERIVED`)**: Unlike Antigravity (`gen_metadata` TTFT+stream durations) and Claude (`cost-state.totalAPIDuration`), Codex rollouts do not log explicit per-request API latency; Codex `active_api_s` is derived as `elapsed_s - merged_tool_exec_s` (which includes minor CLI/harness overhead).
5. **Test/benchmark time inside developer sessions**: Claude `cost-state.totalToolDuration` aggregates all tool execution (including `make verify`, pytest, and git commands) without a separate benchmark-only counter; orchestrator-run baseline (`183 s`) and post-merge (`212 s`) verification durations are exact.

---

## 9. Recommendations for Future Campaigns

1. **Preflight disk & quota checks**: Record `df -h` and provider quota status before starting multi-hour campaigns; abort early if target partition free space drops below 5 GiB.
2. **Capture pre/post quota snapshots**: Log Anthropic and Google subscription quota screenshots or status lines at campaign start and end so longitudinal audits have exact weekly deltas across all three providers.
3. **Preserve review artifacts on `/tmp` fallback**: When workspace disk space is constrained, mirror any `/tmp` review logs back into `build/` after space is freed so iteration artifacts remain complete.
4. **Track subagent wrappers explicitly**: When delegating CLI agents through orchestrator wrapper subagents (`codex-session`), include wrapper sessions in telemetry extraction so secondary model usage (e.g., `Gemini 4 Hydrogen`) is never overlooked.
