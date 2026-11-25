Resolved all three review findings in commit `2ef81e04377f0497dae6365df9943836c144d377` on `research/build-codegen/e2`.

E2 now uses short relative compiler paths, excludes path-bearing debug contents from published evidence, and preserves exact literal bytes and offsets while masking variable `CONST` padding. Fresh tests assert exact function starts under `-ot`, `-os`, and `-od`.

Both checkouts passed all **27 tests**. Full runs from 45- and 104-character checkout roots produced byte-identical `results.json` and `consolidation_rows.csv`, with zero checkout-path leakage in the JSON. The production diff against `7c23d23` was empty.