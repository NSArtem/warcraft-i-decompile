# Resource and convergence report

Mechanically derived from frozen responses, the rebuilt ledger and recorded provider telemetry. No value is estimated.

## Convergence by round

| round | decisions | unanimously accepted | unanimously rejected | conditional | disputed | conflict | withdrawn+superseded | open objections |
|---|---|---|---|---|---|---|---|---|
| r00 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 29 |
| r01 | 48 | 0 | 0 | 25 | 8 | 0 | 0 | 57 |
| r02 | 51 | 13 | 3 | 4 | 6 | 0 | 0 | 63 |
| r03 | 52 | 27 | 4 | 5 | 0 | 3 | 11 | 64 |
| r04 | 54 | 29 | 4 | 1 | 0 | 0 | 11 | 12 |
| r05 | 54 | 37 | 4 | 1 | 0 | 0 | 12 | 2 |
| r06 | 54 | 37 | 4 | 0 | 0 | 0 | 12 | 1 |
| r07 | 54 | 38 | 4 | 0 | 0 | 0 | 12 | 0 |

## Final ledger state

- rounds read: ['r00', 'r01', 'r02', 'r03', 'r04', 'r05', 'r06', 'r07']
- rounds skipped (barrier open or no manifest): []
- admitted propositions: 93
- unverified propositions (hash not anchored): 0
- historical revision-identity conflicts: 3 (two hash-anchored texts for one revision; resolved by a later revision, never by the Secretary choosing)
  - `DEC-C01` revision 2 (rounds r02, r03); current revision 3
  - `DEC-C09` revision 2 (rounds r02, r03); current revision 3
  - `DEC-C13` revision 2 (rounds r02, r03); current revision 3

- decision status: {"UNANIMOUS": 38, "UNANIMOUS_REJECTED": 4, "WITHDRAWN_SUPERSEDED": 12}
- objection status: {"RESOLVED": 64, "WITHDRAWN": 2}
- objections with an identical disposition from all three: 64
- objections closure eligible: 62
- objections whose named resolution includes a withdrawn decision (resolved transitively through its replacements): 4

## Resource usage (recorded invocations)

| round | architect | model | effort | wall_s | input | cached input | output | 5h % | 7d % |
|---|---|---|---|---|---|---|---|---|---|
| r00 | gpt | gpt-6.2-sol | high | 1133.542 | 6588621 | 6348928 | 49969 | 19.0 | 22.0 |
| r00 | claude | claude-opus-5-5 |  | 1211.004 | 13070518 | 12818033 | 112722 | 61.0 | 14.000000000000002 |
| r00 | gemini | gemini-4-neon-high | high | 1577.114 | 8937243 | 8287290 | 160327 |  |  |
| r01 | gemini | gemini-4-neon-high | high | 1090.112 | 8664343 | 8266786 | 94814 |  |  |
| r01 | claude | claude-opus-5-5 | high | 695.968 | 11491981 | 11041012 | 62346 | 32.0 | 22.0 |
| r01 | gpt | gpt-6.2-sol | high | 956.655 | 9411826 | 9014656 | 39979 | 19.0 | 37.0 |
| r02 | claude | claude-opus-5-5 | high | 550.723 | 10622746 | 10472731 | 55515 | 53.0 | 24.0 |
| r02 | gemini | gemini-4-neon-high | high | 653.716 | 4809250 | 4587059 | 66731 |  |  |
| r02 | gpt | gpt-6.2-sol | high | 1029.18 | 4906910 | 4681600 | 40641 | 36.0 | 40.0 |
| r03 | gpt | gpt-6.2-sol | high | 1402.404 | 9735114 | 9423360 | 63057 | 59.0 | 43.0 |
| r03 | gemini | gemini-4-neon-high | high | 1630.752 | 3930172 | 3631785 | 186820 |  |  |
| r03 | claude | claude-opus-5-5 | high | 540.661 | 6891492 | 6082713 | 67758 | 51.0 | 31.0 |
| r04 | claude | claude-opus-5-5 | high | 320.359 | 18265270 | 18131686 | 37462 | 96.0 | 33.0 |
| r04 | gemini | gemini-4-neon-high | high | 795.561 | 3461077 | 2850185 | 87094 |  |  |
| r04 | gpt | gpt-6.2-sol | high | 1159.727 | 7466058 | 6935552 | 47632 | 22.0 | 47.0 |
| r05 | gpt | gpt-6.2-sol | high | 234.388 | 1842471 | 1679616 | 10487 | 5.0 | 48.0 |
| r05 | claude | claude-opus-5-5 | high | 405.309 | 1531749 | 1416591 | 29809 | 39.0 | 37.0 |
| r05 | gemini | gemini-4-neon-high | high | 239.598 | 1041373 | 775928 | 28794 |  |  |
| r06 | gpt | gpt-6.2-sol | high | 81.285 | 1156651 | 1129728 | 3450 | 8.0 | 49.0 |
| r06 | claude | claude-opus-5-5 | high | 127.456 | 1195005 | 1158514 | 12169 | 44.0 | 37.0 |
| r06 | gemini | gemini-4-neon-high | high | 117.323 | 2170187 | 2038676 | 10753 |  |  |
| r07 | gpt | gpt-6.2-sol | high | 41.352 | 627363 | 616320 | 1661 | 9.0 | 49.0 |
| r07 | gemini | gemini-4-neon-high | high | 61.298 | 1617796 | 1602682 | 4060 |  |  |
| r07 | claude | claude-opus-5-5 | high | 33.333 | 509937 | 497617 | 3106 | 45.0 | 37.0 |
| editor | claude | claude-opus-5-5 | high | 659.242 | 8979929 | 8817582 | 65233 | 67.0 | 39.0 |
| editor-v2 | claude | claude-opus-5-5 | high | 171.464 | 3912765 | 3876999 | 16262 | 74.0 | 40.0 |
| approval | claude | claude-opus-5-5 | high | 171.669 | 3894398 | 3867661 | 16373 | 80.0 | 40.0 |
| approval | gpt | gpt-6.2-sol | high | 318.966 | 8088497 | 7967104 | 12562 | 24.0 | 51.0 |
| approval | gemini | gemini-4-neon-high | high | 276.969 | 1644672 | 1486209 | 29804 |  |  |
| editor-v3 | gpt | gpt-6.2-sol | high | 326.41 | 6284914 | 6216320 | 14472 | 36.0 | 53.0 |
| approval-3 | gpt | gpt-6.2-sol | high | 142.582 | 5529321 | 5473920 | 5629 | 45.0 | 55.0 |
| approval-3 | gemini | gemini-4-neon-high | high | 151.247 | 603105 | 490841 | 16567 |  |  |
| approval-3 | claude | claude-opus-5-5 | high | 131.993 | 4911828 | 4419835 | 12266 | 23.0 | 44.0 |

### Failed invocations (consumed quota, produced no response)

| round | architect | attempt | wall_s | api_error | input | output | cost (API-equivalent) |
|---|---|---|---|---|---|---|---|
| r03 | claude | 01-provider-rate-limit | 381.505 | usage_limit_reached | 11883473 | 31583 | 8.732420 |
| editor-v3 | claude | 01-provider-rate-limit | 409.747 | usage_limit_reached | 15015888 | 36890 | 4.344956 |

Quota percentages are provider-reported utilisation of the shared subscription window after the invocation; they are not attributable to the consilium alone and are never summed across rows.

## Sessions

- gpt: native session `01a21b18-3f30-7111-a0a7-0aefa369a288`, invocations 11
- claude: native session `13aab0ab-0931-4926-815e-bfba7f5aa256`, invocations 14
- gemini: native session `56960ce2-155d-4fff-b3f0-4444e1f86949`, invocations 10

## Resource distribution

| architect | invocations | completed | failed | wall_s | input tokens (per-invocation sum) | API-equivalent cost delta (USD) |
|---|---|---|---|---|---|---|
| gpt | 11 | 11 | 0 | 6826.491 | 61637746 | 0 |
| claude | 14 | 12 | 2 | 5810.433 | 112176979 | 64.804304 |
| gemini | 10 | 10 | 0 | 6593.69 | 36879218 | 0 |

Token totals are sums of per-invocation deltas, computed inside one native session in `start_utc` order. Claude's `total_cost_usd` is a cumulative API-equivalent estimate; only the differences are additive and they are not monetary charges. Codex and AGY expose no monetary counter, so no cost is reported for them.

### Claude cost-delta ledger (API-equivalent)

| round | attempt | status | start_utc | delta (USD) | cumulative (USD) |
|---|---|---|---|---|---|
| r00 | - | COMPLETED | 2026-11-27T03:41:42.507923Z | 6.8372946 | 6.837294599999998 |
| r01 | - | COMPLETED | 2026-11-27T08:56:40.035480Z | 7.0626344 | 13.899929 |
| r02 | - | COMPLETED | 2026-11-27T09:16:59.458327Z | 4.4048062 | 18.304735200000003 |
| r03 | 01-provider-rate-limit | PROVIDER_RATE_LIMIT | 2026-11-27T10:34:00.562898Z | 8.73242 | 27.037155200000008 |
| r03 | 02-continuation | COMPLETED | 2026-11-27T14:35:02.505929Z | 9.0418626 | 36.0790178 |
| r04 | - | COMPLETED | 2026-11-27T14:51:59.272600Z | 5.4440812 | 41.523099 |
| r05 | - | COMPLETED | 2026-11-27T20:41:23.035286Z | 5.7758278 | 47.29892679999999 |
| r06 | - | COMPLETED | 2026-11-27T20:49:35.184605Z | 0.7669468 | 48.06587359999999 |
| r07 | - | COMPLETED | 2026-11-27T20:52:45.123296Z | 0.2601714 | 48.32604499999999 |
| editor | - | COMPLETED | 2026-11-27T20:55:20.783019Z | 4.3666804 | 52.692725399999986 |
| editor-v2 | - | COMPLETED | 2026-11-27T21:09:19.981711Z | 1.3866718 | 54.07939719999998 |
| approval | - | COMPLETED | 2026-11-27T21:14:14.906267Z | 1.3148002 | 55.39419739999999 |
| editor-v3 | 01-provider-rate-limit | PROVIDER_ERROR | 2026-11-27T21:21:48.671319Z | 4.3449558 | 59.73915319999998 |
| approval-3 | - | COMPLETED | 2026-11-28T05:25:31.329621Z | 5.065151 | 64.80430419999998 |

### Effect of the Editor reassignment

Revision 3 was drafted by Architect B up to the point where B's five-hour window was exhausted, then completed by Architect A under the owner's reassignment. B's preserved partial work is counted as a failed invocation (quota consumed, no response of record) and is not double counted: the round slot and the attempt slot of the same invocation collapse to one record. The reassignment moved the remaining editorial cost from the scarce Claude window to the Codex window, and left B's window available for the final independent review. Editorial work, deliberation and final review are separate categories above; failed invocations are listed separately from responses of record.

Quota percentages are shared subscription utilisation, not consilium attribution: other activity on the same subscriptions consumes the same windows.

### Administrative overhead (non-Architect)

Availability preflights and other administrative provider calls. They are not Architect invocations and never produce a verdict.

| kind | provider | at (UTC) | outcome | API-equivalent cost (USD) |
|---|---|---|---|---|
| availability_preflight | claude | 2026-11-27T22:20:00Z | rejected (five_hour 100%) | 0.0 |
| availability_preflight | claude | 2026-11-28T05:23:48Z | allowed (five_hour 0%, seven_day 42%) | 0.16463760000000002 |

Total measured administrative overhead: 0.164638 USD (API-equivalent estimate).

