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

### Failed invocations (consumed quota, produced no response)

| round | architect | attempt | wall_s | api_error | input | output | cost (API-equivalent) |
|---|---|---|---|---|---|---|---|
| r03 | claude | 01-provider-rate-limit | 381.505 | usage_limit_reached | 11883473 | 31583 | 8.732420 |
| editor-v3 | claude | 01-provider-rate-limit | 409.747 | usage_limit_reached | 15015888 | 36890 | 4.344956 |

Quota percentages are provider-reported utilisation of the shared subscription window after the invocation; they are not attributable to the consilium alone and are never summed across rows.

## Sessions

- gpt: native session `01a21b18-3f30-7111-a0a7-0aefa369a288`, invocations 9
- claude: native session `13aab0ab-0931-4926-815e-bfba7f5aa256`, invocations 13
- gemini: native session `56960ce2-155d-4fff-b3f0-4444e1f86949`, invocations 9

