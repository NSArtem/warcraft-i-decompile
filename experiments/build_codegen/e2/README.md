# E2 compilation-context experiment

Use the already configured project dev shell. The supplied `war.exe`, Watcom
10.0a, Wine, and OW2 are required; missing tools fail the experiment.

```sh
python3 -m experiments.build_codegen.e2.run_e2
pytest -q experiments/build_codegen/e2/test_e2.py
```

The runner freshly compiles 96 symbol-database `src` entries, each under its
declared flags and every study variant. It then compiles complete source
concatenations in original address order: whole areas, STATUS flag-compatible
groups, maximal original-adjacent runs, and contiguous subsets with common
original start modulo 16. It never rewrites OMF or substitutes a legacy matcher.

`harness.py` contains selection, generation, compiler invocation, E0 evaluation,
and diagnostic fingerprints. `synthetic.py` contains the flag matrix, loop
shift controls, and static/global/external call controls. Synthetic fixtures
are under `fixtures/`. All generated C, objects, and checkpoints live under
`.scratch/`; results go only to `docs/research/build-codegen/results/e2/`.

The STATUS overlay changes five stale header declarations to match the existing
`(void)` definitions. All 58 STATUS standalone controls must remain identical
and E0-matching with this overlay. No production header changes.

JSON contains each E0 verdict, every non-byte diagnostic, losslessly coalesced
byte-mismatch runs, body fingerprints/fixups, relative offsets, segment hashes,
and same-flags standalone controls. `consolidation_rows.csv` provides the flat
function/context table. `FunctionMatch` and `RegionMatch` remain E0's verdicts;
diagnostic body equality is explicitly weaker than either. Refer to the report
for the non-contiguous-region-bound limitation discovered in E0.

No `make verify`, Build A, goal changes, production edits, or game binaries are
part of this experiment. The pytest suite also generates results if they are
absent, so the harness commit can be tested independently of saved outputs.
