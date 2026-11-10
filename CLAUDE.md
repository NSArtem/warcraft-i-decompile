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

- `wc1-mechanical` (Haiku 5.5): well-specified mechanical work with
  explicit steps and acceptance criteria (signature sweeps, export tooling,
  bulk checks, tests).
- `wc1-analyst` (Sonnet 5.5): reverse-engineering judgment (subsystems, formats,
  module boundaries, semantic naming, matching C).
- Pass `subagent_type` explicitly. One owner per file/area (see
  ANALYST_GUIDE concurrency rules). Split mixed tasks so the mechanical part
  goes to Haiku.

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

Fourth session (2026-11-10, working tree): game-logic area started.
- PATH/UNIT range 0x2c4e0..0x2efd0: 25 functions and 11 data symbols named
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

## Next steps (in order)

1. ~~Codegen study~~ and ~~library names~~ done (third session): GdsAlloc/
   GdsFree, text_colors/text_glyph_fn/text_esc_colors, cursor_save_bm named;
   13 functions T3 + built from C. Remaining sweep-only samples are game code
   (bullet.c, mod_110a0/12c70/13e60/13f60/19470.c): promote them during step 3.
2. ~~Module-ordered build~~ done differently (third session,
   docs/subsystems/build.md): C objects are linked in place between asm
   pieces (BYTE-aligned via tools/wc1/omfpatch.py, data as zero-length
   anchors on the asm's bytes), so the hybrid build is IDENTICAL to the
   original and `make build` now fails otherwise. Per-module asm files are
   not needed for code. Open: real data ownership by C needs the data
   layout (analyst running: analysis/data_layout.toml).
3. Game logic areas (units, orders, pathfinding, AI, network, UI,
   save/score), one analyst per area, using modules.toml ranges.
4. Small follow-ups: ~~file wrappers~~ (FileOpen/FileSeek/FileRead/...
   0x31940..0x31bca, CritErrHandler/CritErrInstall, in resources.toml) and
   ~~GDS heap~~ and ~~`module =` check~~ (symbols.check_modules: must
   equal the analysis/modules.toml range name) done.
