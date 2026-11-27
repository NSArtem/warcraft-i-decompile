# Consilium Hand-off

- **Status:** `ROUND_5_READY_AWAITING_QUOTA`
- **Generated at (UTC):** `2026-11-27T15:15:33.580988Z`
- **Phase:** `ROUND_5_READY_AWAITING_QUOTA`
- **Baseline:** `research/build-codegen-experiments` @ `e6150b856106ae113bb023300b956fff318da7ef`
- **Consilium branch:** `research/build-codegen-consilium`
- **Evidence revision:** `EV-3`
- **Next round:** `r05`
- **Note:** Round 4 frozen; 44 of 54 decisions settled, 52 objections resolved; Round 5 confirmation blocked on Claude quota

## Worktrees
- `secretary`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-sec`
- `gpt`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-a`
- `claude`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-b`
- `gemini`: `/mnt/data/projects/warcraft-1-decompile-wt/cons-c`

## Sessions
- `gpt`: native id `01a21b18-3f30-7111-a0a7-0aefa369a288`, invocations `5`
- `claude`: native id `13aab0ab-0931-4926-815e-bfba7f5aa256`, invocations `6`
- `gemini`: native id `56960ce2-155d-4fff-b3f0-4444e1f86949`, invocations `5`

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
- `r04`: status `frozen`, barrier `closed`
  - `gpt`: `e6a4affde01c9c2a2ca21807be25a7b730b56297cc2a419afd9c34f6ee955a45`
  - `claude`: `a9c0099e502a6de81a030967f26ebea09f8e1cf74ccf842c292a1a352623ec83`
  - `gemini`: `a6f2f9d7989c78aafcf5d0a41c7d532ecbc9a053440ae7f2db1d2d4bc2798a09`

## Ledger
- Decisions: `54` {'UNANIMOUS': 29, 'PROPOSED': 9, 'WITHDRAWN_SUPERSEDED': 11, 'UNANIMOUS_REJECTED': 4, 'CONDITIONAL': 1}
- Objections: `66`

## Resource snapshots
- `r03/gpt`: {'five_hour_used_percent': 59.0, 'five_hour_resets_at_epoch': 1795787722, 'seven_day_used_percent': 43.0, 'seven_day_resets_at_epoch': 1796235589, 'plan_type': 'plus', 'provenance': 'exact (codex rollout rate_limits)'}
- `r03/claude`: {'five_hour_used_percent': 51.0, 'five_hour_resets_at_epoch': 1795807200, 'seven_day_used_percent': 31.0, 'seven_day_resets_at_epoch': 1796299200, 'status': 'allowed', 'provenance': 'exact (claude rate_limit_event)'}
- `r03/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage.'}
- `r04/gpt`: {'five_hour_used_percent': 22.0, 'five_hour_resets_at_epoch': 1795807828, 'seven_day_used_percent': 47.0, 'seven_day_resets_at_epoch': 1796235589, 'plan_type': 'plus', 'provenance': 'exact (codex rollout rate_limits)'}
- `r04/claude`: {'five_hour_used_percent': 96.0, 'five_hour_resets_at_epoch': 1795807200, 'seven_day_used_percent': 33.0, 'seven_day_resets_at_epoch': 1796299200, 'status': 'allowed_warning', 'provenance': 'exact (claude rate_limit_event)'}
- `r04/gemini`: {'provenance': 'unavailable', 'note': 'AGY exposes no reliable local quota percentage.'}

## Blockers
- `{"provider": "claude", "window": "five_hour", "used_percent": 96.0, "status": "allowed", "observed_at_utc": "2026-11-27T15:11:19Z", "resets_at_utc": "2026-11-27T19:20:00Z", "note": "Claude finished Round 4 at 96% of its 5-hour window. A Round 5 confirmation round needs all three Architects; the remaining quota is not sufficient to launch it. Further Claude spending requires owner authorization."}`

## Pending messages
- `{"to": ["gpt", "claude", "gemini"], "kind": "round_5_targeted_confirmation_and_editor_nomination", "prompt": "rounds/r05/prompt-template-inbox.md", "state": "composed_ready_not_launched", "blocked_by": "claude five-hour quota"}`
- `{"to": ["gpt", "claude", "gemini"], "kind": "delivery_of_round_4_responses", "state": "composed (inbox r05)"}`

## Recent commits
```text
79b7a97 consilium: apply Round 4 structured deltas and rebuild the ledgers
e730307 consilium: close the Round 4 barrier and preserve the submitted deltas
10431f3 consilium: collect and validate per-round structured deltas
3c6057c consilium: add the mechanical convergence and resource report
035e684 consilium: compose the Round 4 convergence round with structured deltas
e9c8ac9 consilium: bind a delta to an explicit source response file
0de2f99 consilium: update the hand-off for Round 4 convergence
58d29cf consilium: rebuild the decision and objection ledgers from frozen responses
61a2361 consilium: close the Round 3 barrier
50d7e66 consilium: hash-anchored ledger rebuild with decisions, withdrawals and objection lifecycle
1a99257 consilium: resume Claude Round 3 in the same session and preserve the response
849207f consilium: write prompt metadata for a single-Architect launch
```

## Exact resume procedure
1. Read `state.json`, the latest `rounds/<round>/manifest.json`, `decisions.json`, `objections.json`.
2. Inspect raw logs under `/mnt/data/projects/warcraft-1-decompile-consilium/logs/` and session IDs above.
3. If the next round is pending: compose it from the frozen previous round, then `launch-files`.
4. If resuming an interrupted round: check `logs/<round>/` for partial output; a completed final message is the response of record.
5. Never treat silence or a partial response as agreement.

## Round 4 result (2026-11-27)

All three Architects delivered prose plus a validated structured delta (29, 35
and 21 decision records). The deltas were validated by
`orchestrator/decision_delta.py` and are bound to each Architect's **durable
copy**, not to its final message — the two differ for all three, substantially
for Architect A, and both texts are preserved under `rounds/r04/<arch>/` and
`rounds/r04/<arch>/durable/`. `rounds/r04/deltas.json` records the hashes.

After applying the deltas the ledger reports **44 of 54 decisions settled**
(29 unanimously accepted, 4 unanimously rejected, 11 withdrawn with accepted
replacements), 9 `PROPOSED` and 1 `CONDITIONAL`; **52 of 66 objections
resolved**, 2 withdrawn, 12 open with non-agreeing dispositions.

Remaining mechanical gaps for the next round:

- `DEC-C01`, `DEC-C09`, `DEC-C13` revision 3 republishes the revision-2 text
  byte-identically; A and B have not recorded a position on revision 3.
- `DEC-C05`, `DEC-C07`, `DEC-C10`, `DEC-C16` revision 3 has **different** text
  from revision 2 and no position from A or B.
- `DEC-A15` and `DEC-A16` (new in Round 4) have no position from B or C.
- `DEC-C15` revision 2 remains conditional for Architect A.
- 12 objections have split dispositions.

A Round 5 targeted confirmation prompt is composed and ready at
`rounds/r05/prompt-template-inbox.md`; it also asks for RFC Editor nominations.

## Blocker

Claude finished Round 4 at **96%** of its 5-hour window (window ends
`2026-11-27T19:20Z`). Round 5 requires all three Architects, and the remaining
quota is not sufficient for another substantive turn. No further Claude window
has been authorized for automatic spending.
