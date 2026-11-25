**CONFIRMED.** [Full report](docs/research/build-codegen/E0-matcher-soundness.md) and machine-readable results are committed.

- **Commits:** `b59e34d`, `fae4690`, `df4f5f9`, `54bfd6b`.
- **Controls:** 36 passed, 0 failed. All 12 positives matched; all 24 negatives failed closed.
- **Pytest:** 46 passed.
- **T3 audit:** 519 functions across 514 C files. Both function and region verdicts: **519 MATCH, 0 MISMATCH, 0 UNSUPPORTED, 0 ERROR**.
- **RFC §15 categories:** `unaffected=519`; `code_reloc_defect=0`; `data_pointer_defect=0`; `boundary_extent_defect=0`; `matcher_unsupported=0`; `other_mismatch=0`.
- **Findings:** Legacy false matches reproduced in controls; none discovered among existing T3 functions. Nine negative controls correctly returned `UNSUPPORTED`.
- **Scope:** Production paths unchanged. Two fresh runs produced byte-identical results.

Reproduce in the configured shell:

```sh
cd /mnt/data/projects/warcraft-1-decompile-wt/e0
python3 -m experiments.build_codegen.e0.run_e0 --jobs 4
pytest -q experiments/build_codegen/e0/test_e0.py
```