Resolved all six findings in two commits:

- `6b44c39f846be77b5e8772eb6bc4f4abc995a124` — fixes, tests, and regenerated evidence.
- `dfd2a4c345adcd1ba71e1cf341fd9d3ca9a6f69a` — refreshed report.

**55/55 controls passed; 77 tests passed.** All 519 T3 functions and associated regions match. Production-path diff is empty. The regenerated CSV is byte-identical; only the pre-existing untracked `original` remains.

Exact reproduction output, with all commands exiting 0:

```text
$ python3 -m experiments.build_codegen.e0.run_e0 --jobs 4
E0 controls: 55/55 passed
E0 audit: 50/514 C files, 52 T3 functions
E0 audit: 100/514 C files, 102 T3 functions
E0 audit: 150/514 C files, 154 T3 functions
E0 audit: 200/514 C files, 205 T3 functions
E0 audit: 250/514 C files, 255 T3 functions
E0 audit: 300/514 C files, 305 T3 functions
E0 audit: 350/514 C files, 355 T3 functions
E0 audit: 400/514 C files, 405 T3 functions
E0 audit: 450/514 C files, 455 T3 functions
E0 audit: 500/514 C files, 505 T3 functions
E0 audit: 514/514 C files, 519 T3 functions
{"c_files": 514, "count_matches_expectation": true, "expected_c_files": 514, "expected_functions": 519, "function_verdicts": {"ERROR": 0, "MATCH": 519, "MISMATCH": 0, "UNSUPPORTED": 0}, "functions_discovered": 519, "legacy_false_match_candidates": 0, "legacy_verdicts": {"MATCH": 519}, "nonmatch_functions": 0, "region_verdicts": {"ERROR": 0, "MATCH": 519, "MISMATCH": 0, "UNSUPPORTED": 0}, "rfc15_categories": {"boundary_extent_defect": 0, "code_reloc_defect": 0, "data_pointer_defect": 0, "matcher_unsupported": 0, "other_mismatch": 0, "unaffected": 519}}

$ pytest -q experiments/build_codegen/e0/test_e0.py
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 2.84s

$ git diff 3ee53aa -- tools/ src/ analysis/ tests/ asm/ Makefile flake.nix AGENTS.md
```