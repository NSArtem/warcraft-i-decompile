# mod_2b8e0 – terrain tile tables and autotiling (0x2b8e0..0x2c320)

Terrain tile-rewrite code. It loads four transition tables (A, B, C, D) from resources. Per-cell callbacks, driven by the region walker `fn_2b1b0` (0x2b1b0), step tiles through those tables. An autotiler picks tile ids from a 4-neighbour bitmask. All offsets below were read from the disassembly and from the reconstructed sources in `src/mod_2b8e0/`.

## Functions

| Addr | Name | Notes |
|---|---|---|
| 0x2b8e0 | TerrainTableLoad | T3 match. Loads resource `id` into `*out` and stores a 2-word header (stride, count). |
| 0x2b91c | TerrainTablesInit | Reference only. Picks resource ids from `dat_500da` (0xc0, 0xc3 or other) and loads tables A..D. Then fills the tile-base offsets `dat_5a442`, `dat_5a446`, `dat_5a440` and `dat_5a444` as running sums of the header counts. |
| 0x2ba08 | TerrainTablesFree | T3 match. |
| 0x2ba50 | TerrainTileAdvanceB | Reference only. Callback that steps a tile through table D. Clears bit 7 of the map-flag byte when the entry has flags in 0xf000. Redraws through `TerrainTileToCache` if the cell is inside the 16x12 scroll window. |
| 0x2bb38 | TerrainStartRegionB | Reference only. Reads the scan origin from the unit's words at +0x4e and +0x50. Sets a 3x3 region, `terrain_scan_table = dat_5516c`, and `terrain_scan_cb = TerrainTileAdvanceB`. Then calls `fn_2b1b0`. |
| 0x2bb7c | TerrainTileIsClear | Reference only. Returns 1 if table D entry 1 of the tile's state has no 0xf000 flags. |
| 0x2bbe4 | fn_2bbe4 | Reference only. Spiral search with radius 3, 5, 7 and 9 around a point, using `step4_dx` and `step4_dy`. Returns 1 at the first clear tile. |
| 0x2bd00 | TerrainTileAdvanceA | Reference only. Same idea as B, using table A and `terrain_scan_table`. |
| 0x2bdd4 | TerrainStartRegionA | Reference only. Unit-size dependent (`dat_51aba[type]` and `unit_type_size[type]`). Picks one of the scan tables 0x55192, 0x5517e, 0x55186 or 0x551a4. |
| 0x2bf30 | TerrainFlagTest | T3 match. |
| 0x2bf64 | TerrainAutotileCell | Reference only. 4-bit neighbour mask (S, E, W, N), then map lookup, stride multiply and base lookup. Writes the tile and redraws if visible. |
| 0x2c0bc | TerrainAutotileCross | T3 match. |
| 0x2c100 | TerrainRoadCell | Reference only. Loads the autotile globals for table C (mask 3, map 0x551e4), then calls the cross autotiler. |
| 0x2c14c | TerrainApplyCellFlags | Reference only. Same, with table B (mask 0xc, map 0x551c4). Afterwards sets the high byte of the tile word to `(b & 7) \| 0xa0`. |
| 0x2c1e8 | TerrainFillRectOwnerMask | Reference only. Sets `terrain_rect_cb = TerrainRoadCell`. The mask comes from `owner_block_mask[owner & 0xff]`. |
| 0x2c208 | TerrainFillRectMask | Reference only. Sets `terrain_rect_cb = TerrainApplyCellFlags`. The mask comes from `dat_51dc0[kind & 0xff]`. |
| 0x2c268 | TerrainWallCell | Reference only. Table B, mask 0x10, sets `dat_55204 = 3` around a call to `TerrainAutotileCell(x, y, 0x10)`. |
| 0x2c2c4 | TerrainWallAdvance | Reference only. Steps a wall tile through table B. Recurses to y-1 and y+1 when entry flag 0x2000 is set and `dat_55206` is nonzero. |

## Data layouts

- **Autotile globals** (0x5a450..0x5a461):
  - 0x5a450: base table pointer.
  - 0x5a454: map pointer.
  - 0x5a458: rect callback.
  - 0x5a45c: stride.
  - 0x5a45e: first tile.
  - 0x5a460: flag mask.
- **Tables A..D**: pointers at 0x5514c, 0x55150, 0x55154 and 0x55158. Each has a 2-word header `{stride, count}` at 0x5a430, 0x5a434, 0x5a438 and 0x5a43c. Table entries are u16: low 12 bits are the tile index, 0xf000 holds flags.
- **Tile map and flags**: `tile_map` (0x58584) and `map_flags` (0x5857c) are 64x64 u16 arrays. In a tile word, bits 0..10 are the tile id and the top 5 bits are preserved on rewrite.
- **Scroll window**: `map_scroll_x` and `map_scroll_y` give a 16x12 visible window. `TerrainTileToCache` (0x1246c) is called only for cells inside it.

## Tests

- **T3**: `TerrainTableLoad`, `TerrainTablesFree`, `TerrainFlagTest` and `TerrainAutotileCross` match byte for byte.
- **T4**: the other 14 functions have near-miss reference files. All of them still fail the T3 match. The blockers are unresolved `dat_` relocations, register choice (ebx vs eax, esi vs edi), a hoisted `tile_map` in `fn_2bbe4`, and the shared loop body of the two rect fillers, which cannot be split into separate C functions.
- `tests/test_mod_2b8e0.py` runs each reference against the original with the emulator and compares output registers, watched globals and the tile map. Callees are stubbed: `TerrainTileToCache`, `fn_2b1b0`, `TerrainFlagTest`, `TerrainAutotileCross`, `TerrainAutotileCell`, `TerrainTableLoad`, `TerrainRoadCell` and `TerrainApplyCellFlags`. The stub call logs are compared too.
- The test environment is built deterministically with a seeded RNG.
