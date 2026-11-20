# mod_34c50_c

Module `mod_34c50`: one function, matched at T3 (byte-exact under Watcom 10.0a).

| Function | C file | Status |
|---|---|---|
| PaletteCycleDisable (`void __cdecl PaletteCycleDisable(unsigned char id)`) | src/mod_34c50/palette_cycle_disable.c | T3 MATCH |

## Data layouts
Uses the `palette_cycles` array of 12-byte entries. Entry `id` is indexed with `id * 12`. The enable/disable pair operates on the leading 16-bit flag of an entry. The enable counterpart (0x31920) writes 1 there, and this function clears it. I did not disassemble 0x34c50 for this doc, so that detail is inferred from the neighbouring function.

## Tests
- T3: `tests/test_mod_34c50_c.py::test_t3_files_match` recompiles `palette_cycle_disable.c` and checks it still matches.
- T4: there are no reference functions, so there are no differential tests and no near-miss guard.
