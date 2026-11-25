E3 proved `RegionMatch` for `FarmPanelChanged` and `ScoreTickIncome` in Watcom 10.0a objects with mismatching siblings. Farm’s call already has a self-relative `EXTDEF` fixup to the original `UnitPanelStateChanged` provider. Score matched after swapping the summands, while the baseline differed by one LEA byte.

The requested standalone `DialogHighlightOff` match was refuted. Its original short branch targets a shared `ret` outside the slice, and Watcom folds both highlight symbols onto the same object offset. The matcher rejected the region.

The shifted `CONST` case passed with verified literal boundaries. All required negative controls failed closed. **24 tests passed**, two fresh runs produced byte-identical JSON, and the baseline diff is confined to E3. Both requested commits are on `research/build-codegen/e3` (`ee17095`, `eaaf87a`).

[Report](/mnt/data/projects/warcraft-1-decompile-wt/e3/docs/research/build-codegen/E3-partial-matching.md) · [Results JSON](/mnt/data/projects/warcraft-1-decompile-wt/e3/docs/research/build-codegen/results/e3/results.json)