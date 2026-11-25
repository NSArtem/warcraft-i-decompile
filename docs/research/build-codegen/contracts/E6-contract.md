# Experiment E6 Contract & Developer Assignment — Multi-Function T4 Verification (`wc1.cemu`)

## 1. Mission & Research Question

You are the Developer for **Experiment E6** of the Build & Codegen Infrastructure research campaign.
- **Experiment ID:** `E6`
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e6`
- **Branch:** `research/build-codegen/e6`
- **Baseline commit:** `3ee53aa5d4e7911e7f8d1bb0097de17223c8a559`
- **Environment:** You are already running inside the Nix dev shell with `WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, `TMPDIR` configured for this isolated worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `wcc386`, `wlink`, `nasm` directly.

**Research question:**
Can an experimental multi-function T4 verification prototype on top of `wc1.cemu` / `wc1.emu` safely support all three verification modes — **`Isolated`**, **`Group`**, and **`Integrated`** — using explicit `verification_boundary` + `dependency_substitution_policy`, symbol-aware relocation resolution, Unicorn address hooks (`UC_HOOK_CODE`), and strictly typed logical pointer correspondence (Mandatory Correction R2), WITHOUT machine-code patching, WITHOUT redirecting verified C implementations to original machine code, and WITHOUT weakening any anti-cheat guarantee?

**Hypothesis:**
Both complex real multi-function cases (`OptionsDialog`+`OptionsRefresh`+`OptionsApplyTimer` from `GAMEDLG.C`, and `IntroFrame`+`IntroLoadCreditLines` from `PLAYFLIC.C`) pass differential verification cleanly across `Isolated`, `Group`, and `Integrated` modes, while all negative anti-cheat and impossible-isolation cases fail closed.

## 2. Mandatory Reading & Source Files

Read before implementing:
- `docs/architecture/rfc-build-codegen-infrastructure.md` (§2.2.6, §3 #12, §11.1–11.3, §14 E6)
- `tools/wc1/cemu.py`, `tools/wc1/emu.py`, `tools/wc1/t4spec.py`
- `src/gamedlg/options_dialog_reference.c`, `src/gamedlg/options_refresh.c`, `src/gamedlg/options_apply_timer.c`, `tests/test_gamedlg.py` (lines 260–305)
- `src/playflic/intro_frame.c`, `src/playflic/player_reference.c` (`IntroLoadCreditLines` at `0x22d40`), `tests/test_playflic_t4.py`

## 3. Strictly Permitted Scope & Prohibitions

**Permitted write paths ONLY:**
- `experiments/build_codegen/e6/` (experimental Python harness, multi-function C fixtures, pytest suite, runner CLI)
- `docs/research/build-codegen/E6-multifunction-t4.md`
- `docs/research/build-codegen/results/e6/` (machine-readable JSON results)

**STRICTLY PROHIBITED:**
- Do NOT modify any production file under `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.
- Do NOT run `make verify` directly (run targeted `pytest experiments/build_codegen/e6/` and CLI scripts only).
- Do NOT patch compiled C machine code bytes or original machine code bytes to install stubs.
- Do NOT redirect functions INSIDE the `verification_boundary` to original machine code merely to obtain matching numerical pointer addresses (Mandatory Correction R2!).

## 4. Technical Requirements & Binding Interpretations (Mandatory Correction R2)

### 4.1 Experimental Multi-Function CEmu Harness (`experiments/build_codegen/e6/mf_cemu.py`)

Build an isolated prototype (importing `wc1.emu.Emu`, `wc1.cemu`, `wc1.omf`, `wc1.match`, `wc1.symbols`) supporting:

1. **Declarative Contract:**
   - `VerificationMode`: `"isolated"` | `"group"` | `"integrated"`
   - `VerificationBoundary`: explicit set of verified function link names (and their exact `[lo, hi)` byte ranges in BOTH the compiled C object and original `war.exe`).
   - `DependencySubstitutionPolicy`: explicit map of allowed external/sibling dependencies OUTSIDE `verification_boundary` -> `(orig_addr, stub_handler, stack_pop, expected_symbol, mechanism)` where mechanism is `"orig_addr_stub"`, `"symbol_aware_reloc"`, or `"c_entry_hook"`. Includes explicit allowlist for trusted built-in runtime models (e.g., `0x31789` `_memcpy`).
   - `PointerFieldSpec` (for R2 strictly typed pointer correspondence in `Group` / `Integrated` modes): explicitly typed watch regions (e.g. `(watch_addr, offset, expected_logical_domain)` or typed function-pointer slots) where numerical difference `(orig_ptr, c_ptr)` is accepted **ONLY IF**:
     - Both `orig_ptr` and `c_ptr` resolve to the EXACT same logical function symbol in the declared `VerificationBoundary` (bijective logical map `orig_addr(sym) <-> c_addr(sym)`),
     - Pointer equality & aliasing relations are preserved (if two slots hold equal pointers in orig, they MUST hold equal pointers in C; if distinct in orig, distinct in C),
     - Callback identity & actual callback behavior are verified (not masked!),
     - Arbitrary non-declared bytes or wrong-function pointers (e.g., `OptionsRefresh` swapped with `OptionsApplyTimer`) STILL FAIL CLOSED!

2. **Two Non-Patching Interception Mechanisms:**
   - **Symbol-aware relocation resolution** (ONLY for symbols OUTSIDE `verification_boundary` and EXPLICITLY listed in `dependency_substitution_policy`): resolve `EXTDEF`/`LEXTDEF` relocations to `orig_addr(sym)` instead of `local_names[sym]` so both calls AND function-pointer values match `orig_addr`. NEVER apply to symbols INSIDE `verification_boundary`!
   - **Unicorn address hook (`UC_HOOK_CODE`)** for direct intra-TU `call rel32` without OMF `FIXUPP`: install a symmetric entry hook on `c_entry_addr` (mirroring `emu.stubs[orig_addr]`), strictly ONLY for symbols OUTSIDE `verification_boundary` and EXPLICITLY declared in `dependency_substitution_policy`, AND verify static/dynamic safety:
     - Static/disassembly pre-check on compiled `_TEXT`: detect if an intended substituted sibling was **inlined** (no call to its entry, or entry unreachable while body merged), or if a **shared epilogue / interior jump** from inside `verification_boundary` jumps into the interior of a substituted sibling (or vice versa), bypassing entry hooks! When clean isolation cannot be proven, **FAIL CLOSED** with an explicit `IsolationImpossibleError` recommending `Group` or `Integrated` mode!

3. **Hardened Anti-Cheat Audit (`audit_mf_run`):**
   Preserve ALL existing `cemu`/`t4spec` anti-cheat invariants AND enforce:
   - Any stub inside `verification_boundary` (in either `orig` or `c` address ranges) -> **FAIL CLOSED** (`boundary_stubbed`).
   - Any undeclared stub outside `verification_boundary` (not in `dependency_substitution_policy` or trusted runtime allowlist) -> **FAIL CLOSED** (`undeclared_stub`).
   - Asymmetric substitution (stubbed on orig side but not C side, or vice versa) -> **FAIL CLOSED** (`asymmetric_substitution`).
   - Redirecting a function inside `verification_boundary` to original machine code -> **FAIL CLOSED** (`verified_c_redirected_to_orig`).
   - Untyped or mismatched pointer normalization (wrong target, broken aliasing, or non-pointer byte diff) -> **FAIL CLOSED**.
   - Code byte tampering (`orig_patched` / `c_patched`), `trace_active`, zero instructions executed, or zero observations -> **FAIL CLOSED**.

### 4.2 Real Multi-Function Test Fixtures & Scenarios (`experiments/build_codegen/e6/fixtures/` & `scenarios.py`)

Create temporary consolidated multi-function C fixtures INSIDE `experiments/build_codegen/e6/fixtures/` (NEVER editing `src/`):
1. **Real Case A — `GAMEDLG` Options family (`options_tu.c`):**
   Consolidate `OptionsApplyTimer` (`0x1a778`), `OptionsRefresh` (`0x1a79c`), and `OptionsDialog` (`0x1a800`) into ONE multi-function C file compiled with Watcom 10.0a (`-s -ot -ol -4r -zp2`).
   Verify:
   - **Baseline bug reproduction:** Show that legacy `wc1.cemu.run_pair` fails on consolidated `options_tu.c` (due to `p.refresh` / `p.timer` getting heap `0x80xxxx` addresses vs `0x1a79c`/`0x1a778`, and `c_stubbed` if stubbing a sibling).
   - **Mode 1 (`Isolated`):** Boundary = `{OptionsDialog_}`; `OptionsRefresh_` and `OptionsApplyTimer_` explicitly substituted outside boundary -> verify `OptionsDialog` passes with exact pointer values (`0x1a79c`, `0x1a778`) via symbol-aware resolution + symmetric stubs.
   - **Mode 2 (`Group`):** Boundary = `{OptionsDialog_, OptionsRefresh_, OptionsApplyTimer_}`; `DialogRun` stub ACTUALLY INVOKES the `p.refresh` and `p.timer` callback pointers passed inside `OptionsParams` (so C run executes REAL compiled C `OptionsRefresh` and `OptionsApplyTimer` in emulator heap, NOT original machine code!), watches `prefs_block`, `OptionsParams`, and stub logs, and uses strictly typed logical pointer correspondence (R2) to verify callback identity, pointer equality, AND callback side effects!
   - **Mode 3 (`Integrated`):** Boundary = `{OptionsDialog_, OptionsRefresh_, OptionsApplyTimer_}` running with real downstream `SndApplyOptions` (or realistic integrated call path with stubs only at hardware/UI boundary `DialogRun`/`clock`/`ModalScreen`)!
2. **Real Case B — `PLAYFLIC` IntroFrame + IntroLoadCreditLines (`playflic_pair_tu.c`):**
   Consolidate `IntroLoadCreditLines` (`0x22d40`) and `IntroFrame` (`0x22e84`) into ONE multi-function C file compiled with Watcom 10.0a. Inspect the compiled OMF `_TEXT` to PROVE whether Watcom 10.0a emits a direct intra-TU `call rel32` WITHOUT OMF `FIXUPP`!
   Verify:
   - **Baseline bug reproduction:** Show that legacy `wc1.cemu` bypasses `emu.stubs[0x22d40]` on the intra-TU call from `IntroFrame`.
   - **Mode 1 (`Isolated`):** Boundary = `{IntroFrame_}`; `IntroLoadCreditLines_` explicitly substituted via symmetric `UC_HOOK_CODE` entry hook -> passes `run_pair` with identical stub call logs & watched globals (`frame_ready`, `intro_tick_count`).
   - **Mode 2 (`Group`):** Boundary = `{IntroFrame_, IntroLoadCreditLines_}`; stubs only at external boundary (`TextWidth`, etc.) -> passes `run_pair` with both compiled C functions executing together!

### 4.3 Mandatory Strict Negative Controls (`experiments/build_codegen/e6/test_e6.py`)

Implement and assert ALL 7 required negative controls fail closed:
1. **N1 (`stub_inside_boundary`):** Attempt to install a stub on a function inside `verification_boundary` (e.g., stubbing `OptionsRefresh_` in Group mode) -> MUST fail closed.
2. **N2 (`undeclared_substitution`):** Install a stub on an external or sibling callee NOT declared in `dependency_substitution_policy` -> MUST fail closed.
3. **N3 (`asymmetric_substitution`):** Stub active only on original side or only on C side -> MUST fail closed.
4. **N4 (`incorrect_pointer_normalization`):**
   - (a) Swapped callback pointers (`p.refresh = OptionsApplyTimer; p.timer = OptionsRefresh`) -> MUST fail closed despite both being valid boundary functions!
   - (b) Broken aliasing (two pointers equal in orig, unequal in C) -> MUST fail closed!
   - (c) Non-pointer memory diff inside a watched buffer -> MUST fail closed!
5. **N5 (`verified_c_redirected_to_orig`):** Attempt to redirect a function INSIDE `verification_boundary` (`OptionsRefresh_`) to original `0x1a79c` via relocation override -> MUST fail closed (R2 invariant!).
6. **N6 (`interior_entry_bypass`):** Synthetic multi-function C / asm fixture where a branch/jump enters a substituted sibling at an interior offset bypassing its entry hook (e.g., shared epilogue or mid-function jump) -> MUST fail closed with `IsolationImpossibleError`.
7. **N7 (`inlined_callee_isolation_impossible`):** Synthetic fixture where Watcom 10.0a inlines (or eliminates the call to) a `static` / `inline` sibling that the test tries to substitute in `Isolated` mode -> MUST fail closed with `IsolationImpossibleError` (cannot claim `Isolated` when callee is inlined!).

## 5. Deliverables, Acceptance Criteria & Atomic Commits

Deliverables:
- `experiments/build_codegen/e6/mf_cemu.py`
- `experiments/build_codegen/e6/fixtures/` (consolidated `options_tu.c`, `playflic_pair_tu.c`, synthetic negative fixtures)
- `experiments/build_codegen/e6/run_e6.py` (reproducible CLI generating `docs/research/build-codegen/results/e6/results.json`)
- `experiments/build_codegen/e6/test_e6.py` (full pytest suite covering baseline bug repros, Isolated/Group/Integrated positive cases, and N1–N7 negative controls)
- `docs/research/build-codegen/E6-multifunction-t4.md` (complete findings, R2 pointer-identity analysis, limitations, reproduction commands)

Acceptance criteria:
1. `pytest -q experiments/build_codegen/e6/test_e6.py` passes 100%.
2. `python3 -m experiments.build_codegen.e6.run_e6` cleanly reproduces `docs/research/build-codegen/results/e6/results.json`.
3. Zero modifications outside `experiments/build_codegen/e6/` and `docs/research/build-codegen/` (`git diff 3ee53aa -- tools/ src/ analysis/ tests/ Makefile` is empty).
4. Create 3–4 clean atomic commits on branch `research/build-codegen/e6`:
   - Commit 1: `exp(e6): multi-function cemu prototype with boundary, substitution policy, and R2 pointer correspondence`
   - Commit 2: `exp(e6): GAMEDLG/PLAYFLIC multi-function fixtures and Isolated/Group/Integrated + N1-N7 tests`
   - Commit 3: `exp(e6): E6 runner, machine-readable results, and multi-function T4 report`
5. End your final message with a concise summary: commit SHAs, test pass counts, exact observations (including whether `IntroFrame->IntroLoadCreditLines` had 0 OMF fixups, pointer correspondence results, and N1–N7 outcomes), and reproduction commands.
