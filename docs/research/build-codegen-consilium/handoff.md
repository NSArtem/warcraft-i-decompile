# Consilium Hand-off

- **Status:** `PAUSED_AWAITING_OWNER`
- **Generated at (UTC):** `2026-11-27T11:02:16.642180Z`
- **Phase:** `PAUSED_AWAITING_OWNER`
- **Baseline:** `research/build-codegen-experiments` @ `e6150b856106ae113bb023300b956fff318da7ef`
- **Consilium branch:** `research/build-codegen-consilium`
- **Evidence revision:** `EV-3`
- **Next round:** `r03`
- **Note:** Claude 5-hour window exhausted during Round 3; GPT and Gemini responses preserved; barrier open

## Owner decision required — Claude 5-hour window

Round 3 is **not frozen**. GPT and Gemini produced complete Round 3 responses
(`d44f4382…`, `b1a3c227…`); both are stored and **undelivered**. Claude was
rejected by the provider at **101% of its 5-hour window** after 381 s; its
stored text is the provider notice, not a substantive response. The
provider-reported reset is **2026-11-27T13:50:00Z** (17:50 Asia/Yerevan).

The charter authorizes one full 5-hour window per provider. Resuming Claude
after 13:50Z consumes a **second** window and therefore requires explicit owner
authorization. Do not deliver the GPT or Gemini Round 3 texts to Claude before
Claude's own Round 3 response is completed and the barrier is frozen.

After authorization and the reset, resume only Claude in the existing session:

```bash
claude -p --model claude-opus-5-5 --effort high --dangerously-skip-permissions \
  --output-format stream-json --verbose \
  --resume 13aab0ab-0931-4926-815e-bfba7f5aa256 \
  "$(cat docs/research/build-codegen-consilium/rounds/r03/prompt-claude.md)"
```

Then preserve and hash the response, run `run_architect.py freeze --round r03`,
rebuild the ledger and metrics, and only then deliver the frozen Round 3 texts
to all three Architects. If the owner does not authorize a second Claude
window, the consilium remains paused with the present artifacts.

## Worktrees
- `secretary`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-sec`
- `gpt`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-a`
- `claude`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`
- `gemini`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-c`

## Sessions
- `gpt`: native id `01a21b18-3f30-7111-a0a7-0aefa369a288`, invocations `4`
- `claude`: native id `13aab0ab-0931-4926-815e-bfba7f5aa256`, invocations `4`
- `gemini`: native id `56960ce2-155d-4fff-b3f0-4444e1f86949`, invocations `4`

## Rounds
- `r00`: status `frozen`, barrier `closed`
  - `gpt`: `22477c0cf5f8f211d459c5ec72f26cdb7b0c24903bc6dc5e659f696b6b53b7c1`
  - `claude`: `9905f1b405acd6e3bef445fd697d255de6aebb0f29d10d2c328035aadc047203`
  - `gemini`: `32e9252ac50bed45838437e2144bbcaa585e70c7c87fe9dd6ed0f160e10771f6`
- `r01`: status `frozen`, barrier `closed`
  - `gpt`: `482cbb192515d260ecdc9e878361b2bd0a6ea0a6ce5feed8370c41f37d109f5d`
  - `claude`: `ee07dd4bfd85cd8d706da39f262739f3eb7cfb601327ea52cd658d79869806d5`
  - `gemini`: `aecdde79852ef02bef2206c6243ad90da483c980982f413a4ef6d9a6714edf66`
- `r02`: status `frozen`, barrier `closed`
  - `gpt`: `0b876293a831962f9b5f0ff94905f3d2c82987af3fc7d2e70cd4513b7678b728`
  - `claude`: `a45939623d3dff96f35958a4d54a96ec026ba937001848c12c359d38565a2233`
  - `gemini`: `51f761d7da8c26bb1a9450e464fbc12d7c570855e61f1380ff6b6aa34e093780`
- `r03`: status `blocked_partial`, barrier `open`
  - `gpt`: `d44f43822f979c1485c40c704fc124e8b2333fd18a3e936936b9db923fcd41a8`
  - `claude`: `cb171b39634d90db44ca61f6b76523a915dc2b7e391e1573688a818c66a88a3e`
  - `gemini`: `b1a3c227e19e640e3e21bd46efbd9b0718ab5d4d1fd39d46b2cf9af6f92c9283`

## Ledger
- Decisions: `51` {'UNANIMOUS': 13, 'DISPUTED': 14, 'PROPOSED': 12, 'CONDITIONAL': 12}
- Objections: `63`

## Resource snapshots
- `r01/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage.'}
- `r02/gpt`: {'five_hour_used_percent': 36.0, 'five_hour_resets_at_epoch': 1795787722, 'seven_day_used_percent': 40.0, 'seven_day_resets_at_epoch': 1796235589, 'plan_type': 'plus', 'provenance': 'exact (codex rollout rate_limits)'}
- `r02/claude`: {'five_hour_used_percent': 53.0, 'five_hour_resets_at_epoch': 1795787400, 'seven_day_used_percent': 24.0, 'seven_day_resets_at_epoch': 1796299200, 'status': 'allowed', 'provenance': 'exact (claude rate_limit_event)'}
- `r02/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage.'}
- `r03_pause/claude`: {'five_hour_used_percent': 101.0, 'status': 'rejected', 'resets_at_epoch': 1795787400, 'seven_day_used_percent': 28.0, 'provenance': 'exact (claude rate_limit_event)'}
- `r03_pause/codex`: {'five_hour_used_percent': 59.0, 'seven_day_used_percent': 43.0, 'provenance': 'exact (codex rollout rate_limits)'}

## Blockers
- `{"provider": "claude", "window": "five_hour", "used_percent": 101.0, "status": "rejected", "resets_at_epoch": 1795787400, "resets_at_utc": "2026-11-27T13:50:00Z", "observed_at_utc": "2026-11-27T11:02:04.045191+00:00", "note": "The authorized Claude 5-hour window is exhausted. Round 3 has GPT and Gemini responses but no substantive Claude response. A second Claude window requires owner authorization."}`

## Pending messages
- `{"to": ["claude"], "kind": "round_3_completion", "prompt": "rounds/r03/prompt-claude.md", "barrier": "must complete before GPT/Gemini Round 3 texts are delivered", "delivery": "not_delivered"}`
- `{"to": ["gpt", "claude", "gemini"], "kind": "round_3_freeze", "delivery": "blocked_on_claude"}`

## Recent commits
```text
92b8446 consilium: preserve gemini Round 3 state and telemetry
a83049c consilium: preserve claude Round 3 state and telemetry
e263f6a consilium: preserve gpt Round 3 state and telemetry
9325265 consilium: add RFC Editor drafting template
76826ab consilium: add immutable-draft approval delivery
d63e96d consilium: prepare and launch Round 3 targeted deliberation
a059145 consilium: add targeted-deliberation composition and metrics
b0cfa73 consilium: advance state to Round 3
f185653 consilium: close Round 2 barrier and update the decision ledger
ac36dc9 consilium: preserve gemini Round 2 response and telemetry
4823881 consilium: preserve claude Round 2 response and telemetry
d315233 consilium: preserve gpt Round 2 response and telemetry
```

## Exact resume procedure
1. Read `state.json`, the latest `rounds/<round>/manifest.json`, `decisions.json`, `objections.json`.
2. Inspect raw logs under `/mnt/data/projects/warcraft-1-decompile-consilium/logs/` and session IDs above.
3. If the next round is pending: compose it from the frozen previous round, then `launch-files`.
4. If resuming an interrupted round: check `logs/<round>/` for partial output; a completed final message is the response of record.
5. Never treat silence or a partial response as agreement.
