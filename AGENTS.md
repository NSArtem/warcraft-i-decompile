# Warcraft I decompilation — session guide

Evidence-driven source reconstruction of Warcraft: Orcs & Humans (DOS, CD
v1.22h `war.exe`). Read `README.md`, `docs/GOAL.md` (scope, definition of
done, milestones; progress via `make progress`), `docs/METHODOLOGY.md`
(evidence, confidence, verification tiers) and `docs/ANALYST_GUIDE.md` (tools,
conventions, concurrency rules) before working.

## Ground rules

- All commands run in the Nix dev shell: `nix develop -c <cmd>`.
- Never commit `original/` or `build/` (copyrighted game data and anything
  generated from it). Commit as described under "Commits" below.
- Every name/type/claim lives in `analysis/symbols/*.toml` with evidence and
  confidence; `verified` only via a mechanical check (match:/libsig:/difftest:).
- `make verify` must stay green (toolchain check, symbols, round-trip, C
  matches, compile check under both compilers, build, tests).  It needs Watcom
  10.0a: `make toolchain` installs it into `original/watcom/10.0a` (git-ignored,
  supplied like the CD) from `$WATCOM10A` (an install directory or the
  `wcc10.0a.tar.gz` tarball, sha256-checked; docs/subsystems/compiler.md).
- C targets Watcom 10.0a first (`/* codegen-compiler: 10.0a */` header line);
  OW2 (no header) is the fallback; every file compiles under both.  Retry an
  OW2 near miss with 10.0a spellings (bitfields for `test byte`, a volatile or
  dword-view read for `mov eax,[addr-2]; sar eax,0x10`, a `short` loop index
  for `movsx`/`imul` walks, OD frames `-s -od -4r -zp2` [+ `-d1+`]) before
  writing a t3_blocker (docs/subsystems/codegen.md, compiler.md).
- One function per C object wherever the neighbours are not all C (wcc386
  16-byte aligns a second function, the original does not), and a C object's
  CONST anchors follow code order (a literal shared by two objects needs a data
  symbol).
- The project goal is `make goal` passing (docs/GOAL.md section 4). Work in
  the order of docs/GOAL.md section 3 and "Next steps" below; after each
  committed unit, run `make progress` so the session shows where things stand.
- **The finish line is fixed: only the user changes it.** Without the user's
  explicit approval, do not change the gates or scope (docs/GOAL.md sections
  1, 2 and 4), the tier definitions (docs/METHODOLOGY.md), the classification
  rules in tools/wc1/progress.py (scope, PLACEHOLDER, NAMED_CONFIDENCE, done),
  the `goal`/`verify` Makefile targets, or what an existing test checks.
  Never make progress by reclassifying: an entry moves to clib.toml only with
  libsig or semantic evidence that it is Watcom runtime code, and a confidence
  goes up only with new evidence. Defining gate 3 (the M3 scenario set) is a
  proposal to the user, not a decision. If a rule looks wrong or a gate cannot
  be met, stop and say so with the evidence.

## Commits

The session owner (the main agent) commits on its own as work completes;
subagents never commit (enforced: OpenCode by the permission denies in
.opencode/agents/, Claude Code by the PreToolUse hook
.claude/hooks/subagent_guard.py, which also blocks `make build`/`roundtrip`,
edits to Makefile/flake/asm/war.h/.claude/.opencode and nested subagents). Commits are atomic:

- **One logical change per commit**, complete with its tests and docs. Examples:
  a function (or a tightly related group) promoted to T3/T4 with its test and
  TOML update; one area's symbols + notes; one tool change + its tests; one
  doc fix. Do not mix areas, or a shared-tool change with area work: commit
  the tool first, then the work that uses it.
- **Every commit leaves `make verify` green.** Run it before each commit that
  touches tools/, src/, analysis/, tests/ or the Makefile; doc-only commits
  need `make symbols` at most.
- **Commit when a unit is done**, not at the end of a long session; do not
  carry finished but uncommitted work into the next unit. Half-done work is not
  committed: finish it, or describe it in AGENTS.md's next steps.
- **Stage explicit paths** (no `git add -A` / `git add .`); do not commit files
  you did not create or change (another agent's or the user's untracked work).
- **Message:** one title line, no body or trailers, saying what changed and its
  proof where there is one, e.g. `T3: UnitResetPath 0x2cebc (built from C)`,
  `wc1.emu: run compiled C objects (T4 harness) + tests`.
- The hand-off update (AGENTS.md current state and next steps, the
  docs/HISTORY.md block) goes in the commit whose state it describes (or right
  after it, on its own); see "Hand-off" below.
- **Branches:** do development, fixes, analysis and decompilation work on a
  branch off local `main`, not directly on `main`. Unless the user says
  otherwise, the session owner is free to pick the branch and its name
  (subagents never create, switch or merge branches). Name it
  `<prefix>/<topic>`, with a short kebab-case topic:
  - `feature/` - tools, pipeline and infrastructure (`feature/wave4-nextgen`);
  - `fix/` - bug fixes (`fix/overnight-runner`);
  - `decomp/` - T3/T4 promotions and area work, including production runs
    (`decomp/mod-1eba0`, `decomp/wave4-run-2`);
  - `analysis/` - symbols, formats, naming, classification and audits without
    new C (`analysis/runtime-unclassified`);
  - `docs/` - documentation-only work.
- **Merging:** when the branch's work is complete and `make verify` is green,
  merge it into local `main` with `git merge --no-ff <branch>`; never
  fast-forward or squash.
- No history rewriting (amend of an earlier unit, rebase, force), and no push
  unless the user asks.

## Subagents

Two named subagents are defined, for Claude Code (`.claude/agents/`) and
OpenCode (`.opencode/agents/`) respectively:

- `wc1-mechanical` (small/fast model): well-specified mechanical work with
  explicit steps and acceptance criteria (signature sweeps, export tooling,
  bulk checks, tests).
- `wc1-analyst` (strong reasoning model): reverse-engineering judgment
  (subsystem/format analysis, module boundaries, semantic naming, matching C).
- Select the subagent explicitly. One owner per file/area (see ANALYST_GUIDE
  concurrency rules). Split mixed tasks so the mechanical part goes to
  `wc1-mechanical`.


## Hand-off

This file holds only three things: the rules (above), the current state and
the next steps.  Keep it short; it is loaded into every session.

- **Current state** is a snapshot, rewritten (not appended) at hand-off:
  `make progress` numbers, gate status, the last commit verified green,
  work in flight, blockers.
- **Next steps** lists open work only, in order.  Delete finished items
  instead of striking them through.
- Session narrative - what was done, commit ids, findings, rejected
  approaches, cancelled subagent work - goes to **docs/HISTORY.md** as one
  dated block appended at the end.  Durable technical knowledge goes to the
  area's docs/subsystems/*.md (HISTORY.md is a log, not a reference).

## Current state (2026-11-24)

- **Dependency-scoped schema-v2 caching + exhausted Wave 4A production run:**
  - Implemented and independently reviewed (`APPROVE`, 0 Must Fix / 0 Should Fix
    in Round 2, Gemini 4 Neon High) shared per-unit dependency fingerprinting in
    `tools/wc1/wave4_fp.py` for both Wave 4A (`ReconcileCache`) and Wave 4B
    (`RetryCache`), backed by stamped OMF dependency capture in `t3_audit.py` /
    `audit_state.json` / `omf_deps.json`, fail-open safety, 5-state cache
    diagnostics, bounded in-run requeueing (`failed_fingerprints`, max 3), and
    safe legacy v1 rejection without deletion (`3bd6939`, `fe17966`, merged
    `--no-ff` at `5eebd59`, +68 unit/real-project E2E tests).
  - Supervised sequential Wave 4A production run (`feature/wave4a-production-run`,
    `5eebd59..667dbb0`, merged `--no-ff` at `f994a7c`) **exhausted the Wave 4A
    backlog**: **80 automated commits** (**+4 T3** promotions: `fa6b63c`,
    `bc804fa`, `d9d1681`, `e29eae6`; **76 verified `RECONCILED`** commits;
    **137 unresolved relocations eliminated**; **104 functions unblocked**;
    **0 infra failures / 0 infra repairs**) in `6.19 h` wall time (`131` Codex
    `gpt-6.2-sol/low` calls, `+6.0pp` 7d quota `51.0% -> 57.0%`). Only
    `owner_5aa90` (15 symbols; `MainMenu 0x15578` pre-function switch jump table
    `MATCH_UNBUILDABLE`) and 13 cleanly v2-cached `AMBIGUOUS`/`NO_IMPROVEMENT`
    groups remain. Wave 4B dependency-clean queue grew from `306` to **`324`**.
    Reports preserved under `build/wave4/wave4a_production_run2_report.json`.
- `make progress` at `f994a7c`: in scope 1010 (game 882, gfx 27, resource 11,
  runtime 90; 6 unclassified), named 900 (89.1%), **T3 510 (50.5%; 10.0a 509,
  ow2 1)** + T4 375 (37.1%) = **DONE 880 (87.1%)**, 6 unchecked reference C
  (4 PLAYFLIC.C + 1 EndScreen real ref-C divergences marked xfail + 1
  `WaitInputOrTimeout` in `mod_1bf80` left unwired by `5fa133b`).
- `make verify` green at `f994a7c`: **1719 passed + 11 skipped + 5 xfailed**,
  Build A **IDENTICAL** (`510 functions from 505 C files`).
- **Unattended runs are bounded** (incident 2026-11-22: overnight hung 3 h in
  the permuter on `src/mod_1eba0/minimap_init.c`): compile timeouts (10.0a
  180 s + `wineserver -k`, OW2 too), threaded permuter with a timeout circuit
  breaker + 900 s wall budget, `[TOOLCHAIN ERROR]`/exit 78 stops the run,
  capped + heartbeating pytest runs, overnight stall watchdog
  (`--stall-timeout 1200`, STALLED item rolled back, run goes on).
- `make goal`: gate 1 FAIL (880 of 1010 done), gate 2 PASS, gate 3 FAIL - the
  T5 scenario set is undefined; the user deferred it until M3 starts
  (defining it is a proposal to the user).
- Milestones (docs/GOAL.md section 3): M1 T4 harness done, M4 original compiler
  (Watcom 10.0a) done, M2 area coverage in progress (`wc1.dossier` +
  `wc1.permuter` + `wc1.batch_driver` + hardened `wc1.overnight` + Wave 4A/4B
  reconciliation/recovery pipeline with schema-v2 dependency-scoped caches +
  `wc1.tui` live), M3 not started.
  - Runtime T4 audit: trust boundary in docs/ANALYST_GUIDE.md; the
    361/373 repo sweep and its 12 legacy nodes in docs/HISTORY.md.
- The untracked BULLET.C / mod_1eba0 / `mod_3aac0_c.h` drafts were scrapped
  by the user (to be redone from scratch).
- No subagent work or overnight runner in flight.  History: docs/HISTORY.md.

## Next steps (in order)

0. High-ROI Wave 4 follow-ups:
   - Run supervised `--wave wave4b` production sweep on the **324**
     dependency-clean Wave 4B candidates (using the new schema-v2
     dependency-scoped `RetryCache`, with `--window-budget 1.0` alongside
     explicit `--codex-max-5h-pct` / `--codex-max-7d-pct` /
     `--codex-max-7d-delta-pp` to avoid mid-verify 5h rollover exits).
   - Handle pre-function switch jump tables (e.g. `MainMenu 0x15578`) in
     `wc1.build` or detect `MATCH_UNBUILDABLE` flips in Wave 4A before full
     `make verify`, unlocking `owner_5aa90` (15 remaining unresolved relocs,
     +2–3 immediate T3s).
   - Optional low-priority fingerprint hardening from Review Round 2: skip
     persisting `audit_state.json`/`omf_deps.json` stamps under active
     `INCLUDE`/`WCC386` overrides, skip `report.json` bootstrap on `tool_sig`
     mismatch, and check full `fails` before `fails[:8]` truncation in
     `_compile_check_files`.
1. Use `python3 -m wc1.overnight` (opens `wc1.tui` interactive launcher on a
   TTY; or `--tui` / `--headless`) or `python3 -m wc1.batch_driver` for M2
   completion, verifying with `make verify` before each atomic commit:
   - Redo `BULLET.C` from scratch (the draft was scrapped); its callers use
     the low placeholders `fn_11a10`/`fn_11cb0`/`fn_11cd8`/`fn_11ddc`/
     `fn_11e70`/`fn_11ec0`/`fn_11f10`/`fn_11f78` in `mod_104b0.toml`.  `mod_1eba0`
     (the hung run's area) is to be redone too.
   - Run hardened `wc1.overnight` (`1c5e825`, default `--max-chunk-insns 500`)
     on remaining clean Wave 2/3 queue items (68 `needs_human` functions remain
     filtered out of the unattended loop); deferred review notes: per-item
     deadline / slow-compile breaker in batch_driver, pgid PID reuse in stall
     kill, forkserver question for `match._pool`.
   - Supervised handling of the 68 `needs_human` items (cross-TOML `fn_*` /
     `low` upgrades, `codegen_promo.toml` promotions, `mod_2efd0`/`mod_13f60`
     unbuildable T3s, `mod_1bf80` `WaitInputOrTimeout`).
2. Fix the 6 remaining unchecked reference-C entries so unchecked `ref` drops
   to 0: 4 in `PLAYFLIC.C` (`tests/test_playflic_t4.py`), 1 in `EndScreen`
   (`tests/test_mod_2efd0_t4.py`, `LayerAdd` `id`/`res` args swapped), and
   1 in `mod_1bf80` (`WaitInputOrTimeout`, `src/mod_1bf80/wait_input_or_timeout_reference.c`).
3. Classify the remaining 6 unclassified runtime functions
   (`make progress --kind runtime`).
4. Turn remaining T4/reference C into T3 where 10.0a spellings allow (ground
   rules). Remaining `MATCH_UNBUILDABLE` cases include SaveErrorDialog 0x1aca8
   (data anchor order), DialogHighlightOff 0x16d48, IntroFadeStep 0x22eac,
   FarmPanelChanged 0x28254 (sibling mismatches), IntroOpPlaySound/SyncSound
   (0x2315c/0x23170 shared epilogue), src/audio/sound.c, src/graphics/gfx_prim.c,
   and OW2 sweep-only samples in src/codegen/.
5. Semantic names for the remaining fn_* placeholders, inside their areas
   (feed list: handler tables 0x51210/0x5159c + entries 0x11344/0x113e0/
   0x114d8/0x114ec, strings 0x569d4/0x569e0, fn_12f24 record reader,
   mod_13e60 words 0x51530/0x51532, mod_13f60 neighbours 0x1517c..0x15244 +
   table block 0x51610..0x51698 + buffers 0x59230/0x59260, RNG family
   fn_150f0/fn_19470 + dat_50d7c, fn_24bf0 serializer).
6. Data ownership by C (needed for M3): the data layout
   (analysis/data_layout.toml) does not exist yet; the C objects anchor on
   the asm's data bytes today (docs/subsystems/build.md).
7. Waiting for the user's approval / review:
   - Optional final Opus 5.5 (`claude -p --model opus`) sign-off on `1c5e825`.
   - Review of stricter T4 test updates (`tests/test_mod_16390_c4.py`,
     `tests/test_mod_16390_c.py::test_edit_field_draw`, 5 zero-observation
     tests in `2f7d862` + `9a5d1f9`); optional migration of the 12 legacy
     hand-written T4 nodes to `cemu.run_pair`.
   - Optional runtime pytest `conftest.py` hook failing `make verify` when
     `war.exe`/`$WATCOM` are present and any `ref_verified_by`-cited node was
     uncollected, skipped, or xfailed.
   - The discovery change that merges shared return blocks (STATUS.C 0x28074
     is split at 0x28090/0x28093; merging makes it T3-able,
     docs/subsystems/status.md); the gate 3 scenario set, when M3 starts.
8. M3 (all-C build + T5 scenarios) after M2.
