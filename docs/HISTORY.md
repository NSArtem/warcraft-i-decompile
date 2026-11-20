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

