# Making Warcraft I decompilation feasible on Claude Pro

Yes—this project can plausibly continue on Claude Pro, but not with the current “Opus coordinator + many autonomous Sonnet analysts” architecture. The workable design is to make the compiler, matcher, emulator, and a small deterministic controller do the orchestration; Claude becomes a bounded source-generation and semantic-analysis component.

No project source or configuration changes were made during the analysis. The existing untracked BULLET.C work was preserved.

## What actually consumed the window

The expensive Claude session ran for about 21 minutes:

| Measurement | Result |
|---|---:|
| Claude sessions | 1 Opus coordinator + 11 Sonnet agent runs/restarts |
| Unique model requests | 480 |
| Context input/cache counters | 53.5M tokens |
| Output | 524.8k tokens |
| Thinking | 282.8k tokens |
| Committed result | one area: 11 T3 + 3 T4 |
| Cancelled first-wave agents | 7 |
| Context spent by those cancelled agents | 30.2M, or 56% |
| Output from those cancelled agents | 308k, or 59% |
| Extra `/goal` calls after “stop” | 8 Opus requests, 754k cache reads |

Each analyst eventually carried 150–246k tokens of context. Every grep, file read, `wc1.match`, rewrite, and test iteration resent that growing history. Anthropic documents precisely this behaviour: every turn includes the conversation so far, project context, and the new request. [Claude Code usage documentation](https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code)

The fatal sequence was:

1. The repo-wide `/goal` launched nine Sonnet analysts concurrently.
2. Seven independently read the same methodology, guides, examples, symbols, and code.
3. They were stopped around eight minutes later.
4. Their edits were reverted into temporary storage.
5. Two replacement agents then had to reload the same context.
6. The global goal hook continued calling Opus after the user explicitly stopped.

The global goal was also structurally unsuitable: `docs/GOAL.md` says gate 3 is undefined and requires user approval. A persistent “make all gates pass” hook therefore cannot terminate autonomously.

## What the DeepSeek run proves—and does not prove

The seven-hour OpenCode/DeepSeek campaign was highly productive: it moved the project from 156 to 463 done functions. But it used:

- 23 sessions;
- 992M cache-read tokens;
- 8.47M fresh input tokens;
- 1.46M output tokens;
- 2.52M reasoning tokens;
- 17 successful and 6 failed sessions.

So it proves that lower-intelligence models can perform this mechanical work when surrounded by strong mechanical verification. It does **not** prove that the existing orchestration is token-efficient. OpenCode succeeded by tolerating almost a billion cached-context tokens until its weekly quota finally stopped it.

Claude reproduced approximately the same token-flood pattern, but against a much smaller Pro allowance.

## The instructions are not the primary problem

The combined `AGENTS.md`/`CLAUDE.md` setup passes the quick audit; `AGENTS.md` scores approximately 45/47, grade A, on the full audit. `CLAUDE.md` correctly imports it rather than duplicating it.

The always-read instructions and required documentation total about 5,300 words. That is not negligible, but it cannot explain agents reaching 150–246k contexts. The dominant cost was the interactive tool loop.

The two conscious instruction costs are the always-loaded evolving status/next-steps block and requiring every analyst to read several general documents plus a complete finished-area example. A generated task packet can replace most of that for workers without weakening the owner’s safety rules.

## Recommended architecture: compiler-driven batch reconstruction

The central change is:

> Claude does not browse, grep, compile, or iterate interactively. A deterministic controller gathers evidence, calls Claude for a bounded transformation, and validates the result itself.

### 1. Generate compact function packets mechanically

For each function or small related family, a tool produces a self-contained packet containing:

- symbolic disassembly and control-flow structure;
- callers, callees, prototypes, and calling convention;
- referenced strings and data symbols;
- known structure fields;
- module compiler flags;
- one or two relevant matched examples;
- the exact expected output schema.

The model never needs to search the repository. It sees only the packet.

This replaces hundreds of `Read`, grep, `wc1.func`, `wc1.xref`, and custom per-area `*_dis.py` calls.

### 2. Separate semantic reasoning from code generation

Run two distinct passes.

**Module semantic pass:** one Sonnet-medium call over an entire 15–20-function module proposes:

- semantic names;
- prototypes and record layouts;
- evidence and honest confidence;
- function families and reusable implementation patterns.

**Mechanical implementation pass:** functions are grouped by shape—packet writers, state handlers, dialog wrappers, arithmetic helpers—and generated in batches of perhaps three to six using Sonnet-low or medium.

This means the expensive subsystem understanding happens once, not again inside every function’s compile loop.

### 3. Make compilation the search agent

The controller applies candidates in a disposable area worktree and runs:

- Watcom 10.0a matching;
- OW2 fallback;
- compile-check;
- T4 pair tests where needed.

For mismatches, it automatically explores the finite codegen vocabulary already discovered by this project:

- bitfield versus byte test;
- signed/unsigned widths;
- `short` loop indices;
- volatile or dword-view reads;
- local reuse and expression order;
- OD/debug flags;
- known prologue and register-allocation variants.

Only after those mechanical alternatives fail does Claude receive a second request containing the original candidate and a compact first-difference report—not an entire compiler log.

This is the most important leverage point. `wc1.match` is an objective oracle; there is no need for multiple agents to debate correctness.

### 4. Template most T4 work

The 59 missing difftests should not be 59 independent agent investigations. The controller can classify them into families and instantiate test templates:

- pure arithmetic/state functions;
- memory transformation;
- recorded external calls;
- packet/serial functions;
- graphics operations.

Claude supplies edge cases, meaningful inputs, and watch ranges once per family. The harness generates the repetitive test body and checks compiled C against the original.

### 5. Persist progress outside conversation history

Use a generated ledger with states such as:

```text
queued → packeted → named → candidate → T3-match/T4-pass
       → integration-ready → verified → committed
```

The ledger contains paths, hashes, match status, first divergence, and validation commands—not narrative.

A quota boundary then loses at most the currently running candidate. Nothing depends on resuming a 200k-token subagent conversation.

## How to call Claude on the $20 subscription

The installed Claude Code 2.1.326 supports the necessary headless controls. A worker would conceptually use:

```sh
claude -p \
  --safe-mode \
  --tools "" \
  --model sonnet \
  --effort low \
  --no-session-persistence \
  --output-format json \
  --json-schema '<candidate schema>'
```

The packet contains the compact task rules and evidence.

Two important details:

- Do **not** use `--bare` for this design. In the installed version, `--bare` refuses OAuth/keychain authentication and requires an API key or `apiKeyHelper`, so it does not use the included $20 Pro allocation.
- `--safe-mode --tools ""` retains normal subscription authentication while removing plugins, MCP instructions, auto-memory, agents, project hooks, and the entire tool-use loop. The controller—not the model—runs Nix, the compilers, tests, and git operations.

This is still ordinary use of the unmodified Claude Code CLI, not an API-credit design.

## Quota orchestration

Parallelism should be zero or one for the batch worker. Anthropic explicitly states that parallel sessions share the same limits and consume them proportionally. [Claude cloud-session limitations](https://code.claude.com/docs/en/claude-code-on-the-web#limitations)

The existing `/home/artem/.claude/statusline-command.sh` already receives five-hour and weekly usage percentages. A future controller should:

- refuse to start a new batch around 70–80% of the five-hour window;
- finish and checkpoint the current batch;
- exit cleanly;
- continue from the ledger after reset;
- reserve the final 20% for integration, verification, and recovery.

It should not sleep inside a hook for five hours: caches expire, contexts remain oversized, and hooks do not improve efficiency.

Also:

- Never use repo-wide `/goal` for this project.
- If `/goal` is used at all, scope it to one atomic unit: “finish BULLET.C, verify, commit, stop.”
- Hard-deny a second concurrent analyst in the hook. “Maximum two” is still too high for a fixed subscription budget.
- Use a fresh context after each module; compacting a chatty 200k context is inferior to beginning the next bounded packet cleanly.

Pro is currently $20/month, has five-hour and weekly limits, and does not include API usage. Limits are shared across Claude surfaces and vary with conversation length, model, effort, and tool use. [Claude Pro details](https://support.claude.com/en/articles/8325606-what-is-the-pro-plan), [usage-limit explanation](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work)

## Model policy—without the “just use Haiku” answer

I would use:

- **Sonnet medium:** one semantic pass per module.
- **Sonnet low:** structured C/test candidate generation from complete packets.
- **Sonnet medium:** one repair attempt with the compiler diff.
- **Opus:** only a manually selected queue of genuinely ambiguous cases—shared epilogues, module boundaries, uncertain semantic naming, M3 architecture.
- **Haiku:** optional formatting or schema repair, not central to the plan.

The major saving comes from reducing 40–80 model requests per area to approximately 4–10—not from swapping Sonnet for Haiku.

## Practical feasibility

Under the current orchestration, Pro is not feasible: the measured cost was nearly one five-hour window for roughly fourteen completed functions plus one partial area.

Under the batch architecture, feasibility should be decided by a pilot, not optimism. Use one representative 15–20-function module and require:

- no more than 8–10 Claude requests;
- one live Claude request at a time;
- at least an 8–10× reduction in context per completed function;
- no discarded partial modules;
- unchanged evidence/confidence rules;
- unchanged `make verify` and goal gates.

If the pilot cannot achieve that reduction, a $20 Claude-only completion is probably not realistic. If it does, the project becomes a paced multi-month Pro project rather than a continuous autonomous sprint.

The strongest recommendation is therefore: build the per-function evidence packet, deterministic candidate validator, and resumable ledger first; then benchmark it on BULLET.C. Agent teams, cloud parallelism, additional subagents, and more elaborate parent prompts all preserve the current bad economics.
