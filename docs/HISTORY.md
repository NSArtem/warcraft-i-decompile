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

## 2026-11-22 (morning) — `wc1.overnight` 3-hour hang: bounded compiles, permuter breaker, toolchain stop, stall watchdog

- **Incident:** an unattended `wc1.overnight` run at 24d24c2 (Python 3.14.7)
  hung for 3 h in overnight → `wc1.batch_driver` → `permuter.permute_file()`
  on `src/mod_1eba0/minimap_init.c` (0x1eba0); `graceful_stop` acts only at
  item boundaries and could not break it, and the machine needed a reboot.
- **Analysis (from the code; not reproduced):** a wine/wcc386 compile that hits
  oldcc's 180 s timeout was turned into a plain `SystemExit` and scored as a
  bad candidate, so a stuck Wine cost 180 s per candidate (~48 min per
  `permute_file`, called twice per function); OW2 compiles had no timeout;
  batch_driver's T4 pytest runs were silent and uncapped; overnight had no
  watchdog.  The 3.14 default start method (forkserver) behind the old
  ProcessPool permuter may have played a part too; the new code does not use
  a process pool there.
- **Fix (one commit):**
  - `wc1.oldcc`: `OldCCTimeout`; on timeout `wineserver -k` for the prefix;
    `quiet` diagnostics; `.log` cleanup.  `wc1.match`: `CompileTimeout`
    (a SystemExit subclass) for both compilers, OW2 timeout, `quiet`.
  - `wc1.permuter`: ThreadPoolExecutor (each compile is its own process),
    candidates submitted in order with at most `jobs` in flight, lowest-index
    match wins; any exception = failed candidate; the first compile timeout
    stops the search (`env_error`, CLI exit 2); 60 s per candidate, 900 s
    wall budget, `on_progress` heartbeat.
  - `wc1.batch_driver`: `ToolchainError` from permuter `env_error` or a
    `CompileTimeout` in the T3 classify/diff paths → `[TOOLCHAIN ERROR]`,
    exit 78 (`EXIT_TOOLCHAIN`); pytest runs capped (`_run_capped`: kills the
    /proc descendants) and beating the worker meta every 60 s; permuter
    heartbeat; faulthandler on SIGUSR1.
  - `wc1.overnight`: stall watchdog (`--stall-timeout`, default 1200, 0 off,
    must be ≥ PYTEST_TIMEOUT + 60) on child output + worker stream/meta
    heartbeat (monotonic, drains pending output first), SIGUSR1 stack dump,
    process-group kill, item archived + rolled back as `STALLED` and the run
    goes on; `TOOLCHAIN_ERROR` archives + rolls back and stops the run.
  - Tests: `tests/test_permuter_unit.py` (new, fake compiler), stall/toolchain
    e2e and CLI tests in `tests/test_overnight.py`, `_run_capped`/`_permute`
    in `tests/test_batch_driver.py`, timeout + `wineserver -k` in
    `tests/test_oldcc.py`; `**_kw` on existing fakes only.
- **Opus 5.5 subagent reviews:** the design review moved the permuter from
  processes to threads, made the winner deterministic by index, caught the
  missing OW2 timeout and the silent uncapped pytest runs (watchdog needs a
  heartbeat).  The implementation review's adopted notes: toolchain errors
  fatal + `wineserver -k`; pytest heartbeat and `--stall-timeout`
  validation; kill pytest descendants; drain output before declaring a stall;
  monotonic clocks; de-flaked stall tests; missing tests; docs.  Deferred (in
  AGENTS.md next steps): a per-item deadline / slow-but-under-timeout compile
  breaker, pgid PID reuse, a redundant `.log` unlink, the forkserver question
  for `match._pool`.
- **Verified:** `make verify` green (1355 passed, 11 skipped, 5 xfailed; build
  IDENTICAL); `make progress` DONE 794/1010 (78.6%).  The `mod_1eba0` draft
  the hung run left is untracked and was not touched.


## 2026-11-22 (follow-up) - review of the hang fix 1ed5753

An outside review of 1ed5753 found four gaps; all checked against the code
and fixed:

- `make verify` ran unwatched (a stuck Wine compile inside it would wedge
  the night again): now under the stall watchdog (output only), STALLED +
  rollback, also for the repair re-verify.
- A stall left Wine running: overnight now runs `wineserver -k` after the kill.
- `match.compile_check` turned a `CompileTimeout` into an ordinary compile
  failure (batch_driver's area compile-check and `_apply_t4_patch_result`,
  where the SystemExit also escaped `except Exception` and left the patched
  file unrestored).  It now raises; batch_driver maps it to `ToolchainError`
  (file restored); the `wc1.match` CLI prints `[TOOLCHAIN ERROR]`, exits 78,
  and overnight stops on that marker in verify output too.
- `_run_capped`'s final `communicate()` could block on a pipe held by an
  escaped grandchild: 5 s cap, then close the pipes.

Smaller: a toolchain stop is now FAILED with exit 78 (was DONE/0); the
permuter never applies a winner after a timeout; TUI icons for
STALLED/TOOLCHAIN_ERROR; monotonic clock in `_kill_stalled`; `timer.join` in
`call_claude`; doc typo; AGENTS.md gate count.  Tests: verify stall + verify
toolchain marker (`test_overnight.py`, Wine reset faked by an autouse
fixture), `compile_check`/CLI timeout (`test_match_all.py`), restore +
ToolchainError and the escaped-grandchild pipe (`test_batch_driver.py`, shown
to hang on the old code), timeout-never-applies (`test_permuter_unit.py`).

The user scrapped the untracked BULLET.C / mod_1eba0 / `mod_3aac0_c.h` drafts
(to be redone from scratch).  That showed HEAD was green only with them in
the tree: committed SpellHolyVision/SpellPoisonCloud/SpellRainOfFire (T3),
UnitRemove, UnitsInitGame and UnitsDraw ref C and the `mod_3aac0` fliph ref C
used names defined only in the draft (`BulletCreate` etc.) or included its
header.  Repaired without semantic claims: `fn_11cb0`/`fn_11cd8`/`fn_11ddc`/
`fn_11e70`/`fn_11f10`/`fn_11f78` low placeholders (mod_104b0.toml),
`unit_half_size` 0x59530 (medium, from the UnitsInitGame loop), inlined
`Rect`/`Bitmap` (docs/subsystems/mod_3aac0_c.md); `make verify` 1360 passed.

## 2026-11-22 (evening) - `wc1.t3_audit`: read-only bulk T4 -> T3 audit

New `tools/wc1/t3_audit.py` + `tests/test_t3_audit.py` (26 fake-driven unit
tests), docs/ANALYST_GUIDE.md.  It compiles every in-scope T4 reference C under
Watcom 10.0a (declared flags, then the permuter's 10.0a presets, stopping at
the first exact whole-object match), runs `build.check_t3_buildable` on
matches, and writes JSON/Markdown/CSV to `build/t3_audit/`; no source or
TOML is changed.  Full run (about 7 min, 2982 compiles): 432 T4 =
MATCH_BUILDABLE 5 (AilInit 0x269f0, SaveSlotPath 0x14740, SelectionBoxTrack
0x2f0c8, StatusPanelDraw 0x28894, StatusPanelInit 0x29120), MATCH_UNBUILDABLE
4 (SaveErrorDialog 0x1aca8 data anchor order; DialogHighlightOff 0x16d48,
IntroFadeStep 0x22eac, FarmPanelChanged 0x28254 sibling mismatches), MISMATCH
421, SKIPPED 2 (NetModemWaitResponse_tail 0x2070e, PathPeekStep 0x2c4e0),
no compile or toolchain errors.  Independent read-only wc1-analyst (Opus 5.5)
review: round 1 APPROVE with 4 Should Fix (a timeout inside the buildability
check now aborts as TOOLCHAIN_ERROR; COMPILE_ERRORs beside a parallel timeout
are discarded; tests added; `check_t3_buildable`'s swallowed timeouts,
cpu_count parallelism and anchors-cache write documented, not changed),
round 2 APPROVE.  Open: `build._compile_one` should re-raise
`match.CompileTimeout` (shared tool, separate change); promotion of the 5
candidates needs separate authorization.

## 2026-11-23 - T3 promotions of the 5 `wc1.t3_audit` candidates

Branch `feature/wc1.t3_promotions`, one commit per function, each with
`make verify` green and `wc1.match` MATCH under Watcom 10.0a with the audit's
flags: AilInit 0x269f0 (`ccc9770`, `-d1+` fixes the frame-slot order;
test_audio_snd.py got a per-file flags override instead of weakening the area
flags check), SaveSlotPath 0x14740 (`921af24`, `-oa`), SelectionBoxTrack
0x2f0c8 (`d68d68b`, `-oa`), StatusPanelDraw 0x28894 (`af05689`, `-oa` keeps
the SelectionFirst type in edx), StatusPanelInit 0x29120 (`c99cbfb`, flags
unchanged; the stale blocker was the then-unnamed LayerAdd 0x21d0c).  The
`*_reference.c` files were renamed to their T3 names, the TOML entries moved
`ref` -> `src` with `match:` evidence, and the T4 difftests still run on the
T3 C.  No blockers.  `make progress`: DONE 880 (87.1%), T3 458; final
`make verify` 1493 passed + 11 skipped + 5 xfailed.  Merged into local main
(no push).

## 2026-11-23 - Wave 4: T4 -> T3 recovery in `wc1.overnight`

- New `tools/wc1/wave4.py` (discovery from ref C + difftest evidence, ordering by a fresh
  `build/t3_audit/report.json` else a deterministic fallback, MATCH_UNBUILDABLE last; deterministic
  audit, bounded LLM repair of the existing ref C with restore on any failure, promotion ref -> src,
  outcomes PROMOTED / NO_IMPROVEMENT / UNBUILDABLE / FAILED / TOOLCHAIN_ERROR).  `batch_driver
  t3-recovery`, `--wave wave4` / `--wave4-max-calls` in overnight, TUI wave selector.  Commits are
  gated on PROMOTED + T3 delta == promoted entries + IDENTICAL `make verify` + path allowlist.
- Independent `wc1-analyst` review: REJECT first (M1 generic repair loops also ran for wave4, M2
  difftest pass could be all-skipped), fixed with S1 (difftest timeout), S2 (resume call budget
  reduced by calls already used), S5 (IDENTICAL required) + mutation-checked tests.  Not changed:
  restart retries NO_IMPROVEMENT functions (exclusion is per run), a repair patch that breaks
  compilation ends FAILED instead of spending remaining calls.
- No real recovery, LLM call or promotion was run.

## 2026-11-23 - Wave 4 first real run; two archived matches recovered

- First real Wave 4 run (`--wave wave4`, Codex, 2 calls max per item): 10 functions,
  19 calls.  NO_IMPROVEMENT: 0x12594, 0x1284c, 0x1295c, 0x26b3c, 0x26f1c, 0x26fd4,
  0x270dc, 0x27554.  PROMOTED but rolled back by `make verify`: SndStopData 0x27278
  (1 call; `test_reference_c_is_still_a_near_miss` required a near miss per file) and
  FogMapClear 0x12404 (2 calls; the old promotion kept the T4 `verified_by` and added a
  second one, `Cannot overwrite a value`).  Fixes merged before this session
  (`dc4cd09`, `35cdc19`).
- Recovery without LLM calls (branch `feature/wc1.wave4-recover-archived`): the archives
  `build/failed/20261123_030615_w4_27278/` and `..._030809_w4_12404/` held the patched C,
  the TOML and `failure.log`; the outcomes JSON in `build/wave4/outcomes/` names the change.
  The C bodies and the compiler/flags headers were restored byte for byte (comments
  updated; the archived SndStopData file also kept its old multi-line header comment,
  dropped); the archived TOMLs were not used, the entries were promoted with the current
  `wave4.promote_toml_text` (FogMapClear's T4 `verified_by` moved to evidence, former
  blockers kept as evidence).  SndStopData: one positive `&&` guard instead of two
  `continue`s gives the original's near `je rel32` loop exit (main's version under 10.0a:
  `+0x1a got 74 want 7e`).  FogMapClear: `i` first, `p` `register`, compiler OW2 -> 10.0a
  (main's version under 10.0a: `+0x2 got 8b want a1`).  `wc1.match` MATCH for both, both
  MISMATCH under `--cc ow2`; difftests `test_snd_stop_data_t4`,
  `test_fog_map_clear_reference_c_matches_original`, `test_fog_map_loops[FogMapClear]` pass
  on the T3 C.  `tests/test_cmd_123f0.py`'s hand-written built/by_match sets gained 0x12404.
- Commits: `679771e` (SndStopData), `bae2e6d` (FogMapClear), `35cce49` (review wording
  fix); `make verify` green at each (1562 passed + 11 skipped + 5 xfailed, IDENTICAL).
  `make progress`: T3 458 -> 460, T4 427 -> 425, DONE 880 unchanged.
- Independent wc1-analyst (Opus 5.5) review, read-only: round 1 APPROVE (each commit built
  IDENTICAL in a separate worktree; Should Fix: stale "not built" evidence line, fixed;
  optional notes on doc wording, applied, and on `wave4.set_flags_header` and a FogMapClear
  flags exception in the area test, deferred to next steps).

## 2026-11-23 - Wave 4 hardening and first automatic commit

- Starting from `0fed057`: `250ee99` canonicalizes single-line and multi-line
  compiler/flag metadata without throwing away the surrounding C or comments;
  `a146041` adds an explicit match test for FogMapClear with its own no-`-ol` flags,
  retaining both existing differential checks.
- `ba547f4` suppresses fully exhausted, clean `NO_IMPROVEMENT` searches across
  invocations, fingerprinting the recovery inputs rather than HEAD. Quota,
  toolchain, infrastructure and incomplete searches are not cached. The
  `--wave4-retry` bypass leaves normal outcome/diagnostic reporting intact;
  previous receipts are archived in `build/wave4/history/`.
- `0122e43` supports inline TOML evidence and gates a promotion on the actual
  T4 -> T3 transitions for the reported object, a clean worker exit and a real
  `IDENTICAL` build result. Difftests see the promoted compiler flags. The
  disposable-repo integration test uses real Watcom, the game image, `make
  verify` and Git, stubbing only the model response. It exercises a successful
  commit and rollback/archival after full-gate and Git-hook rejections. The
  fixture uses a short path because Watcom 10.0a crashed on nested xdist paths.
- Controlled run: SpellCastOrder `0x27aa4` was the audit's closest register-only
  near miss (score `0,0,2,0,0`). Ran one item with Codex `gpt-6.2-sol:high`,
  a two-call limit, 65% short-window / 80% weekly caps, a 3pp weekly run cap
  and no quota sleep. One call (15.3s) eliminated the pointer alias, making
  both indexed accesses use EBX as in the original. Watcom 10.0a matched with
  `-s -ot -oa -ol -4r -zp2`. Usage was 31% -> 34% (5h) and 23% -> 24% (7d).
  The runner emitted **`COMMITTED a2bb4d2`** with +1 T3, not just `PROMOTED`;
  log `build/wave4/hardening-real-27aa4.log`. Full verify: Build A IDENTICAL,
  1607 passed, 11 skipped, 5 xfailed. Progress: T3 461, T4 424, DONE 880/1010.
- Independent Sol high review round 1: REJECT. `c4f438e` required tracked C
  and all owning TOMLs before the worker, confirmed the receipt's actual
  owners, pinned promotion bytes across verification, and restored both
  worktree and index on rejection. Added real-CLI regressions for an
  untracked owner, a late C rewrite, and a staged stray file; isolated the
  fixture Wine prefix and bounded its child processes.
- `b450509` keyed misses on the matcher's symbol addresses and function
  extents, handled commented include directives, and rejected incomplete
  receipts and unresolved dependency forms. An explicit address now
  overrides the default skip list for a targeted retry. `make verify`:
  Build A IDENTICAL, 1613 passed, 11 skipped, 5 xfailed.
  A read-only check formed cache keys for all 424 eligible Wave 4 candidates.
- Independent Sol high review round 2: APPROVE, no remaining Must Fix
  findings. Its two follow-ups were to bypass the retry cache on C90
  trigraphs and document the exclusive-worktree and non-mutating-hook
  requirements. The final follow-up required strengthening the trigraph
  test: the old scanner must silently miss a real include, not reject an
  unterminated comment. The corrected regression fails with the guard
  disabled; Sol high gave final APPROVE with no remaining Must Fix or
  Should Fix findings. Final `make verify` at `ee6f5a9`: Build A IDENTICAL,
  1614 passed, 11 skipped, 5 xfailed.

## 2026-11-24 - Wave 4 Next Generation (Wave 4A + Wave 4B) & Supervised Production Run

- **Phase 0 baseline recovery (`feature/t3-symbol-reconciliation`, `efa12f9..c3a3ea2`, merged `--no-ff` at `433e10a`)**:
  Recovered and independently reviewed (`APPROVE`, 0 Must Fix, 3 Should Fix, 2 Optional)
  the 13 interrupted reconciliation commits (+34 T3 promotions: T3 461 -> 495, T4 424 ->
  390, named 894 -> 899, DONE 880/1010). Resolved all findings in two atomic commits on
  `feature/wave4-nextgen`: `5d78f23` (hardened `wc1.match` extent-retry fixup guard and
  deterministic unresolved diagnostics + 3 tests) and `7a58b26` (updated 5 stale
  `t3_blocker` descriptions and dropped redundant `test_mod_1dca0` re-compile check).
  Fresh full `wc1.t3_audit` baseline on `7a58b26`: 390 T4 functions, 81 affected by 147
  unresolved external relocations.
- **Wave 4A + Wave 4B architecture (`4514bb5`, merged `--no-ff` into local `main` at `20060ec`)**:
  - `tools/wc1/wave4_deps.py`: structured dependency inventory from `attempts[].unresolved`,
    multi-source binary corroboration (best-attempt `original_candidate`, original calls/LE
    fixups, AST-extracted test `EXTRA`, established mappings — never identifier spelling
    alone), generic `-zp2` header struct layout & containing-owner detection, conservative
    ABI/data compatibility validation, and syntax-aware C symbol rewriter (protecting
    comments, codegen headers, strings, preprocessor lines, struct/union/enum bodies,
    member accesses, local/param/typedef/macro/static collisions, and multi-declarator
    statements).
  - `tools/wc1/wave4a.py`: incremental per-unit `build/wave4/audit_state.json`, input-
    sensitive `ReconcileCache` (`build/wave4/reconcile_cache/`), commit-gated
    `build/wave4/mappings.json`, zero-LLM auto-promote + mechanical paths, bounded
    fresh-context LLM research (`RESEARCH_SCHEMA`, `clib.toml`/protected-TOML/interior-
    `[[data]]`/`verified_by`/anti-weakening guards), dependency-driven reprocessing, and
    verified intermediate `RECONCILED` acceptance (`unresolved_after < unresolved_before`,
    zero regressions, Build A `IDENTICAL`).
  - `tools/wc1/wave4.py`, `batch_driver.py`, `overnight.py`, `tui.py`, `docs/ANALYST_GUIDE.md`:
    Wave 4B routes unresolved-relocation functions to Wave 4A (`--wave4-include-unresolved`
    override), ranks pure codegen near-misses ahead of unresolved relocations, exposes
    `--wave wave4a`, `--wave wave4b`, combined `--wave wave4`, `--wave4a-max-calls`,
    `batch_driver t3-reconcile`, and writes `build/wave4/metrics.json`.
  - Tests: `tests/test_wave4_deps.py`, `tests/test_wave4a.py`, `tests/test_wave4a_end_to_end.py`
    (real Watcom 10.0a, OW2, `war.exe`, `make verify`, Git), `tests/test_wave4_cli.py`.
  - Independent read-only Phase 8 review: Round 1 `REJECT` (6 Must Fix: unnamed-param ABI
    regex, staged new-file rollback in `_wave4_status`/`_rollback_tree`, shadowing/over-drop
    in mechanical rewriter, `clib.toml`/`verified_by`/interior-`[[data]]` guards, premature/
    Cartesian `mappings.json` writes, `SKIPPED`/`ToolchainAbort` handling; + 7 Should Fix +
    5 Optional); all resolved and verified in Round 2 **`APPROVE`** (`1650 passed`, IDENTICAL).
- **Supervised sequential production run by Agent B (`20060ec..26c8da5` on `feature/wave4-production-run`, merged `--no-ff` into local `main`)**:
  - 6 sequential stages across `4.55 h` runner wall time (`worker_seconds = 2648.7 s`,
    `verify_seconds = 11333.7 s`), Codex Plus (`gpt-6.2-sol/low`, hard caps `5h<=85%`,
    `7d<=75%`, `+15pp` delta, `--no-sleep`):
    - **Wave 4A zero-LLM mechanical**: 13 commits (2 T3: `33437f4`, `51bfc82`; 11 `RECONCILED`).
    - **Wave 4A bounded LLM research**: 16 commits (6 T3: `17c6495`, `78b7427`, `e2bc40e`,
      `3fd51be`, `94094cb`, `6902b78`; 10 `RECONCILED`), 1 `AMBIGUOUS` (`data_59848`),
      43 unresolved relocations eliminated, 38 functions unblocked (`26` calls, `+1.0pp` 7d =
      `8.0 T3/7d-pp`, `1.115` useful commits/call).
    - **Wave 4B codegen recovery**: 3 T3 commits (`ac30ef6` `NetModemCommand`, `0694ca6`
      `DialogItemLoop`, `26c8da5` `SetRacesScreen`), 20 cached `NO_IMPROVEMENT` misses
      (`43` completed-item / `45` total ledger calls, `+2.0pp` 7d).
    - **3 live-diagnosed infra repairs** (each with regression test, `make verify` green,
      independent read-only review `APPROVE`): `49a93d4` (`test_tui.py` async poll flake),
      `b36c418` (`wave4a._compile_check_files` 2-tuple unpack + diagnostics), `9e01d28`
      (`t4spec.audit_t4_log` fresh OMF compile bypassing stale in-process `cemu._MODS`).
  - Final progress at `26c8da5`: **T3 495 -> 506 (50.1%, +11)** (crossed 50% built from C!),
    T4 390 -> 379 (-11), named 899 (89.0%), DONE 880/1010 (87.1%); Codex quota `5h: 0% -> 16%`,
    `7d: 48% -> 51%` (`+3.0pp`); `make verify` green (`1651 passed, 11 skipped, 5 xfailed`,
    Build A `IDENTICAL`); full metrics preserved in `build/wave4/production_report.json`.

## 2026-11-24 - Dependency-Scoped Cache Invalidation & Wave 4A Backlog Exhaustion

- **Per-unit dependency fingerprints (`feature/wave4-dependency-fingerprints`, `3bd6939`, `fe17966`, merged `--no-ff` into local `main` at `5eebd59`)**:
  - Replaced global `matcher_signature()` cache invalidation with a shared schema-v2
    dependency-scoped fingerprinting engine (`tools/wc1/wave4_fp.py`) for both Wave 4B
    (`RetryCache`, `RECOVERY_VERSION = 5`) and Wave 4A (`ReconcileCache`,
    `RECONCILE_VERSION = 2`), backed by exact compiled OMF dependency capture in
    `tools/wc1/t3_audit.py` and stamped persistence in `build/wave4/audit_state.json` +
    `build/wave4/omf_deps.json`.
  - Fail-open safety (`bypass_uncertain` on missing/stale/unstamped OMF deps, trigraphs,
    unsupported includes, env overrides), 5-state cache diagnostics in `build/wave4/metrics.json`,
    bounded in-run retry eligibility (`failed_fingerprints`, `MAX_IN_RUN_WAVE4_ATTEMPTS = 3`),
    and safe legacy v1 handling (untouched on disk, rejected once as `miss_legacy_schema`).
  - Tests: `tests/test_wave4_fingerprints.py` (66 unit/integration tests) +
    `tests/test_wave4_fingerprints_e2e.py` (2 real-project E2E tests with real Watcom 10.0a,
    OW2, `war.exe`, `make verify`, and Git proving both unrelated preservation and relevant
    invalidation for Wave 4B and Wave 4A). Real-repo cost: `0.60s` for 379 Wave 4B functions,
    `1.74s` for 97 Wave 4A groups.
  - Independent read-only review (Gemini 4 Neon High): Round 1 `REJECT` (3 Must Fix, 5 Should Fix,
    3 Optional — all resolved in `fe17966`); Round 2 **`APPROVE`** (0 Must Fix, 0 Should Fix).
    Post-merge `make verify`: `1719 passed, 11 skipped, 5 xfailed`, Build A `IDENTICAL`.
- **Supervised Wave 4A production run 2 (`feature/wave4a-production-run`, `5eebd59..667dbb0`, merged `--no-ff` into local `main` at `f994a7c`)**:
  - **Exhausted the Wave 4A dependency backlog** across two contiguous runs (`6.19 h` wall time;
    `verify_seconds = 16,275.45s` [73.1%], `worker_seconds = 4,203.09s` [18.9%],
    fingerprinting/audit/orchestration `1,792.33s` [8.05%]) using Codex Plus
    (`gpt-6.2-sol/low`, `--wave4a-max-calls 2`, caps `5h<=85%`, `7d<=75%`, `+15pp` cumulative
    delta, `--no-sleep`):
    - **80 automated commits** (**+4 T3** promotions: `fa6b63c` `data_59854`, `bc804fa`
      `data_59858`, `d9d1681` `data_5985c`, `e29eae6` `data_59860`; **76 verified `RECONCILED`**
      commits), **137 unresolved relocations eliminated**, **104 functions unblocked**,
      `18 AMBIGUOUS`, `6 NO_IMPROVEMENT`, `3` expected `owner_5aa90` rollbacks, **0 infra
      failures / 0 infra repairs**.
    - Live schema-v2 cache validation: `4/4` Run 1 misses survived 67 unrelated commits at Run 2
      startup (`preserved_unrelated=4`, `hits=4`); `10` in-run requeues triggered strictly by
      scoped dependency changes; post-run dry-run hit `13/13` remaining cached groups with `0`
      uncertain bypasses. Only `owner_5aa90` (15 symbols; `MainMenu 0x15578` pre-function switch
      jump table `MATCH_UNBUILDABLE`) remains uncached.
    - Quota & tokens: `131` Codex calls (`1,639,737` input / `162,688` cached / `60,185` output /
      `5,714` reasoning tokens), `7d: 51.0% -> 57.0%` (`+6.0pp` cumulative, 40% of cap),
      `5h` peak `31.0%` (`0.611` useful commits/call, `1.046` relocs eliminated/call,
      `12.93` useful commits/hr).
  - Final progress at `f994a7c`: **T3 506 -> 510 (50.5%, +4)** (`10.0a: 509, ow2: 1`),
    T4 379 -> 375 (-4), named 899 -> 900 (89.1%, +1), DONE 880/1010 (87.1%); Wave 4B
    dependency-clean queue grew `306 -> 324`; full metrics preserved in
    `build/wave4/wave4a_production_run2_report.json`.

## 2026-11-25 - Verification Performance Optimization (`feature/verification-performance`)

- **Cross-provider orchestrated optimization (`5677541..4a21a87`, 33 atomic commits, merged `--no-ff` into local `main` at `eebe586`)**:
  - Orchestrated by Antigravity (`agy`, Gemini 4 Neon High) with Claude Opus 5.5 High (Iterations 1–4, `f0e886c..8d3f654`) and Codex GPT-6.2 Sol High (Iterations 5–7, `4696eb8..4a21a87`) as Developers, and independent read-only Codex GPT-6.2 Sol High across 7 review rounds to final **`APPROVE` (0 Must Fix, 0 Should Fix, 0 Optional)**.
  - **Root causes eliminated (without weakening verification, `Makefile`, `src/`, or `t4spec.audit_t4_log` fresh compiles)**:
    1. **`wc1.symbols` & `wc1.t4spec` (`f0e886c`, `8ee3ed4`, `fe4867e`)**: `cProfile` revealed `symbols.load()` took `2.14 s` (98% in `check_ref_verified_by()` executing 5.3M `ast.walk()` visits per call across 377 citations in 93 files, including collection-time calls across all 21 xdist processes). Added content-verified (`sha256`) TOML/AST caches returning fresh copies, single-walk alias/tamper/call-graph passes, and guarded `check_modules` bisect (`symbols.load()` `2138 -> 372 ms` cold / `18 ms` warm; `pytest --collect-only` `11.27 -> ~1.0 s`).
    2. **`wc1.insns`, `wc1.analysis`, `wc1.loaded`, `wc1.emit` (`77b123e`, `335eeea`, `630cb74`, `bdf44be`, `817b112`, `28f46e8`, `29d1aea`, `7d81593`, `4696eb8`, `1a008a1`)**: Eliminated per-instruction Capstone ctypes re-decoding across `emit`/`roundtrip`/`build`/E2E via format-5 flat validated instruction tables in the content-addressed analysis cache (single `war.exe` + `modules.toml` read, loaded-code identity via `wc1.loaded` with reload/seal fail-closed bypass, lazy `Insn`/`Operand` wrappers, read-only fields, Capstone-compatible `reg_name()`; `emit()` `1585 -> 176–246 ms` byte-identical).
    3. **`wc1.roundtrip` (`bb3a23c`, `65d6964`)**: Proves an already-converged `analysis/raw_insns.txt` in 1 NASM pass instead of 2, falling back cleanly to the full diagnostic loop on any error or mismatch (`roundtrip` `5.71 -> 1.40 s`).
    4. **Test-suite critical paths & scheduling (`49a865b`, `9e9d236`, `c71bdfa`, `f7d76cb`, `d2a6b31`, `4ba1781`, `d6b5e69`, `0298ce3`, `4a7eee5`, `50fae66`, `4ff854c`, `8d3f654`, `4cbd0e3`, `291ef3f`, `4a21a87`)**: Replaced 26 sequential `wc1.match` subprocesses in `tests/test_playflic.py` with parametrized in-process matching (+ dedicated CLI coverage in `test_match_all.py`); resolved per-invocation symbol snapshots once per test in hot differential suites (`test_snd.py` preserved untouched to keep Wave 4A's cached `sym_dat_555f8` fingerprint intact); added LPT initial-chunk heuristic in `tests/conftest.py`; seeded Wave 4 E2E disposable repos with the content-addressed analysis cache and placed them on `/dev/shm` only when cgroup v1/v2 mount-tree reachability, headroom, and LF-only procfs parsing prove safe memory availability, with shared `oldcc.find_wineserver` bounded teardown. Also fixed two pre-existing flakes (`0cda392` atomic heartbeat write in `test_overnight.py`, `5708b27` zombie-reap race in `wc1.live.pid_alive`).
    5. **Deferred**: Persistent cross-process compiler artifact cache (Hypothesis F) — after the above fixes, `match-all` (`3.29 s`) + `compile-check` (`3.44 s`) total `6.73 s`, not worth cache invalidation complexity.
  - **Post-merge verification & benchmarks at `eebe586` (20-core Ultra 7 255HX, warm caches, quiet host load `1.04`)**:
    - **Full `make verify` (3 sequential runs)**: `192.56 s` -> **`52.56 s` median** (`50.10 / 52.56 / 55.34 s`, **3.66× speedup**, `-72.7%` wall); user CPU `2233.54 s` -> **`349.64 s` median** (**-84.3%**).
    - **Stages**: `toolchain-check` `0.04 -> 0.05 s`, `symbols` `2.32 -> 0.51 s`, `roundtrip` `5.71 -> 1.40 s`, `match-all` `6.86 -> 3.29 s`, `compile-check` `3.48 -> 3.44 s`, `build` `6.77 -> 3.23 s`, `pytest -n auto` `166.81 -> 40.11 s` median (`37.82–43.21 s`).
    - **Targeted tests**: PLAYFLIC T3 `91.88 s` -> 26 tests (`0.06–0.07 s` each standalone), `FogUpdateTile` `53.13 -> 0.23 s`, `SndInit` `29.36 -> 0.95 s`, `ScoreInit` `19.33 -> 0.08 s`. Every test in the 2,238-test suite now finishes under `17 s` in parallel (`16.62 s` max).
    - **Correctness**: **`2238 passed, 11 skipped, 5 xfailed`** (+519 regression tests), Build A **`IDENTICAL`** (`510 functions from 505 C files`), `make progress` unchanged (**T3 510, T4 375, Named 900, DONE 880/1010**). Full benchmark logs preserved under `build/verify-performance/`.


## 2026-11-27 - Post-campaign cleanup: M2 metadata, E7 provenance, calibration reproducibility

- **Manager:** Claude Code (Opus 5.5); Developers/Reviewers `opencode-go/deepseek-v4.1-flash`
  via `opencode2` (fresh sessions, the overnight campaign's hardened runner).  Telemetry:
  `docs/telemetry/campaigns/2026-11-27-post-campaign-cleanup/report.md`; raw logs in
  `/mnt/data/wc1-artifacts/orch-20261127-cleanup/`.
- **`feature/m2-mechanical-cleanup` (`dae45bd..`, not merged):**
  - `28839d3` / `0f7a89f` / `81eb7ec` `wc1.t3_audit`: reproduced on `dae45bd` (code identical to
    E7 `5667e2f7`) and fixed: `_default_system_headers`/`_tool_sig` ignored an explicit
    checkout (a copy without `original/` was "fresh"); `build_improved_audit_snapshot` compared
    the report's tool_sig with itself; `by_link=None`, symbol-less records, `{}`/incomplete OMF
    summaries and malformed fields were fresh or raised; non-portable digests were not refused;
    a failed `git status` was recorded as a clean tree; malformed reports/scores raised; host paths
    embedded in flags escaped the guard.  New `check_improved_record` (fresh / stale / partial /
    malformed, `unresolved_symbols`), `check_improved_snapshot` (header checked against live
    identity), `--check-improved`.  `wave4_fp.tool_signature` gained an optional `compiler_root`
    (default unchanged).  The one intended test change: `by_link=None` is now partial, not fresh.
  - `d26fb5d` `wc1.m2_inventory` GROUP_META corrected (DG-01 empty, IntroOpSyncSound under DG-03,
    DG-05 = fn_150f0/NetLinkHandshake/4 data symbols, BULLET.C eligibility); classification unchanged;
    `tests/test_m2_inventory.py` reconciles with the real overnight queue (14 / 76 / 8).
  - `6f33d68` OW2 no longer called the original compiler (`game_random.c`, `mod_19470.toml`,
    `REFERENCES.md`); `9f5ff6e` address-keyed codegen_promo staging guard.
  - `4ff89a3`/`f2d9816` E7 snapshot revalidation (historical file unchanged): 139 fresh (9 not
    dependency-clean, verified-unresolved symbols) / 63 stale - 62 via headers changed by the M2
    renames (`mod_295d0.h` 20, `mod_16390.h` 17, `mod_2efd0.h` 8, ...) or own edits, 19 with
    renamed symbols (`fn_19478_`, `fn_13e94_`, `fn_2b308_`, `fn_26360_`, `fn_2b390_`), 1 renamed
    ref (`fn_26360_reference.c`).  Regeneration needs a full `wc1.t3_audit` run (report.json gone).
  - `61470fa`/`78e3cf6` (Codex `gpt-6.2-sol` high, user-approved after the OpenCode Go quota ran out):
    `rev-pc-02` REQUEST_CHANGES found that rebuilding a snapshot stamped symbol addresses from the
    build-time map instead of the map the audit scored with (a move/rename in between passed as
    fresh) and that symbol coverage was unprovable (a deleted `symbols` key or partial map passed);
    plus NaN scores and path-like symbol keys.  `dev-pc-05` (Codex) added the audit-time
    `omf_symbol_addrs` stamp, embedded OMF summaries with exact name coverage, integer-only scores,
    symbol-name validation and the `absent_symbols` terminology.  Legacy E7 records are now at best
    `partial`: revalidation 0 fresh / 139 partial / 63 stale (all need regeneration).
  - `736878c`/`7a7b83a` (`rev-pc-03` -> `dev-pc-06`, Codex high): a replaced address stamp passed as
    audit evidence; rows with incomplete provenance were silently dropped; a missing `best.unresolved`
    looked dependency-clean; wrong `addr` / non-improving records passed; a metadata-less attempt kept
    the unit summary complete.  Fixed with an audit-time OMF+stamp digest, `record_sha256`, explicit
    fixup evidence, strict record semantics and incomplete-on-missing-metadata.
  - `64480e1`/`74c91b4` (`rev-pc-04` -> `dev-pc-07`, Codex high; the last round was bounded to
    self-consistency checks because the campaign excludes a general integrity redesign): edited/mixed
    report evidence and impossible fixups minted fresh records; snapshot row deletion/duplication/
    substitution passed.  Fixed with `row_evidence_sha256` (row identity + declared + selected attempt
    + OMF summary + stamp, eligibility derived from `attempts`), matcher-shaped fixup checks (verified
    on 685 real unresolved fixups), duplicate/summary/header checks and a header `records_sha256`.
    Threat model documented: stale, malformed, partially edited or mixed evidence is detected; a
    deliberate rewrite that recomputes every digest is not (remedy: a fresh audit).  Legacy E7
    snapshot: 0 fresh / 139 partial / 63 stale, `record_set_integrity` unchecked.
  - `c56eb38`, `c165b35`, `ee83f6f`, `aedb47c` (session owner, after narrow Codex medium checks
    `rev-pc-05`..`rev-pc-08`, each confirming the previous fix and finding one more unbound field of a
    saved report: toolchain/tier/declared score/first_diff -> per-row `row_sha256` bound to the header
    and checked before eligibility; an edited checkpoint -> final-only `meta.results_sha256`; scope and
    stats -> whole meta; `schema`/`near_misses` -> the final seal covers the whole report document;
    plus a whole-document `snapshot_sha256`).  Independent confirmation of `aedb47c` is pending: the
    Codex 5h window reached 97% (5h 19% -> 97%, 7d 22% -> 34% over rounds 2-8).
  - Reviews: `rev-pc-01` REQUEST_CHANGES (all 9 reported defects confirmed fixed; HIGH "None
    addresses counted fresh" adjudicated by-design - the 9 such records are exactly the 9
    non-dependency-clean ones and the live check proves the symbols are still absent - made
    explicit; 2 LOWs fixed in `81eb7ec`).  The fix session `dev-pc-04` hit the OpenCode Go
    monthly limit, so the session owner wrote `81eb7ec`; it was then reviewed by Codex in rounds 2 and 3 (below).
  - Progress unchanged: T3 539, DONE 912; `make verify` green on every commit (2495 passed at `aedb47c`).
- **`research/model-calibration-engineering` (`cea804e..d55d493`, not merged):** `/tmp/wc1-orch-20261127`
  preserved byte-for-byte in `/mnt/data/wc1-artifacts/orch-20261127/` (+ `-extra/`: relocated
  R3 review copy, oracle pre-check, 17 Codex rollouts) with SHA256SUMS; sanitized in-tree copies
  (scripts, hidden oracles, 18 patches, 20 reviewer reports, 39 prompts/final messages/stderr,
  ledgers); R3 adjudicated (not a clean control: defects (a)-(d) real and MEDIUM/LOW; the INFO
  "truncated patch.diff" claim is a false positive - the diff is the complete 450-line commit diff);
  single-trial qualifications; `REPRODUCIBILITY.md`, `verify_artifacts.py`, D1 replay 6/6.
  `rev-rc-01` APPROVE (LOW wording findings fixed), `rev-rc-02` APPROVE.
- Notes: the preserved runner's `verify` subcommand never dispatched (`--cmd` overwrote the
  subparser dest); long serialized-verify TMPDIRs (~130-char pytest paths) break a 10.0a compile
  under Wine in `tests/test_t4spec.py` - keep labels short.
