# mod_2ced0_c3 — unit death / construction-completion step

| Addr | Name | Status |
|---|---|---|
| 0x2d0e0 | `UnitStartDeath` | T4 reference only (`unit_start_death_reference.c`) |

## UnitStartDeath(Unit *u)
Per-tick step that sets `s4c=10`, increments `s52`, calls `SndConstructionTick`, then:
- `s52 < s50`: progress branch, `b1a = s52*255 / s50`, computed from dword views at +0x50 and +0x4e (high words).
- `s52 == s50`: `b1a = 0xff`, return.
- `s52 > s50`: completion. It sets `b1c = type` and `b7 = 0`, then calls `fn_26360(u,2)` and `fn_13c84`. It sets flag 0x80 and calls `fn_13c04`. It sets `status_dirty = 1`, decrements `dat_50d98[owner]`, then calls `fn_1c9c0` and `SndWorkComplete`. Finally it scans the 200-entry unit array (stride 0x5c) for a unit with `(flags & 0x207) == 0`, `flags & 8` set and the dword at +0x52 equal to `u`. For the first match it calls `fn_1cf94(q)`, decrements the byte at `u+0x4e`, calls `fn_2e5c8(q, &unit_type_size[type])`, and returns.

## Data layout (Unit, 0x5c bytes)
Offsets: b7 +7, flags +0x10, b1a +0x1a, type +0x1b, b1c +0x1c, owner +0x1e, s4c +0x4c, s4e +0x4e, s50 +0x50, s52 +0x52. The pointer in the scan overlaps s52 and the following pad bytes.

## Tests
- T3: no files are matched yet, so no T3 assertion is made.
- Near-miss guard: the reference still fails to match. The only difference is the encoding of the `jl` at 0x2d0fd (orig +0x100, got +0xfd), which is a relative-displacement difference.
- T4 (`tests/test_mod_2ced0_c3.py::test_unit_start_death`) runs the reference against the original in the emulator. Callees are stubbed and their register arguments logged. The unit array is allocated in `init_emu`, and the test watches the array, `dat_50d98` and `status_dirty`. Cases cover the progress branch, the equal case, completion with no match, completion with a match, a match blocked by flag 0x200, and a candidate without flag 8.
