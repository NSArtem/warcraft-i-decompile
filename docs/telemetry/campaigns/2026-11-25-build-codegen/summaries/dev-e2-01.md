Completed E2: [report](/mnt/data/projects/warcraft-1-decompile-wt/e2/docs/research/build-codegen/E2-compilation-context.md).

Commits: `96f3593` (harness/tests), `022df03` (CSV formatting), `b1614b9` (results/report).

- **Alignment:** 10.0a uses 16 bytes with `-4r -ot`, four with `-3r`/`-5r`; OW2 uses 16 with both tested `-4r`/`-5r` presets.
- **96 T3 functions:** native consolidation retained **83**, lost **13**, gained **0**. Compatible groups: **81/15/0**. No native same-flags instruction-body changes; failures include layout/E0 bounds, one data-anchor collision, and one forced-flag difference.
- **Domino probe:** 63 edits, 210 neighbor observations; zero neighbor instruction changes, one data-anchor match loss.
- **Validation:** 21 tests pass, JSON/CSV reproduce byte for byte, production diff is empty.

Reproduce:

```sh
python3 -m experiments.build_codegen.e2.run_e2
pytest -q experiments/build_codegen/e2/test_e2.py
```