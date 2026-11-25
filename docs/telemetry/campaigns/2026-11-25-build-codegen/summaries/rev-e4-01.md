I'll start by orienting myself in the review worktree and reading the key documents.
All verification steps are complete. Here is my independent review.

---

# Independent Adversarial Review — Experiment E4 (`rev-e4-01`)

**Under review:** `02e43f6`, `a82e572`, `1a32b17` (detached HEAD `1a32b17`, baseline `654711eb`).
**Environment:** existing dev shell; no `nix develop`, no `make verify`, no tracked files edited.

## 1. Verdict

`VERDICT: APPROVE`

## 2. Findings

No Must-Fix or Should-Fix items. Four low-severity/optional observations, none of which weakens any claim the report makes:

| # | Severity | Location | Explanation | Required resolution |
|---|---|---|---|---|
| F1 | Low (optional hardening) | `experiments/build_codegen/e4/omf_extract.py:592-608`, `e3/partial_matcher.py:45` | `_require_verified` accepts any `VerifiedRegion` instance as the E3 proof as-is. `VerifiedRegion` is a plain frozen dataclass with no validation, so a fabricated proof is trusted: my probe extracted `[1,3)` (mid-function, bytes `89 e5`) using a hand-built proof that no E3 evaluation produced. The independent scan still enforces branch/clised closure and pre/post byte invariance, and Build A link identity would fail for a bad range, so this is not exploitable end-to-end; the report explicitly states the "only input is an E3 `VerifiedRegion`" trust boundary, and the unit test deliberately forges one to test the self-check. | Optional: require `verification_scope`/non-empty `entries` (or re-run `evaluate_region`) for a bare proof object, and/or narrow the parameter type to `Evaluation`. |
| F2 | Low (evidence traceability) | `run_e4.py:positive_thread`, `omf_extract.py:865` | `extracted_object_loadable_sha256` is computed on the pre-`apply_data_plan` object; the object actually linked (`build/e4/ba/{score,farm}/c_{306,400}.obj`) differs by `b3.rewrite` normalizing segment `align` 3/5 → 1, so the recorded digest cannot be recomputed from the linked artifact. Text, fixups, publics, externs, data are byte-identical (I diffed the canonical views); the plan is a no-op for these two cases. | Optional: record the post-plan digest or label the pre-plan one; name the linked `c_*.obj` in the report. |
| F3 | Low (robustness) | `_chunks` (`omf_extract.py:611`) vs `e5/omf_b3.py:54` `Fix.encode` | No explicit `0 <= doff < 1024` guard in the shared encoder; E4's chunk planner guarantees it. I reproduced the silent failure mode with a *fixture-built* object that puts a fixup at offset 1024 in one `LEDATA` (encoded `loc=10` instead of 9) — E4's own path never produces this, and all legal boundary positions I probed were fine. | Optional: assert the doff bound so a future regression fails closed. |
| F4 | Low (theoretical, untested) | `_segdef`/`_segdef32` (`omf_extract.py:96,143`) | A 16-bit "big" segment (64K, attr bit 1, length field 0) is widened to `SEGDEF32` with length 0 and the big bit kept; re-parsing yields length 0 (verified directly), so a 64K *data* segment (NASM OMF16 input) would be mis-emitted. Not exercised by the corpus (fixtures are small); does not affect a `_TEXT` slice, whose length is taken from `hi-lo`. | Optional: map big→0x10000 during widening, or reject. |

## 3. Independent verification summary

**Scope (clean).** `git diff 654711eb -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md` is empty. `git diff --stat 654711eb..HEAD` = 15 files, all under `experiments/build_codegen/e4/` and `docs/research/build-codegen/`. Three atomic commits match the contract's prescribed messages; docs only in commit 3.

**Tests and reproduction.** `pytest -q experiments/build_codegen/e4/test_e4.py` → **17 passed in 29.03 s** (no skips/xfails/monkeypatch in the E4 code). `python3 -m experiments.build_codegen.e4.run_e4` → exit 0. `git diff -- docs/.../results/e4/results.json` is **empty** (byte-identical rewrite); `results.json` sha256 `892d3bee…eb043`, identical to the file in the independent `/e4` dev worktree. No path/timestamp markers (`/mnt`, `/tmp`, `/nix`, `wc1e5-`, ISO timestamps) in the JSON. `git status --porcelain` after the run shows only the pre-existing `?? original` symlink — no stray files.

**Build A positives are genuine, not ASM fallbacks.** In `build/e4/ba/score/war.map`, `0001:00014e90 ScoreTickIncome_` is defined by `c_306.obj` (THEADR `…/score_reference.c`), and the surrounding ASM pieces split at `0x14e8e` / `0x14edd` exactly around the slice; `farm/war.map` shows `0001:00018254 FarmPanelChanged_` from `c_400.obj` with pieces split at `0x18237`/`0x18298`. The emitted objects are exactly the slices: `_TEXT` 77 B / 68 B, publics only the extracted function, six rebased fixups each. `compare.txt`: `IDENTICAL`, `fixups: A=8770 B=8770 only-A=0 only-B=0`, entry/stack equal. I independently loaded both exes: bytes at the slice range equal `war.exe` (`0` diffs), and the farm call at `0x28291` resolves to `0x281f4` (the sibling). `c_functions` 520/515 objects vs 519/514 baseline, as reported.

**Positive 3 / 3b / 4.** `p3_slice.obj` externs are exactly `E4_C_`, `wc1_anchor_20000` with fixups `[2, self-rel, ext]`, `[10, absolute, ext]`; `wc1.compare` on `p3_rebuilt` vs `p3_oracle` → `IDENTICAL`. `p3b_slice.obj` text is `5589e5e8 00000000 5dc3` with the sole change being the 4-byte field 24→0 plus `EXTDEF E4_C` + self-relative `FIXUPP32`; oracle identical. `p4_slice.obj` emits `LEDATA32 (0,1022)` and `(1022,478)` with `FIXUPP32 doff=0, loc=9`; oracle identical. My own extra boundary probes (fixup at 1021/1022/1023 in a 3000-byte `LEDATA`, and 1024/2046 with chunked input) all split before the field, keep `doff=0`, and link identical.

**Fail-closed behaviour.** All eight controls re-run and returned the documented codes: `N1_on`/`N1_off` → `outgoing_rel8` (candidate `[0x5f,0x70)` at `0x16d48`, rel8 `[104, 94, 0x16d31]`, E3 `MISMATCH`), `N2` → `interior_target`, `N3` → `ambiguous_symbol` (DB entry removed; identity never inferred from `war.exe`), `N4`/`N4b` → `data_layout_mismatch`, `N5` → `relocation_target_mismatch`, `N6` → `incomplete_closure`. Six RFC §6.2 classes covered.

**Adversarial probes (all as required).** Checksum-preserving mutation of an address field + real E3 proof → `relocation_target_mismatch`; mutation of an opcode byte + real E3 proof → `unsupported_construct: compiled byte differs from the verified original`; unverified `Evaluation` → rejected (`outgoing_rel8`, never extracted); forged `VerifiedRegion` → accepted (F1, trust boundary); synthetic intra-slice `seg(_TEXT)` fixup whose original loader target disagrees → `relocation_target_mismatch`; non-`off32` location → `unsupported_construct`; unfixed absolute immediate → unchanged (placement-dependent, not a relocation; harmless for Build A).

**Contract/soundness answers.** E3 `RegionMatch` is required on the `Evaluation` path (a non-`VerifiedRegion` proof re-scans and raises, with finding codes); byte invariance is enforced twice (against the original before planning, and against the compiled slice after emission, masking only `off32` fields wholly inside the slice); `rel8` is never widened (outgoing `rel8` fails closed, N1); unknown targets are never named from `war.exe` (N3 is the executable demonstration). The only pre-existing untracked item in the root is the `original` symlink, unchanged by the run.

Elapsed review time ≈ 9 minutes of the 30-minute budget.