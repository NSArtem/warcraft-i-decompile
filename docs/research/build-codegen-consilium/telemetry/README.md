# Telemetry record

Every file here is derived from recorded invocations and frozen responses. No
value is estimated. Where a provider exposes no quota, the record says
`unavailable` rather than guessing.

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
| `token_provenance` | which provider record the numbers came from |
| `five_hour_used_percent`, `seven_day_used_percent` | provider-reported utilisation **after** the invocation, for the shared subscription window. These are shared with other activity on the same subscription and are not attributable to the consilium alone |

## `failed-invocations.csv`

Invocations that consumed provider quota but produced no substantive response,
kept separate from `resource-usage.csv` so a failure never looks like a
response and a response never hides a failure. Cost figures are the provider's
API-equivalent estimate, not an actual charge.

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
- `revised` – decisions whose author published a revision > 1 in that round;
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
