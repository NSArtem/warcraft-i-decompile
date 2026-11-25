# Experiment E1 Repair Assignment (`dev-e1-02`, Fresh Replacement Session)

You are a **fresh Developer session** (`dev-e1-02`) assigned to resolve the single MEDIUM finding from Independent Review Round 1 (`rev-e1-01`, `VERDICT: REQUEST_CHANGES`) on Experiment E1.
- **Worktree:** `/mnt/data/projects/warcraft-1-decompile-wt/e1`
- **Branch:** `research/build-codegen/e1` (current HEAD: `4b5dd79388fa4cc16e1166be936c7b3d736bfab1`, baseline `7c23d2371e95d8de93f0ba1652c8d44b858da273`)
- **Environment:** Already inside the Nix dev shell for this isolated worktree. Do NOT invoke `nix develop`; run `python3`, `pytest`, `git` directly.

## Strictly Permitted Scope
- Edit ONLY under `experiments/build_codegen/e1/` and `docs/research/build-codegen/`.
- Do NOT modify `tools/wc1/`, `src/`, `analysis/`, `tests/`, `Makefile`, `flake.nix`, or `AGENTS.md`.

## Single Reviewer Finding to Resolve (1 MEDIUM)
- **Location:** `experiments/build_codegen/e1/test_e1.py:217` (and `run_e1.py` / `disasm_evidence.txt` if needed)
- **Issue:** In another checkout/worktree path (such as a review worktree or the integrated campaign repo!), `pytest -q experiments/build_codegen/e1/test_e1.py` failed 1/17 because it unconditionally compared raw committed bytes containing absolute checkout-dependent `THEADR` object SHA-256 hashes and absolute diagnostic paths!
- **Required resolution:**
  1. Keep raw `obj_sha256` recorded in `results.json` AND add a checkout-independent `parsed_omf_digest` (hashing parsed segments, data bytes, publics, statics, and fixups — independent of THEADR source path!) so cross-checkout identity of compiled machine code & relocations is strictly verified!
  2. Make `test_e1.py` portable across any checkout path:
     - Strictly compare ALL scientific results, parsed OMF digests, code bytes, relocations, branch encodings/targets, public offsets, padding, E0 verdicts/findings, Build A IDENTICAL status, and disassembly content against committed artifacts (stripping/normalizing only checkout-path-dependent raw `obj_sha256` and root path prefixes in diagnostic messages).
     - Test raw byte-for-byte determinism (including raw `obj_sha256`) across two fresh runs in the SAME checkout (or verify raw `obj_sha256` exact equality when checkout root matches `results.json`'s recorded checkout root).
  3. Update `docs/research/build-codegen/E1-shared-epilogues.md` and `docs/research/build-codegen/results/e1/` cleanly.
  4. Verify `pytest -q experiments/build_codegen/e1/test_e1.py` passes 100%, `git diff 7c23d23 -- tools/ src/ analysis/ tests/ Makefile` is empty, and commit cleanly (`exp(e1): make replay verification portable across checkouts while retaining raw hashes`).
