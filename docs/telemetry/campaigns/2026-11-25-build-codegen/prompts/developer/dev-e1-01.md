# Experiment E1 Contract & Developer Assignment — Shared Epilogue Reproduction

## 1. Mission & Research Question

You are the Developer for **Experiment E1** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E1`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e1`
- **Branch:** `research/build-codegen/e1`
- **Baseline commit:** `7c23d2371e95d8de93f0ba1652c8d44b858da273` (includes approved E0 `experiments/build_codegen/e0/matcher_proto.py`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured). Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
Does Watcom C/C++ 10.0a naturally reproduce original cross-function shared epilogues (including jumps spanning across an intermediate function!) when neighboring functions are compiled together in one translation unit, WITHOUT manual ASM insertions?

**Hypothesis:**
In standalone compilation, shared-epilogue callers cannot emit cross-function `rel8` branches into a sibling's epilogue; under joint compilation in original function order, Watcom 10.0a naturally emits cross-function epilogue jumps, confirming the compilation-context hypothesis — and when all constituent function bodies match, the joint region passes E0 `RegionMatch` and builds Build A `IDENTICAL`.

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.4, §2.2.5, §14 E1)
- `experiments/build_codegen/e0/matcher_proto.py` (use E0's strengthened matcher for ALL `FunctionMatch` / `RegionMatch` verdicts!)
- Group A (`mod_16390`): `src/mod_16390/dialog_hit_test_reference.c` (`DialogItemHitTest` `0x16cc8`, `DialogHighlightOn` `0x16d34`, `DialogHighlightOff` `0x16d48`) and `src/include/mod_16390.h`
- Group B (`PLAYFLIC.C`): `src/playflic/intro_op_play_sound.c` (`0x2315c`), `src/playflic/intro_op_sync_sound.c` (`0x23170`), `src/playflic/player_reference.c` (`IntroOpWaitSound` `0x231cc`), and `src/include/playflic.h`

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e1/` (experimental scripts, temporary consolidated C fixtures, tests)
- `docs/research/build-codegen/E1-shared-epilogues.md`
- `docs/research/build-codegen/results/e1/` (machine-readable JSON results + preserved disassembly/OMF evidence)

**STRICTLY PROHIBITED:**
- Do NOT modify any production file under `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT use manual `__asm` / `#pragma aux` assembly insertions to force epilogue jumps.
- Do NOT run `make verify` directly (run targeted `pytest experiments/build_codegen/e1/` and experimental scripts only).

## 4. Technical Requirements & Binding Interpretations (Mandatory Corrections R1 & R6)

### 4.1 Mandatory R1 Separation of Outcomes
For EVERY candidate function and EVERY compiled variant (standalone vs joint, original order vs reversed/subset order, flag variants), record SEPARATELY:
1. `shared_epilogue_reproduced` (bool): Did Watcom 10.0a emit a cross-function branch targeting a sibling function's epilogue?
2. `exact_branch_encoding` (dict): Compiled branch opcode, bytes, target offset, target function, vs original bytes/target offset (explicitly preserving the R6 **`74 f5` vs `74 f3`** observation on `DialogHighlightOn`!).
3. `function_match_verdict` (E0 `matcher_proto` `FunctionMatch` verdict + findings).
4. `region_match_verdict` (E0 `matcher_proto` `RegionMatch` verdict + findings).
5. `build_a_integrated_identical` (bool / status): Whether an isolated Build A link under `build/e1/` (using the compiled joint object in place without editing production files) produces `wc1.compare == IDENTICAL`!

### 4.2 Required Experimental Matrix
1. **Group A (`mod_16390`: `DialogItemHitTest` `0x16cc8`, `DialogHighlightOn` `0x16d34`, `DialogHighlightOff` `0x16d48`):**
   - Compare:
     - (A1) Standalone compilation of each of the 3 functions individually (`-s -ot -ol -4r -zp2`, `-s -os -ol -4r -zp2`, `-s -ot -oa -ol -4r -zp2`, `-s -ot -ol -5r -zp2`).
     - (A2) Joint compilation of the current `dialog_hit_test_reference.c` bodies in original order (`0x16cc8 -> 0x16d34 -> 0x16d48`) across those flag sets — explicitly capturing and preserving the exact disassembly showing `74 f5` vs original `74 f3` and explaining the exact byte-delta cause!
     - (A3) Check whether a clean, idiomatic pure-C spelling of `DialogItemHitTest` (no ASM!) that matches `0x16cc8`'s exact length/code makes `DialogHighlightOn` emit exact `74 f3` and whether the entire 3-function region (`0x16cc8..0x16d5e`) achieves E0 `RegionMatch` + isolated Build A `IDENTICAL`! (If `DialogItemHitTest` still mismatches on an unrelated instruction, document that honestly under R1 — optimization reproduction is still a confirmed positive finding!)
     - (A4) Negative order control: compile in reversed order (`DialogHighlightOff -> DialogHighlightOn -> DialogItemHitTest`) to test whether original order matters for Watcom 10.0a epilogue sharing.
2. **Group B (`PLAYFLIC.C`: `IntroOpPlaySound` `0x2315c`, `IntroOpSyncSound` `0x23170`, `IntroOpWaitSound` `0x231cc`):**
   - Compare:
     - (B1) Standalone compilation of each of the 3 functions individually.
     - (B2) Joint compilation of all 3 functions in original order (`IntroOpPlaySound -> IntroOpSyncSound -> IntroOpWaitSound`, spanning across the intermediate function `IntroOpSyncSound`!) under Watcom 10.0a (`-s -ot -ol -4r -zp2`, `-s -ot -oa -ol -4r -zp2`, `-s -os -ol -4r -zp2`, `-s -ot -ol -5r -zp2`). Check whether Watcom 10.0a reproduces `74 93` (`0x231d7 -> 0x2316c`) and `75 89` (`0x231e1 -> 0x2316c`) across `IntroOpSyncSound`, AND check `IntroOpWaitSound`'s exact C body vs `0x231cc` disassembly!
     - (B3) Pair-only control (`IntroOpPlaySound + IntroOpWaitSound` without `IntroOpSyncSound`) and reversed-order control.
     - (B4) Isolated Build A link test: if the 3-function joint region achieves E0 `RegionMatch`, link it into an isolated `build/e1/war_group_b.exe` and verify `wc1.compare == IDENTICAL` (0 byte diffs, 0 fixup diffs across all 8770 LE fixups)!
3. **Preserved Reproducible Evidence (R6):**
   - Save complete disassembly listings (original vs standalone vs joint), exact branch byte sequences, OMF object SHA-256 hashes, public offsets, inter-function padding bytes, E0 verdicts, and Build A comparison results in `docs/research/build-codegen/results/e1/results.json` and `docs/research/build-codegen/results/e1/disasm_evidence.txt`.

## 5. Deliverables, Acceptance Criteria & Atomic Commits

Deliverables:
- `experiments/build_codegen/e1/` (fixtures, `run_e1.py`, `test_e1.py`)
- `docs/research/build-codegen/results/e1/results.json` & `disasm_evidence.txt`
- `docs/research/build-codegen/E1-shared-epilogues.md`

Acceptance criteria:
1. `pytest -q experiments/build_codegen/e1/test_e1.py` passes 100%.
2. `python3 -m experiments.build_codegen.e1.run_e1` reproduces `results.json` deterministically.
3. Zero production modifications (`git diff <BASE> -- tools/ src/ analysis/ tests/ Makefile` is empty).
4. 2–3 clean atomic commits on `research/build-codegen/e1`:
   - Commit 1: `exp(e1): shared epilogue reproduction harness, fixtures, and pytest suite`
   - Commit 2: `exp(e1): preserved empirical results, disassembly evidence, and E1 report`
5. End with a concise summary: commit SHAs, Group A & Group B R1 breakdown (`shared_epilogue_reproduced`, `exact_branch_encoding`, `FunctionMatch`, `RegionMatch`, `Build A IDENTICAL`), scientific verdict, and reproduction commands.
