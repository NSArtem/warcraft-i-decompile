I'll start by exploring the worktree state and the relevant files.
Now let me implement the F1 fix in `synthetic_corpus.py`.
Now let me test the digest across two scratch dirs:
Now let me replace it with the recipe-literal-anchored version:
Now let me update those spots and add the new tests:
Now add the F2 `conftest.py`:
All findings are resolved and committed. Final report:

## E8 `dev-e8-04` — rev-e8-02 findings resolved

**Commit:** `06235f6 exp(e8): resolve rev-e8-02 findings (normalize CONST pad digest, conftest, zero-skip fresh tests)` on `research/build-codegen/e8` (parent `dc1d028`), clean status (only the pre-existing untracked `original/` tree remains).

### F1 (HIGH) — reproducible `synthetic_manifest.json`
- Reproduced the drift independently: the CONST pad between `"e8 g17 b\0"` and `"e8 g17 t\0"` came out as `79 00 73` (old `build/e8`), `20 00 32` (fresh dirs), `3e 00 26` (another forced rebuild) — the compiler writes heap residue into the alignment gap.
- `synthetic_corpus.py`: replaced `image.data_sha256` with **`image.semantic_data_sha256`** plus an `image.data_padding_normalized` census (9 CONST literals, 6 gaps / 13 bytes, explicit gap offsets, and a note explaining the 10.0a behaviour). New `semantic_data(prog, mapinfo)`:
  - locates the recipe's **declared** C literals (from `SPEC` source pieces, NUL included) by content in the linked data object, so every literal byte **and offset** is covered, `_DATA` initializers are kept verbatim;
  - zeroes *only* the unclaimed compiler gaps, and fails loudly if any gap reaches 4 bytes or if a declared literal is missing from both linked objects (no silent weakening).
- Evidence: `run_e8 --refresh` twice → byte-identical artifacts; a full build in three different scratch directories (including the pre-existing `build/e8` with different pad bytes) yields the same digest; the pytest suite on a cleared cache regenerates the committed artifacts byte-identically.

### F2 (LOW) — plain pytest bootstrap
- Added `experiments/build_codegen/e8/conftest.py` with the same repo-root `sys.path` bootstrap as `e1/conftest.py` (no e4/e5 conftest exists in this worktree); `pytest -q experiments/build_codegen/e8/test_e8.py` now collects directly.

### F3 (LOW) — zero skips on a fresh checkout
- Added a session autouse fixture `e8_caches` that builds Corpus A and populates the B1/B2 caches whenever `war.exe` + the 10.0a `clib3r.lib` are present; removed all seven `needs_libsig_cache` skips and the `corpus.json` skip guard on the regeneration test. Skips remain only for genuinely absent user inputs (`war.exe`, `setup.exe`, libraries).
- **Verified on a cleared `build/e8/`: `pytest -q experiments/build_codegen/e8/test_e8.py` → 30 passed, 0 skipped, 0 failed (172.9 s).**

### F4 (NIT) — doc precision
- `112 extents` = 111 distinct objects (`clib3r:cstrt386` contributes both `_TEXT` and `BEGTEXT`), same clarification for the sensitivity run's 111 extents = 110 objects; relocation rule now states *non-self-relative* (a `call`/`jmp` `rel32` is not one), matching `verify_segment()`; added a Corpus A bullet documenting the padding-normalized digest and refreshed the artifact hash table.

### Extra tests added
- `test_synthetic_data_digest_is_padding_independent` — committed digest reproduced by a forced rebuild in `tmp_path`.
- `test_data_digest_excludes_only_the_compiler_padding_gaps` — perturbs every pad to 4 values (digest unchanged) and flips every one of the 183 non-pad data bytes (each changes or is rejected).

**Gates:** zero production diffs (`git diff c946f38 -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` empty); `git diff HEAD -- docs/research/build-codegen/results/e8/` empty; artifacts stable across two `--refresh` runs and a fresh-cache pytest regeneration. `make verify` was not run, per instructions.