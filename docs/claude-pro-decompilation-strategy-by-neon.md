# Making Warcraft I decompilation feasible on Claude Pro ($20)

Analysis by Gemini 4 Neon, 2026-11-20. Based on direct inspection of the repo (`HEAD` at `221be7c`), the existing strategy reports (`docs/claude-pro-decompilation-strategy-by-opus-5.5.md`, `docs/claude-pro-decompilation-strategy-by-sol-5.6.md`), raw Claude session JSONLs (`9b62d788`, `7fd2c9ac` + all 11 subagents), the 91 Warcraft sessions in `/home/artem/.local/share/opencode/opencode.db`, `/home/artem/.claude/settings.json`, and `wc1.progress` / `wc1.analysis` over the remaining 533 in-scope functions.

## 1. What the raw session logs actually show (4 findings the prior reports missed)

The immediate incident in `7fd2c9ac` is already documented: Opus launched 9 Sonnet analysts concurrently under a repo-wide `/goal` hook that cannot terminate (gate 3 is undefined), 7 were stopped after 8 minutes wasting ~58% of that session's spend, and the Stop hook burned 8 extra Opus turns after the user interrupted. Four deeper measurements from the raw traces explain the underlying economics:

### 1.1 The 5-hour window was already heavily spent *before* `7fd2c9ac` began

Session `9b62d788` (Opus 5.5, 21:30–22:30 UTC — the `make verify` speedup work) ran **83 Opus requests, 12.1M cache reads, 221.7k cache writes, and 91.5k output (~$10–$29 API-equivalent)** and ended 56 seconds before `7fd2c9ac` started (22:30–22:51 UTC, ~**$31–$35 API-equivalent** across Opus + 11 Sonnet runs). Together they consumed **563 requests, 2.01M cache-create, 63.79M cache-read, and 616k output (~$41–$64 API-equivalent)** inside the same 5-hour window.

### 1.2 Inside a *completed* Claude area (`mod_1b800`), 48% of the cost was brute-forcing T3 byte-matches on 3–4 stubborn functions — despite REPL batching already being enabled

`/home/artem/.claude/settings.json` has `CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1` (JS `REPL` + `Poll` batching) and `autoCompactWindow: 400000` (allowing context to grow unchecked to 246k). Even with REPL batching, the single completed Claude analyst (`agent-a3d137f81449df6ee.jsonl`, `mod_1b800`, 14 done functions: 11 T3 + 3 T4) burned **78 Sonnet requests, 246k peak context, 11.78M cache reads, and 102k output (~$5.99 API-equivalent, ~$0.43/function)**.

Turn-by-turn phase breakdown of `mod_1b800`:

| Phase | Turns | Cache create | Cache read | Output | API-equiv | Share |
|---|---:|---:|---:|---:|---:|---:|
| 1. Orientation / docs (T01–T02) | 2 | 30k | 26k | 0.5k | $0.13 | 2% |
| 2. Disasm / xrefs / 8 ad-hoc Python scripts (T03–T24) | 22 | 93k | 1.94M | 21.6k | $1.26 | 21% |
| 3. Header + TOML (T25–T28) | 4 | 10k | 0.50M | 11.9k | $0.37 | 6% |
| 4. **Initial C for all 18 functions + match setup** (T29–T32) | **4** | **7k** | **0.55M** | **2.3k** | **$0.23** | **4%** |
| 5. **T3 byte-match chasing on 3–4 functions** (T33–T68) | **36** | **76k** | **6.46M** | **43.0k** | **$2.87** | **48%** |
| 6. T4 difftests (T69–T74) | 6 | 16k | 1.35M | 10.4k | $0.62 | 10% |
| 7. Docs + final TOML (T75–T78) | 4 | 13k | 0.95M | 12.3k | $0.52 | 9% |
| **Total** | **78** | **246k** | **11.78M** | **102.0k** | **$5.99** | **100%** |

Writing the initial C for all 18 functions took 1 turn (T29) and $0.23. Nearly half the budget ($2.87, 36 turns, 6.46M cache reads) went to iterating on `snd_enemy_scan.c`, `unit_alert_suppress_area.c`, `fn_1bd04.c`, and `snd_event.c` at 143k–216k context — including writing a JS `perms()` generator in T53 to permute `int x, y, w, h, r, c;` — only to abandon T3 at T64 and move those functions to `*_reference.c` (T4) anyway.

### 1.3 OpenCode + DeepSeek confirms that T3 mismatch loops — not function count or model IQ — drive token burn

Across 91 OpenCode sessions on this repo:
- `deepseek-v4.1-flash` (55 sessions across variants): **1.41B cache-read, 13.9M fresh input, 2.16M output, 3.70M reasoning tokens**.
- `qwen3.8-flash` (27 sessions): **228M cache-read, 1.44M output**.
- Per-area DeepSeek sessions averaged **193–314 assistant turns** and **43M–93M cache reads** (~5–8× more context tokens per area than Claude Sonnet's 11.8M for `mod_1b800`).

Comparing two completed DeepSeek areas exposes the real cost driver:
- `STATUS.C` (**81 functions**): 61.4M cache reads (**0.76M/function**), 203 turns — mostly short, regular functions that matched on tries 1–2.
- `mod_24860` (**10 functions**): 82.8M cache reads (**8.28M/function**), 280 turns — 11× more tokens per function because of T3 mismatch loops.

DeepSeek proved that **when surrounded by strong mechanical oracles (`wc1.match` + `wc1.cemu`), frontier intelligence is not the bottleneck**; the `O(T²)` chat loop around exploration and compiler trial-and-error is.

### 1.4 The remaining 533 functions are skewed small/partially-done — and 1,699 Ghidra drafts sit unused on disk

From `wc1.progress` + `wc1.analysis` at `HEAD` (`477 / 1010` done = 47.2%, **533 undone**, 26,999 total instructions, avg **50.7 insns/function**):

- **By missing work:**
  - `('C-vs-original difftest',)` only: **59 (11.1%)** — already named, reference C already written (`NETWORK.C` 22, `PLAYFLIC.C` 18, `mod_16390` 12, `mod_2efd0` 4, `mod_13f60` 2, `PACKET.C` 1).
  - `('C',)` only: **165 (31.0%)** — already semantically named (`mod_13f60` 43, `mod_16390` 20, `mod_2ced0` 12, `PLACEBOX.C` 11, `SND.C` 8, `mod_2c4e0` 8, …).
  - `('name', 'C')`: **308 (57.8%)** (plus 1 needing `'name'` only).
- **By instruction count:**
  - `<= 15` instructions (trivial): **125 (23.5%)**
  - `16–40` instructions (small): **177 (33.2%)** — **56.7% (302 / 533) are `<= 40` instructions**
  - `41–100` instructions (medium): **157 (29.5%)**
  - `101–250` instructions (large): **69 (12.9%)**
  - `> 250` instructions (huge): **5 (0.9%)**
- **Unused Ghidra export:** `build/ghidra/decomp/` already contains **1,699 decompiled `.c` files**, yet `mod_1b800` never read them and spent 22 turns manually decoding assembly from scratch. The project rule (*"Ghidra output is a hint, never evidence"*) forbids citing Ghidra in TOML `evidence` — it does **not** forbid feeding Ghidra's C as a free structural draft whose reconstructed C is then mechanically proven by `wc1.match` or `wc1.cemu`.

## 2. Why "just switch to Haiku" or "cap at 2 agents" does not solve the economics

- **Swapping Sonnet → Haiku inside the same 78-turn loop** still resends 150k–240k of history per turn (`O(T²)` cache reads), and Haiku takes more turns to converge on Watcom 10.0a codegen idioms, eroding much of the per-token savings.
- **Capping concurrency to 1–2 agents** eliminates the 58% parallel-cancellation waste, but still leaves ~$6/module (~$200–$250 API-equivalent for the remaining 533 functions) — slow and fragile against Claude Pro's 7-day cap.

The 10–15× lever is removing the two tasks LLMs are most expensive at:
1. Interactive repository exploration (21% of `mod_1b800`), and
2. Brute-force compiler search for Watcom 10.0a register allocation and statement order (48% of `mod_1b800`).

## 3. Four feasible orchestration architectures for a $20 Claude Pro plan

### Option A: Local Decomp-Permuter + Stateless Module-Batch Pipeline (Pure Claude Pro, highest ROI)

Extends the compiler-driven stateless pipeline with two missing levers: **module-level batching** and a **local score-guided permuter** (analogous to `decomp-permuter` used in N64/GC matching decompilations).

- **Local Watcom 10.0a permuter (`wc1.permuter`, 0 LLM tokens):**
  Watcom 10.0a compiles in ~0.13 s/file across CPU cores (`docs/subsystems/compiler.md`). Instead of spending 36 LLM turns permuting local declarations at 200k context, a local Python hill-climber takes Claude's first-draft C and tests **50–300 deterministic mutations in 3–10 seconds for $0**, scoring candidates by instruction diff distance (separating opcode/structural mismatches from register-only mismatches):
  - flag presets (`OPT`, `OPT + -oa`, `DBG`, `OD`, `OD + -d1+`),
  - local variable declaration order permutations (the primary Watcom 10.0a register-allocation lever),
  - `int` ↔ `short` / signed ↔ unsigned loop indices,
  - `volatile` / dword-view reads (`mov eax, [addr-2]; sar eax, 16`),
  - bitfield vs mask (`test byte` under 10.0a),
  - `for` ↔ `while` ↔ `do-while`, `++i` ↔ `i++`, branch polarity, local temp reuse.
- **Stateless Claude invocation on Pro OAuth with shared prompt-cache prefix:**
  Claude Code `2.1.326` supports:
  ```sh
  claude -p --safe-mode --tools "" \
    --exclude-dynamic-system-prompt-sections \
    --no-session-persistence \
    --model sonnet --effort medium \
    --output-format json --json-schema <schema>
  ```
  - `--safe-mode --tools ""` keeps Pro OAuth authentication (unlike `--bare`, which requires an API key) while disabling MCP servers, hooks, memory, and the multi-turn tool loop.
  - `--exclude-dynamic-system-prompt-sections` plus an identical prefix (`compact rules + war.h + module header`) allows sequential stateless calls within the same module to hit the 5-minute prompt cache without carrying `O(T²)` chat history.
- **Batch by *module* (6–15 functions per call), not 1 call per tiny function:**
  Since 57% of remaining functions are `<= 40` instructions, an entire 15-function module is ~700 instructions (~10–15k input tokens including Ghidra drafts and xrefs).
  1. **Call 1 (Sonnet medium) — Module semantic pass:** Input = one pre-built module dossier (`wc1.dossier`). Output = JSON of semantic names, prototypes, struct definitions, evidence (citing only disassembly addresses/strings, never Ghidra), and confidence. Python generates `<area>.toml` and `<area>.h` and validates via `wc1.symbols`.
  2. **Call 2 (Sonnet low/medium) — Batch C generation:** Input = Stage 1 header/names + symbolic disasm + `build/ghidra/decomp/*.c` drafts + 2 matched 10.0a exemplars for the module's codegen flags. Output = all 10–15 C functions in one JSON payload.
  3. **Local pass (0 tokens):** `wc1.match` on all functions → `wc1.permuter` on every mismatch.
  4. **Calls 3–5 (Sonnet medium, only remaining mismatches, capped at 1–2 retries/fn):** Fresh ~6k-token call containing *only* that single function's C and a side-by-side instruction diff (`wc1.match --diff`). If still unmatched after 2 tries → **hard cutoff**, auto-record the exact first-difference instruction as `t3_blocker`, route to T4.
  5. **Call 6 (Sonnet low):** Declarative T4 test specs for non-T3 functions + concise subsystem doc.
- **Resumable ledger & quota gating:** A JSONL/SQLite ledger tracks per-function state (`queued → named → drafted → permuted → t3|t4 → verified → committed`). The driver checks the 5h usage percentage (same fields as `/home/artem/.claude/statusline-command.sh`) and stops cleanly around 70–80%, losing at most one in-flight call.
- **Estimated cost:** **~$0.40–$0.60 API-equivalent per 15-function module** (6–8 calls, ~70k total tokens vs $5.99 / 78 calls / 12.1M tokens in `mod_1b800`) → **~$15–$25 API-equivalent across all 533 remaining functions** (12–15× reduction on Sonnet, comfortably feasible on a $20 Pro plan over a few weeks).

### Option B: Strict "T4-First / 1-Shot T3" Staging (Same Rules, Halves Spend Immediately)

`docs/GOAL.md` already defines `DONE = semantic name AND (T3, OR T4 with t3_blocker)`. Trying T3 with 10.0a + `codegen.md` idioms is required; spending 36 LLM turns per stubborn function is not.

- Enforce a mechanical **2-attempt T3 budget per function** (initial C + local `wc1.permuter` + at most 1 diff-guided repair call).
- Easy/medium functions (~60–70% of the remaining 533, especially the 302 functions `<= 40` insns) become T3 immediately.
- Stubborn register-allocation functions immediately become `*_reference.c` + exact `t3_blocker` + T4 difftest, reaching Gate 1 at half the token cost.
- After Gate 1 (or with leftover weekly quota), run an offline `wc1.permuter` sweep + targeted T3-upgrade pass over `ref` functions if desired.

### Option C: Keep Interactive Claude Code, Fix the Bottlenecks (Lowest Engineering Effort)

If you prefer staying inside normal interactive Claude Code without maintaining a headless `claude -p` driver, three small shared tools plus session hygiene still deliver a **5–8× reduction**:

1. **Drop the Opus coordinator, parallel subagents, and repo-wide `/goal`.** Run directly in a fresh `/clear` **Sonnet** session per module (`effort: medium`, lower `autoCompactWindow` from `400000` to `120000` or `/clear` after each module). Paying Opus to spawn and supervise a single Sonnet subagent is pure overhead.
2. **Pre-generate `wc1.dossier <module>` before prompting Claude** (replaces T01–T24). Claude starts with a single `Read` of `build/<area>/dossier.md` instead of 22 exploratory turns and 8 ad-hoc Python scripts.
3. **Use `wc1.match --diff` and `wc1.permuter` from Bash** (replaces T30–T68 and eliminates per-area `*_dis.py` / `*_match.py` copies).
4. **Hard-cap T3 retries in the module prompt** (2 manual attempts + permuter → T4).
5. **Enforce max concurrency = 1 in `.claude/hooks/subagent_guard.py`** (or block subagents altogether during single-module work).

Expected cost: drops from **78 turns / $5.99** to **~12–18 turns / $0.80–$1.20 per module** (4–6 modules per 5h Pro window with zero discarded work).

### Option D: Asymmetric Hybrid — Stateless DeepSeek/OpenCode Engine + Claude Pro Architect/Auditor

OpenCode Go (`deepseek-v4.1-flash`, `qwen3.8-flash`, `glm-5.3`) only hit its weekly quota because its chatty 250-turn agent loop burned 1.4B tokens.

- Plug **OpenCode/DeepSeek** into **Option A's stateless packet pipeline** for the high-volume mechanical stages (Stage 2 C drafting, Stage 4 mismatch retries, T4 test scaffolding). Cutting OpenCode's per-area burn from ~65M → ~2M tokens keeps it well under its weekly cap too.
- Spend **$20 Claude Pro** exclusively where frontier reasoning actually moves the needle:
  1. **Module semantic naming, struct layouts, and evidence audits** (catching incorrect claims like the 6 errors the crashed session left in `save_score.toml`),
  2. **The 74 large functions (`> 100` insns) and 5 huge functions (`> 250` insns)**,
  3. **Hard `t3_blocker` puzzles, shared epilogues, and M3 all-C build / T5 scenario design.**

Claude spend drops to **~$0.10–$0.20 per module** (~30× lower than today) while achieving higher semantic accuracy than DeepSeek alone. *(Skip if the constraint is strictly Claude-only.)*

## 4. Split the remaining 533 functions into 4 specialized workstreams

Whichever orchestration option (A–D) is chosen, stop running the same monolithic analyst loop on every remaining function:

| Workstream | Count | Share | What is actually missing | Lowest-cost strategy |
|---|---:|---:|---|---|
| **1. `ref`-only (missing difftest)** | 59 | 11.1% | `wc1.cemu` tests only (`NETWORK.C` 22, `PLAYFLIC.C` 18, `mod_16390` 12, `mod_2efd0` 4, `mod_13f60` 2, `PACKET.C` 1) | Declarative table-driven `wc1.cemu` runner (auto-stubs callees from xrefs + randomized/edge inputs). ~1 short Claude call per module for non-trivial preconditions instead of 335-line pytest files. |
| **2. Already named, missing C** | 165 | 31.0% | C only (`mod_13f60` 43, `mod_16390` 20, `mod_2ced0` 12, `PLACEBOX.C` 11, `SND.C` 8, `mod_2c4e0` 8, …) | Skip Stage 1 entirely. Feed Ghidra draft + disasm + existing TOML prototype directly into batch C generation + `wc1.permuter`. |
| **3. Small unnamed (`<= 40` insns)** | ~180–200 | ~35% | Name + short C (e.g. `mod_20c30` 32 fn avg 24 insns; `mod_1dca0`, `mod_1e9a0`, `mod_13b30`) | High-density batches of 15–20 small functions in 1 prompt with Ghidra drafts. Most T3-match on Try 1. |
| **4. Medium/large unnamed (`> 40` insns)** | ~110–130 (only 5 `> 250`) | ~23% | Genuine RE judgment + C | Standard Option A/C pipeline with hard 2-try T3 cutoff; escalate only the ~10–15 hardest to Opus. |

Clearing Workstreams 1 and 2 first knocks out **224 / 533 functions (42% of the entire remaining backlog)** with almost zero reverse-engineering discovery cost.

## 5. The 4 shared tools to build first (high leverage for every option)

`tools/wc1/` already accumulated 8 duplicate per-area scripts (`bullet_dis.py`, `bullet_match.py`, `mod_1b800_dis.py`, `mod_2efd0_dis/match/cmp.py`, `mod_104b0_match.py`, `net_match.py`) because `wc1.match` only reports `byte +0x2a: got 89 want 8b` and there is no one-shot packet generator. Four small shared tools pay for themselves within 1–2 modules:

1. **`tools/wc1/dossier.py` (`python3 -m wc1.dossier <module|addrs>`)**: Emits one compact, token-budgeted markdown/JSON dossier per module containing auto-detected codegen flags (`codegen_survey`), symbolic disassembly (`wc1.func`), `build/ghidra/decomp/` draft, callers/callees with DB prototypes, referenced strings and data symbols, and relevant `src/include/*.h` structs. Eliminates 20+ exploratory turns per area.
2. **`wc1.match --diff <file.c>`**: Side-by-side Capstone instruction diff of original vs compiled object, classifying **register-only**, **immediate/offset**, and **opcode/structural** mismatches plus the exact first-difference original address (directly usable in `t3_blocker`). Eliminates all per-area `*_dis.py` / `*_match.py` scripts and makes 1-shot diff repairs sharply more accurate.
3. **`tools/wc1/permuter.py` (`python3 -m wc1.permuter <file.c>`)**: Multi-core local Watcom 10.0a hill-climber (0 tokens, ~5 s/fn) searching local declaration permutations, compiler flag presets, `short`/unsigned widths, `volatile`/dword-view reads, bitfields, and loop shapes. Directly attacks the **48% T3-chasing cost** measured in `mod_1b800`.
4. **Declarative `wc1.cemu` T4 test runner (`tools/wc1/t4spec.py`)**: Replaces 300+ lines of repetitive per-area pytest boilerplate with compact declarative specs (`func`, `c_file`, `args_gen`, `stub_callees`, `watch_addrs`), cutting both T4 output tokens and the cost of clearing the 59 pending `ref` functions.

## 6. Recommended execution sequence

1. **Immediate config hygiene (zero code):** In `/home/artem/.claude/settings.json`, set default `model` to `sonnet`, `effortLevel` to `medium`, and reduce `autoCompactWindow` (or `/clear` after every module). Never run repo-wide `/goal` while Gate 3 is undefined. Harden `.claude/hooks/subagent_guard.py` to enforce max 1 concurrent analyst.
2. **Build the 4 shared tools** (`wc1.dossier`, `wc1.match --diff`, `wc1.permuter`, `wc1.t4spec`) in one focused session.
3. **Benchmark on `BULLET.C` (already partially drafted untracked) + `mod_2b8e0`:**
   - **Pure Claude Pro path:** Run **Option A** (stateless `claude -p --safe-mode --tools "" --exclude-dynamic-system-prompt-sections` + `wc1.permuter` + hard 2-try T3 cutoff + ledger). Acceptance bar: **< $0.75 API-equivalent and `<= 8` Claude calls per 15-function module**.
   - **Interactive Claude Pro path (no custom driver):** Run **Option C** (one fresh Sonnet session per module fed by `wc1.dossier` + `wc1.permuter`).
   - **Hybrid path (fastest & cheapest overall):** Run **Option D** (stateless OpenCode/DeepSeek on Workstreams 1–3; Claude Pro on semantic naming/audits, Workstream 4, and M3).
4. **Execute in ROI order:** Workstream 1 (59 `ref`-only difftests) → Workstream 2 (165 named-no-C) → Workstream 3 (small unnamed in 15-fn batches) → Workstream 4 (large unnamed) → M3 all-C build & T5 scenario set.
