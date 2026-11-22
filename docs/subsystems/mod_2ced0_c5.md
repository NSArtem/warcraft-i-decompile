# mod_2ced0_c5 – UnitsDraw

Module `mod_2ced0`, function at 0x2d8c8 (called from `ViewportLayerCallback`, 0x1b00c).

| Addr | Name | Status |
|------|------|--------|
| 0x2d8c8 | `UnitsDraw` | reference only (`units_draw_reference.c`), T4 difftest |

## Behaviour (from disassembly)
1. Scroll = `map_scroll_x/y << 4` (0x500d0/0x500d2).
2. Pass 1 over `draw_list` (0x5a490, null-terminated). Sets flag 0x10 in `u->flags`, skips units with flags&0x20d or bit 0x100 of word +0xe. Otherwise calls `GrpFrameInfo`, clips the sprite to the 240x176 viewport, clears flag 0x10, dispatches `sprite_blitters[u->c8]` (0x55288), and draws a linked sprite via `UnitDrawSprite` if type >= 0x20 and `[u+0x58]` is non-null.
3. Resets `damage_fire_heavy/light` positions to -16, then draws the 100-entry `object_array` (0x26 bytes each) with `UnitDrawSprite`.
4. Pass 2 over `draw_list`: for units still flagged 0x10 it draws up to 3 nested selection or health rectangles using `VLine` and `HLine`. It sets `draw_color` (0x5ad30) to 0xdb, to `dat_51808[color]`, to 0x72, or to 0x74.

## Why reference only
The original packs Rect, Bitmap and scratch locals into overlapping 16-bit stack slots. It reads them through dword `>>16` views at `[esp+0xa]`, `[esp+0x2a]` and `[esp-0x2]`. Its frame is `sub esp,0x38`, and the C89 reference compiles to `sub esp,0x40`. The T3 byte match therefore fails.

## Tests
- `test_ref_mismatch`: near-miss guard, so the reference must still not match.
- `test_units_draw`: T4 differential test with 4 fixed and 60 random cases.
  - Stubs: `GrpFrameInfo` (writes deterministic bitmap and offsets), `UnitDrawSprite`, `VLine`, `HLine`, and the 8 blitter slots, all with call logs.
  - Watched memory: units, links, objects, fire buffers and `draw_color`.
  - All buffers are allocated in `init_emu`.
