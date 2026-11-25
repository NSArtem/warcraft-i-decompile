E1 confirmed: Watcom 10.0a reproduces both shared epilogues using pure C.

| Successful variant | Sharing | Exact branches | FunctionMatch | RegionMatch | Build A |
|---|---|---|---|---|---|
| A: revised C, `-oa -5r` | On/Off: true | `74 f3`, `74 df` | 3/3 MATCH | MATCH | IDENTICAL |
| B: supplied C, `-5r` | Wait: true, across Sync | `74 93`, `75 89` | 3/3 MATCH | MATCH | IDENTICAL |

Both builds have **0 byte differences and 0 fixup differences across 8,770 fixups**. The A near-miss `74 f5` versus original `74 f3` is preserved and explained.

**17/17 tests pass**, covering 97 variants and deterministic evidence replay. Production files are unchanged.

Commits on `research/build-codegen/e1`:

- `0428f1275ed8` — harness, fixtures, tests
- `4b5dd79388fa` — results, disassembly, report

[Read the E1 report](/mnt/data/projects/warcraft-1-decompile-wt/e1/docs/research/build-codegen/E1-shared-epilogues.md).

```sh
python3 -m experiments.build_codegen.e1.run_e1
pytest -q experiments/build_codegen/e1/test_e1.py
```