# mod_13f60 (area mod_13f60_c): unit order dispatch handlers

Order-update handlers called through the order dispatch table (unit in eax, `int` return, 1 = handled/keep order, 0 = done). Offsets are from the disassembly and `OrderUnit` in `src/include/mod_13f60.h`.

## Functions

| Addr | Name | Notes |
|---|---|---|
| 0x13f60 | OrderUpdateGone | calls 0x2e96c(u), returns 0 |
| 0x13f68 | OrderUpdateDeath | type 0x33 / <0x20 uses `death_sound_by_type` (0x5156c); else 0x13860 + TerrainStartRegionA; ends with UnitSetOrder(u,0) |
| 0x13ff0 | UnitIdleTurn | 0x19478(0x1b) random: 0 turns facing -1, 1..3 turns +1 (mask 7) |
| 0x14084 | OrderUpdateJoin | hp>5 or 0x13a90 true: reset AI site counts, set owner 0, flag 0x500de |= 1 |
| 0x14140 | OrderUpdateSpell | sets `spell_order`, uses `order_props[order]` bits 1/2/4, calls SpellCastOrder |
| 0x141e0 | OrderUpdateRepair | heals dest (+0x52) by 8 hp, costs from 0x50060/0x50074 |
| 0x14334 | UnitWorkProgress | progress counter bytes +0x3f/+0x40/+0x41, writes % into +0x1a |
| 0x143cc | OrderUpdateProduce | completes training/building, refunds on cancel (flag 0x20) |
| 0x145d0 | DispatchFatal | `FatalError(dat_56b10)` |

T3-matched (byte-exact): order_update_research.c, order_update_stop.c, save_file_finish.c.

## Data
- OrderUnit: +0x10 flags, +0x16 hp, +0x1b type, +0x1e owner, +0x1f order, +0x52 dest pointer.
- Produce uses a different view (`PUnit`): flags at +0x0e, otype +0x3e, position words at +0x40..0x44.
- Globals: `dat_50060`/`dat_50074` per-player resource longs[5], `training_count`, `unit_max_hp`.

## Reference files (T4 only)
Each `*_reference.c` is a near-miss. The blockers are unresolved `fn_XXXXX` or `dat_*` relocations, a register allocation difference (UnitIdleTurn), or a few extra or missing opcodes (UnitWorkProgress, OrderUpdateProduce). They must still fail T3.

`tests/test_mod_13f60_c.py` runs `t4spec.run_spec` for each one against the original code. Callees are stubbed and their calls logged, and the compiled C and the original must produce identical registers, memory and call logs. Unit buffers are allocated inside `init_emu`. Callees whose address isn't in the disassembly (e.g. UnitSetNextOrder, SpellCastOrder) are stubbed by looking up the symbol DB address. TerrainStartRegionA is not stubbed, so the death test avoids the type >= 0x20 branch.
