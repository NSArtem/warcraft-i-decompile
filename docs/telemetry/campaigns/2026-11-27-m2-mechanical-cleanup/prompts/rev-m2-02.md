# Independent Adversarial Review Round 2 — Campaign A (`feature/m2-mechanical-cleanup`, `b0196b4..b8d8fb11`)

You are a fresh, independent, read-only Reviewer inspecting branch `feature/m2-mechanical-cleanup` inside `/mnt/data/projects/wc1-wt-on/m2-rev` (detached HEAD at `b8d8fb11`, base `b0196b4`).
Do NOT modify repository files or create commits.
Do NOT run full `make verify` (the Manager runs serialized `make verify` after your approval).

## Context
Round 1 review (`rev-m2-01`) verified all core A1/A2/A3/A4 work, scope/governance, `0x23170` deferral, `0x1bf94` T4 audit, all 12 semantic names, and Build A `IDENTICAL`, and returned `REQUEST_CHANGES` for:
- **H1**: `tests/test_overnight.py::test_build_queue_with_needs_human_filters_unautomatable` failed on newly DONE addresses (`0x1132c`, `0x13e94`, `0x15170`, `0x26360`, `0x2b308`).
- **H2**: `tests/test_overnight.py::test_bullet_c_clean_functions_queued_after_default_skip_removal` failed on newly DONE `0x123cc`.
- **M1**: `src/include/mod_2b2f0.h` had stale `TargetModeGet` / `TargetModeLeave` prototypes.
- **M2**: `docs/subsystems/mod_2b2f0.md:19` falsely said `target_mode_enter_reference.c` and `target_mode_exit_reference.c` still mismatch.
- **M3**: 4 stale `fn_214d4` evidence refs in `analysis/symbols/{net_link,save_score,status}.toml`.
- **LOW 1–7**: doc casing/notes, `test_codegen_promo.py` docstring, `mod_19470.toml` semicolon, `net_game_start_reference.c` `int` extern, `mod_2b2f0.toml` `unsigned short` proto, `mod_16390.h` comment.

Commit `b8d8fb11` was created to resolve every finding.

## Verification Checklist
1. Inspect `git show b8d8fb11` completely and verify every single Round 1 finding (H1, H2, M1, M2, M3, LOW 1–7) is resolved cleanly WITHOUT weakening any test or verification gate (confirm `test_overnight.py` still enforces `"locked TOML"` on remaining `0x150f0` and all still-blocked `needs_human` guards!).
2. Confirm scope/governance remained untouched across `b0196b4..b8d8fb11` (`Makefile`, `flake.nix`, `AGENTS.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md`, `tools/wc1/progress.py`, `LOCKED_TOMLS`, `PROTECTED_TOMLS`, `build.py`, `emit.py`, `omfpatch.py`).
3. Run:
   - `nix develop -c python3 -m wc1.symbols`
   - `nix develop -c python3 -m wc1.match --all`
   - `nix develop -c python3 -m wc1.match --compile-check`
   - `nix develop -c python3 -m wc1.build` (confirm `IDENTICAL`)
   - `nix develop -c python3 -m wc1.progress`
   - `nix develop -c pytest -q tests/test_overnight.py tests/test_overnight_wave4.py tests/test_codegen.py tests/test_codegen_promo.py tests/test_mod_2b2f0.py tests/test_mod_13f60_c.py tests/test_mod_19470.py tests/test_snd_f1.py tests/test_packet.py tests/test_mod_1bf80.py tests/test_progress.py tests/test_t4spec.py`
4. Report any remaining genuine findings by severity, and end with an explicit standalone line:
`VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` or `VERDICT: REJECT` or `VERDICT: BLOCKED`

---
## Session Operational Rules & Hard Deadline
- **Launch time:** `2026-11-26T22:43:58.379672Z` (Unix epoch `1795733038`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-26T23:13:58Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-26T23:04:58Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly authorized. Batch independent shell commands where safe.
