# Experiment E0 Contract & Developer Assignment — Matcher Soundness Regression Suite + Full T3 Re-Audit

## 1. Mission & Research Question

You are the Developer for **Experiment E0** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E0`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e0`
- **Branch:** `research/build-codegen/e0`
- **Baseline commit:** `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`
- **Environment:** You are already running inside the Nix dev shell with `WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured for this isolated worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
Does an experimental strengthened matcher implementing the RFC's **Normalized Addressing Obligations** model reliably close all three confirmed verification gaps in `tools/wc1/match.py` — (1) leading `_TEXT` bytes and pre-function jump tables, (2) reverse original→compiled relocation obligations, and (3) pointer relocations in module-local data segments — passing 100% of positive controls, failing closed on 100% of negative controls, and revealing the exact audit status of all existing `519` T3 functions?

**Hypothesis:**
The strengthened matcher passes 100% of positive controls (including pre-function jump tables, `0xa0000` hardware constants, and intra-`CODE_OBJ` `rel32` calls without LE loader fixups), fails closed on 100% of negative controls, and cleanly audits all 519 existing T3 functions into mutually exclusive verdicts + unrestricted per-function findings.

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.1, §3 #5, §5.1–5.3, §14 E0, §15)
- `tools/wc1/match.py`, `tools/wc1/omf.py`, `tools/wc1/build.py`, `tools/wc1/symbols.py`, `tools/wc1/progress.py`
- `src/mod_13f60/choose_campaign_dialog.c` (real pre-function jump table at `0x157d8..0x157e8`, fn at `0x157e8`)
- `src/playflic/intro_op_clear_screen.c` or `src/gamedlg/help_screen.c` (real `0xa0000` hardware constant)

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e0/` (all experimental Python code, synthetic C/OMF fixtures, tests)
- `docs/research/build-codegen/E0-matcher-soundness.md`
- `docs/research/build-codegen/results/e0/` (machine-readable JSON/CSV results)

**STRICTLY PROHIBITED:**
- Do NOT modify any production file under `tools/wc1/`, `src/`, `analysis/`, `tests/`, `asm/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT modify any symbol tiers or TOML files.
- Do NOT run `make verify` directly (run targeted `pytest experiments/build_codegen/e0/` and `python3 -m ...` checks only; full `make verify` is managed globally by the Manager).
- Do NOT merge or switch branches; stay on `research/build-codegen/e0`.

## 4. Technical Requirements & Binding Interpretations

### 4.1 Strengthened Matcher Prototype (`experiments/build_codegen/e0/matcher_proto.py`)

Implement an isolated, importable module building on `wc1.analysis`, `wc1.omf`, `wc1.match`, `wc1.symbols`:

1. **Verdict & Findings Model (Mandatory Correction R3):**
   - Mutually exclusive verdict per function and per region: `"MATCH"`, `"MISMATCH"`, `"UNSUPPORTED"`, `"ERROR"`.
   - Unrestricted `findings: list[dict]` per function/region — NEVER cap or drop findings to 1 per function! A function with 3 independent defects MUST report all 3.
   - Each finding contains: `code`, `category` (`code_bytes`, `code_reloc_forward`, `code_reloc_reverse`, `data_bytes`, `data_reloc_forward`, `data_reloc_reverse`, `leading_bytes`, `extent_retry`, `unsupported_construct`, `error`), `offset` (or null), `orig_addr` (or null), `message`, `evidence`.
   - Any unsupported relocation `loc`, unsupported `target_kind`, or ambiguous construct MUST produce verdict `"UNSUPPORTED"` (fail closed; NEVER `"MATCH"`).

2. **Normalized Addressing Obligations Model (RFC §5.2):**
   Represent every addressing obligation explicitly with:
   `kind` (`abs_code`, `abs_data`, `rel32_code`, `rel8_code`), `src_offset`, `field_size`, `target`, `addend`, `evaluation_rule`, `requires_static_resolution`, `requires_le_fixup`.
   Do NOT require literal 1:1 equality between OMF `FIXUPP` and LE `p.fix_at`:
   - `abs_code` / `abs_data` (targeting `CODE_OBJ`/`DATA_OBJ`): requires BOTH OMF `FIXUPP` (compiled) AND LE `p.fix_at` (original).
   - `rel32_code` (cross-function `call`/`jmp rel32` in `_TEXT`): requires OMF `FIXUPP(self_rel=True)` for external targets (or exact intra-segment relative displacement when target is in the same `_TEXT` segment), and does NOT require an LE loader fixup!
   - Non-relocatable hardware constants (e.g., `0xa0000`): have NEITHER LE `p.fix_at` NOR OMF `FIXUPP` -> checked via ordinary exact byte comparison.

3. **Closing All 3 Confirmed Soundness Gaps:**
   - **Gap 1 — Leading `_TEXT` bytes (`[0, first_pub_off)`):**
     Compute `region_orig_start = first_pub_addr - first_pub_off` when `first_pub_off > 0` (verify all publics agree or report mismatch). Verify EVERY byte and EVERY forward & reverse addressing obligation in `[0, first_pub_off)` (e.g., pre-function switch jump tables like `ChooseCampaignDialog` `0x157d8..0x157e8`). Distinguish `FunctionMatch` (function body `[off, end)`) vs `RegionMatch` (whole closed region `[0, total_end)` including leading bytes, all publics/statics, all obligations, and all local data segments).
   - **Gap 2 — Reverse Original→Compiled Relocation Obligations:**
     For every original LE fixup `a in p.fix_at` inside `[orig_start, orig_end)` (including leading bytes AND inside function bodies), verify there is a compiled OMF `FIXUPP` at the corresponding offset covering `a` with matching `kind`, `size`, and resolved target (`target + addend == orig_target`). A hardcoded numeric address whose bytes match `war.exe` but lacks an OMF `FIXUPP` MUST fail closed with `MISMATCH` (`code_reloc_reverse`).
     Also check external `call`/`jmp rel32` instructions in the original whose target lies outside the compiled `_TEXT` region: compiled code MUST either carry an OMF `FIXUPP(self_rel=True)` resolving to that target (never a hardcoded `rel32` displacement without relocation!).
   - **Gap 3 — Module-Local Data Segment Pointer Relocations (`_DATA`, `CONST`, etc.):**
     When a data segment `s` is anchored at `sb` (derived consistently from code fixups):
     - Verify non-fixup bytes against original image `[sb, sb + len(s.data))`.
     - **Forward check:** For EVERY `fu in s.fixups`, verify `fu.loc` is supported (loc 9 / off32, else `UNSUPPORTED`), resolve its target (`ext` via DB, `seg` via `seg_base` — including `_TEXT` or another data segment!), compute `resolved = target_addr + addend`, and verify that original `p.fix_at` HAS a fixup at `sb + fu.offset` targeting `resolved`! (Note: handle `self_rel` in data as `UNSUPPORTED`.)
     - **Reverse check:** For EVERY original LE fixup `a in p.fix_at` with `sb <= a < sb + len(s.data)`, verify that `s.fixups` HAS a corresponding OMF `FIXUPP` at offset `a - sb`! Hardcoded pointer bytes in data without an OMF `FIXUPP` MUST fail closed with `MISMATCH` (`data_reloc_reverse`).
   - **Extent Retry Hardening (RFC §5.3):**
     Only permit trimming `[hi, end)` when:
     (a) `off < hi < end` where `hi = off + (orig_fn_end - base)`,
     (b) `text.data[hi:end]` is strictly `is_filler(...)`,
     (c) NO compiled `FIXUPP` overlaps `[hi, end)`,
     (d) NO original LE fixup `p.fix_at` falls inside `[base + (hi - off), base + (end - off))` that belongs to the function itself (i.e. `orig_fn_end` check must not hide code or fixups before `orig_fn_end`).

### 4.2 Positive & Negative Control Suite (`experiments/build_codegen/e0/controls.py` & `test_e0.py`)

Implement and verify ALL 10 RFC E0 controls PLUS boundary controls (compare against legacy `wc1.match.match_module` where informative to prove the legacy gap existed and is now closed!):
- **P1:** Correct pre-function jump table — real `src/mod_13f60/choose_campaign_dialog.c` (`0x157e8`, table at `0x157d8..0x157e8`). Must `MATCH` (`FunctionMatch` + `RegionMatch`).
- **N1:** Corrupted pre-function jump table entry — mutated/reordered case target in `ChooseCampaignDialog` (or synthetic OMF derived from it). Must `MISMATCH` (fail closed), proving Gap 1 is closed.
- **P2:** Correct absolute relocation — real T3 function referencing global data/code with OMF `FIXUPP` + LE `p.fix_at`. Must `MATCH`.
- **N2:** Hardcoded numerical address (`CODE_OBJ`/`DATA_OBJ`) with missing OMF `FIXUPP` — exact matching raw bytes for a real function, but stripped OMF `FIXUPP` (or C casting literal address). Must `MISMATCH` (`code_reloc_reverse`), proving Gap 2 is closed.
- **P3:** Genuine hardware constant (`0xa0000`) without LE fixup or OMF `FIXUPP` — real `src/playflic/intro_op_clear_screen.c` (and/or `src/gamedlg/help_screen.c`). Must `MATCH` with 0 false positives.
- **P4:** Correct local data pointer table — synthetic/real object with `_DATA`/`CONST` pointer table whose OMF `FIXUPP`s match `war.exe` `p.fix_at` (e.g. referencing real `war.exe` data table with LE pointer fixups!). Must `MATCH`.
- **N3:** Corrupted local data pointer target — same table with one pointer targeting the wrong symbol/address. Must `MISMATCH` (`data_reloc_forward`) while legacy `wc1.match.match_module` masks it! Proves Gap 3 is closed.
- **N4:** Hardcoded pointer in local data segment (raw bytes match original, OMF `FIXUPP` missing where `p.fix_at` exists). Must `MISMATCH` (`data_reloc_reverse`).
- **N5:** Byte-similar but semantically mismatched addressing field (e.g., wrong target+addend pair or absolute vs self-relative mismatch). Must `MISMATCH`.
- **P5:** Correct `rel32` call/jmp within `CODE_OBJ` without LE loader fixup — real T3 function calling another function via `call rel32`. Must `MATCH`.
- **N6:** Invalid `extent retry` — object whose tail past `orig_fn_end` contains non-filler code or a `FIXUPP`. Must `MISMATCH`.
- **N7:** Unsupported / ambiguous relocation form — e.g., non-loc-9 fixup (e.g. `loc=11` ptr16:32) or `target_kind="frame"` / `"grp"`. Must return `"UNSUPPORTED"` (NEVER `"MATCH"`).
- **N8 (Multi-finding R3 control):** Single object simultaneously containing >=2 independent defects (e.g. missing code relocation + corrupted data pointer). Must return `"MISMATCH"` with ALL independent findings present in `findings`.

### 4.3 Full Read-Only Re-Audit of All Existing T3 Functions (`experiments/build_codegen/e0/reaudit_t3.py`)

Discover ALL existing in-scope T3 functions dynamically from `symbols.load()` + `progress.classify()` (expected: `519` functions across `514` C files — record the exact discovered count).
For every T3 file:
- Compile once under its declared `codegen-compiler` (`10.0a` or `ow2`) and declared `codegen-flags` into an isolated directory `build/e0/obj/` (use bounded parallelism, e.g., `jobs=4` or `8`, reusing `wc1.match.compile_c`).
- Run BOTH legacy `wc1.match.match_module` AND the strengthened E0 matcher (`FunctionMatch` and `RegionMatch`).
- Record for every T3 function:
  - `addr` (hex), `name`, `link_name`, `src`, `compiler`, `cflags`, `obj_sha256`
  - `legacy_verdict`
  - `e0_function_verdict` (`MATCH`/`MISMATCH`/`UNSUPPORTED`/`ERROR`)
  - `e0_region_verdict` (`MATCH`/`MISMATCH`/`UNSUPPORTED`/`ERROR`)
  - `rfc15_category` (one of: `unaffected`, `code_reloc_defect`, `data_pointer_defect`, `boundary_extent_defect`, `matcher_unsupported`, `other_mismatch`)
  - `findings` (full list, unrestricted)
  - `leading_bytes_len`, `data_segments_checked`, `data_fixups_checked`, `code_fixups_checked`, `reverse_le_fixups_checked`
- Save:
  - `docs/research/build-codegen/results/e0/controls.json`
  - `docs/research/build-codegen/results/e0/t3_reaudit.json`
  - `docs/research/build-codegen/results/e0/t3_reaudit.csv`
- Write comprehensive report `docs/research/build-codegen/E0-matcher-soundness.md` with:
  - Executive summary & scientific verdict (`CONFIRMED`/`REJECTED`/`PARTIALLY_CONFIRMED`/`INCONCLUSIVE`)
  - Full control matrix (P1–P5, N1–N8) with legacy vs strengthened comparison
  - Full T3 re-audit statistics, breakdown across all 5 RFC §15 categories, and complete table of ANY non-`MATCH` function (with exact address, file, compiler, flags, and full findings evidence)
  - Explicit reproduction commands and limitations.

## 5. Acceptance Criteria & Atomic Commits

1. `pytest -q experiments/build_codegen/e0/test_e0.py` passes 100%.
2. `python3 -m experiments.build_codegen.e0.run_e0` reproduces both `controls.json` and the full 519-T3 re-audit cleanly from scratch.
3. Zero modifications outside `experiments/build_codegen/e0/` and `docs/research/build-codegen/` (`git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile` is empty).
4. Create 3–4 clean atomic commits on branch `research/build-codegen/e0`:
   - Commit 1: `exp(e0): strengthened matcher prototype with normalized addressing obligations`
   - Commit 2: `exp(e0): positive and negative soundness controls + pytest suite`
   - Commit 3: `exp(e0): full read-only re-audit of 519 existing T3 functions + machine-readable results`
   - Commit 4: `docs(e0): E0 matcher soundness and T3 re-audit report`
5. End your final message with a concise structured summary: commit SHAs, control pass/fail counts, exact T3 re-audit counts by verdict and RFC §15 category, any discovered false matches or unsupported cases, and exact reproduction commands.
