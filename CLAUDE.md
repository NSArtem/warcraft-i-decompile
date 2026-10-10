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

Reviewed 2026-10-10 and committed (5f725a6): `make verify` green (the build's
`DIFFERENT` line is expected with C replacements); `tools/wc1/clib_sig.py`
repaired (short or shared-address library units are reported as weak
candidates unless corroborated, not as matches); `modules_libsig.py` deleted
(byte-only, no relocation cross-check, false positive at 0x18af0);
`resources_war.py` decodes all 583 DATA.WAR entries (difftest pending).

Second session 2026-10-10 (uncommitted, `make verify` green, 61 tests):
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
- No T3 match anywhere except InitPaths: OW2 wcc386 does not reproduce the
  original codegen (ebp frames, `sub esp,0`, short jumps) for resources,
  audio and graphics functions. `src/{resources,audio,graphics}/*.c` are
  non-matching reference C, outside `make match-all`.

## Next steps (in order)

1. Codegen study (one `wc1-analyst`): characterise why OW2 output differs
   (flags sweep incl. -3r/-4r/-5r, -of, -d1/-d2, -zp; per-module patterns:
   which modules match like InitPaths and which don't); decide whether a
   period Watcom 10.x compiler is needed. Blocks bulk C work.
2. Module-ordered build (per-module asm files from `analysis/modules.toml`)
   so whole C modules can replace asm while keeping the image identical.
3. Game logic areas (units, orders, pathfinding, AI, network, UI,
   save/score), one analyst per area, using modules.toml ranges.
4. Small follow-ups: resources.md/resources.h still call the game file
   wrappers (0x31964/0x31a80/...) fopen/fseek — clib showed they are game
   wrappers (real clib fseek 0x3bb86 etc.); name the GDS heap (0x32558
   alloc / 0x32780 free, CHECKSIG guards, likely MMGR.C); optional
   `symbols.py` check of `module =` fields
   against modules.toml.
