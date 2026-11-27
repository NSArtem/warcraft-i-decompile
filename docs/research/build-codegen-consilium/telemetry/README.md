# Telemetry record

Every file here is derived from recorded invocations and frozen responses. No
value is estimated. Where a provider exposes no quota, the record says
`unavailable` rather than guessing.

All derived files are produced by `orchestrator/telemetry_gen.py` from the
authoritative per-attempt invocation records under `rounds/`; they are never
hand-edited. `telemetry_gen.py --check` fails if the files drift. The generator
deduplicates a round-slot copy of an attempt, sorts invocations by real
`start_utc` before differencing, groups cumulative counters by native session,
and rejects a negative cost delta unless the record documents a provider reset.
Regression tests: `orchestrator/test_telemetry_gen.py`.

## `invocations.jsonl`

One authoritative record per actual invocation, including failures. Carries the
provider-reported `usage`, the `usage_per_invocation` delta view and the
`cumulative` counter, the quota after the invocation, and the source `meta.json`.
This is the record of record; the CSVs are projections of it.

## `resource-usage.csv`

One row per Architect invocation that produced the round's response of record.

| column | meaning |
|---|---|
| `round`, `architect` | round id and Architect |
| `model`, `effort` | model and reasoning effort as observed by the harness |
| `wall_s` | wall-clock seconds of the invocation |
| `input_tokens` | provider-reported input tokens. Claude/Gemini values include cache reads and cache creation; Codex values are the rollout cumulative counter for that invocation only (never summed across rounds) |
| `cached_input_tokens` | provider-reported cache-hit input |
| `output_tokens` | provider-reported output tokens (thinking included where the provider reports it that way) |
| `reasoning_tokens` | separate reasoning counter where the provider exposes one (Codex). Claude/Gemini report thinking inside their own result records; those values live in `failed-invocations.csv` and in the round `meta.json`, not here |
| `counter_scope` | `per_invocation` for every row. Codex and AGY publish a *cumulative* session counter; their rows are the difference between consecutive snapshots, and the cumulative value stays in the round `meta.json`. Never sum a cumulative counter across rows |
| `token_provenance` | which provider record the numbers came from |
| `cost_delta_usd` | Claude only: the API-equivalent cost difference from the previous invocation in the same native session, in `start_utc` order. It is an estimate, not a monetary charge |
| `cumulative_cost_usd` | Claude only: the provider's cumulative `total_cost_usd` after this invocation |
| `start_utc` | the real invocation start; all cumulative deltas are computed in this order |
| `five_hour_used_percent`, `seven_day_used_percent` | provider-reported utilisation **after** the invocation, for the shared subscription window. These are shared with other activity on the same subscription and are not attributable to the consilium alone |

## `summary.json`

Per-Architect totals: invocation/completed/failed counts, wall time, token
totals and the full Claude cost-delta ledger. Sums of `cost_delta_usd` are the
only cost figure that may be added; a cumulative `total_cost_usd` is never a
per-invocation charge.

## `failed-invocations.csv`

Invocations that consumed provider quota but produced no substantive response,
kept separate from `resource-usage.csv` so a failure never looks like a
response and a response never hides a failure. Cost figures are the provider's
API-equivalent estimate, not an actual charge. Failed invocations stay in the
cumulative cost chain: a later delta is measured from the failed invocation's
cumulative value, not from the previous success.

## `quota-snapshots.jsonl`

Append-only provider quota readings. `round` says why the reading was taken
(`preflight`, `rNN`, `rNN_resume`, `pause`). Cumulative counters are recorded as
read; they are never summed across rows.

## `sessions.jsonl`

One row per frozen response: status, hashes, wall time, usage and quota. Rows
written before the current schema may carry fewer fields; they are preserved.

## `round-metrics.csv`

Computed by replaying the ledger up to each round (`ledger_lib.build(upto=...)`):

- `new_proposals` – decisions first seen in that round;
- `newly_unanimous` – change in the count of unanimously accepted decisions;
- `revised` – decisions whose highest admitted revision increased during that
  round (restatements of an already-admitted revision are not counted);
- `resolved_objections` – change in the count of objections closed by explicit
  unanimous disposition (none so far: no round has produced closing
  dispositions from all three Architects);
- `opened_objections` – objections first raised in that round;
- `position_changes` – explicit changes recorded in the round's `metrics.json`;
- `disputed_open` – decisions still `DISPUTED` or `CONFLICT` at the end of the
  round (state, not a delta);
- `evidence_revisions` – evidence revisions available in that round.

## Not recorded

Secretary (OpenCode) overhead is not measured in tokens; the provider exposes
no reliable counter for it. Concurrent campaigns consume the same shared
subscription windows; those readings are attributed to the subscription, not to
the consilium.
