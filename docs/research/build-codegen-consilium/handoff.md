# Consilium Hand-off

- **Status:** `ROUND_4_PENDING`
- **Generated at (UTC):** `2026-11-27T14:49:43.156868Z`
- **Phase:** `ROUND_4_PENDING`
- **Baseline:** `research/build-codegen-experiments` @ `e6150b856106ae113bb023300b956fff318da7ef`
- **Consilium branch:** `research/build-codegen-consilium`
- **Evidence revision:** `EV-3`
- **Next round:** `r04`
- **Note:** Round 3 frozen; ledger repaired; convergence round next

## Worktrees
- `secretary`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-sec`
- `gpt`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-a`
- `claude`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`
- `gemini`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-c`

## Sessions
- `gpt`: native id `01a21b18-3f30-7111-a0a7-0aefa369a288`, invocations `4`
- `claude`: native id `13aab0ab-0931-4926-815e-bfba7f5aa256`, invocations `5`
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
- `r03`: status `frozen`, barrier `closed`
  - `gpt`: `d44f43822f979c1485c40c704fc124e8b2333fd18a3e936936b9db923fcd41a8`
  - `claude`: `f7f9449d7c621013a744c961d00c706745f2d1413ba35f5206d7078620d7522a`
  - `gemini`: `b1a3c227e19e640e3e21bd46efbd9b0718ab5d4d1fd39d46b2cf9af6f92c9283`

## Ledger
- Decisions: `52` {'UNANIMOUS': 27, 'PROPOSED': 2, 'WITHDRAWN_SUPERSEDED': 11, 'CONDITIONAL': 5, 'UNANIMOUS_REJECTED': 4, 'CONFLICT': 3}
- Objections: `65`

## Resource snapshots
- `r03_resume/gpt`: {'five_hour_used_percent': 0.0, 'five_hour_resets_at_epoch': 1795807827, 'seven_day_used_percent': 44.0, 'seven_day_resets_at_epoch': 1796235589, 'plan_type': 'plus', 'provenance': 'exact (codex rollout rate_limits, disposable preflight thread 01a21d6a)', 'attribution_note': 'Shared subscription; other campaigns may consume the same windows.'}
- `r03_resume/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage; no agy invocation was needed for this resume.'}
- `r03_resume/hiapi`: {'used_percent': None, 'provenance': 'unavailable', 'note': 'Secretary provider; administrative overhead only, no architectural authority.'}
- `r03/gpt`: {'five_hour_used_percent': 59.0, 'five_hour_resets_at_epoch': 1795787722, 'seven_day_used_percent': 43.0, 'seven_day_resets_at_epoch': 1796235589, 'plan_type': 'plus', 'provenance': 'exact (codex rollout rate_limits)'}
- `r03/claude`: {'five_hour_used_percent': 51.0, 'five_hour_resets_at_epoch': 1795807200, 'seven_day_used_percent': 31.0, 'seven_day_resets_at_epoch': 1796299200, 'status': 'allowed', 'provenance': 'exact (claude rate_limit_event)'}
- `r03/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage.'}

## Blockers
- None recorded.

## Pending messages
- `{"to": ["gpt", "claude", "gemini"], "kind": "round_4_convergence", "state": "to be composed", "delivery": "after the Round 3 barrier (closed); contains all three frozen Round 3 texts"}`
- `{"to": ["gemini"], "kind": "revision_identity_confirmation", "state": "required", "detail": "revision 2 of DEC-C01, DEC-C09 and DEC-C13 has two different published texts (R2 and R3). The ledger fails closed until the author states which text is revision 2 or publishes revision 3."}`

## Recent commits
```text
50d7e66 consilium: hash-anchored ledger rebuild with decisions, withdrawals and objection lifecycle
1a99257 consilium: resume Claude Round 3 in the same session and preserve the response
849207f consilium: write prompt metadata for a single-Architect launch
14cbb89 consilium: never present a stale position file as a fresh response
15726ab consilium: record Round 3 resume authorization and fresh preflight
0f78227 consilium: resume one Architect without rerunning completed peers
5f5fe51 consilium: record owner decision to pause indefinitely
d4c85d4 consilium: record Round 3 delivered prompt hashes
4938118 consilium: pause Round 3 on Claude 5-hour exhaustion
da2afd8 consilium: classify provider failures and record Round 3 partial barrier
92b8446 consilium: preserve gemini Round 3 state and telemetry
a83049c consilium: preserve claude Round 3 state and telemetry
```

## Exact resume procedure
1. Read `state.json`, the latest `rounds/<round>/manifest.json`, `decisions.json`, `objections.json`.
2. Inspect raw logs under `/mnt/data/projects/warcraft-1-decompile-consilium/logs/` and session IDs above.
3. If the next round is pending: compose it from the frozen previous round, then `launch-files`.
4. If resuming an interrupted round: check `logs/<round>/` for partial output; a completed final message is the response of record.
5. Never treat silence or a partial response as agreement.

## Round 3 resumed and closed (2026-11-27)

The owner resumed the paused campaign and authorized spending the Claude window
that opened at `2026-11-27T13:50Z` to finish Round 3. Preflight, authorization
record and attempt history are in `rounds/r03/resume.json`; the delivered
continuation prompt is `rounds/r03/prompt-claude-continuation.md`
(`84badd0a…`, 6287 bytes) with only its operational timestamps refreshed.

Claude was resumed in the same native session (`13aab0ab…`) and produced a
complete Round 3 response (`f7f9449d…`, 137535 bytes, 540.7 s, model
`claude-opus-5-5`, effort high) covering 38/38 indexed decisions, 63/63
objections and 69 structured positions, plus one new probe. The interrupted
attempt 01 remains preserved with its provider error
(`cb171b39…`, HTTP 429 `usage_limit_reached`, 381.5 s, 11.88M input tokens,
$27.04 API-equivalent). GPT and Gemini were not rerun, and neither saw a peer's
Round 3 text before the barrier closed.

Barrier: closed at `2026-11-27T14:45:05Z`; the three Round 3 texts are now
deliverable.

## Ledger repair

`decisions.json` and `objections.json` were rebuilt from the frozen responses
with `orchestrator/ledger_lib.py` (schema version 2). The previous ledger lost
every revision published as prose rather than in a `Proposition:` block,
classified unanimous rejections as `DISPUTED`, and kept withdrawn proposals as
live disputes. The new builder admits a revision only when its exact text is
hash-anchored, fails closed on two texts sharing one revision, counts a position
only on the current revision, separates author withdrawals from peer reports,
and closes an objection only on explicit dispositions.

Net effect: 21 revisions that the old ledger could not see are now admitted;
27 decisions are unanimously accepted and 4 unanimously rejected (the old
ledger reported 13 and 0); 11 withdrawn duplicates are recorded as
`WITHDRAWN_SUPERSEDED` with their replacement decisions.

## Live issues for Round 4

1. **Revision identity (Architect C).** `DEC-C01`, `DEC-C09` and `DEC-C13`
   revision 2 has two different published texts (Gemini R2 and Gemini R3).
   Both are hash-consistent with their own stated hashes, so the ledger cannot
   choose. Recorded as `CONFLICT`; needs the author's statement of which text
   is revision 2, or a revision 3.
2. **Missing live positions.** `DEC-A14` (new in GPT R3) and `DEC-C15`
   revision 2 have no position from two Architects each.
3. **Conditional acceptances.** `DEC-B06`, `DEC-C05`, `DEC-C07`, `DEC-C10`,
   `DEC-C16` record explicit conditions; they are not unconditional consensus.
4. **Objection closure.** 64 objections remain `OPEN`; 60 are unanimously
   upheld and 16 name only unanimously resolved decisions, so they are eligible
   for explicit closure but no Architect has yet given a closing disposition.
5. **Canonicalisation.** There are 11 withdrawn `DEC-B*` duplicates whose
   replacements are unanimous; the Architects must confirm the mapping rather
   than the Secretary merging them.
