# mod_20c30_ui (0x20c30..0x21100)

UI order/command helpers of module `mod_20c30`: pending-order setters, stop, move mode, cancel construction/production, return-to-town-hall.

## Functions
| Function | Addr | Status |
|---|---|---|
| ui_cancel_construction, ui_cancel_production, ui_order_move_mode, ui_order_set_next3_11, ui_order_stop, ui_return_to_town_hall, ui_set_pending_order3/4/10/14, ui_worker_return_order | 0x20c30..0x21040 | T3 byte-matched (src/mod_20c30/*.c) |
| UnitGetTargetIfType50 | 0x21040 | reference only, T4 difftest |

## UnitGetTargetIfType50
Returns the unit's target (`u+0x52`) if its type byte (`+0x1b`) is 0x32. With no target, it checks `dat_5008c[u->type @+0x1e]`. If that entry is nonzero, it returns 0. Otherwise it looks up `object_map[(x>>16) + ((y>>16)<<6)]`, using the dword views at `+0x4c` and `+0x4e`. It returns that unit if its type is 0x32, else 0.

The reference does not match because the original has an extra `mov eax, edx` at 0x21048. The near-miss guard asserts it still fails to match.

## Tests
`tests/test_mod_20c30_ui.py` runs `assert_t3_matches` on the T3 files and `assert_ref_mismatch` on the reference. It also runs a T4 differential test of the reference against the original. The test covers the target-set, type, unit-type-flag and map-entry combinations. Buffers are allocated in `init_emu`.
