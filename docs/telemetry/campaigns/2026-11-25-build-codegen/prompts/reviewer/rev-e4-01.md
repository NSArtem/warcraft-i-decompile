# Independent Adversarial Review — Experiment E4 (`rev-e4-01`)

You are the fresh **Independent Reviewer** (`rev-e4-01`) for **Experiment E4** (Selective OMF Extraction Feasibility).

- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/rev-e4-01` (detached at `1a32b171d61c776e2abcbb412d1169c999b55d1a`)
- **Baseline:** `654711eb32f5ef7c84c46e108e5a1435c2011a73`
- **Commits under review:**
  - `02e43f6cf58a03a741dcc16423172c80cf7a6c2b` (`exp(e4): conservative OMF32 selective slice extractor enforcing relocation equivalence`)
  - `a82e572d071452171e42bbb1e7f6fdc073480ac4` (`exp(e4): Build A IDENTICAL extraction tests and 6 fail-closed negative controls`)
  - `1a32b171d61c776e2abcbb412d1169c999b55d1a` (`docs(e4): E4 selective OMF extraction results and feasibility report`)
- **Environment:** Already inside the Nix dev shell for this isolated review worktree (`WC1_ROOT`, `PYTHONPATH`, `WATCOM`, `WINEPREFIX`, and short per-session `TMPDIR` configured; caches pre-warmed). Do NOT invoke `nix develop` and do NOT run `make verify`. Run `python3`, `pytest`, `git` directly. Do NOT edit tracked files.

## Adversarial Verification Checklist
1. Read `docs/research/build-codegen/contracts/E4-contract.md`, `docs/research/build-codegen/E4-omf-extraction.md`, and inspect all 3 commits + `experiments/build_codegen/e4/{omf_extract.py,run_e4.py,test_e4.py,fixtures/}`.
2. Run `pytest -q experiments/build_codegen/e4/test_e4.py` and `python3 -m experiments.build_codegen.e4.run_e4` in this review worktree (check `git diff -- docs/research/build-codegen/results/e4/results.json` is empty, byte-identical cross-worktree reproducibility, zero leaked paths/timestamps, zero stray files in repo root).
3. Verify **scope**: Confirm `git diff 654711eb -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty.
4. **Adversarial soundness audit (RFC §6.1–6.4):**
   - Does `omf_extract.py` genuinely require E3 `RegionMatch` BEFORE extraction?
   - Does it enforce the byte-invariant self-check (ZERO opcode, length, register, or non-address immediate modifications; NEVER converts `rel8` to `rel32`; NEVER infers unknown targets solely from `war.exe`)?
   - Do BOTH real Build A extractions (`ScoreTickIncome 0x24e90` and `FarmPanelChanged 0x28254`) genuinely link the extracted C slices (NOT ASM fallbacks!) into Build A `IDENTICAL` (`0` byte diffs, `8,770/8,770` LE fixups)? Inspect the linker `.map` and emitted `.obj`!
   - Do Positive Case 3 (`A -> C` across mismatching `B` — both compiled fixup and bare `rel32` forms + E5 Fix B3 `wc1_anchor_*` `CONST` literal) and Positive Case 4 (>1024 B `LEDATA32` split before a 4-byte fixup crossing bytes 1022–1026) genuinely work and link identically?
   - Do ALL 6+ fail-closed negative controls (N1a `DialogHighlightOn` + N1b real `DialogHighlightOff` `0x16d48` outgoing `rel8`, N2 interior target, N3 ambiguous/unknown symbol, N4 unproven mutable data layout, N5 incorrect relocation target, N6 incomplete closure / shared jump table) genuinely fail closed with exact reason codes?
   - Run 2–3 quick adversarial `python3 -c` probes (e.g., trying to bypass E3 precondition, mutating a non-relocated byte, or passing a fixup crossing chunk boundary) to try to break fail-closed behavior!

## Output Format
End with an explicit verdict line in your final message:
1. `VERDICT: APPROVE` | `VERDICT: REQUEST_CHANGES` | `VERDICT: REJECT` | `VERDICT: BLOCKED`
2. Findings list (if any: Severity, Location, Explanation, Required resolution).
3. Concise independent verification summary.

---
## Session Operational Rules & Hard Deadline (Appended by Runner)
- **Launch time:** `2026-11-25T20:31:19.820029Z` (Unix epoch `1795638679`)
- **Hard wall-clock limit:** `1800 s` (~`30 min`, hard cutoff `2026-11-25T21:01:19Z`)
- **70% wrap-up checkpoint:** `1260 s` (`2026-11-25T20:52:19Z`) — check elapsed time periodically with `date -u +%s`.
- **Pacing:** Begin writing your final review report and explicit `VERDICT: ...` line by the 70% mark.
- **Efficiency:** Do NOT use `sleep` polling loops. Do NOT run `make verify` or the full repository test suite unless explicitly required by your assignment. Batch independent shell commands into a single step where safe to reduce turn latency.
