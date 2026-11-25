I'll start by exploring the E7 experiment directory to understand the current state.
Now let me implement the shared short-path helper in `common.py`:
Now add the regression tests:
Resolved both Round 1 findings and committed on `research/build-codegen/e7`.

**Commit:** `4194a2f` — `exp(e7): resolve rev-e7-01 path portability and CSV LF findings`

## What changed

**1. Checkout path portability (Must Fix)**
- Reproduced the crash and measured the real limits: Watcom 10.0a `wcc386` access-violates at a 154-char root; empirically an `-i=` argument fails at 129 bytes (124-char path + `Z:` + `-i=`) and the source operand at 130 chars (132 with `Z:`).
- Added `common.compiler_path` / `common.compiler_root`: every compiler-facing path is rewritten through a short mirror `<tmp>/wc1e7-<hash>/repo` (a symlink to the checkout), bounded by `COMPILER_PATH_LIMIT = 112`; over-long paths raise instead of crashing Wine. Non-checkout paths (e.g. `--scratch` elsewhere) get a short sibling link.
- `common.short_oldcc` redirects 10.0a's two hard-coded `-i=` paths (`src/include`, installation `h/`); `common.compile_short` is now the single compile entry point for calibration cells, native OW2 controls, placement checks, Build A links and the capability probe (which also runs with a short `cwd`/exe path and strips both path forms from diagnostics).
- Evidence is unchanged: paths appear only in `DEBTYP` debug metadata of `-d1+` objects; runtime segments/hashes are byte-identical (verified against committed `runtime_sha256` for c06/c19/c05).

**2. CSV LF (Optional)** — `csv.DictWriter(..., lineterminator="\n")`; `t4_new_matches.csv` regenerated from `calibration_matrix.json` (content identical modulo EOL; 65 CRLF → 0).

**Docs** — new `## Compiler path portability` section with measured limits, the mirror mechanism, the no-evidence-change argument, and both regression tests.

## Verification
- `pytest -q experiments/build_codegen/e7/test_e7.py` → **20 passed** (18 pre-existing + 2 new: short-path bound test, and a full capability probe + real `-d1+` cell run under a ≥154-char symlinked checkout whose output must equal the committed capability DB and runtime hash; both fail on the old code).
- `git diff --check` clean; `git diff 7c23d23 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` **empty**.
- Full 21,618-compile sweep not re-run, as directed. Working tree clean except the pre-existing untracked `original/`.