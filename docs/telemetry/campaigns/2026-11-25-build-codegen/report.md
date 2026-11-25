# Orchestration Telemetry Report: Build & Codegen Infrastructure Campaign (E0–E8)

- **Campaign ID:** `2026-11-25-build-codegen`
- **Repository:** `NSArtem/warcraft-i-decompile`
- **Git Boundaries:** RFC baseline `6f319ac8` (`architecture/build-codegen-rfc`), campaign branch `research/build-codegen-experiments`, terminal integration `9ae6dce5` (`E0`–`E8` all merged `--no-ff`, `0` production diffs)
- **Campaign Window (UTC):** `2026-11-25T17:29:48Z` to `2026-11-25T21:27:15Z` (**3h 57m 27s** = `14,247 s` wall clock)

---

## 1. Executive Telemetry Summary

Across **38 total campaign sessions** (1 Antigravity Manager orchestrator + 36 logged Developer/Reviewer subagents + 1 Manager-killed session `dev-e7-02` halted at ~25 s per user quota directive), the campaign executed, independently reviewed, and integrated all **9 RFC experiments (E0–E8)** in **3h 57m 27s** elapsed wall time, delivering **401/401 passing experimental + infra tests** and a clean serialized global `make verify` (`83.41 s`, `2257 passed`).

| Metric | Value | Provenance |
|---|---:|---|
| Campaign elapsed wall time (`17:29:48Z` – `21:27:15Z`) | **3h 57m 27s** (`14,247 s`) | `EXACT` |
| Sum of subagent wall times (concurrently overlapped across worktrees) | **7h 12m 41s** (`25,961.26 s`) | `EXACT` |
| Effective concurrency speedup (`sum_wall / elapsed_wall`) | **1.82×** | `DERIVED` |
| Serialized global `make verify` runs / duration / lock wait | **1 run**, `83.41 s` (`0.002 s` wait) | `EXACT` |
| Total campaign sessions | **38** (1 Manager, 19 logged Dev + 1 killed Dev `dev-e7-02`, 17 logged Rev) | `EXACT` |
| Total model requests / steps (`178` Manager + `1,181` subagent steps*) | **1,359** | `EXACT` |
| Total tool calls (`340` Manager + `2,220` subagents) | **2,560** | `EXACT` |
| Manager normalized prompt tokens (`Gemini 4 Neon`, High) | **51,690,636** (`98.0%` cache-read: `50,656,013`) | `EXACT` |
| Subagent normalized prompt tokens (Codex + OpenCode Go) | **201,589,605** (`97.9%` cache-read: `197,275,264`) | `EXACT` |
| Combined normalized prompt tokens (Manager + Subagents) | **253,280,241** (`97.9%` cache-read) | `DERIVED` |
| Combined output tokens (`253,868` Manager + `877,427` subagents) | **1,131,295** | `EXACT` |
| Logged subagent reasoning tokens (see semantics below) | **960,208** | `EXACT` |
| OpenAI Codex quota consumed (Window 1: `17:36–18:10Z`) | **+53.0 pp** 5h (`15%→68%`) / **+8.0 pp** 7d (`75%→83%`) | `EXACT` |
| OpenAI Codex quota consumed (Window 2 after reset: `18:24–18:55Z`) | **+95.0 pp** 5h (`0%→95%`) / **+15.0 pp** 7d (`0%→15%`) | `EXACT` |
| OpenCode Go (`deepseek-v4.1-flash`) subscription quota % | Not exposed locally by CLI | `UNAVAILABLE` |
| Google Antigravity (`Gemini 4 Neon`) subscription quota % | Not exposed locally by CLI | `UNAVAILABLE` |
| Independent review rounds / defect catches (`REQUEST_CHANGES` + `TIMED_OUT` with defect) | **17 rounds** across 9 experiments; **8 defects caught** before integration | `EXACT` |

*\*Note on step/turn granularity:* Codex CLI reports 1 outer `turn.completed` per `codex exec` invocation (internal tool loops appear in `tool_calls`), whereas `opencode2` reports 1 `step_finish` per LLM request inside the agent loop. Both are reported transparently without conflating definitions.

---

## 2. Token Accounting Semantics & Breakdown

### Preserved Provider Accounting Semantics
- **Google Antigravity (`transcript.jsonl`, Manager):** `input_tokens` (`1,034,623`) **excludes** `cache_read_tokens` (`50,656,013`); `normalized_prompt_tokens = input_tokens + cache_read_tokens = 51,690,636`. `output_tokens` (`253,868`) includes thinking/reasoning (`reasoning_tokens` not split out in `transcript.jsonl`).
- **OpenAI Codex CLI (`codex-cli 0.172.0`):** `input_tokens` **includes** `cached_input_tokens` (`normalized_prompt_tokens == input_tokens`). `output_tokens` includes `reasoning_tokens`.
- **OpenCode Go (`opencode2 v2.4.1`, `opencode-go/deepseek-v4.1-flash`):** Raw JSONL reports uncached `input` and `cache.read` separately; `run_agent.py` normalizes `input_tokens = input + cache.read` (matching Codex). `reasoning` is reported **separately** from visible `output` tokens (`total_generated_tokens = output_tokens + reasoning_tokens`).

### 2.1 By Provider, Model, Effort & Role

| Provider / Harness | Model & Effort | Role | Sessions (`OK`/`TO`) | Sum Wall (s) | Tool Calls | Normalized Prompt Tokens | Cache-Read % | Output Tokens | Reasoning Tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Google / `antigravity-cli` | `Gemini 4 Neon` (`high`) | Manager | 1 (`1/0`) | 14,247.0* | 340 | 51,690,636 | 98.0% | 253,868 | *(incl. in out)* |
| OpenAI / `codex-cli 0.172.0` | `gpt-6.1-sol` (`high`) | Developer | 8 (`7/1`) | 8,229.1 | 585 | 45,456,929 | 98.3% | 348,903 | 135,152 |
| OpenAI / `codex-cli 0.172.0` | `gpt-6.1-sol` (`high`) | Reviewer | 5 (`5/0`) | 950.1 | 105 | 4,117,071 | 91.4% | 36,060 | 12,353 |
| OpenAI / `codex-cli 0.172.0` | `gpt-6.2-sol` (`medium`) | Developer | 3 (`3/0`) | 1,365.0 | 105 | 7,295,723 | 96.5% | 56,042 | 16,349 |
| OpenAI / `codex-cli 0.172.0` | `gpt-6.2-sol` (`medium`) | Reviewer | 4 (`4/0`) | 595.1 | 76 | 3,324,918 | 92.4% | 19,019 | 3,209 |
| OpenCode Go / `opencode2 v2.4.1` | `deepseek-v4.1-flash` (`default`) | Developer | 8 (`4/4`) | 9,478.8 | 841 | 108,484,768 | 98.5% | 299,253 | 447,541 |
| OpenCode Go / `opencode2 v2.4.1` | `deepseek-v4.1-flash` (`default`) | Reviewer | 8 (`6/2`) | 5,343.1 | 508 | 32,910,196 | 96.8% | 118,150 | 345,604 |
| **Subagent Subtotal** | — | **Dev + Rev** | **36 (`29/7`)**† | **25,961.3** | **2,220** | **201,589,605** | **97.9%** | **877,427** | **960,208** |

*\*Manager wall time overlaps all child sessions and is never added to subagent wall time.*
*†Excludes `dev-e7-02` (`gpt-6.2-sol medium`), killed by Manager ~25 s after launch at `18:46Z` per user Codex quota directive before `run_agent.py` exited to emit a session record; its pre-launch quota snapshot (`84%` 5h / `13%` 7d) and kill decision are logged in `events.jsonl` and `quota_snapshots.jsonl`.*

### 2.2 Per-Experiment Resource Roll-Up (`experiments.csv`)

| Exp | Status | Outcome | Dev / Rev Sessions | Sum Wall (s) | Normalized Prompt Tokens | Output Tokens | Reasoning Tokens | Review Trajectory |
|---|---|---|---:|---:|---:|---:|---:|---|
| **E0** | `COMPLETED` | `CONFIRMED` | 2 / 2 | 1,761.0 | 6,607,594 | 76,025 | 22,974 | `RC` (6 findings) → **`APPROVE`** |
| **E1** | `COMPLETED` | `CONFIRMED` | 2 / 2 | 1,346.5 | 8,884,684 | 54,269 | 17,627 | `RC` (1 path hash) → **`APPROVE`** |
| **E2** | `COMPLETED` | `PARTIALLY_CONFIRMED` | 2 / 2 | 2,140.6 | 15,103,455 | 83,705 | 27,873 | `RC` (3 determinism/path) → **`APPROVE`** |
| **E3** | `COMPLETED` | `PARTIALLY_CONFIRMED` | 1 / 1 | 1,636.0 | 5,910,423 | 45,806 | 68,927 | **`APPROVE`** (1st round!) |
| **E4** | `COMPLETED` | `CONFIRMED` | 2 / 1 | 3,134.7 | 33,490,928 | 116,351 | 175,803 | **`APPROVE`** (1st round!) |
| **E5** | `COMPLETED` | `CONFIRMED` | 2 / 2 | 3,943.5 | 22,735,038 | 100,718 | 174,426 | `TO` (path crash) → **`APPROVE`** |
| **E6** | `COMPLETED` | `PARTIALLY_CONFIRMED` | 2 / 2 | 1,808.2 | 7,632,393 | 72,970 | 25,098 | `RC` (2 HIGH ABI/trunc) → **`APPROVE`** |
| **E7** | `COMPLETED` | `CONFIRMED` | 2* / 2 | 2,867.7 | 18,109,148 | 110,256 | 102,148 | `RC` (path/CRLF) → **`APPROVE`** |
| **E8** | `COMPLETED` | `PARTIALLY_CONFIRMED` | 4 / 3 | 7,323.1 | 83,115,942 | 217,327 | 345,332 | `TO` (B1 bug) → `RC` (pad drift) → **`APPROVE`** |

*\*Plus killed `dev-e7-02` (~25 s).*

---

## 3. Subscription Quota Consumption & Mid-Campaign Overrides

### 3.1 OpenAI Codex Quota Trajectory (42 Exact Snapshots)
Full timestamped records live in [`quota_snapshots.jsonl`](quota_snapshots.jsonl). Crucially, **both Codex rolling windows reset cleanly mid-campaign** between `18:09:38Z` and `18:24:28Z` (never treated as negative consumption):

1. **Window 1 (`17:36:39Z` – `18:09:38Z`, `resets_at = 1795631851` / `1795934407`):**
   - Covered E0 (`dev-e0-01/02`, `rev-e0-01/02`) and E6 (`dev-e6-01/02`, `rev-e6-01/02`) on `gpt-6.1-sol` `high`.
   - 5h window: `15.0% -> 68.0%` (**`+53.0 pp`**).
   - 7d window: `75.0% -> 83.0%` (**`+8.0 pp`**).
2. **Window Rollover (`18:09:38Z` – `18:24:28Z`):**
   - Both `primary_5h` (`resets_at -> 1795648789`) and `secondary_7d` (`resets_at -> 1796235589`) reset cleanly to `0%` while `dev-e1-01`, `dev-e2-01`, and `dev-e7-01` were running.
3. **Window 2 (`18:24:28Z` – `18:55:24Z`):**
   - Covered E1, E2, E7 (Round 1), E5 (`dev-e5-01`), and E3 (`dev-e3-01`) across `gpt-6.1-sol high` and `gpt-6.2-sol medium`.
   - 5h window: `0.0% -> 95.0%` (**`+95.0 pp`**); 7d window: `0.0% -> 15.0%` (**`+15.0 pp`**).
   - At `18:46Z` (`84%` 5h used), the user issued a **Codex spawn freeze** and requested killing newly launched `dev-e7-02`; already-running `dev-e5-01` (`86%`) and `dev-e3-01` (`95%`) were allowed to complete cleanly.
4. **Total OpenAI Codex consumption across both windows:** **`+148.0 pp`** cumulative 5h budget and **`+23.0 pp`** cumulative 7d budget (`EXACT`).

### 3.2 User-Directed Model / Effort / Harness Transitions
1. **Phase 1 (`17:36–18:35Z`):** `codex-cli 0.172.0` / `gpt-6.1-sol` (`high`) — 13 sessions (E0, E6, initial E1/E2/E5/E7).
2. **Phase 2 (`18:35–18:55Z`):** User switched new Codex spawns to `gpt-6.2-sol` (`medium`) to conserve quota — 7 sessions (`dev-e1-02`, `rev-e2-01`, `dev-e2-02`, `rev-e1-02`, `dev-e3-01`, `rev-e7-01`, `rev-e2-02`). Reasoning tokens dropped sharply per review (**`802` avg** on `gpt-6.2-sol medium` vs **`2,471` avg** on `gpt-6.1-sol high`, **-67.5%**) while still catching real Must-Fix bugs in `rev-e2-01` and `rev-e7-01`!
3. **Phase 3 (`18:55–20:30Z`):** User froze Codex spawns and switched all new Developer/Reviewer sessions to **`opencode2 v2.4.1`** (`opencode-go/deepseek-v4.1-flash`) — 12 pre-hardening sessions (`dev-e7-03`, `rev-e5-01`, `rev-e3-01`, `rev-e7-02`, `dev-e5-02`, `dev-e8-01`, `rev-e5-02`, `dev-e8-02`, `dev-e4-01`, `rev-e8-01`, `dev-e8-03`, `dev-e4-02`).
4. **Phase 4 (`20:30–21:20Z`):** Runner hardening (`063848a`) applied per user timeout diagnosis — 4 post-hardening `opencode2` sessions (`rev-e4-01`, `rev-e8-02`, `dev-e8-04`, `rev-e8-03`).

---

## 4. `opencode2` Timeout Analysis & Runner Hardening Impact (`063848a`)

Prior to runner hardening, **6 of the first 10 finished `opencode2` sessions timed out** (`rev-e5-01`, `dev-e5-02`, `dev-e8-01`, `dev-e8-02`, `dev-e4-01`, `rev-e8-01`) — none due to hangs or provider errors (every session had logged a tool/reasoning event 5–47 s before termination). Root causes were tight `900/1800 s` limits without prompt deadlines, inter-step latency across 66–134 turns, `TMPDIR=<wt>/build/tmp` triggering Watcom 10.0a's ~129-char path crash, unrequested `make verify` / `sleep` polling, and cold review caches.

Hardening commit `063848a` implemented all 7 fixes: `1800 s` reviewer / `2700 s` developer defaults, appended deadline + 70% checkpoint + anti-polling/batching rules, short per-session `/tmp/wc1-<id>` `TMPDIR` (with guaranteed cleanup), verified one-shot `opencode2 run -s <sid>` timeout continuation (throwaway SIGKILL test resumed in **3.6 s** with `same_sid=True` and `11,008` cache-read tokens), partial-success visibility (`dirty_worktree`, `final_report`), fail-closed timeout verdict extraction, and `--warm-cache` review worktrees (~1.2 s pre-warm).

| Cohort | Sessions | Completed cleanly | Timed out | Mean Wall (s) | Outcomes |
|---|---:|---:|---:|---:|---|
| Pre-hardening `opencode2` (`dev-e7-03` .. `rev-e8-01`) | 10 | 4 (`40%`) | 6 (`60%`) | 1,076.3 s | 6 timeouts (all checkpoints recovered cleanly) |
| Post-hardening `opencode2` (`rev-e4-01`, `rev-e8-02`, `dev-e8-04`, `rev-e8-03`) | **4** | **4 (`100%`)** | **0 (`0%`)** | **761.7 s** | `rev-e4-01` **483.2 s** (`APPROVE`), `rev-e8-02` **545.0 s** (`RC`), `dev-e8-04` **1449.9 s** (`COMPLETED`), `rev-e8-03` **568.8 s** (`APPROVE`) |

Every single post-hardening session completed cleanly between **27% and 54%** of its wall-clock budget, and `rev-e8-02` / `rev-e8-03` avoided the 171 s cold-cache penalty completely.

---

## 5. Evaluation of Orchestration Hypotheses (H1–H5)

- **H1 (Fresh disposable sessions reduce token waste vs long accumulated contexts): CONFIRMED.**
  - Fresh repair/handoff sessions (`dev-e0-02` 1.63M, `dev-e6-02` 1.86M, `dev-e1-02` 2.10M, `dev-e2-02` 1.53M, `dev-e7-03` 5.42M, `dev-e4-02` 8.60M) consumed **2–5× fewer prompt tokens** than long initial builds (`dev-e2-01` 11.90M, `dev-e8-01` 25.83M, `dev-e4-01` 20.63M) because task-specific checkpoint packages kept context compact while retaining 96–98% cache hit rates.
- **H2 (Durable repository checkpoints enable zero-loss recovery on forced termination): CONFIRMED.**
  - Across **7 timed-out sessions** (`dev-e7-01`, `rev-e5-01`, `dev-e5-02`, `dev-e8-01`, `dev-e8-02`, `dev-e4-01`, `rev-e8-01`), **0% of completed experimental work was discarded**: every code artifact, 21,618-compile calibration matrix, and review defect diagnosis was preserved in worktree files or raw logs and handed cleanly to fresh successors.
- **H3 (Independent fresh-session adversarial reviews catch genuine scientific & methodological defects): STRONGLY CONFIRMED.**
  - Independent reviewers blocked integration on **8 of 9 initial/intermediate rounds** (`E0`: 6 soundness bugs; `E6`: 2 HIGH ABI/truncation bugs; `E1`: path-dependent hash; `E2`: cross-worktree JSON drift + long-path crash; `E7`: 154-char path crash; `E5`: Watcom 10.0a relative-include path crash; `E8` R1: phantom `cstrtx32` overlap corrupting `zero16`/`style_transition` precision in Corpus B1; `E8` R2: Watcom 10.0a uninitialized `CONST` pad drift). **Only E3 and E4 passed on Round 1**, and both benefited from lessons learned in earlier reviews! Crucially, `opencode-go/deepseek-v4.1-flash` proved an **exceptionally strong adversarial reviewer** once given adequate timeout budgets — uncovering both E5's path crash and E8's deepest methodological ground-truth bug.
- **H4 (Isolated Git worktrees + CoW Wine prefixes + serialized `make verify` enable safe parallel execution): CONFIRMED.**
  - Running 2–3 isolated worktrees concurrently yielded **1.82× effective wall-clock speedup** (`25,961 s` subagent work in `14,247 s` elapsed) with **zero Wine prefix collisions**, **zero git index conflicts**, and **zero concurrent `make verify` races**.
- **H5 (Medium reasoning / budget-tier models maintain quality while drastically extending subscription runway): CONFIRMED.**
  - Switching `gpt-6.1-sol high` → `gpt-6.2-sol medium` cut reviewer reasoning tokens by **67.5%** without sacrificing defect discovery; switching to `opencode-go/deepseek-v4.1-flash` completed the heaviest half of the campaign (E3/E4/E5/E7-R2/E8) with zero additional OpenAI quota consumption and comparable review rigor (at ~2–3× longer wall time per review, completely manageable once limits were raised to `1800 s`).

---

## 6. Cross-Campaign Comparison (`verification-performance` vs `build-codegen`)

| Dimension | `2026-11-25-verification-performance` | `2026-11-25-build-codegen` (this campaign) |
|---|---|---|
| Scope | Production optimization (1 branch, 33 commits, 7 iterations) | 9 parallel research experiments (`E0`–`E8`, 9 branches, 401 tests) |
| Elapsed wall time | `6h 36m 44s` (`5h 25m 50s` net excl. 71m pause) | **`3h 57m 27s`** (0 prolonged interruptions; smooth harness switch) |
| Total sessions | 29 (1 Mgr, 6 wrappers, 8 Dev, 8 Rev, 6 guardian) | **38** (1 Mgr, 20 Dev incl. 1 killed, 17 Rev; 0 wrappers) |
| Normalized prompt tokens | `75.45 M` (`95.4%` cached) | **`253.28 M`** (`97.9%` cached; `141.4 M` on DeepSeek, `60.2 M` Codex, `51.7 M` Gemini) |
| OpenAI Codex quota | `+56 pp` 5h / `+9 pp` 7d | `+148 pp` 5h across 2 windows / `+23 pp` 7d across 2 windows |
| Effective parallelism | Mostly sequential (`~1.0×`) | **1.82×** via isolated worktrees & CoW Wine prefixes |
| Production regressions | `0` (`make verify` `192.6 s -> 52.6 s`) | **`0`** (`0` prod diffs, `make verify` green in `83.4 s`) |
