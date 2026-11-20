# mod_3ac10 (area mod_3ac10_c)

Single-function module at 0x3ac10.

| Addr | Name | Proto | Status |
|---|---|---|---|
| 0x3ac10 | HLine (`HLine_`) | `void HLine(short x, unsigned short y, unsigned short len)` | reference only; near-miss |

## Data
- `cur_bitmap`: pointer to `Bitmap { short width; short height; unsigned char *data; }`.
- `draw_color`: byte fill colour.

## Behaviour
Fills `len` bytes at `data + width*y + x` with `draw_color` (horizontal line, no clipping).

## T3
No C files match yet. `hline_reference.c` is a near-miss: the compiled output has an extra `xor eax,eax` at +0xa (OP/STRUCT). The test guard asserts it still fails to match.

## T4
`test_h_line` runs the reference against the original in the emulator. The bitmap header and pixel buffer are allocated in `init_emu`. The cases cover zero length, negative x, and various widths and colours. The test compares the pixel buffer, which sits behind `cur_bitmap`.
