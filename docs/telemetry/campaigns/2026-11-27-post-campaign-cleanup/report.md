# Post-campaign cleanup — M2 metadata, E7 provenance, calibration reproducibility (2026-11-27)

- **Manager:** Claude Code (Opus 5.5, high effort). **Developer / Reviewer:** `opencode-go/deepseek-v4.1-flash` via `opencode2 v2.4.1` (fresh sessions, hardened runner copied from the overnight campaign: bounded wall time, short `/tmp/wc1-*` TMPDIR, isolated WINEPREFIX, orphan guard, serialized `make verify` lock).
- **Production branch:** `feature/m2-mechanical-cleanup` `dae45bd` → see `git log dae45bd..` (not merged into `main`).
- **Research branch:** `research/model-calibration-engineering` `cea804e` → `d55d493` (not merged).
- **Orchestration logs, prompts and raw session JSONL:** `/mnt/data/wc1-artifacts/orch-20261127-cleanup/` (local, not committed).

## Production results

| Item | Result |
|---|---|
| A1 `wc1.m2_inventory` | stale DG-01/03/05/06 text corrected; `GROUP_META` module-level; per-row classification identical to `dae45bd`; new test reconciles every row with `overnight.build_queue_with_needs_human` (14 eligible / 76 needs_human / 8 default-skipped) |
| A2 docs | OW2-as-original-compiler claims removed (`game_random.c`, `mod_19470.toml`, `REFERENCES.md`); stale codegen.md sample text fixed |
| A3 promo guard | exact-set assertion → address-keyed staging guard (drops/renames/new entries/LOCKED_TOMLS removal still fail) |
| A4–A6 provenance | reproduced and fixed: checkout-rooted compiler tree + tool_sig, live tool_sig in the snapshot builder, `check_improved_record` fresh/stale/partial/malformed (never raises), `check_improved_snapshot`, `--check-improved`, fail-closed OMF digest, unknown git state ≠ clean, malformed reports/scores fail closed, embedded host paths rejected, verified-unresolved symbols reported, snapshot header checked against live identity |
| A7 E7 snapshot | historical artifact unchanged; revalidation `e7_snapshot_revalidation.json` (after `61470fa`): **0 fresh / 139 partial / 63 stale** — the 139 are legacy records without an audit-time symbol stamp or embedded OMF summary (`symbol_coverage` unchecked); the 63 stale ones (source_digest 63, symbols 19, declared_cflags 1) are attributed to M2 header changes and renames; all 202 need regeneration by a full `wc1.t3_audit` run; not integrated into Wave 4B |
| Progress | T3 **539**, DONE **912** (unchanged) |
| `make verify` | green on every commit (last serialized run at `61470fa`: 2411 passed, 11 skipped, 5 xfailed; Build A IDENTICAL, 539 functions from 534 C files) |

## Sessions

| Session | Role | Status / verdict | Wall (s) | Turns | Tools | Input (cached %) | Output | Reasoning | OpenCode session |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `dev-pc-01` | developer | COMPLETED | 495.243 | 63 | 65 | 5,641,937 (97.7%) | 23,448 | 25,793 | `ses_de4fba55dffeHpJjy1IyeMfaur` |
| `dev-rc-01` | developer | COMPLETED | 658.138 | 76 | 117 | 8,276,953 (98.0%) | 49,888 | 15,903 | `ses_de4f89dcaffeFdGTE94ZHgLvGU` |
| `dev-pc-02` | developer | COMPLETED | 319.054 | 40 | 60 | 2,834,223 (96.5%) | 16,287 | 9,101 | `ses_de4ed483cffe0ojvpueFIdo7a9` |
| `dev-pc-03` | developer | COMPLETED | 197.051 | 28 | 33 | 1,779,122 (95.6%) | 8,381 | 12,310 | `ses_de4e72721ffezjCuihw7iNphOD` |
| `rev-rc-01` | reviewer | APPROVE | 475.242 | 65 | 78 | 6,305,195 (97.3%) | 22,890 | 27,791 | `ses_de4e9d358ffeLykDwtxQpSZK9H` |
| `rev-rc-02` | reviewer | APPROVE | 226.032 | 26 | 45 | 1,497,305 (94.0%) | 8,037 | 14,624 | `ses_de4e0ed9affezjDJvu5YJo6CV1` |
| `rev-pc-01` | reviewer | REQUEST_CHANGES | 613.166 | 52 | 82 | 4,287,158 (97.0%) | 18,804 | 34,755 | `ses_de4e21e9fffeHLjPsEsj2MejxI` |
| `dev-pc-04` | developer | FAILED (OpenCode Go monthly limit, 429) | 2.001 | 0 | 0 | 0 (0%) | 0 | 0 | `ses_de4d7bf81ffeQGn4uUsx48I4ov` |
| **Total** | 8 sessions | 7 completed, 1 quota failure | 2985.9 | 350 | 480 | 30,621,893 (97.2%) | 147,735 | 140,277 | |

Accounting: `input = uncached + cache.read`; reasoning is separate from output; OpenCode Go quota percentages are unavailable locally. The Manager's own Claude usage is not instrumented here.

**Quota stop:** `dev-pc-04` (fixes for `rev-pc-01`'s findings) failed on its first request: *OpenCode Go monthly usage limit reached (resets in 13d 12h)*. Per the campaign rules (no Codex, no metered usage), the Manager implemented those three small fixes itself (`81eb7ec`), verified them with targeted tests and `make verify`, and they have **not** had an independent re-review.

## Review outcomes

- `rev-rc-01` (research, `cea804e..912f0b1`): **APPROVE**, 6 LOW + 6 INFO wording/precision findings, all resolved in `eb95430`/`d55d493`; `rev-rc-02` on the fix: **APPROVE**.
- `rev-pc-01` (production, `dae45bd..4ff89a3`): **REQUEST_CHANGES** — confirmed every reported defect fixed (9/9 reproduced on `dae45bd`, gone at HEAD), no weakened gates, invariants intact; raised one HIGH (records with `None` symbol addresses counted fresh) and two LOW (forged empty snapshot header accepted; malformed scores raised `TypeError`). Manager adjudication of the HIGH: the 9 records with `None` addresses are exactly the 9 non-dependency-clean records (`#None <= unresolved_count` in each); `None` records "absent from the symbol DB at mint" and the live check already proves it is still absent (appearance or disappearance makes the record stale), so the semantics were kept but made explicit (`unresolved_symbols`, `fresh_with_unresolved_symbols`, `dependency_clean`/`unresolved_count` consistency). Both LOWs fixed.
- `rev-pc-02` (Codex `gpt-6.2-sol` high, approved by the user after the OpenCode Go quota ran out; production, `dae45bd..c5755b0`): **REQUEST_CHANGES** — HIGH: snapshot rebuilds stamped symbol addresses from the build-time map rather than the audit's scoring map; MEDIUM: symbol coverage unprovable; 3 LOW (NaN scores, path-like symbol keys, absent-name vs unresolved-fixup terminology). Fixed by Codex `dev-pc-05` in `61470fa`; artifact regenerated in `78e3cf6`. Round 3: see docs/HISTORY.md.

## Operational notes

- The preserved runner's `verify` subcommand never dispatched (`--cmd` overwrote the subparser dest `cmd`); fixed in the local working copy only (the committed research artifact stays verbatim).
- Long verify labels made pytest tmp paths ~130 chars and a Watcom-under-Wine compile in `test_t4spec` failed with rc=5; short labels (`/tmp/wc1-vfy-a6`) pass. The first runs also saw `wine client error: recvmsg` while another (unrelated) session was compiling.
