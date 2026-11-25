E5 completed in three commits: `d701bf0`, `481ce61`, `de82374`.

- 84 tests passed.
- Nine Build A links were **IDENTICAL**: zero byte differences; all 8,770 fixups matched.
- Whole-segment and verified per-symbol anchoring succeeded.
- Canonical `-ot` still mismatches; explicit `_DATA` arrays work under native `-ot`.
- CLI reproduced `results.json` byte for byte. Zero production diffs.

[Report](/mnt/data/projects/warcraft-1-decompile-wt/e5/docs/research/build-codegen/E5-data-anchors.md) documents the supported subset and limitations.