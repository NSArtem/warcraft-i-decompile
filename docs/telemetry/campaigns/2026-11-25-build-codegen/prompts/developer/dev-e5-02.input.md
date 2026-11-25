# Developer Repair Assignment — Experiment E5 (`dev-e5-02`)

You are the replacement **Developer** (`dev-e5-02`) for **Experiment E5** (Data-Anchor Decoupling Fix B3), addressing the path-portability / Watcom 10.0a compiler crash uncovered during independent review (`rev-e5-01`).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e5`
- **Branch:** `research/build-codegen/e5` (HEAD: `de82374233463453b9a8ae9ba338d1e3642b8a67`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wlink`, `nasm`, `git` directly.

## Finding to Resolve (Must Fix)
Independent review (`rev-e5-01`) reproduced a deterministic **Watcom 10.0a `wcc386.exe` Access Violation** when compiling two E5 fixtures (`experiments/build_codegen/e5/fixtures/native_context.c` and `experiments/build_codegen/e5/fixtures/gamedlg_data.c`) from a longer checkout path (e.g., `/mnt/data/projects/warcraft-1-decompile-wt/rev-e5-01`, and even intermittently at `/mnt/data/projects/warcraft-1-decompile-wt/e5`):
- Root cause: Watcom 10.0a `wcc386.exe` crashes with an access violation when resolved source/include paths exceed its ~128–130 character internal buffer (especially combined with `#include "../../../../src/gamedlg/defeat_dialog.c"` and long `str(ROOT/src)` / `-i=...` paths passed via `match.compile_c`).
- Note: All scientific substance, 9/9 Warcraft Build A `IDENTICAL` links, negative controls, and byte-identical `results.json` were verified sound once those two fixture compiles used short paths.

## Required Fix
1. Inspect `experiments/build_codegen/e5/build_e5.py`, `experiments/build_codegen/e5/run_e5.py`, `experiments/build_codegen/e5/fixtures/{native_context.c,gamedlg_data.c}`, and (for proven campaign conventions) `experiments/build_codegen/e2/` or `experiments/build_codegen/e7/common.py` (which solved Watcom 10.0a's path-length crash cleanly via short temporary symlinks / relative paths <= 112 chars).
2. Fix `experiments/build_codegen/e5/build_e5.py:compile_source` (and any direct `match.compile_c` calls in `build_e5.py` / `controls.py` / `test_e5.py` + the `#include "../../../../src/gamedlg/defeat_dialog.c"` spelling in `native_context.c` and `gamedlg_data.c` if helpful) so **every** Watcom 10.0a compile in E5 uses short paths (e.g. compiling via a short symlink in `/tmp` to `ROOT` with short `-i` include paths / short source and output paths), guaranteeing zero `wcc386.exe` access violations even when `WC1_ROOT` is a 160+ character directory path!
   - Do NOT alter the compiled object semantics or production code (`tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, `AGENTS.md`).
   - Do NOT embed absolute worktree paths in `docs/research/build-codegen/results/e5/results.json`.
3. Add a regression test in `experiments/build_codegen/e5/test_e5.py` verifying that `compile_source` compiles both `native_context.c` and `gamedlg_data.c` cleanly even when `ROOT` is accessed through a long (>=140 char) symlinked checkout path!
4. Run `python3 -m experiments.build_codegen.e5.run_e5` and `pytest -q experiments/build_codegen/e5/test_e5.py` and confirm **100% pass** and deterministic `docs/research/build-codegen/results/e5/results.json`.
5. Update `docs/research/build-codegen/E5-data-anchors.md` only if any count or note needs updating (e.g. test count or toolchain path-length workaround note).
6. Verify `git diff 1abb053c112332ec901a8961dc918bdcc25d73c4 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty and `git status` is clean (only permitted E5 paths).
7. Create 1 clean atomic commit on `research/build-codegen/e5`:
   - `exp(e5): resolve rev-e5-01 Watcom 10.0a long-path fixture compile crash`

## Output Format
Report commit hash, exact commands run, pytest result, whether `results.json` SHA-256 stayed identical (or exact diff if changed), and long-path regression test verification.
