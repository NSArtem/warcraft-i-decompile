# Session history

Moved out of AGENTS.md on 2026-11-20.  AGENTS.md keeps only the rules, the
current state and the next steps; the narrative of each session (what was
done, commits, findings, rejected approaches, cancelled work) goes here as
one dated block, appended at the end (newest last).  Durable technical
knowledge belongs in the area's docs/subsystems/*.md, not only here.

## 2026-10-10 .. 2026-11-18 (hand-off blocks as kept in AGENTS.md)

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
- tools/wc1/emu.py: built-in flat memcpy model pre-installed for 0x31789
  (`stubs.setdefault`, override-able; guarded by
  tests/test_emu.py::test_memcpy_stub_is_builtin) - the clib memcpy is a
  segmented ES:EDI copy Unicorn cannot run.

2026-11-18 goal definition (owner session):
- docs/GOAL.md: scope (Blizzard's own code; AIL, hand-written asm and the
  Watcom runtime are out), per-function done = semantic name + T3, or T4 with
  a t3_blocker; gates = wc1.progress --check, make verify, all-C build T5;
  milestones M1 T4 harness (compiled C under wc1.emu), M2 area coverage,
  M3 all-C build + T5 scenarios, M4 optional original compiler.
- tools/wc1/progress.py (`make progress`, --check/--json/--todo/--kind);
  symbols.py validates the new func fields ref / ref_verified_by /
  t3_blocker; the 28 functions in *_reference.c files now carry `ref =`
  (tests/test_progress.py guards that).  Snapshot: 1047 in scope, 25 done
  (all T3), 28 reference C not yet checked, T4 = 0 (no C-vs-original harness).
- Existing `verified_by = "difftest: ..."` tests run the ORIGINAL against a
  Python model: they verify claims, not C (METHODOLOGY T4 row clarified).

2026-11-18 M1: T4 harness (`tools/wc1/cemu.py`).
- `cemu.load(emu, src)` compiles a C file with its codegen flags, allocates
  its OMF segments in the emulator's scratch area (dwARF skipped), copies the
  contents, and applies the off32 relocations: externals resolve through the
  symbol database (`extra=` for names the DB has no entry for), file-local
  symbols through the module's LPUBDEF statics (Watcom puts them in the
  external-name table too), and module-local segments (`seg` fixups) to the
  copy.  A missing symbol raises `CEmuError` naming it.
- `cemu.run_pair(emu, orig_addr, cm, name, *args, watch=..., out_regs=...)`
  runs the original and the compiled C on identical inputs (watched memory is
  restored between the two calls) and returns the differences in the output
  registers and watched memory; empty = T4 equal.  Tests pass `out_regs=()`
  for void functions (their eax is scratch and may legitimately differ).
- `tests/test_cemu.py` (5 tests): module layout/addressability, TotalActiveMen
  (0x24e50) C-vs-original on the shared array, a temporary probe C (local
  const array + internal static call + extern data) to exercise
  module-local relocation, the unknown-symbol error, and a deliberate-input
  mismatch to prove run_pair reports differences.
- `make verify` green: 191 tests, build IDENTICAL.

2026-11-18 (owner session, after the T4 conversions): discovery plausibility
vetoes + runtime classification.
- `wc1.cemu` (M1) landed (commit 77483cc) and every reference C was turned
  into T4: save_score (12, commit 3b3d911), cmd_123f0 (12, da4ed6f),
  game_2c4e0 (4, 652f98f), resources LZSS/RegisterCodec/ResourceSeek (5,
  7ecdefe), the archive API (5, a4ab2d3), the six SCORE.C adjusters
  (ef90f30), the SAVE.C load-error dialogs (039fb19), NetLinkExit and
  NotValidTwoPlayerDialog (8c955c1).  Two areas completed in parallel:
  - mod_24860 (the save-file loader/writer, 26524ae): 10 functions named,
    RefRelocate 0x248e0 and SaveReadStream 0x249a4 T3 (one function per
    file, because SaveLoadImage 0x24900 between them is reference C and the
    build places objects in sequence), 8 T4; docs/subsystems/save_format.md
    maps the on-disk format (XOR-0x64 name block, checksum, 15 fixed image
    blocks, pointer relocation modes) and records 0x24860 as data.
  - STATUS.C (3c7bbc3): 81 functions named, 48 T3 (one function per file),
    22 T4, 9 reference C still without a difftest (they need stubs for the
    resource/layer stack), docs/subsystems/status.md (unit command card,
    panel geometry, gates).
  `make progress`: 75 T3 + 78 T4 done, 9 reference C unchecked, in scope
  1040, 153 done.  `make verify` green: 324 tests, build IDENTICAL
  (75 functions from 73 C files).
- Discovery (tools/wc1/analysis.py), user-approved:
  * tail targets that lie in another function's ordinary reach are shared
    epilogues, not functions (`_partition` now records `reach`);
  * `analysis.stack_underflow` vetoes a candidate whose contiguous run pops
    below its own frame; applied to data-ptr/code-ptr/gap-scan seeds and to
    tail promotions, exempting the entry, direct call targets, jump-table
    labels and ail/asm modules; `lss esp`/`mov esp`/`leave` end the walk.
  * result: 1714 -> 1710 starts.  Removed 0x18798 (12-byte data table),
    0x1e3ac (shared epilogue), 0x24860 (XOR-0x64 text buffer; the mod_24860
    analyst's evidence), 0x2c1b3 (block of fn_2c208 laid out before its
    entry), 0x3c461 (shared epilogue of far_strnlen/far_wcsnlen); added the
    callback 0x187a4 that 0x18798 had swallowed.
  * the three runtime pieces 0x3d920 (__terminate), 0x401bd
    (__MemFree_exit), 0x41819 (__exit_with_msg) stay starts and are moved
    out of scope by clib.toml entries with evidence.
  * `tools/wc1/discovery_audit.py` (one row per start: origin, stack
    underflow, odd instructions) and docs/subsystems/discovery.md record the
    rules and the before/after list; before 7 underflow rows -> after 1 (the
    AIL exemption).  tests/test_pipeline.py pins the five removals, the
    added callback, the exemptions and the runtime classification.
- In-scope count 1047 -> 1040 (five non-functions gone, three runtime pieces
  out, one callback in).
- Gate 3 (T5 scenario set) is deferred by the user until M3 starts; M1/M2
  continue.
- Two more discovery observations from the areas (proposals, not applied):
  STATUS.C's 0x28074 body is split at 0x28090/0x28093 (shared `return 0`
  block and a jump over it) because the partition does not merge shared
  return blocks; merging them would make 0x28074 T3-able.  This needs the
  user's approval like the vetoes above.
- tests/test_mod_24860.py and tests/test_status.py run the original under
  wc1.emu; the status area's 9 untested reference functions
  (StatusPanelDraw, UnitPanelUpdate, ButtonDraw, UnitPanelDraw,
  StatusPanelInit/Free/Show/Click, StatusPanelTextRefresh) need LayerAdd/
  LayerFree/ResourceRead stubs before they can be T4.

2026-11-18 shutdown state (owner session, continuation):
- Committed this stretch: discovery vetoes (8901b59), mod_24860 area
  (26524ae), save_score link-state T4 (8c955c1), STATUS.C area (3c7bbc3),
  map_flags pointer fix (ad1d421), clib clock/delay classification (66e6e18),
  input ISR region markers (67b94da), hand-off (1c9c1f2).
- `make verify` green at HEAD: 325 tests, build IDENTICAL (75 functions from
  73 C files).
- `make progress`: 1034 in scope (game 882, gfx 27, resource 11, runtime
  114), 309 named, 75 T3 + 80 T4 done = 155, 9 reference C unchecked, 870
  with no C.  Out of scope 676 (Watcom runtime 482, AIL 156, asm 38).
- New runtime classifications (clib.toml, semantic evidence): clock 0x30e98,
  delay 0x31784, __clock 0x3b8f4, __clock_ticks 0x3b88e,
  __delay_calibrate 0x3b915, __delay_impl 0x3b947 - the game calls plain
  Watcom library entries, they are not Blizzard wrappers.
- Input area started (input.toml, tests/test_input_evt.py): IsrRegionStart
  0x30ea0 and IsrRegionEnd 0x312d8 are the empty DPMI-lock markers, T4 with
  od-frame (OW2 emits `sub esp,4` vs the original `sub esp,0`).  The area's
  remaining 14 functions (EvtPost 0x30eb8, MouseButtonEvent 0x30fa8,
  MouseCallback 0x30fe0, KeyboardISR 0x31104, DpmiLock/UnlockRegion
  0x312f0/0x31360, EvtHook/UnhookKeyboard 0x313d0/0x31450, EvtInitMouse
  0x314a4, EvtShutdownMouse 0x31538, EvtPump 0x31568, EvtGet 0x31598,
  EvtInit 0x316a0, EvtShutdown 0x31764) are named but have no C yet; the
  event-ring layout is in docs/subsystems/input.md and EvtInit 0x316a0.
- Cancelled subagent work (discarded, not committed):
  * mod_16390 area (session ses_e13b10249ffebGIqPV126u7vUN): only
    src/mod_16390/char_printable.c had been produced (no symbols, tests or
    docs); deleted at shutdown.  Nothing to resume from - restart the brief
    from scratch.
  * PLAYFLIC.C area (session ses_e13b10248ffeIeqTGogWD4ktcM): no files
    written; restart from scratch.
- Also still uncommitted/absent from earlier plans: none - the tree is
  clean (only build/, gitignored).

2026-11-18 compiler migration (owner session, user-approved plan): the
original compiler is Watcom C/C++ 10.0a (found by the separate research repo
warcraft-1-decompile-compiler, branch `compiler`; its hunt evidence stays
there - only the knowledge and the needed files were transferred, no
cherry-picks).  Commits f923d32..2eae157:
- Toolchain: flake has Wine (WoW64); `tools/wc1/oldcc.py` runs
  binnt/wcc386.exe under Wine (prefix build/oldcc/wineprefix; output to a
  file, not a pipe, and display drivers off - 0.13 s per compile instead of
  4 s); `make toolchain` / `make toolchain-check`;
  analysis/provenance/watcom10a.sha256 pins the compiler and headers (runtime
  libs optional).  `original/watcom/10.0a` holds the install now.
- Per-file compiler: `/* codegen-compiler: 10.0a */` (line 2) selects 10.0a
  in wc1.match/build/cemu/codegen_sweep; no header = OW2.  `wc1.match --cc`,
  `--compile-check`; objects in build/match/<cc>/ and build/cemu/<cc>/.
  cemu skips 10.x debug segments (DEBSYM/DEBTYP).
- Rules (approved): T3 = byte match under the file's declared compiler;
  `make verify` = toolchain-check + compile-check under both + the rest;
  GOAL M4 done; `make progress` shows T3 per compiler (display only).
- Library comparison against the 10.0a runtime (`wc1.clib_sig --root`):
  175 clib entries byte-identical, 12 new runtime entries, 26 renamed to
  library names (e.g. 0x4091b __CHK -> __STK), in scope 1034 -> 1022; open
  questions in docs/subsystems/clib.md (abort/__terminate at
  0x3d926/0x3d920, exit_ 0x3b439 vs DB exit 0x33f5c, five undecorated
  names left at their old confidence).
- All 72 OW2-matched files switched to 10.0a (still MATCH, build
  IDENTICAL); CMD.C uses `-s -ot -oa -ol -4r -zp2` and CheatCodeCommand
  tests the developer bit through the bitfield `cheat_flags.f.dev`.
- 24 former reference functions are now T3 under 10.0a and built from C
  (one function per file where they were split out of a multi-function
  reference file): CMD.C 4, UnitSetNextOrder, IsrRegionStart/End,
  SndShutdownAil, resources 6, SCORE.C 4, mod_24860 2, STATUS.C 4.  Their T4
  tests still run against the same C; the TOML keeps the old blocker/T4 lines
  as evidence history.  `make progress`: 99 T3 (all 10.0a) + 57 T4 = 156
  done of 1022 in scope; `make verify` green, 499 tests, build IDENTICAL
  (99 functions from 97 C files).
- Blocked on naming, not codegen: GamesDifferDialog 0x24304,
  EnemyDidNotLoadDialog 0x24344 (call 0x1a894, ShowMessage in the tests) and
  NetSendDataMessage 0x24780 (calls 0x131d8) match in code bytes under 10.0a;
  name those two callees (with evidence, in their area) and promote.
- Not switched: the sweep-only samples in src/codegen/ without `src =`
  (bullet.c, mod_110a0/12c70/13e60/13f60/19470.c) stay OW2; fn_19478 does
  not match under 10.0a.  src/audio/sound.c (MusicStop, SndActiveCount) and
  src/graphics/gfx_prim.c (HLine, VLine) mismatch under both.

## 2026-11-19 (owner session, ten areas in parallel)

the goal run that took the
project from 156 to 375 done functions.
- `make progress`: in scope 1010 (game 882, gfx 27, resource 11, runtime 90),
  named 557, T3 253 (all 10.0a), T4 122, reference-not-checked 32, DONE 375
  (37%).  `make build` IDENTICAL (253 functions from 248 C files).
- Committed: link-ring area (bc82ac5), the three dialogs that were blocked on
  unnamed callees (0d26383: ShowMessage 0x1a894, NetSendMessage 0x131d8),
  custom_game 0x50e4e (37b95ea), the `link`-must-be-a-NASM-label guard
  (b39beb6), resources/file layer + GDS (41211e0), clib triage of the 28
  unclassified runtime functions (ebdf35d), then ten area commits: video+
  input library 0x317b0..0x33400 (72e9772), input area (48cdbdb), sound
  mod_269f0 (60f43ce), GAMEDLG.C (af6836f), mod_13f60 = DISPATCH.C+DLGS.C
  (396d938), PLAYFLIC.C (6d70e85), mod_16390 (68e2f51), mod_104b0/110a0/11530
  (8ccc10e), STATUS.C painters (4dc62ef), path_war 0x52538 + the omfpatch test
  fixture (930527c, 3cd81a9).
- Codegen findings that unblocked most of the T3s: 10.0a reproduces the OD
  frames (`-s -od -4r -zp2`; the sound and file-wrapper objects need `-d1+`
  too), the "word variable read as `mov eax,[addr-2]; sar eax,0x10`" idiom is
  a volatile/dword-view read (sound volumes, game_mode), a `short` loop index
  reproduces `movsx`/`imul` ring walks, and a multi-function C file gets its
  second function 16-byte aligned by wcc386 (the original is not) - hence
  **one function per object** wherever the neighbours are not all C.  A C
  object's CONST anchor must also follow code order: two dialogs sharing one
  literal need a data symbol for the string (txt_error_saving 0x56bf8,
  path_war 0x52538).
- Nine clib runtime functions stay in scope as Blizzard code (the triage table
  is in docs/subsystems/clib.md); 12 moved out with libsig evidence.
- Known not-built C: IntroOpPlaySound 0x2315c and IntroOpSyncSound 0x23170
  match but the reference-C ops 0x231cc/0x231ec jump into their interior
  (shared epilogue), so `wc1.build` cannot replace them; they need those two
  to match first (docs/subsystems/playflic.md).
- Committed after that hand-off paragraph was written: mod_2efd0 (2e85b27),
  PACKET.C (e82b3c7), NETWORK.C (4993c2a), mod_295d0 (e292d48), mod_20c30 +
  PLACEBOX.C head (7c6aed1) and the PLACEBOX.C tail names (46dfc39).  Final
  state of the session: named 684/1010 (67.7%), T3 289, T4 172, DONE 460
  (45.5%), build IDENTICAL (289 functions from 284 C files), `make verify`
  green (483 C files x 2 compilers, 862 tests + 11 skipped).
- `make goal` at hand-off: gate 1 FAIL (460 of 1010 done), gate 2 PASS,
  gate 3 FAIL (undefined - see the blocker line above).
- Blocked on the user: gate 3.  docs/GOAL.md section 4.3 still reports FAIL
  because the T5 scenario set is undefined; defining it is a proposal to the
  user (AGENTS.md ground rules), so `make goal` cannot pass until then.
- Tail of the same session, stopped by the OpenCode Go weekly quota
  (06:13): f574205 named the three AI ticks AiSpellcasterTick 0x2a8f4,
  AiIdleUnitTick 0x2ab54 and AiWorkerTick 0x2b064 in mod_104b0.toml (T4 via
  tests/test_mod_295d0.py, reference C in src/mod_295d0/*_reference.c) and
  made src/mod_104b0/{unit_idle_tick,unit_retaliate}.c call them by name.
  `make progress`: named 687, T3 289, T4 175, reference-not-checked 59,
  DONE 463 (45.8%).  `make verify` green at f574205
  (862 passed + 11 skipped, build IDENTICAL).
- Cancelled subagent work (quota, ~9 minutes in, read-only exploration; no
  repo files written - only git-ignored scratch in build/mod_1b800,
  build/mod_2b8e0, build/init): six `wc1-analyst` areas launched on the
  remaining unowned modules - BULLET.C (19 fn, BulletSpawn 0x11b19 is the
  entry seen from UnitCalcDamage), mod_1b800 (0x1b800..0x1c020, 18 fn),
  mod_2b8e0 (18 fn; fn_2b308/2b31c/2b390 referenced from save_score and
  mod_2efd0), mod_19b80 (0x19b80..0x1a3c0, 16 fn; NetPumpEvents 0x19b80 and
  GameScreenInputInit 0x1a328 already in gamedlg.toml, SetHelpText 0x19f80
  requested by the status area), INIT.C (14 fn; new entries go to
  startup.toml, src/init.c stays owner), SND.C + SPELL.C (0x26320..0x26958
  and 0x27670..0x27b20; the SND.C names live in audio.toml).  Nothing to
  resume from - restart each brief from scratch.  The 59 reference-C
  functions without a difftest (NETWORK.C 22, PLAYFLIC.C 18, mod_16390 12,
  mod_2efd0 4, mod_13f60 2, PACKET.C 1) are the other open bulk.

## Next-steps list at the 2026-11-20 restructure (snapshot)

The list as it stood in AGENTS.md when the history moved here; the open items
were carried over to AGENTS.md's "Next steps".

Goal-level order (docs/GOAL.md section 3): M1 T4 harness first, then M2 areas
(step 3 below), then M3.

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
   save/score), one analyst per area, using modules.toml ranges.  Done so
   far (counts after the 10.0a promotions): PATH/UNIT 0x2c4e0 (5 T3 + 3 T4),
   SAVE.C/SCORE.C (6 T3, the rest T4), mod_24860 (4 T3 + 6 T4), STATUS.C
   (52 T3 + 18 T4), CMD.C (10 T3 + 8 T4), plus the input area's two markers
   (T3).  New C goes to Watcom 10.0a first; retry the remaining reference C
   with 10.0a spellings (bitfields for `test byte`, compiler.md) before
   accepting a blocker.
   Next area candidates: finish gfx_evt_vid (14 functions), then mod_269f0
   (19 named, OD sound layer), mod_13f60 (68), mod_16390 (54), PLAYFLIC.C
   (46), mod_20c30 (32), NETWORK.C (31), mod_295d0 (29), mod_2efd0 (26),
   PACKET.C (23), PLACEBOX.C (22), GAMEDLG.C (21), BULLET.C (19).
4. Small follow-ups:
   a. ~~file wrappers~~ (FileOpen/FileSeek/FileRead/... 0x31940..0x31bca,
      CritErrHandler/CritErrInstall, in resources.toml) and ~~GDS heap~~ and
      ~~`module =` check~~ (symbols.check_modules: must equal the
      analysis/modules.toml range name) done.
   b. ~~tools/wc1/analysis.py tails fix~~ done 2026-11-18 (see the session
      block above; the sketch's filler clause was rejected - conditional
      jumps alone promote 0x24ee0, and decoded-filler targets like 0x2c228
      are mid-function code).  ScoreAddForMen 0x24ee0 is in the database.
      ~~Discovery plausibility vetoes~~ done 2026-11-18 (owner session, user
      approved): shared-epilogue reach rule + stack-balance veto; start count
      1714 -> 1710; see docs/subsystems/discovery.md and the session block.
   c. ~~tools/wc1/emu.py built-in memcpy stub~~ done 2026-11-18:
      `self.stubs.setdefault(0x31789, _memcpy)` in `Emu.__init__`
      (tests/test_emu.py::test_memcpy_stub_is_builtin guards it; the
      per-test `stub_memcpy` installs in test_save_score.py are kept as
      explicit overrides).  memset 0x30c50 runs fine natively.

---

## 2026-11-20 / 2026-11-21 — Claude Pro token-saving pipeline + M2 validation (477 -> 590 DONE)

- **Strategy & guardrails** (`473dd84`, `da1be6d`): analyzed prior Claude Pro
  and OpenCode/DeepSeek session logs in
  `docs/claude-pro-decompilation-strategy-by-neon.md`. Added project-local
  `.claude/settings.local.json` (`sonnet`, `effortLevel: medium`, 120k
  autoCompactWindow), enforced max-1 concurrent subagent in
  `.claude/hooks/subagent_guard.py`, and updated `CLAUDE.md` /
  `.claude/agents/wc1-analyst.md`.
- **Token-saving tooling** (`c50aa1b`, `a72831e`, `0688dbd`, `73c1086`,
  `4959f9b`, `8e50248`, `2231416`, `26f4e89`, `c99faa6`, `217ea00`,
  `b9aae7d`, `94dc4f3`, `16bb0e8`):
  - `wc1.match --diff`: fixup-patched Capstone instruction diffing with
    `REG`/`IMM/REL`/`OP/STRUCT` classification and objective scoring.
  - `wc1.dossier`: one-shot module/function dossier generator (disasm, xrefs,
    Ghidra hints, style/flag detection).
  - `wc1.permuter`: local multi-core Watcom 10.0a flag & idiom searcher (zero
    LLM tokens).
  - `wc1.t4spec` + `wc1.emu`: declarative `wc1.cemu` difftest runner with stub
    call logging, auto-resolved `fn_*`/`dat_*` externals, and a built-in flat
    32-bit GDT (`CS=0x08`, `DS/ES/FS/GS/SS=0x10`) + `interrupt=True` frame
    support so `strlen`, `_fmemset`, `lgs` and `__interrupt`/`iretd` execute
    natively under Unicorn.
  - `wc1.batch_driver`: stateless `claude -p --safe-mode --tools "" --json-schema`
    orchestrator (`full` / `c-only` / `t4-only`) with JSONL cost/cache ledger
    (`build/ledger/*.jsonl`), hard `--max-cost`/`--max-calls` caps, 8-function
    T4 chunking, search/replace patch retries, non-clobbering paths, and hard
    rejection of skipped/xfailed generated tests.
- **Validation & M2 progress (+113 DONE functions in 61 Claude calls, ~$6.07
  total API-equiv, ~$0.054/fn vs ~$0.43–$2.40 baseline):**
  - `00cc35c`: `mod_2b8e0` — 18/18 done (8 T3 built from C, 10 T4; 8 calls, $1.27).
  - `961cc03`: `SPELL.C` — 11/11 done (5 T3 built from C, 6 T4; 8 calls, $0.65).
  - Wave 1 (59 unchecked `ref` functions -> 5 remaining xfailed real ref-C
    bugs): `d7879c5` `mod_16390` (12 T4, $0.37), `9b9dcf0` `PLAYFLIC.C` (14 T4 +
    4 xfailed ref-C divergences, $0.86), `d706538` `mod_2efd0` (3 T4 + fixed
    `EndCheckObjectives` `0x50d98` bug + `EndScreen` xfail, $0.23), `32feff1`
    `mod_13f60` (2 T4, $0.10), `c3703ce`/`103366e` `PACKET.C` (1 T4, $0.045),
    `75e4381` `NETWORK.C` (22/22 T4 including both `__interrupt` ISRs + fixed 6
    pre-existing ref-C files: `NetModemInit`, `NetModemCommand`, `NetIpxConnect`,
    `NetSerialIsr`/`Fifo`, `NetSerialStart`, `NetSerialUartInit`; 7 calls, $0.70).
  - Wave 2 (`c-only` on already-named modules): `763eddb` `flic_decode` (6/6:
    1 T3 + 5 T4, $0.36), `c74eafc` `PLACEBOX.C` (11/11: 5 T3 + 6 T4, $0.63),
    `580378d` `SND.C` (8/8: 6 T3 + 2 T4, $0.52), `2ce6aa1` `SCORE.C` (5/5:
    3 T3 + 2 T4, 5 calls, $0.34, zero manual edits).
- **Verified green at `2ce6aa1`:** `make verify` 1042 passed, 11 skipped, 5
  xfailed; `build/war.exe` IDENTICAL (328 functions from 323 C files);
  `make progress` = **590 / 1010 DONE (58.4%)**.

---

## 2026-11-21 — `wc1.overnight` streaming backend + `wc1.tui` `btop`-style monitor & launcher (590 -> 642 DONE)

- **Zero-supervisor overnight run (`3f0a981`..`6c4adcf`):** initial `wc1.overnight`
  ran Wave 2 `c-only` modules unattended, landing +52 DONE functions (590 -> 642,
  63.6%, 341 T3 + 302 T4), then was gracefully stopped on a clean module boundary
  while sleeping on the 5-hour rate-limit reset.
- **Dependencies (`256a174`):** added `textual` (8.2.8) and `rich` (15.0.0) to
  `flake.nix` devShell.
- **Live streaming & atomic IPC (`bfd4932`):**
  - Added `tools/wc1/live.py`: atomic `write_json_atomic` / tolerant `read_json`,
    partial-line-tolerant `tail_events`, NDJSON `stream-json` parser, normalized
    `five_hour`/`seven_day` `rate_limits.json`, `control.json` IPC, and safe
    process-group `terminate_process_tree`.
  - Switched `wc1.batch_driver.call_claude` to
    `--output-format stream-json --verbose --include-partial-messages` with
    separate stdin/stderr threads and timeout watchdog (zero pipe deadlock,
    process-tree cleanup), streaming thinking/output/permuter/match/verify events
    to `build/live/workers/<area>.jsonl` and live quota to `rate_limits.json`.
- **Overnight runner controls & metrics (`e3720db`):**
  - Fixed `progress_done_count()` T3/T4 uppercase counting; added `ledger_metrics`
    (5h/7d spend, cache-hit %, burn-rate sparkline, `$/fn`, est functions left),
    live `five_hour`/`seven_day` quota check + textual `resets ...` fallback,
    multi-worker/provider-ready `build/live/state.json` schema, and `stream-json`
    bounded repair.
  - Added control handling (`pause`/`resume` at safe module boundary, `wake`,
    `graceful_stop`/`SIGUSR1`, `kill`/`SIGTERM` with immediate process-tree
    termination and active-module-only rollback preserving pre-existing WIP).
  - Added `--tui`, `--headless`, and TTY-only interactive launcher routing when
    `python3 -m wc1.overnight` is run without flags (`--dry-run` and non-TTY
    never open TUI).
- **`wc1.tui` `btop`-style dashboard & launcher (`45fc832`):**
  - Standalone attach/detach Textual + Rich client (`tools/wc1/tui.py`): header
    bar (`DONE/1010`, build badge, state pill, clock), Quota & Pace (5h/7d bars,
    budget marker, burn-rate sparkline, cache-hit, `$/fn`), toggleable
    Functions/Modules Heatmap (`░▒▓■█◆✕·` + mouse/arrow inspector), selectable
    Agents & Queue (`claude`/`codex` provider ready), auto-updating Live Stream
    (`a`/`t`/`v` filters, `f`/End follow, manual scroll pause), interactive
    Launcher modal (4 presets + editable flags spawning detached runner),
    Kill confirmation modal, and Recent Commits modal (`q` only detaches).
  - Verified with `tests/test_live_stream.py`, `tests/test_overnight.py`,
    `tests/test_tui.py` (Textual Pilot), real 1010-fn attach/detach/stop smoke
    test, and full `make verify` green at `45fc832` (1146 passed, 11 skipped,
    5 xfailed; `build/war.exe` IDENTICAL, 341 functions from 336 C files).



## 2026-11-21 — Overnight runner fixes, salvage (+33 DONE, +15 T3), Claude Opus 5.5 review

- **Root-cause diagnosis of unattended `wc1.overnight` failures:**
  - `run_bounded_repair` matched `"rate_limit"` across raw `stream-json` lines,
    triggering 100% false positives on normal `rate_limit_event` (`status: "allowed"`).
  - `PLAYFLIC.C` was missing from `DEFAULT_SKIP` (`IntroOpPlaySound`/`IntroOpSyncSound`
    cannot build standalone due to shared epilogue branches from `0x231d7`/`0x231e1`),
    causing a 25-iteration sleep loop generating stray `playflic_c1..25` files.
  - On repair rate-limit, dirty edits were not rolled back before `continue`, leaking
    edits into subsequent iterations and polluting `done_before`, while `_next_free_area`
    reused stale budget-exhausted ledgers.
  - `test_call_claude_timeout_kills_process_tree` / `test_immediate_kill_terminates_child_tree`
    had a process-reap race on `pid_alive`.
- **Runner fixes (`e9b4cd2`, post-review `342fc6a`, `9b48f13`):**
  - Fixed `run_bounded_repair` rate-limit detection (structured `rate_limit_event` +
    word-bounded regexes only when `rc != 0` or `is_error`, recording partial cost on
    all exit paths; retries repair once on the same tree on real rate limit before
    archiving).
  - Added `"PLAYFLIC.C"` to `DEFAULT_SKIP`; hardened `_ledger_is_resumable` (rejects
    empty, finished, failed, rolled-back, or exhausted ledgers) and made `_next_free_area`
    strictly monotonic with per-queue reservation.
  - Added clean archive+rollback on `KeyboardInterrupt`, unhandled `Exception`,
    `ImmediateKillError`, and repair abort, empty-dir pruning in `_rollback_tree`,
    pre-commit `_verify_staged_toml_refs` guard, and preserved unstarted ledgers on
    `must_wait --no-sleep`.
  - In `wc1.batch_driver` (`9b48f13`), froze `target_addrs` in the ledger and keyed
    Stage 2 draft replay by function address (`files_map`) so partial TOML updates
    never shift batch indices on resume.
- **Salvaged & promoted functions from `build/failed/` (`b6f73f9`..`ec46f65`):**
  - `mod_13f60` (`b6f73f9`, `e2da5fd`): +11 DONE (9 T3 including `PreviewRectUpdate`,
    `ArmyLabelsDraw`, `PreviewToggle` promoted via `layers[]` + 2 T4).
  - `mod_2ced0` (`49671ad`, `ec46f65`): +8 DONE (1 T3 `UnitAdvanceOrder` + 7 T4;
    added `damage_fire_heavy`/`damage_fire_light` data symbols and exact blockers).
  - `mod_16390` (`ca3bcd5`): +8 DONE (8 T4 difftested).
  - `mod_33520` (`7ffef7e`, `5f22eff`): +4 DONE (4 T3: `CritErrLockStart`,
    `CritErrHandler`, `CritErrLockEnd`, `CritErrInstall` + `crit_err_installed` data).
  - `mod_348c0` (`5f219ce`, `0e2af44`): +1 DONE (`RectOutline` T4; retried
    `-s -ot -ol -4r -d1+ -zp2` and `-s -od -4r -zp2 [+ -d1+]` per methodology).
  - `error_fatal` (`ade19ee`, `09515bb`): +1 DONE (`FatalError` promoted to T3 after
    adding `fatal_hook`, `str_error_hdr`, `str_error_tail` data symbols).
- **Verified green at `ec46f65`:** `make verify` passes (1189 passed, 11 skipped,
  5 xfailed; `build/war.exe` IDENTICAL with 356 functions from 351 C files);
  `make progress`: **678/1010 DONE (67.1%)** (+33 DONE, +15 T3 vs `c20a87a`).

## 2026-11-21 (late) — Unattended overnight failure diagnosis, pipeline hardening (`93a83f0`), Opus 5.5 review

- **Diagnosis of the 2026-11-21 18:52–21:18 unattended run (27 runs: 15 COMMITTED [+43 DONE: 678→721], 12 FAILED):**
  - Only **2 of 12** failures (`mod_16390_c1`, `mod_33520_c2`) were normal hard T4 failures; **10 of 12 (83%)** were systematic pipeline bugs:
    1. **Unreplaceable T3 loop** (`mod_2efd0_c1`, `mod_13f60_c5`, `mod_13f60`): `SelectionClickUnit` (`0x2efd0`), `MissionDefeat` (`0x2f73c`), and `ChooseCampaignDialog` (`0x157e8`) matched T3 locally so `batch_driver` wired `src =`, `wc1.build` failed on interior branches/jump tables, and bounded repair deleted `src =` → `delta_done=0`.
    2. **All-or-nothing Stage 4 & missing post-repair `ref_verified_by` wiring** (`mod_2ced0_c1`, plus partial loss in committed `mod_1bf80` `5fa133b` leaving `WaitInputOrTimeout` unchecked `ref`): 1 failing test blocked all `ref_verified_by` writes; repair got all 4 tests passing (`1206 passed`) but hit its cap before editing TOMLs → rolled back.
    3. **Missing `--addrs` target handoff** (`mod_13f60` full): `overnight` never passed `item["addrs"]` to `batch_driver`, letting `full` pull in already-named unreplaceable functions and `codegen_promo.toml` entries.
    4. **Locked `codegen_promo.toml` trap** (`mod_110a0`, `mod_13e60_f1`, `mod_13f60`): `batch_driver` wrote `src =` into `codegen_promo.toml`, breaking `tests/test_codegen_promo.py::test_codegen_promo_entries_exist`.
    5. **Data-in-code false starts queued** (`mod_11530` `0x11530`, `mod_110a0` `0x110a0`): documented `[[data]]` entries in `mod_104b0.toml` were queued as functions → 0 files drafted.
    6. **Cross-TOML `fn_*`/`low` & name-only re-queue loop** (`score_f1` `0x257dc`, `snd_f2` `0x26360`/`0x26390`, `mod_2b2f0_f1`): `batch_driver` never upgraded cross-TOML entries, causing passing T4 runs with `delta_done=0` and re-queuing functions that already had T3/T4 C.
    7. **Stage 1 emitted `confidence="low"` on a T4 function** (`mod_30bd0` `VidSetupBackbuffer` `0x30bd0`), failing `is_semantic()` despite passing T4 + `make verify`.
- **Opus 5.5 (`claude -p --model opus`) reviews (3 passes: diagnosis + diff + re-review → `APPROVE`):**
  - Confirmed diagnosis; caught committed fake T4 in `tests/test_snd_f1.py` (`test_fn_26360` / `test_bullet_start_anim` always `pytest.skip` because they check non-`_reference.c`, leaving a false `ref_verified_by` on `mod_20c30.toml:521`) and untracked `analysis/symbols/bullet.toml:230-232` mutation from pre-fix `snd_f2`; steered unbuildable T3s to the `IntroOpPlaySound` pattern (no fake `t3_blocker`) and cross-TOML upgrades to `needs_human`.
  - Diff review caught `build.check_t3_buildable()` reading in-place-emptied objects from `build/obj/` (silently blinding anchor-order checks), missing per-node Stage 4 wiring in `run_t4_only`, ledger-window scoping for post-repair wiring, and `f["limit"]` vs `f["end"]` range check; all 5 diff findings fixed and verified before `APPROVE`.
- **Implemented & committed (`93a83f0`):**
  - `tools/wc1/build.py`: shared `check_placed_plan()` + `check_t3_buildable()` using unpatched temp objs in `build/match/placecheck/` and mtime-keyed `build/cache/anchors.json` (never touching `build/obj/`).
  - `tools/wc1/batch_driver.py`: explicit `--addrs` with strict eligibility (`EXIT_NOTHING_TO_DO=77`) and frozen-ledger check (`EXIT_ADDR_MISMATCH=76`); `LOCKED_TOMLS` (`codegen_promo.toml`) + untracked WIP TOML protection; mechanical `check_t3_buildable()` gate with IntroOpPlaySound-style unbuildable-T3 recording; `find_forbidden_test_cheat()` + zero-skip `_pytest_output_passed()` + `verify_t4_node()` + per-node Stage 4 wiring & `stage4_pending` ledger records; Stage 1 honest-confidence guidance.
  - `tools/wc1/overnight.py`: `build_queue_with_needs_human()` filtering data-in-code, locked TOMLs, untracked WIP TOMLs, unbuildable T3s, name-only entries, existing cross-TOML entries, and incomplete T4s (68 fn skipped cleanly in `--dry-run`); passes `--addrs`; removes `ref_verified_by` editing from repair prompt; mechanical `_wire_verified_t4_after_repair()`; hardened commit gate (`_check_no_regression`, strict per-module `_check_allowed_paths`, `_verify_new_ref_verified_by`, wider cheat scan, `verified_by = "match: ..."` verification).
  - Added 10 tests in `tests/test_batch_driver.py` and `tests/test_overnight.py`.
- **Verified green at `93a83f0`:** `make verify` passes (`1257 passed, 13 skipped, 5 xfailed`, `build/war.exe` IDENTICAL with 378 functions from 373 C files); `make progress`: **721/1010 DONE (71.4%)** (378 T3 all 10.0a, 349 T4, 6 unchecked ref).
- **Awaiting user approval (left untouched per ground rules):** fix always-skipping `tests/test_snd_f1.py` & `mod_20c30.toml:521` fake T4; clean up untracked `bullet.toml:230-232` dangling `ref_verified_by` and orphaned `src/snd/bullet_start_anim_reference.c`; tighten skip-on-missing-symbol tests and optionally add pytest-node existence validation in `wc1.symbols`.

## 2026-11-21 (late-2) — User-approved T4 skip tightening, SND.C `0x26360`/`0x26390` fixes, `wc1.symbols` AST validator (`f56c951`..`64bb40a`), Opus 5.5 review

- **User approved** fixing `tests/test_snd_f1.py` / `0x26390` / untracked `bullet.toml`, tightening the skip-on-missing-symbol tests, and adding `ref_verified_by` pytest-node validation to `wc1.symbols`. Audited all 349 `ref_verified_by` citations across `analysis/symbols/*.toml` first and uncovered one additional broken citation (`analysis/symbols/mod_295d0.toml:534` `AiInitUnitOrder` citing prefix `test_t4_ai_init_unit_order` instead of the 3 real passing tests `_worker`/`_town_hall`/`_summoned`).
- **Opus 5.5 (`claude -p --model opus --effort high`) reviews (plan review + diff review + final sign-off → `APPROVE`):**
  - Plan review approved Option A for `0x26390`, split commits cleanly (area fixes first, validator last), required `0x10200`-byte `anim_table` + `0xfffe`/odd offsets + upper-bit-dirty `edx` (`0x12345678`) coverage + explicit `repo_root` param + reusing one AST helper in `batch_driver.verify_t4_node`, and flagged a pre-existing clean-checkout issue (`6ca6f34` `src/mod_3aac0/bitmap_blit_transparent_fliph_reference.c:4` includes untracked `src/include/mod_3aac0_c.h`).
  - Diff review caught two items (change `t3_blocker` on `0x26360`/`0x26390` back to `codegen:` per `docs/GOAL.md:78` since the insn sequence differs, and document the new `make symbols` `ref_verified_by` AST checks in `docs/ANALYST_GUIDE.md`); both fixed and approved.
- **Landed 4 atomic commits:**
  - `f56c951` (`T4: SND.C BulletStartAnim 0x26390 + fix fn_26360 0x26360 reference C and difftests`): fixed 8-bit `unsigned char` masking (`mov cl,dl; xor ch,ch`) in `src/snd/fn_26360_reference.c` and `src/snd/bullet_start_anim_reference.c`, moved `0x26390` `BulletStartAnim` with full disassembly/caller evidence into tracked `analysis/symbols/snd_f1.toml` (and locally removed its `TEMP draft` duplicate lines 222–232 from untracked `analysis/symbols/bullet.toml` — kept untracked; all 8 `wc1.bullet_match` matches still hold), fixed `0x26360` evidence in `mod_20c30.toml`, rewrote `tests/test_snd_f1.py` with real wired T4 difftests (zero skips, `0x10200` table, `0x60`-byte watched object, callee-saved regs), updated `docs/subsystems/snd_f1.md`.
  - `bc7acb5` (`mod_295d0: fix AiInitUnitOrder 0x29cf8 ref_verified_by test node citations`): cited all 3 real tests (`_worker`, `_town_hall`, `_summoned`).
  - `db851e0` (`tests: fail loudly instead of pytest.skip on missing symbols in T4 helpers`): tightened `tests/test_mod_16390_t4.py`, `test_mod_3aac0_c.py`, `test_flic_decode.py`, `test_startup_c1.py` (`raise AssertionError` instead of `pytest.skip`) and removed dead `if False` skip in `test_mod_3d260_c.py`.
  - `64bb40a` (`wc1.symbols: validate ref_verified_by pytest nodes and skip/xfail cheats via AST + tests`): added mtime-cached AST validator (`parse_ref_verified_by_nodes`, `validate_ref_verified_by_entry`, `check_ref_verified_by`) to `tools/wc1/symbols.py` wired into `load(root=..., repo_root=...)` (checks relative `tests/*.py`, every cited `file::node` / `Class::method`, rejects inline/decorator/alias/raise skip & xfail cheats and unconditional `pytestmark`, requires `ref` filename mention), reused it in `batch_driver.verify_t4_node`, passed `repo_root` from `overnight.py`/`batch_driver.py`, documented in `docs/ANALYST_GUIDE.md`, and added `test_ref_verified_by_validation` in `tests/test_pipeline.py`.
- **Verified green at `64bb40a`:** `make verify` passes (`1260 passed, 11 skipped, 5 xfailed`, `build/war.exe` IDENTICAL with 378 functions from 373 C files); `make progress`: **722/1010 DONE (71.5%)** (`named` 752 / 74.5%, `T3` 378 all 10.0a, `T4` 349, 6 unchecked ref); `wc1.overnight --dry-run` `needs_human` dropped 68→67 (`untracked WIP TOML` gone).

## 2026-11-22 — Overnight Wave-3 progress (+31 DONE), `wc1.overnight`/`batch_driver` v2 hardening (`635593f`), salvages (+8 DONE: `2808a11`..`4819b60`), Opus 5.5 review

- **Unattended overnight run (`2dbbdfd`..`a20980c`, +31 DONE: 722→753):** landed 7 clean commits (`mod_30bd0`, `mod_20a80`, `mod_1dca0`, `mod_20c30_ui`, `mod_209e0`, `mod_3b3a0`, `mod_34060`) and surfaced 4 failure causes across 5 failed runs:
  1. `mod_16390_c2` (12 fn = 1,966 insns) & `mod_2ced0_c2` (4 fn = 956 insns): fixed 12-fn chunks blew the `$1.10` budget before Stage 4 could fix tests; `make verify` short-circuited at `compile-check` so `overnight_repair` fixed the 2 compile errors without seeing 5 pytest failures, then rolled back the whole batch (including 1 T3 + 6 passing T4s).
  2. `mod_33520_c3` & `mod_13f60_c6`: false positive in `_verify_staged_toml_refs` checking legacy split-file `verified_by = "match: ..."` paths on old unrelated entries that already have `src =` (14 such entries across `graphics.toml`, `input.toml`, `mod_13f60.toml`; 0 without `src =`).
  3. `mod_13b30`: Stage 1 invented duplicate data link name `_unit_type_callback` (`0x51408` vs `0x510d8`), printed `[warn]`, and crashed in `permuter` on `symbols.load(strict=True)`.
- **Opus 5.5 (`claude -p --model opus --effort high`) reviews (plan + diff + final sign-off → `APPROVE`):**
  - Plan review caught unstable `(mode, m, ci)` failure keys (switched to `(mode, m, tuple(addrs))`), chunk-level vs module-level failure isolation, ledger-delta tracking of shared `repair_budget`, pre-repair `pytest`/`wc1.symbols` probe, and `link_name`-based Stage-1 disambiguation before cache/header write.
  - Diff review caught redundant `mod_13f60_c6` C/test edits (reverted; kept only `mod_13f60.toml` `verified_by`), `_disambiguate_semantic_names` header replacement clobbering earlier intra-batch declarations or existing externs (fixed via line-scoped `_patch_header_decl`), mislabelled `CriticalErrorPrompt` `od-frame:` blocker (fixed to `codegen:`), missing abort/polling cases in `test_mod_33520_c3.py` (added with RAM-backed watched event cursor), `I16(&cursor_hotspot_y)` cleanup, and 900s probe timeouts; all 9 items fixed and approved.
- **Landed 4 atomic commits:**
  - `635593f`: `wc1.overnight`/`batch_driver` instruction-capped chunking (`--max-chunk-insns 500`, `_pack_chunks`, stable chunk keys, chunk-isolated retries), 2-round shared-budget repair + pre-repair diagnostic probe (with 900s timeout), `_verify_staged_toml_refs` `not fn.get("src")` guard, Stage-1 `_disambiguate_semantic_names` + `_patch_header_decl` + hard post-Stage-1 `DriverError`, plus 4 new unit tests.
  - `2808a11`: `mod_16390` salvage (**+7 DONE**): T3 `UiInputInit` (`0x18488`, `playflic.toml` — kept in `playflic.toml` along with `0x184cc` to preserve `test_mod_16390.py:272` `len(mine)==52`) + 6 T4s (`DialogRelocate`, `DialogCreate`, `DialogLoop`, `UiKeyDispatch`, `UiEventPump`, `UiEventPumpNet`) with trimmed `tests/test_mod_16390_c2.py` and updated `docs/subsystems/mod_16390.md`.
  - `4e43964`: `CriticalErrorPrompt` (`0x33520`, `graphics.toml`) T4 salvage (**+1 DONE**) without empty `mod_33520_c3.h`, with full retry/abort/polling T4 coverage in `tests/test_mod_33520_c3.py`.
  - `4819b60`: `mod_13f60` `ChooseCampaignDialog` (`0x157e8`) marked `confidence = "verified"` + `verified_by` via existing `choose_campaign_dialog.c` T3 match (+0 DONE, removes unbuildable T3 from queue).
- **Verified green at `4819b60`:** `make verify` passes (`1300 passed, 11 skipped, 5 xfailed`, `build/war.exe` IDENTICAL with 397 functions from 392 C files); `make progress`: **761/1010 DONE (75.3%)** (`named` 783 / 77.5%, `T3` 397 all 10.0a, `T4` 369, 6 unchecked ref, 9 unclassified runtime).

## 2026-11-22 (late) — Unattended overnight failure investigation, T4 cheat-bypass closure & runtime oracle audit (`9f6b8ad`..`1c5e825`), Opus 5.5 review

- **Stopped live unattended `wc1.overnight` runner cleanly** (sent `kill` via `build/live/control.json`; rolled back in-flight `mod_2ced0_c4` cleanly; `4a7fadc` `UnitStartDeath` and `bd86e41` `mod_16390_c4` had already committed on `main`).
- **Four root causes uncovered behind the failed `mod_16390_c3` run:**
  1. **Critical silent T4 cheat bypass (`bd86e41`, `mod_16390_c4`):** `stage4_fix2` defined `_expect_mismatch` wrapping `t4spec.run_spec` in `with pytest.raises(AssertionError):`, bypassing all static/exit-code checks and falsely marking 3 broken functions DONE while hiding a real infinite-loop bug in `src/mod_16390/outro_play_flic_reference.c:56` (`layers[13].x + .w` instead of `.y + .h`), a 2-arg `ListDraw` stub bug in `DialogActivateItem`, and an inline-`rep movsd` vs `memcpy`-stub mismatch in `DialogRun`.
  2. **Blind/test-only Stage 4 & repair turn exhaustion:** `run_full_module` Stage 4 omitted disassembly; `stage4_fix`/`t4fix` received neither disassembly nor `*_reference.c` and could only patch tests (driving the `_expect_mismatch` cheat in `mod_16390_c4` and input-weakening `yo=-3 -> -4` in `mod_2ced0_c4`); `run_bounded_repair` `--max-turns 10` exhausted turns on both `mod_16390_c3` and `mod_2ced0_c4`.
  3. **Stale `EditFieldDraw` (`0x174c0`) prototype (visible `mod_16390_c3` failure):** `src/include/mod_16390.h:174` and `analysis/symbols/mod_16390.toml:448` declared `void EditFieldDraw(short x, short y, short w, short h, int caret)` (4 stack bytes) instead of `void EditFieldDraw(Rect r, short caret)` (16 stack bytes, `ret 0x10`), contradicting `edit_field_draw_reference.c` (hidden via `#define` hack) and making `test_edit_field_draw` pass accidentally on zeroed stack bytes; this made `EditFieldRun` (`0x17588`) unfixable.
  4. **Full-repo 373-node runtime oracle audit (`WC1_T4_AUDIT_LOG` across all 80 test files):** **361/373** passed strict runtime audit (`8067` records; zero swallowed assertions repo-wide); uncovered **5 real vacuous zero-observation T4 tests** (`FogUpdateTile` `0x1e9a0`, `PaletteCyclesClear` `0x334fc`, `HLine` `0x3ac10`, `DrawNumberRight` `0x2f878`, `DrawNumberCentre` `0x2f8bc`), where watching `DrawText` exposed a **real missing `/ 2` bug** in `src/mod_2efd0/draw_number_centre_reference.c:14` (`x - w` instead of `(short)(x - (short)w / 2)`). The remaining 12 pre-existing tracked hand-written nodes bypass `cemu.run_pair` matching `link_name` and were left unmodified (`tests/test_network.py`: `0x1fb60`/`0x201c0`/`0x2020c`/`0x2061c`, `tests/test_resources_lzss.py`: `0x31870`/`0x34480`/`0x3452c`/`0x41550`, `tests/test_graphics_lib.py`: `0x33150`/`0x331be`, `tests/test_network_t4_2.py`: `0x2070e`, `tests/test_game_2c4e0.py`: `0x2c4e0`).
- **Opus 5.5 (`claude -p --model opus --effort high`) review rounds (5 full rounds):**
  - Round 1 (diagnosis & plan): `approve with changes` (added runtime oracle audit log, shared AST cheat prefilter, anti-weakening diff, full-repo audit).
  - Round 2 (`4a7fadc..28e3349`): caught 14 items (`emu.call` override, nonce/replay, `run_spec_done` mid-loop abort, realpath vs basename, strict `case`/`ref_patch` validation, `DrawNumberCentre` odd/zero/negative rounding); all fixed in `9e13a26` + `9a5d1f9`.
  - Round 3 (`28e3349..9a5d1f9`): caught `CModule`/`Emu` method/attribute tampering (`publics` redirect, `src` forgery, prebuilt `mod=`, `c_insns`); fixed in `e3dd8f8`.
  - Round 4 (`9a5d1f9..e3dd8f8`): caught C-side stubbing/tracing/empty `_c_ranges` and out-of-process OMF digest verification; fixed in `18c0c96`.
  - Round 5 (`e3dd8f8..548aca4`): confirmed Should-Fix G (`$WATCOM` unset / compile failure fail-closed) and caught 2 Must-Fix F (`c_patched`) bypasses (decoy `cmod.base` vs `c_addr`/`publics`/`_c_ranges`, and instance overrides of `_reloc_patch`/`_target`); both closed and tested in `1c5e825`. Round 6 sign-off hit Claude's 5-hour quota (`resets 6:10am Asia/Yerevan`).
- **Landed 12 atomic commits (each verified green with `make verify`):**
  - `9f6b8ad`: `T4: mod_16390_c4 remove _expect_mismatch cheat and fix OutroPlayFlic loop/harnesses`.
  - `43d6047`: `wc1: runtime T4 oracle audit, shared AST cheat prefilter, and anti-weakening diff + tests`.
  - `52bf80d`: `wc1: Stage 4 disasm/ref-C patching, repair header/turn-cap hardening + tests`.
  - `6c881bd`: `mod_16390: fix EditFieldDraw 0x174c0 prototype (Rect by value + caret, ret 0x10) and T4 test`.
  - `2f7d862`: `T4: fix 5 zero-observation difftests (FogUpdateTile/PaletteCyclesClear/HLine/DrawNumber*) and DrawNumberCentre /2 bug`.
  - `28e3349`: `wc1.symbols: validate multiline/env-gated pytestmark via AST + test`.
  - `9e13a26`: `wc1: close Opus review bypasses (emu.call, nonce, run_spec_done, realpath, strict case/ref_patch) + tests`.
  - `9a5d1f9`: `T4: mod_2efd0 exercise odd/zero/negative TextWidth rounding in DrawNumberCentre`.
  - `e3dd8f8`: `wc1: guard CModule/Emu method tampering, source sha256, and c_insns in T4 audit + tests`.
  - `18c0c96`: `wc1: guard C-side stubs/trace/empty ranges and verify out-of-process OMF digest + tests`.
  - `548aca4`: `wc1: verify C code bytes in emu (c_patched) and fail closed on OMF digest audit + tests`.
  - `1c5e825`: `wc1: bind c_patched to c_addr/publics, guard all CModule methods, fail closed on missing ref_rel + tests`.
- **Verified green at `1c5e825`:** `make verify` passes (`1315 passed, 11 skipped, 5 xfailed`, `build/war.exe` IDENTICAL with 397 functions from 392 C files); `make progress`: **765/1010 DONE (75.7%)** (`named` 783 / 77.5%, `T3` 397 all 10.0a, `T4` 373, 6 unchecked ref, 9 unclassified runtime).
