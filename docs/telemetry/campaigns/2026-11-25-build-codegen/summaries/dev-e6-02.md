Both HIGH findings are fixed and committed on `research/build-codegen/e6`:

- `45498e521bb9` — callback ABI validation and contiguous ownership isolation.
- `b6e2554286cb` — refreshed report and results JSON.

Verification: **96 tests passed**, no skips or xfails; all **14 negative variants rejected**; runner `--check` confirmed byte-identical JSON.

All edits stayed within the permitted scope. The required baseline diff is empty; existing untracked `original` remains untouched.