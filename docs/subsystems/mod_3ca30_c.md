# mod_3ca30_c — 2bpp glyph blitter

Module `mod_3ca30` (area `mod_3ca30_c`) contains `DrawGlyph2bpp` at 0x3ca30.

| Addr | Name | Notes |
|---|---|---|
| 0x3ca30 | DrawGlyph2bpp(unsigned char ch) | Draws one 2-bits-per-pixel glyph at `text_dest`, advances `text_dest` by glyph width, returns width. |

## Data layout
- `text_dest` (ptr): current output pointer.
- `text_glyph_table` (ptr): glyph table base. Entry for `ch` is at `tbl + (ch - text_first_char)*3`: u16 offset of bitmap data from table base, u8 width in pixels.
- `text_rows`, `text_bytes_per_row` (u8): row count and number of 4-pixel groups per row.
- `text_max_x` (u16): extra stride added after each row.
- `text_colors[4]`: palette map. Pixel value 0 is transparent.

## Behaviour
Each row consumes up to `width` pixels. Each byte holds 4 pixels, 2 bits each, low bits first. If the remaining width is 0, the destination advances 4 without consuming source bytes.

## Status
- T3: no matched files yet (reference only).
- Reference `draw_glyph_2bpp_reference.c` is a near miss. The original at 0x3ca40 loads `[0x5acfa]` into ebp, and the reference gets ebx (+0x10), which is a register allocation difference.
- T4: `tests/test_mod_3ca30_c.py::test_draw_glyph_2bpp` runs the reference against the original under emulation. It uses random glyph tables and watches `text_dest` and the return value.
