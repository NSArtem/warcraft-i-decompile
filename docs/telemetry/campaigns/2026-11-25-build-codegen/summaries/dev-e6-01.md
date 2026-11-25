Implemented E6. [Report](/mnt/data/projects/warcraft-1-decompile-wt/e6/docs/research/build-codegen/E6-multifunction-t4.md) and [results](/mnt/data/projects/warcraft-1-decompile-wt/e6/docs/research/build-codegen/results/e6/results.json) are committed.

- **73 tests passed**; JSON reproduced byte-for-byte.
- Both real families pass Isolated, Group and Integrated modes.
- R2 checks four typed pointer slots and actual compiled callback execution.
- **N1–N7 fail closed**, covering ten variants.
- Real `IntroFrame -> IntroLoadCreditLines` has **one OMF fixup**, refuting the zero-fixup premise. A supplemental zero-fixup fixture passes entry-hook verification.
- All changes stay within permitted paths.

Commits: `c9bc5de`, `257f256`, `732a605`, `bb64f22`.

```sh
pytest -q experiments/build_codegen/e6/test_e6.py
python3 -m experiments.build_codegen.e6.run_e6
python3 -m experiments.build_codegen.e6.run_e6 --check
```