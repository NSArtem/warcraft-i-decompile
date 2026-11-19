# Making this project fit a $20 Claude plan

Analysis by Claude Opus 5.5, 2026-11-20. No repo changes were made for it.

## What the logs show

**The 20-minute session that used up the window (`7fd2c9ac`)**
- At 22:32:26 the Opus main session started **9 Sonnet analysts at once**. That goes against the "max two agents" memory: a memory note is not something the harness enforces.
- In 8 minutes they ran 1,851 turns: 49.4M cache-read tokens, 1.7M cache-write and 0.5M output. Seven were stopped together at 22:40:38.
- Only two produced anything: mod_1b800 (committed as 7ed9ee1) and the BULLET.C files that are still untracked. **About 60% of the tokens went to work that was thrown away.** The same thing happened on 11-19 ("six cancelled analysts, nothing to resume").
- Each subagent starts with **~26k tokens of context before doing anything** and averages 20–41k per turn. **The cost is roughly turns × ~30k.** The mod_1b800 agent took 386 turns for 14 finished functions, about 28 turns and ~840k cache-read tokens per function.
- Most turns are small steps that could be batched:

  | Agent | Command calls |
  |---|---|
  | mod_19b80 | 101 × grep |
  | mod_1b800 | 78 × wc1.match |
  | NETWORK | rewrote its test file with Write until it had written 550k characters |

- Each area also writes its own private copy of the disassembly and match tooling. The tool list has `bullet_dis`, `bullet_match`, `mod_1b800_dis`, `mod_2efd0_dis`/`_match`/`_cmp`, `mod_104b0_match`, `net_match`, and the agents also used a `snd_match`. The agent rules forbid touching shared tools, so every agent pays to rebuild the same thing.
- The earlier Opus session (`9b62d788`) made 190 single-file Reads on Opus (12M cache-read tokens). Opus is expensive to use for reading files.

**DeepSeek / OpenCode**
- About **1.4 billion** cache-read tokens, 14M fresh input and 2.2M output across ~90 sessions.
- The one "make goal pass" session with 22 subagents used 896M tokens; each area took 25–95M.
- **Per area, Claude Sonnet was actually 4–7× more token-efficient than DeepSeek** (mod_1b800 took 12M). DeepSeek only seemed cheap because its plan doesn't meter tokens, so the waste never showed.
- Copying the DeepSeek workflow onto Claude would need roughly 25–30 windows.

**What that means:** a capable model isn't the bottleneck. Two other things are:
1. Running a chatty agent loop where every grep or compile costs ~30k tokens of re-read context.
2. Starting many agents at once under a hard limit, so the window ends in many half-done pieces of work that can't be resumed.

## Proposals, highest impact first

### 1. Treat each function as a single model call, driven by a script
Matching a function is mostly searching for the C that compiles to the right bytes. A script can run that search and call the model only to write the C.

- **A deterministic driver** (a Python tool) builds a self-contained packet for one function:
  - the disassembly;
  - callers and callees with their known names and prototypes;
  - data references with their symbols;
  - the relevant `war.h` types;
  - 2–3 already-matched neighbouring functions as style examples.
- **The model is called statelessly** with that packet:
  - `claude -p --bare --system-prompt-file rules.txt --tools "" --model haiku`;
  - run from a directory with no `CLAUDE.md`, so nothing gets imported;
  - no tools, no multi-turn loop: packet in, C out.
- **The driver compiles and matches under both compilers itself.** On a mismatch it first tries the 10.0a spellings from `codegen.md` on its own (bitfields, a volatile/dword-view read, a `short` loop index, the OD frame flags). Those are fixed rewrites and need no model. Only then does it send back a **compact diff** (the differing instructions only) for at most 2–3 retries.
- **Escalation:** Haiku, then Sonnet. Whatever is still unmatched goes into a blocker queue that a strong model or you look at in a batch.
- **Same fixed prefix for every call** (rules, then `war.h`, then examples), and a module's functions run one after another. The shared part then stays in the prompt cache.
- **A ledger file records each function's result.** A quota stop then loses at most one function; the next window picks up where the last one stopped.
- **Similar functions** (the 20 packet senders, dialog handlers) are handled once as a template and then filled in for the others.

My estimate is ~10k tokens in and ~1.5k out per attempt, so **~20–40k raw tokens per function versus ~1M now**. Weighted for cache-read discounts it's maybe 4–8× cheaper, plus no waste from parallel runs. The remaining 547 functions would come to about 2–3 windows of model time instead of 8+ (with zero waste) or 20+ (as things run now). This is a rough estimate.

The judgment work (naming, evidence, area docs) stays with a Sonnet session. It runs once per area over the driver's results, not inside the matching loop.

### 2. Flip the roles: Claude plans and reviews, DeepSeek does the volume
DeepSeek has already shown it can do the area work. Its tokens cost you nothing extra; Claude's are what's scarce. `opencode run` exists and supports `--agent`, `--format json`, `--worktree` and `--auto`.

- **A Claude session (Sonnet, or Opus once per area)** handles the judgment:
  - writes the brief: module boundaries, hypotheses, acceptance criteria;
  - starts `opencode run --agent wc1-analyst --worktree <area> --format json "<brief>"` in the background;
  - reads only three things from the result: the final report, the TOML diff (the claims and their evidence), and the `make verify` result;
  - approves or sends back a correction, then commits.
- **Claude's cost per area** would be maybe 50–150k tokens, against ~12M for a Sonnet analyst doing the work itself. That is about 100× less.
- It also spends Claude where it is better than DeepSeek: checking evidence, catching confidence claims that are too high, choosing semantic names.

This is the cheapest option overall. It only fails the "with Claude" condition if that means Claude-only.

### 3. If you keep Claude Code subagents, fix the setup
- **Enforce the limit in the hook, not in a memory note.** `subagent_guard.py` already intercepts `Agent`; it could refuse a third agent while two are running.
- **Work in function-sized units, one or two at a time,** each recorded in a ledger or commit as it finishes. Parallel agents don't make anything faster under a fixed window; they just spend it sooner.
- **One shared tool that gathers everything for a function in one call** (dis + xrefs + names + data symbols + match status), plus a `wc1.match` mode that prints a compact diff. This replaces the per-area `*_dis.py`/`*_match.py` copies and the 100-grep loops. It's one shared-tool commit, made once.
- **Smaller agent setup:** a `tools:` allowlist in the agent frontmatter, no claude.ai MCP connectors (Gmail, Drive, Slides and others are attached to this project), and an instruction to batch lookups and use Edit instead of Write.

This alone might cut costs 2–3×. It's useful, but it doesn't change the basic economics the way 1 or 2 does.

### 4. Use Opus only where nothing else works
Use it for the t3_blocker cases (like 0x231cc/0x231ec, HLine/VLine), reviewing area naming, and decisions about module boundaries, done in one batch per day. Don't use it as the orchestrator that reads files.

## Recommendation
Start with **1 and add 2's review step** (Claude reviews the claims; the match search runs as a script). If you're fine with DeepSeek doing bulk work, **2 alone** is the quickest way back to making progress.

Either way, the first thing to build is the same: the shared per-function context tool plus the ledger. Every option needs it, and its absence explains much of the turn count.
