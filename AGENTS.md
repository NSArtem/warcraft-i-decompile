# Warcraft I decompilation — session guide

Evidence-driven source reconstruction of Warcraft: Orcs & Humans (DOS, CD
v1.22h `war.exe`). Read `README.md`, `docs/METHODOLOGY.md` (evidence,
confidence, verification tiers) and `docs/ANALYST_GUIDE.md` (tools,
conventions, concurrency rules) before working.

## Ground rules

- All commands run in the Nix dev shell: `nix develop -c <cmd>`.
- Never commit `original/` or `build/` (copyrighted game data and anything
  generated from it). Commit only when the user asks; one-line messages.
- Every name/type/claim lives in `analysis/symbols/*.toml` with evidence and
  confidence; `verified` only via a mechanical check (match:/libsig:/difftest:).
- `make verify` must stay green (symbols, round-trip, C matches, build, tests).

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

## State at hand-off (2026-10-10)

Done and verified: Nix env; extraction with hash checks; LE parser; code
discovery (1704 functions, 97.3%); T1 round-trip byte-identical; T2 wlink
relink load-equivalent and boots in DOSBox-X; `wc1.match` (T3);
`wc1.emu` (Unicorn harness); `InitPaths` (0x1d7cc) matched in `src/init.c`
and taken from C in the build (hybrid exe boots).

Reviewed 2026-10-10 and committed (5f725a6): `make verify` green; `tools/wc1/clib_sig.py`
repaired (short or shared-address library units are reported as weak
candidates unless corroborated, not as matches); `modules_libsig.py` deleted
(byte-only, no relocation cross-check, false positive at 0x18af0);
`resources_war.py` decodes all 583 DATA.WAR entries (difftest pending).

Second session 2026-10-10 (committed 72d226a, `make verify` green, 61 tests):
- Discovery: dead (gap-scan) functions and tail-jump-only targets are now
  starts unless the preceding function jumps past them; AIL fillers skipped
  (1340 -> 1704 functions).
- Ghidra export works (`-scriptPath`, added `__watcall` prototype): 1704/1704.
- Areas finished, each with `docs/subsystems/<area>.md` and tests:
  clib (~250 runtime entries, 43 verified by libsig/difftest; runtime is
  interleaved with game code), resources (WAR format, LZSS decoder difftest
  over all 583 entries), audio (Miles AIL 3.x at [0x34d83,0x3aac0), cdecl;
  game sound layer), graphics+input (video/palette/layers/blitters/text,
  8 difftests; keyboard ISR, mouse, event queue), modules
  (`analysis/modules.toml`: 159 ranges, mostly medium, from zero padding
  between objects; 14 guide names, low/medium).
- Codegen study (after 72d226a, `docs/subsystems/codegen.md`): three styles
  per object -- OPT `-s -ot -ol -4r -zp2` (default now), DBG = OPT + `-d1+`,
  OD (not reproducible with OW2; use T4). C files carry a `codegen-flags:`
  header read by wc1.match/wc1.build. 9 functions are now T3-verified and
  built from C (src/init.c, src/codegen/{init,snd,mod_33a30,mod_34380,
  mod_409a0,res_init}.c); `make match-all` checks every `src=` file; hybrid
  exe boots to the same intro screens. Other src/codegen files match only
  under `wc1.codegen_sweep` (callees/data not yet named in the DB).

Fourth session (2026-11-10, committed dcd6205): game-logic area started.
- PATH/UNIT range 0x2c4e0..0x2efd0: 26 functions and 11 data symbols named
  with evidence in `analysis/symbols/game_2c4e0.toml`, area notes in
  `docs/subsystems/game_2c4e0.md` (unit record layout, path objects, draw
  list, per-tick update).
- 4 more functions T3 (`wc1.match`) and built from C: DrawListRemove 0x2cfa8,
  UnitResetPath 0x2cebc, UnitUpdateDamageFrame 0x2d0ac, UnitSetNextOrders
  0x2eed4 (`src/game_2c4e0/`); the hybrid build stays IDENTICAL.
- Near-miss reference C (logic right, OW2 register allocation differs) for
  DrawListSort/Insert, UnitSetNextOrder and PathPeekStep; do not add `src=`
  for those. The source idioms that fixed the matches (unsigned mask local,
  reuse the local for the order byte) are documented in the area notes.
- Tests: `tests/test_game_2c4e0.py` (T3 re-check + near-miss guard).

Fifth session (2026-11-15, UNCOMMITTED work tree, quota stopped the session):
- Session start `make verify` green (103 tests) at HEAD 7351664.
- `wc1-mechanical` ses_e23b0a04affeTOEexWShHRbRGj DONE: codegen sweep-only
  samples triaged -> `analysis/symbols/codegen_promo.toml` (10 fn + 4 data,
  address-derived placeholder names) and `tests/test_codegen_promo.py` (green).
  6 of the sample functions now MATCH under `wc1.match` (fn_1132c, fn_123cc,
  fn_12cd4, fn_13e94, fn_15558, fn_19478); fn_15170/fn_15230 are NOT naming
  problems: unnamed functions between them (0x1517c..0x151ac, 0x15244) make
  wc1.match compare past the real extent (tool fix sketch in next steps c).
- `wc1-analyst` CMD area crashed at the very end (ses_e23b0d0a1ffeMXpMIpqqCHcDWV,
  "Upstream response was not valid JSON"; a follow-up resume attempt
  ses_e22eae1f3ffez2QinGuBtNwIBu was aborted) but the work is COMPLETE and
  green: `analysis/symbols/cmd_123f0.toml` (19 fn + data),
  `docs/subsystems/cmd_123f0.md`, `src/cmd_123f0/` (6 T3 + 12 reference C),
  `src/include/cmd_123f0.h`, `tests/test_cmd_123f0.py` (all pass),
  `tools/wc1/cmd_123f0_dump.py`. T3: 0x123f0 MapViewInitLimits, 0x125c4
  MapViewScrollUp, 0x12620 MapViewScrollDown, 0x12688 MapViewScrollLeft,
  0x126e4 MapViewScrollRight, 0x12a2c CheatCodeCommand -- all need the `-oa`
  flag set (-s -ot -oa -4r -zp2, in each file's codegen-flags header). The
  analyst left `src =` out per its brief: the session OWNER adds them (see
  next steps b).
- `wc1-analyst` SAVE/SCORE area crashed mid-work (ses_e23b0b971ffeDEMQTdcT7snFQ0):
  symbols/doc/tests INCOMPLETE. Existing: `analysis/symbols/save_score.toml`
  (32 fn + data), `src/save_score/{save,score}.c`, `src/include/save_score.h`,
  `tests/test_save_score.py` with 13 FAILING tests, NO
  `docs/subsystems/save_score.md`, no reference C the tests expect
  (save_reference.c, score_reference.c). Details in next steps.
- Scratch moved to build/scratch/ (pt_a/b.err, tam_c.err from the crashed
  analyst); `docs/SPEEDUP.md` is a legitimate note (nix/Watcom cold-build
  diagnosis) left by an agent, keep it.

Sixth session (2026-11-17): fifth session finished and committed, all green.
- save_score area COMPLETED (fresh `wc1-analyst`): tests/test_save_score.py
  24/24 green; docs/subsystems/save_score.md written (message layout/types,
  handshake, net_load_state machine, exact score model + adjuster table);
  src/save_score/{save,score}_reference.c added (near-miss C guarded by
  tests). Genuine T3 + built from C: WordInRange 0x2417c (the merged
  zero-exit spelling), ScoreSetUncapped 0x257c0 (via the match.py extent
  fix). The five other formerly match-claimed functions were DOWNGRADED to
  difftest (T4) - each one OW2 register-allocation difference, documented
  per function; ~25 source spellings tried, none steered OW2.
  Corrections vs the crashed session's TOML: fn_12f24 returns 0 = record
  stored at [edx]; NetSendDataMessage proto is (len, data); 0x250fc reads
  the MEN counters (the original's own copy-paste quirk); 0x25198's
  other-branch divides by 8; 0x2529c's other-branch does cap-clamp; the
  score adjuster model was rewritten from the disassembly (inverted
  claw-back ratio, others-only forced-1 rule).
- cmd_123f0 wired into the build (owner): `src =` added to the six T3
  entries, `make build` IDENTICAL (23 functions from 21 C files),
  tests/test_cmd_123f0.py guard updated, docs/subsystems/cmd_123f0.md
  sections 4/7 updated.
- tools/wc1/match.py extent fix: match_module retries a failed comparison
  with the extent clamped at the ORIGINAL's flow end (code discovery,
  last reachable instruction) when the module only adds alignment filler
  past it (`is_filler`, moved to match.py and shared with
  codegen_sweep). The mechanical agent's sketch (next discovered start)
  was not enough - that still compares the original's inter-function
  filler; the flow end is what works. fn_15170/fn_15230 now T3 (verified
  in codegen_promo.toml); codegen.md's match table is all-T3 now;
  make match-all green.
- fn_23edc renamed NetLinkHandshake (codegen_promo.toml, semantic name +
  analysis from the save_score area; src/codegen/mod_13f60.c extern
  updated, still MATCH).
- 0x24ee0 ScoreAddForMen is DEFERRED, not lost (TOML NOTE + doc section 6):
  discovery does not promote conditional tail-jump targets, so an entry
  there would break test_pipeline/test_ghidra. Ready-to-paste entry + the
  analysis.py patch sketch are in docs/subsystems/save_score.md section 6.
- flake.nix pins the Watcom toolchain with a GC root (.gcroots/, ignored);
  wc1-mechanical model switched to opencode-go/deepseek-v4.1-flash.
- `make verify` green: 173 tests, build IDENTICAL.

2026-11-18 follow-up (same owner session): discovery promotes conditional
tail-jump targets; ScoreAddForMen restored.
- tools/wc1/analysis.py: the `tails` scan in partition() now accepts the
  COND_JUMPS mnemonics as well as `jmp` (the fall-through guard is
  unchanged).  10 new starts program-wide (1704 -> 1714), each entered only
  by conditional/unconditional jumps and preceded by a terminator or
  undecoded filler; the partition's validity metric improved (functions
  with crossing flow 33 -> 29).  0x24ee0's preceding filler is UNDECODED,
  so the plain `t not in ends` guard already admits it - the filler clause
  from the save_score report's sketch was tried and REJECTED: it also
  promoted 0x2c228, whose preceding `mov eax,eax` (0x2c226) is reachable
  in-function code in front of a mid-function spill block, splitting the
  genuine function 0x2c208 (counterexample recorded in
  docs/subsystems/save_score.md section 6).
- analysis/symbols/save_score.toml: ScoreAddForMen 0x24ee0 entry added
  (verified via the two adjuster difftests); tests/test_save_score.py's
  discovery test renamed test_tail_jump_entries_are_discovered_starts and
  now asserts 0x24ee0/0x2505c are starts; save_score.md section 6 records
  the history.

## Next steps (in order)

0. ~~Finish the fifth session~~ done (sixth session, above).
1. ~~Codegen study~~ and ~~library names~~ done (third session): GdsAlloc/
   GdsFree, text_colors/text_glyph_fn/text_esc_colors, cursor_save_bm named;
   13 functions T3 + built from C. Remaining sweep-only samples are game code
   (bullet.c, mod_110a0/12c70/13e60/13f60/19470.c): promoted 2026-11-15 via
   codegen_promo.toml, all T3 since the 2026-11-17 extent fix; semantic
   renames of the remaining fn_* placeholders happen during step 3 areas
   (feed list from the mechanical report: handler tables
   0x51210/0x5159c + entries 0x11344/0x113e0/0x114d8/0x114ec, strings
   0x569d4/0x569e0, fn_12f24 record reader, mod_13e60 words 0x51530/0x51532,
   mod_13f60 neighbours 0x1517c..0x15244 + table block 0x51610..0x51698 +
   buffers 0x59230/0x59260, RNG family fn_150f0/fn_19470 + dat_50d7c,
   ~~save-slot fn_23edc~~ renamed NetLinkHandshake 2026-11-17, fn_24bf0
   serializer).
2. ~~Module-ordered build~~ done differently (third session,
   docs/subsystems/build.md): C objects are linked in place between asm
   pieces (BYTE-aligned via tools/wc1/omfpatch.py, data as zero-length
   anchors on the asm's bytes), so the hybrid build is IDENTICAL to the
   original and `make build` now fails otherwise. Per-module asm files are
   not needed for code. Open: real data ownership by C needs the data
   layout (analyst running: analysis/data_layout.toml).
3. Game logic areas (units, orders, pathfinding, AI, network, UI,
   save/score), one analyst per area, using modules.toml ranges.
4. Small follow-ups:
   a. ~~file wrappers~~ (FileOpen/FileSeek/FileRead/... 0x31940..0x31bca,
      CritErrHandler/CritErrInstall, in resources.toml) and ~~GDS heap~~ and
      ~~`module =` check~~ (symbols.check_modules: must equal the
      analysis/modules.toml range name) done.
   b. ~~tools/wc1/analysis.py tails fix~~ done 2026-11-18 (see the session
      block above; the sketch's filler clause was rejected - conditional
      jumps alone promote 0x24ee0, and decoded-filler targets like 0x2c228
      are mid-function code).  ScoreAddForMen 0x24ee0 is in the database.
   c. tools/wc1/emu.py built-in memcpy stub (from the save_score report):
      `self.stubs.setdefault(0x31789, _memcpy)` - the clib memcpy at
      0x31789 is a segmented ES:EDI copy Unicorn cannot run; tests
      currently install `stub_memcpy` per test
      (tests/test_save_score.py). memset 0x30c50 runs fine natively.
