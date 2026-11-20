# mod_1af20_c1: fog-of-war drawing and place-box release

Module `mod_1af20` (area `mod_1af20_c1`). These three functions have only reference C. They do not match byte-for-byte.

## Functions

| Addr | Name | Status | Blocker |
|---|---|---|---|
| 0x1af20 | FogDrawCell | reference | Branch displacement differs: original `je +0x6c` at 0x1af2b, compiled `je +0x70`. |
| 0x1af90 | FogDrawViewport | reference | The original prologue starts with `push ebx`, which the compiled code lacks. |
| 0x1b4dc | PlaceBoxRelease | reference | Register allocation differs. The original saves ebx/ecx/edx/esi and does `sar dx,4` and `sar bx,4` in 16-bit registers. |

## Behaviour (from the reference C)

- **FogDrawCell(cell, dst)**:
  - The cell index is `cell & 0x1f`.
  - Index 0 draws nothing.
  - Index 10 calls `FillBlack16(dst)`.
  - Any other index reads 4 mini-tile words from `fog_cell_table + idx*8`. It calls `MiniTileMasked` at dst+0, +8, +0xa00 and +0xa08.
- **FogDrawViewport()**:
  - It walks a 15×11 grid of cells.
  - The source is `fog_map + scroll_y*64 + scroll_x`. The map is 64 words wide, so each row advances the source by 0x31 after the 15 cells.
  - dst starts at `dat_5a874 + 0xf48` and advances 0x10 per cell and 0x1310 per row.
- **PlaceBoxRelease(evt)**:
  - It takes the event x at +4 and y at +6.
  - It subtracts the viewport origin (0x48, 0xc) and bounds-checks against 0xf0 × 0xb0.
  - It shifts the result right by 4 to get a cell, then adds the map scroll.
  - It then calls `NetSendPlaceConfirm(packed x|y<<16)` and `fn_1a388(0)`.

## Data

- `fog_cell_table`: pointer to 8-byte entries, each holding four u16 tiles.
- `fog_map`: pointer to u16 cells, 64 per row.
- `map_scroll_x`, `map_scroll_y`: u16.
- `dat_5a874`: pointer to the destination framebuffer.

## Tests

- T3: no files match yet, so the list is empty.
- Near-miss guard: `assert_ref_mismatch` checks that the three reference files still fail to match.
- T4: `tests/test_mod_1af20_c1.py` runs each reference function against the original code in the emulator. Callees are stubbed and their register arguments are logged. All buffers are allocated inside `init_emu`.
