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
- No history rewriting (amend of an earlier unit, rebase, force), no push,
  no branch juggling unless the user asks.

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

## Current state (2026-11-20)

- `make progress` at f574205: in scope 1010 (game 882, gfx 27, resource 11,
  runtime 90), named 687, T3 289 (all 10.0a) + T4 175 = **DONE 463 (45.8%)**,
  59 reference C without a difftest.
- `make verify` green at f574205: 862 passed + 11 skipped, build IDENTICAL
  (289 functions from 284 C files).
- `make goal`: gate 1 FAIL (463 of 1010 done), gate 2 PASS, gate 3 FAIL - the
  T5 scenario set is undefined; the user deferred it until M3 starts
  (defining it is a proposal to the user).
- Milestones (docs/GOAL.md section 3): M1 T4 harness (`wc1.cemu`) done, M4
  original compiler (Watcom 10.0a) done, M2 area coverage in progress, M3 not
  started.
- Areas done (symbols + docs/subsystems/<area>.md + tests): PATH/UNIT
  0x2c4e0, SAVE.C/SCORE.C, mod_24860 (save format), STATUS.C, CMD.C, input,
  link ring, resources/file layer + GDS, clib triage, video+input library,
  sound mod_269f0, GAMEDLG.C, mod_13f60 (DISPATCH.C+DLGS.C), PLAYFLIC.C,
  mod_16390, mod_104b0/110a0/11530, mod_2efd0, PACKET.C, NETWORK.C,
  mod_295d0, mod_20c30 + PLACEBOX.C.
- No subagent work in flight.  History: docs/HISTORY.md.

## Next steps (in order)

1. M2, the remaining unowned modules, one `wc1-analyst` each (briefs
   cancelled 2026-11-19 by quota with nothing to resume - restart from
   scratch):
   - BULLET.C (19 fn; BulletSpawn 0x11b19 is the entry seen from
     UnitCalcDamage);
   - mod_1b800 (0x1b800..0x1c020, 18 fn);
   - mod_2b8e0 (18 fn; fn_2b308/2b31c/2b390 are referenced from save_score
     and mod_2efd0);
   - mod_19b80 (0x19b80..0x1a3c0, 16 fn; NetPumpEvents 0x19b80 and
     GameScreenInputInit 0x1a328 are already in gamedlg.toml; SetHelpText
     0x19f80 is requested by the status area);
   - INIT.C (14 fn; new entries go to startup.toml, src/init.c stays owner);
   - SND.C + SPELL.C (0x26320..0x26958 and 0x27670..0x27b20; the SND.C names
     live in audio.toml).
2. T4 for the 59 reference-C functions without a difftest: NETWORK.C 22,
   PLAYFLIC.C 18, mod_16390 12, mod_2efd0 4, mod_13f60 2, PACKET.C 1.
3. Turn T4/reference C into T3 where 10.0a spellings allow (ground rules).
   Known cases: IntroOpPlaySound 0x2315c and IntroOpSyncSound 0x23170 match
   but cannot be built until the reference-C ops 0x231cc/0x231ec (which jump
   into their shared epilogue) match too (docs/subsystems/playflic.md);
   src/audio/sound.c (MusicStop, SndActiveCount) and src/graphics/gfx_prim.c
   (HLine, VLine) mismatch under both compilers; the sweep-only samples in
   src/codegen/ without `src =` (bullet.c, mod_110a0/12c70/13e60/13f60/
   19470.c) are still OW2 (fn_19478 does not match under 10.0a).
4. Semantic names for the remaining fn_* placeholders, inside their areas
   (feed list: handler tables 0x51210/0x5159c + entries 0x11344/0x113e0/
   0x114d8/0x114ec, strings 0x569d4/0x569e0, fn_12f24 record reader,
   mod_13e60 words 0x51530/0x51532, mod_13f60 neighbours 0x1517c..0x15244 +
   table block 0x51610..0x51698 + buffers 0x59230/0x59260, RNG family
   fn_150f0/fn_19470 + dat_50d7c, fn_24bf0 serializer).
5. Data ownership by C (needed for M3): the data layout
   (analysis/data_layout.toml) does not exist yet; the C objects anchor on
   the asm's data bytes today (docs/subsystems/build.md).
6. Waiting for the user's approval: the discovery change that merges shared
   return blocks (STATUS.C 0x28074 is split at 0x28090/0x28093; merging makes
   it T3-able, docs/subsystems/status.md); the gate 3 scenario set, when M3
   starts.
7. M3 (all-C build + T5 scenarios) after M2.
