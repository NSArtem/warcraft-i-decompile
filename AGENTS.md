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

## Current state (2026-11-22)

- `make progress` after 24d24c2 + the overnight hang fix: in scope 1010 (game
  882, gfx 27, resource 11, runtime 90; 8 unclassified), named 817 (80.9%),
  T3 414 (all 10.0a) + T4 385 = **DONE 794 (78.6%)**, 6 unchecked reference C (4 PLAYFLIC.C + 1 EndScreen
  real ref-C divergences marked xfail + 1 `WaitInputOrTimeout` in `mod_1bf80`
  left unwired by pre-fix commit `5fa133b`).
- `make verify` green at the overnight hang-fix commit (after 24d24c2): 1355
  passed + 11 skipped + 5 xfailed, build IDENTICAL.
- **Unattended runs are bounded** (incident 2026-11-22: overnight hung 3 h in
  the permuter on `src/mod_1eba0/minimap_init.c`): compile timeouts (10.0a
  180 s + `wineserver -k`, OW2 too), threaded permuter with a timeout circuit
  breaker + 900 s wall budget, `[TOOLCHAIN ERROR]`/exit 78 stops the run,
  capped + heartbeating pytest runs, overnight stall watchdog
  (`--stall-timeout 1200`, STALLED item rolled back, run goes on).  Root
  cause not reproduced (docs/HISTORY.md, docs/ANALYST_GUIDE.md).
- `make goal`: gate 1 FAIL (765 of 1010 done), gate 2 PASS, gate 3 FAIL - the
  T5 scenario set is undefined; the user deferred it until M3 starts
  (defining it is a proposal to the user).
- Milestones (docs/GOAL.md section 3): M1 T4 harness (`wc1.cemu` + `wc1.t4spec`
  + flat 32-bit GDT/`iretd` in `wc1.emu`) done, M4 original compiler (Watcom
  10.0a) done, M2 area coverage in progress (`wc1.dossier` + `wc1.permuter` +
  `wc1.batch_driver` + hardened `wc1.overnight` with instruction-capped
  chunking, disassembly+ref-C Stage 4/repair, runtime T4 oracle audit
  `WC1_T4_AUDIT_LOG` + nonce + `run_spec_done` + `orig_patched`/`c_patched` +
  out-of-process OMF digest + shared AST cheat prefilter + anti-weakening diff,
  and `wc1.tui` live), M3 not started.
  - **Runtime T4 audit trust boundary & repo sweep:** The audit defends against
    accidental/opportunistic LLM cheats and mid-run overrides, not a hostile
    in-process sandbox (e.g. post-load `cmod.extra` mutation, external stubs
    toggling `emu.trace`/`emu.stubs` mid-call, or deliberate env/file forging).
    Full-repo 373-node audit passed **361/373** (`0` swallowed assertions; 5
    vacuous zero-observation tests fixed in `2f7d862`); 12 pre-existing tracked
    hand-written nodes bypass `cemu.run_pair` matching `link_name` and remain
    untouched (`tests/test_network.py`: `0x1fb60`/`0x201c0`/`0x2020c`/`0x2061c`,
    `tests/test_resources_lzss.py`: `0x31870`/`0x34480`/`0x3452c`/`0x41550`,
    `tests/test_graphics_lib.py`: `0x33150`/`0x331be`,
    `tests/test_network_t4_2.py`: `0x2070e`, `tests/test_game_2c4e0.py`:
    `0x2c4e0`).
- Areas done (symbols + docs/subsystems/<area>.md + tests): PATH/UNIT
  0x2c4e0, SAVE.C/SCORE.C (named C complete), mod_24860 (save format),
  STATUS.C, CMD.C, input, link ring, resources/file layer + GDS (11/11 done),
  clib triage, video+input library, sound mod_269f0 + SND.C (named C complete,
  plus `AnimTableLoad`/`AnimTableFree` T3 + `BulletStartAnim` T4 in
  `snd_f1.toml` and real T4 for `fn_26360`), GAMEDLG.C, mod_13f60
  (DISPATCH.C+DLGS.C), PLAYFLIC.C + flic_decode (named C complete), mod_16390
  (52/54 done; `EditFieldDraw` prototype fixed in `6c881bd`, `OutroPlayFlic`/
  `DialogActivateItem`/`DialogRun` genuinely verified in `9f6b8ad`),
  mod_104b0/110a0/11530, mod_2efd0, PACKET.C, NETWORK.C (22/22 T4), mod_295d0,
  mod_20c30 + PLACEBOX.C, mod_2b8e0 (18/18 done), SPELL.C (11/11 done),
  overnight Wave 3 batches `2dbbdfd`..`4a7fadc`, salvages `2808a11`..`4819b60`,
  and T4 oracle/pipeline hardening `9f6b8ad`..`1c5e825`.
- Untracked pre-existing WIP in tree (not yet committed): the `mod_1eba0`
  draft the hung run left (`analysis/symbols/mod_1eba0.toml`, `src/mod_1eba0/`,
  `src/include/mod_1eba0.h`; not reviewed), `BULLET.C` draft
  (`analysis/symbols/bullet.toml` — cleaned of its `0x26390` TEMP draft,
  `src/bullet/` 19 files — 8 already T3 MATCH, `src/include/bullet.h`,
  `tools/wc1/bullet_dis.py`, `tools/wc1/bullet_match.py`) and
  `src/include/mod_3aac0_c.h` (note: committed `6ca6f34`
  `src/mod_3aac0/bitmap_blit_transparent_fliph_reference.c` `#include`s
  untracked `src/include/mod_3aac0_c.h`, so a clean checkout needs it
  committed or inlined).
- No subagent work or overnight runner in flight.  History: docs/HISTORY.md.

## Next steps (in order)

1. Use `python3 -m wc1.overnight` (opens `wc1.tui` interactive launcher on a
   TTY; or `--tui` / `--headless`) or `python3 -m wc1.batch_driver` for M2
   completion, verifying with `make verify` before each atomic commit:
   - Finish & land untracked `BULLET.C` (19 fn; 8 already T3 MATCH under
     `wc1.bullet_match`; upgrade placeholders `0x11a10`/`0x11ec0` in
     `mod_104b0.toml`, fill disassembly evidence in `bullet.toml`, T4-test the
     remaining 11, remove `tools/wc1/bullet_dis.py` + `bullet_match.py`).
   - Before the next unattended night, watch one supervised `wc1.overnight`
     item end to end (the hang fix is tested with fakes only); deferred
     review notes: a per-item deadline / slow-compile breaker in
     batch_driver (a compile that is slow but under its timeout is not
     caught), pgid PID reuse in the stall kill, the forkserver question for
     `match._pool`.
   - Run hardened `wc1.overnight` (`1c5e825`, default `--max-chunk-insns 500`)
     on remaining clean Wave 2/3 queue items (`EditFieldDraw` `0x174c0` is now
     fixed so `mod_16390_c3` `EditFieldRun` is unblocked; 68 `needs_human`
     functions remain filtered out of the unattended loop).
   - Supervised handling of the 68 `needs_human` items (cross-TOML `fn_*` /
     `low` upgrades, `codegen_promo.toml` promotions, `mod_2efd0`/`mod_13f60`
     unbuildable T3s, `mod_1bf80` `WaitInputOrTimeout`).
2. Fix the 6 remaining unchecked reference-C entries so unchecked `ref` drops
   to 0: 4 in `PLAYFLIC.C` (`tests/test_playflic_t4.py`), 1 in `EndScreen`
   (`tests/test_mod_2efd0_t4.py`, `LayerAdd` `id`/`res` args swapped), and
   1 in `mod_1bf80` (`WaitInputOrTimeout`, `src/mod_1bf80/wait_input_or_timeout_reference.c`).
3. Classify the remaining 9 unclassified runtime functions
   (`make progress --kind runtime`).
4. Turn T4/reference C into T3 where 10.0a spellings allow (ground rules).
   Known cases: IntroOpPlaySound 0x2315c and IntroOpSyncSound 0x23170 match
   but cannot be built until the reference-C ops 0x231cc/0x231ec (which jump
   into their shared epilogue) match too (docs/subsystems/playflic.md);
   src/audio/sound.c (MusicStop, SndActiveCount) and src/graphics/gfx_prim.c
   (HLine, VLine) mismatch under both compilers; the sweep-only samples in
   src/codegen/ without `src =` (bullet.c, mod_110a0/12c70/13e60/13f60/
   19470.c) are still OW2 (fn_19478 does not match under 10.0a).
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
   - Optional final Opus 5.5 (`claude -p --model opus`) sign-off on `1c5e825`
     once the 5-hour quota resets (Round 5 approved Should-Fix G and specified
     the exact two Must-Fix F bypasses closed & tested in `1c5e825`).
   - Review of stricter T4 test updates landed to replace broken/vacuous
     existing tests (`tests/test_mod_16390_c4.py`,
     `tests/test_mod_16390_c.py::test_edit_field_draw`, and the 5
     zero-observation tests in `2f7d862` + `9a5d1f9`); optional migration of
     the 12 legacy hand-written T4 nodes to `cemu.run_pair`.
   - Clean-checkout fix for `6ca6f34`: commit untracked
     `src/include/mod_3aac0_c.h` (or inline its declarations into
     `src/mod_3aac0/bitmap_blit_transparent_fliph_reference.c`).
   - Optional runtime pytest `conftest.py` hook failing `make verify` when
     `war.exe`/`$WATCOM` are present and any `ref_verified_by`-cited node was
     uncollected, skipped, or xfailed.
   - The discovery change that merges shared return blocks (STATUS.C 0x28074
     is split at 0x28090/0x28093; merging makes it T3-able,
     docs/subsystems/status.md); the gate 3 scenario set, when M3 starts.
8. M3 (all-C build + T5 scenarios) after M2.
