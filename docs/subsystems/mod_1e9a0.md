# mod_1e9a0 (0x1e9a0..0x1eba0): fog-of-war region update helpers

| Addr | Name | Notes |
|---|---|---|
| 0x1e9a0 | FogUpdateTile | per-tile callback for TerrainWalkRegion; remaps owner's bit field of fog_map[tile] through fog_transition_table |
| 0x1ea18 | FogUpdateArea5 | sets scan params (5x5, fog_shape_5, FogUpdateTile) and walks region |
| 0x1ea58 | FogUpdateArea6 | same, 6x6, fog_shape_6 |
| 0x1ea98 | FogUpdateArea7 | same, 7x7, fog_shape_7 |
| 0x1ead8 | FogUpdateArea8 | same, 8x8, fog_shape_8 |
| 0x1eb18 | FogUpdateArea9 | same, 9x9, fog_shape_9 |
| 0x1eb58 | FogUpdateArea11 | same, 11x11, fog_shape_11 |

## Data
- fog_map (pointer to u16 per tile); each owner has a bit field selected by fog_owner_mask[o] / fog_owner_shift[o] (0x51dde / 0x51de2; the arrays overlap, shift[0] == mask[2]).
- fog_transition_table (0x52598): u16 [state][11], indexed by the field value shifted down and by `*terrain_scan_table`.
- fog_cur_owner (0x599d0): owner index used by FogUpdateTile.
- fog_shape_N tables at 0x5268a..0x52888 are the region shapes.

## T3
The six FogUpdateAreaN files match byte-exactly under 10.0a and are re-checked by `assert_t3_matches`.

## T4
FogUpdateTile has no matched C yet. The reference file differs only in register choice at 0x1e9ad (`add edx,eax` in the original, `add eax,edx` in ours). It is guarded by `assert_ref_mismatch`. A difftest runs the reference against the original over tiles, owners, field values and scan indices. `fog_map` and `terrain_scan_table` are pointed at buffers allocated in `init_emu`.
