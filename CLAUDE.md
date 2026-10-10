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
- `wc1-analyst` (Opus): reverse-engineering judgment (subsystems, formats,
  module boundaries, semantic naming, matching C).
- Pass `subagent_type` explicitly. One owner per file/area (see
  ANALYST_GUIDE concurrency rules). Split mixed tasks so the mechanical part
  goes to Haiku.

## State at hand-off (2026-10-10)

Done and verified: Nix env; extraction with hash checks; LE parser; code
discovery (1340 functions, 97.3%); T1 round-trip byte-identical; T2 wlink
relink load-equivalent and boots in DOSBox-X; `wc1.match` (T3);
`wc1.emu` (Unicorn harness); `InitPaths` (0x1d7cc) matched in `src/init.c`
and taken from C in the build (hybrid exe boots).

Interrupted: six background agents were stopped before finishing. They left
partial, unreviewed files: `tools/wc1/clib_sig.py`, `tools/wc1/modules_libsig.py`,
`tools/wc1/resources_war.py`, plus scratch in `build/{clib,modules,audio,graphics,resources}`.
The editor also reported on-disk changes to shared tools
(`tools/wc1/analysis.py`, `emit.py`, `match.py`) while agents ran; the tree is
not in git yet, so **first run `make verify`** and review those files before
building on them.

## Next steps (in order)

1. `make verify`; review/repair the partial agent files above.
2. Ask the user whether to make the initial git commit (nothing committed yet).
3. Relaunch work, each area with its own files:
   - `wc1-mechanical`: runtime library signature sweep vs OW2 `clib3r.lib`/math
     libs → verified entries in `analysis/symbols/clib.toml` (strcpy already
     proven); Ghidra headless export → `build/ghidra/decomp/` +
     `python3 -m wc1.ghidra_decomp`.
   - `wc1-analyst`: module boundaries (`analysis/modules.toml`, using the
     Insider's Guide module list in `docs/REFERENCES.md`); `.WAR` archive +
     LZSS decompression with a difftest; graphics/input; AIL audio + game
     sound layer; then semantic naming of runtime functions that don't
     byte-match OW2.
4. With module boundaries known: module-ordered build (per-module asm files)
   so whole C modules can replace asm while keeping the image identical.
5. Game logic areas (units, orders, pathfinding, AI, network, UI, save/score),
   one analyst per area.
