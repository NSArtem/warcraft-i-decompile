# Experiment E5 Contract & Developer Assignment — Data-Anchor Decoupling (`Fix B3`)

## 1. Mission & Research Question

You are the Developer for **Experiment E5** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E5`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e5`
- **Branch:** `research/build-codegen/e5`
- **Baseline commit:** `1abb053c112332ec901a8961dc918bdcc25d73c4` (includes approved E0 `experiments/build_codegen/e0/matcher_proto.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
1. Does OMF32 `FIXUPP32(seg -> EXTDEF wc1_anchor_<addr>)` rewriting — with full `THREAD` subrecord expansion, correct `FLAT`/`DGROUP` frame handling, and E0-verified data bytes+pointer relocations — allow linking multi-segment (`_DATA` + `CONST` + `_BSS`) and out-of-order data-anchor C objects into **Build A `IDENTICAL`** (`0` byte diffs, `0` diffs across all `8770` LE fixups) WITHOUT modifying canonical C source or leaking `wc1_anchor_*` into `src/`/`analysis/`/`tests/`?
2. Separately, what happens to `SaveErrorDialog` (`0x1aca8`) under native `-ot` vs `-os`, and are both whole-segment and per-symbol anchor mappings feasible under `wlink`?

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.2, §6.1–6.3, §8.1–8.3, §14 E5)
- `tools/wc1/omf.py`, `tools/wc1/omfpatch.py`, `tools/wc1/build.py`, `tools/wc1/emit.py`, `asm/wc1.inc`
- `experiments/build_codegen/e0/matcher_proto.py`
- `src/gamedlg/save_error_dialog_reference.c` (`0x1aca8`), `src/gamedlg/defeat_dialog.c` (`0x1ab28`), `src/gamedlg/victory_dialog.c` (`0x1aa7c`), `src/gamedlg/game_save_dialog.c` (`0x1abc0`)

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e5/` (OMF32 Fix-B3 rewriter prototype, isolated Build A link harness, fixtures, runner, pytest suite)
- `docs/research/build-codegen/E5-data-anchors.md`
- `docs/research/build-codegen/results/e5/` (machine-readable JSON results)

**STRICTLY PROHIBITED:**
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- `wc1_anchor_*` symbols may exist ONLY inside generated temporary `build/e5/` `.obj`/`.asm` artifacts — NEVER in canonical `src/`, `analysis/`, or `tests/`.
- Do NOT merge mutable objects by content or compensate for wrong struct layouts.
- Do NOT run `make verify` directly.

## 4. Technical Requirements

### 4.1 Experimental OMF32 Data-Anchor Rewriter (`experiments/build_codegen/e5/omf_b3.py`)
Implement a clean, fail-closed OMF32 rewriter supporting:
1. **Full `FIXUPP32` + `THREAD` parsing & re-encoding:**
   - Maintain OMF32 `THREAD` state (Frame threads F0–F3 and Target threads T0–T3) across records.
   - When rewriting a `FIXUPP32` record attached to `_TEXT` (or any retained code/data segment), expand `THREAD`-referenced frame/target fields explicitly when needed so rewritten fixups are 100% self-contained and valid OMF32!
   - Rewrite fixups targeting anchored data segment `si` (`target_kind == "seg", target == si`) to `target_kind == "ext"` referencing a newly appended `EXTDEF` `wc1_anchor_<orig_addr:05x>`, preserving exact `loc`, `self_rel`, inline addend, explicit `disp`, AND testing/handling `FLAT` vs `DGROUP` `FRAME` encodings (`fmethod=5` Target vs `fmethod=1` GRPDEF `DGROUP` vs `fmethod=2` EXTDEF) cleanly so `wlink` emits identical LE fixups!
   - Support BOTH:
     - **Whole-segment anchoring:** entire data segment `si` anchored at `orig_base` -> single `EXTDEF wc1_anchor_<orig_base>` (preserving addends).
     - **Per-symbol anchoring (experimental feasibility test):** distinct verified `CONST` literal / independent symbol anchors within a segment -> separate `EXTDEF wc1_anchor_<sym_addr>` with adjusted inline addend = `0` (or offset within symbol), STRICTLY gated by RFC §6.3 rules (proven boundary, byte+pointer match, aliasing preserved)!
   - Empty anchored data segments (zero length in `SEGDEF32`, drop their `LEDATA`/`LIDATA` and attached `FIXUPP32`, preserving any `THREAD` definitions from dropped `FIXUPP` if subsequent records rely on them — or fail closed cleanly if unsupported!).
   - Verify E0's full data byte + pointer relocation check BEFORE permitting any anchor rewrite!
   - Fail closed on unsupported `loc`, `LIDATA` edge cases if unverified, mutable content-merging, or unverified layout shifts.

### 4.2 Isolated Build A Link Harness & Required 4 Scenarios (`experiments/build_codegen/e5/run_e5.py` & `test_e5.py`)
Build an isolated experimental Build A linker (outputting ONLY to `build/e5/`, using the repo's real `war.exe`, `asm/wc1.inc`, `nasm`, `wlink`, `wc1.compare` — single unified asm data piece with `GLABEL wc1_anchor_<addr>` emitted at each needed anchor address, zero code-order data splitting!):
1. **Scenario 1 — `SaveErrorDialog` (`0x1aca8`) + `DefeatDialog` (`0x1ab28`) non-monotonic anchor conflict:**
   - Reproduce the exact legacy failure (`C objects' data anchors are not in code order`: `DefeatDialog` `0x56c0c` before `SaveErrorDialog` `0x51ea6`).
   - Test `SaveErrorDialog` under BOTH `-s -os -ol -4r -zp2` (exact match in standalone) AND investigate native `-s -ot -ol -4r -zp2` (documenting why standalone `-ot` gives `0x24` string stride vs `0x22` in `_DATA`, and testing whether placing strings with `-ot` in a multi-fn `_DATA`/string layout reproduces `0x22`!).
   - Link BOTH `DefeatDialog` (`0x1ab28`) and `SaveErrorDialog` (`0x1aca8`) together with all other T3s into `build/e5/war_s1.exe` using Fix B3 (`wc1_anchor_*`) and prove **`wc1.compare == IDENTICAL`** (exact image + all 8770 LE fixups)!
2. **Scenario 2 — Multi-segment object (`_DATA` + `CONST` + `_BSS`):**
   - Test BOTH (a) a real multi-segment `GAMEDLG` experimental consolidation (e.g. combining functions referencing `CONST` strings + `_DATA` strings/vars, or real `DefeatDialog` + `SaveErrorDialog` + `VictoryDialog` / `GameSaveDialog` in one object!) AND (b) a synthetic Watcom 10.0a object containing ALL THREE segments (`_DATA` + `CONST` + `_BSS`) simultaneously, proving Fix B3 links multi-segment objects cleanly with identical `wlink` output!
3. **Scenario 3 — `THREAD`-containing `FIXUPP32` records:**
   - Generate a real Watcom 10.0a (or controlled OMF32) object containing actual `THREAD` subrecords (Watcom 10.0a emits `THREAD` subrecords in larger objects or multi-ref objects — check real compiled objects first and also include a targeted `THREAD` fixture!) and prove `omf_b3.py` expands and rewrites `THREAD` fixups cleanly into valid `wlink`-linkable OMF32 (with Build A `IDENTICAL` where real)!
4. **Scenario 4 — `FLAT` vs `DGROUP` frame encoding verification:**
   - Explicitly test and document how `wlink` resolves `EXTDEF` anchors under `fmethod=5` (target), `fmethod=2` (EXTDEF), `fmethod=1` (`DGROUP`), and verify final LE fixup object/offset records (`wc1.compare` — all 8770 fixups!) for every tested frame mode!
5. **Negative Controls (Fail Closed):**
   - N1: Anchored data segment with 1 altered byte -> rejected before rewrite.
   - N2: Anchored data segment with corrupted pointer relocation target -> rejected via E0 check before rewrite.
   - N3: Attempted mutable `_DATA` content-based merging / unverified interior struct offset remapping -> rejected fail-closed.
   - N4: Leaked `wc1_anchor_*` check -> assert zero `wc1_anchor_` occurrences anywhere in `src/`, `analysis/`, `tests/`.

## 5. Deliverables, Acceptance Criteria & Atomic Commits
- Deliverables: `experiments/build_codegen/e5/{omf_b3.py,build_e5.py,fixtures/,run_e5.py,test_e5.py}`, `docs/research/build-codegen/results/e5/results.json`, `docs/research/build-codegen/E5-data-anchors.md`.
- Report explicitly separates whole-segment vs per-symbol anchor feasibility, exact `SaveErrorDialog` `-ot` vs `-os` findings, and `FLAT`/`DGROUP` frame mechanics.
- `pytest -q experiments/build_codegen/e5/test_e5.py` passes 100%; `python3 -m experiments.build_codegen.e5.run_e5` reproduces `results.json`; zero production diffs.
- 2–3 clean atomic commits:
  1. `exp(e5): OMF32 Fix-B3 data-anchor rewriter with THREAD and FLAT/DGROUP handling`
  2. `exp(e5): isolated Build A link scenarios, negative controls, and pytest suite`
  3. `docs(e5): E5 data-anchor decoupling results and report`
