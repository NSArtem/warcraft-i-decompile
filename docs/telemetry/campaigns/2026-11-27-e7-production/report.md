# Production Campaign Telemetry — E7 Compiler Presets & Deterministic T3 Promotions

- **Campaign ID:** `2026-11-27-e7-production`
- **Repository:** `NSArtem/warcraft-i-decompile`
- **Starting `main` commit:** `e14d5c0a5d37d2f85ffcfcc311008004bb5c40da`
- **Implementation branch:** `feature/e7-compiler-presets` (not auto-merged into `main`)
- **Verified code commit:** `5667e2f76a53090dd2077d0047a967cdf30d08de`
- **Manager / Analyst:** Gemini 4 Neon (High) via Antigravity (`fa9c6210-2ce0-46fb-9a09-fc614e3329d7`)
- **Developer / Reviewer:** `opencode-go/deepseek-v4.1-flash` via `opencode2 v2.4.1` (fresh isolated sessions)

---

## 1. Outcome Summary

| Metric | Before (`main` `e14d5c0`) | After (`5667e2f`) | Delta |
|---|---:|---:|---:|
| In-scope T3 (`src =`, built from C) | 519 (518 `10.0a`, 1 `ow2`) | **532** (531 `10.0a`, 1 `ow2`) | **+13 T3** |
| In-scope T4 (`ref =` + difftest) | 385 | **372** | **-13 T4** |
| Unchecked `ref` | 6 | 6 | 0 |
| `DONE` (named + T3, or T4 + blocker) | 899 (89.0%) | **899** (89.0%) | 0 (T4→T3 promotions) |
| Watcom `10.0a` search presets (`permuter.FLAG_PRESETS`) | 8 (`10.0a`) + 1 (`ow2`) | **14** (`10.0a`) + 1 (`ow2`) | **+6 presets** |
| Build A (`wc1.build` + `wc1.compare`) | `IDENTICAL` (`519` fns / `514` files) | **`IDENTICAL` (`532` fns / `527` files, `0` legacy)** | +13 fns / +13 files |
| `make verify` (`nix develop -c make verify`) | green | **green (`57.814 s`, `2284 passed, 11 skipped, 5 xfailed`)** | +46 tests |

- **Added Watcom `10.0a` presets** (single source of truth in `tools/wc1/permuter.py`, preserving default `-s -ot -ol -4r -zp2` at index 0, all 8 original `10.0a` presets, `match.DEFAULT_CFLAGS`, and native OW2 fallback):
  - `-s -ot -ol -5r -zp2` (`c06`, placed before `c07` for minimal `-4r → -5r` diff)
  - `-s -ot -oa -ol -5r -zp2` (`c07`)
  - `-s -ot -ol -5r -d1+ -zp2` (`c19`)
  - `-s -os -4r -zp2` (`c22`, completes E7 Tier 1)
  - `-s -ot -ol -3r -zp2` (`c10`, E7 Tier 2)
  - `-s -ot -ol -4r -of+ -zp2` (`c26`, E7 Tier 2)
- **Task C residual T4 snapshot:** `t4_improved_audit.json` contains **202** improved residual T4 `MISMATCH` functions (**193** dependency-clean), with checkout-portable `sys:`/`repo:` source digests, strict report provenance enforcement, and `omf_deps_sha256` validation (**202/202 fresh** in independent checkouts). No residual T4 canonical flags were altered.

---

## 2. Atomic Commits on `feature/e7-compiler-presets`

1. `196153c121c5519c0f59a58edac5656a5a43e40c` — `wc1.permuter/t3_audit/wave4: add E7 10.0a presets and preset-aware audit invalidation + tests`
2. `2b10939b8a99c1db019c4e77794b41f52fbb7de1` — `T3: promote 13 verified E7 Watcom 10.0a -5r candidates (519 -> 532 T3, Build A IDENTICAL)`
3. `59efdd2888d9baf6ae59141d212660d7c0d7ecc8` — `wc1.t3_audit: add provenance-checked improved-T4 audit snapshot for Wave 4B + tests`
4. `5667e2f76a53090dd2077d0047a967cdf30d08de` — `wc1.t3_audit: make improved-T4 digests checkout-portable and enforce report provenance (rev-e7-01 fixes)`

---

## 3. Session & Resource Telemetry

Note on accounting semantics:
- **OpenCode2 (`opencode2 v2.4.1`, `opencode-go/deepseek-v4.1-flash`):** `input_tokens = uncached_input + cache.read` (normalized prompt tokens); `reasoning_tokens` is reported separately from `output_tokens`. `reasoning_time_s` and OpenCode Go subscription quota % are **unavailable** locally.
- **Antigravity Manager (`Gemini 4 Neon`, High):** `normalized_prompt_tokens = uncached_input + cache_read`; `output_tokens` includes thinking/reasoning. `reasoning_time_s` and Antigravity subscription quota % are **unavailable** locally.

| Session ID | Role | Harness / Model | OpenCode / AGY Session ID | Status / Verdict | Wall (s) | Turns / Reqs | Tool Calls | Norm. Prompt Tokens | Cache-Read % | Output Tokens | Reasoning Tokens | Commits |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `manager` | manager | `antigravity-cli` / Gemini 4 Neon (High) | `fa9c6210-2ce0-46fb-9a09-fc614e3329d7` | Active (snapshot) | *(campaign)* | 34 | 0 | 8,686,927 | 95.9% | 65,935 | *(incl. in out)* | telemetry commit |
| `dev-e7-01` | developer | `opencode2 v2.4.1` / `opencode-go/deepseek-v4.1-flash` | `ses_de67123cdffe3551P1qZSjYeQq` | `COMPLETED` | 561.825 | 86 | 93 | 7,266,655 | 98.3% | 27,238 | 13,528 | `196153c`, `2b10939`, `59efdd2` |
| `rev-e7-01` | reviewer | `opencode2 v2.4.1` / `opencode-go/deepseek-v4.1-flash` | `ses_de6673c0fffeBgCrJ1QRFa6ne6` | `COMPLETED` / **`REQUEST_CHANGES`** | 1329.589* | 63 | 81 | 5,247,277 | 97.5% | 16,428 | 31,919 | — |
| `dev-e7-fix-01` | developer | `opencode2 v2.4.1` / `opencode-go/deepseek-v4.1-flash` | `ses_de651d229ffeFD1Kt462oCvDyf` | `COMPLETED` | 403.715 | 50 | 55 | 3,653,767 | 97.1% | 14,952 | 21,101 | `5667e2f` |
| `rev-e7-02` | reviewer | `opencode2 v2.4.1` / `opencode-go/deepseek-v4.1-flash` | `ses_de64ab406ffeZAJiDN1XiPSDxd` | `COMPLETED` / **`APPROVE`** | 470.774 | 72 | 91 | 7,008,480 | 97.8% | 18,856 | 34,792 | — |
| **Subagent Total** | **4 sessions** | `opencode2 v2.4.1` / `deepseek-v4.1-flash` | **0 timeouts / 0 replacements** | **2 dev / 2 rev** | **2,765.903** | **271** | **320** | **23,176,179** | **97.8%** | **77,474** | **101,340** | **4 commits** |

*\*Operational note on `rev-e7-01`:* After emitting its complete review report and `VERDICT: REQUEST_CHANGES` (~8.5 min active work), `opencode2` entered `background_wait` due to a leftover child shell process waiting on an unclosed heredoc `EOF`. Terminating that child PID allowed `opencode2` to exit cleanly (`exit_code: 0`) without triggering a timeout or continuation.

---

## 4. Independent Review Outcomes

- **Round 1 (`rev-e7-01` on `59efdd28`):** **`REQUEST_CHANGES`** — Confirmed Tasks A & B cleanly (`323` targeted tests, `13/13` T3 matches, `Build A IDENTICAL`), and caught two real Task C defects:
  1. **HIGH:** `wave4_fp.unit_source_digest()` hashed absolute paths, causing `t4_improved_audit.json` to verify `202/202` in the producing worktree but `0/202` in the review worktree.
  2. **MEDIUM:** `improved_t4_records()` stamped current presets/base flags without validating report completion, cleanliness, or options, allowing stale/dirty reports to pass freshness.
  3. **LOW:** `omf_deps_sha256` was unvalidated; 3 newly promoted C files kept stale `"Reference C (T4) / not built"` comments.
- **Round 2 (`rev-e7-02` on `5667e2f7`):** **`APPROVE`** — Confirmed all Round 1 findings resolved (`202/202` fresh in review worktree and in a relocated copy; adversarial report-laundering probes rejected `0` records; `omf_deps_sha256` fail-closed; 3 comment-edited files `MATCH` + compile-check clean; `276` targeted tests passed; `Build A IDENTICAL`). Zero CRITICAL/HIGH/MEDIUM findings remain.

---

## 5. Serialized Final Verification (`make verify`)

- **Command:** `nix develop -c make verify` (serialized under `make_verify.lock`, wait `0.001 s`)
- **Commit verified:** `5667e2f76a53090dd2077d0047a967cdf30d08de`
- **Duration:** `57.814 s` (`exit_code: 0`)
- **Results:**
  - `wc1.symbols`: `1370 functions, 954 data symbols`
  - `wc1.roundtrip`: PASS
  - `wc1.match --all`: `527 files, 0 failed`
  - `wc1.match --compile-check`: `879 files x 2 compilers, 0 failures`
  - `wc1.build` + `wc1.compare`: `built build/war.exe: 532 functions from 527 C files (527 placed in sequence, 0 legacy layout)` → `IDENTICAL (loaded image, entry, stack, fixups)`
  - `pytest -n auto`: **`2284 passed, 11 skipped, 5 xfailed in 45.32s`**
