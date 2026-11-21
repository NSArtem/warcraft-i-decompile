# mod_34ad0_c — Line drawing

| Addr | Name | Notes |
|---|---|---|
| 0x34ad0 | `Line_` | `void Line(short x0, short y0, short x1, short y1)` |

## Behaviour
- Computes |dx|, |dy|. If dx==0 it calls `VLine(x, ymin, dy)`; if dy==0 it calls `HLine(xmin, y, dx)`.
- Otherwise it is a Bresenham-style loop. It writes `draw_color` into `cur_bitmap->data[x + y*width]`.
- Endpoints are swapped first so the major axis runs forward.

## Data
- `cur_bitmap`: pointer to `{short width; short height; uchar *data}`.
- `draw_color`: byte.

## Status
- Reference-only (`src/mod_34ad0/line_reference.c`). It does not match yet. The original uses an ebp frame with dword spill slots at [ebp-4..-0x14], and the register shuffle differs from ours.
- No T3 files. A near-miss guard is not registered because the empty-file list is skipped.
- T4: `test_line` runs the compiled reference against the original in the emulator. It covers vertical, horizontal, shallow, steep, reversed, diagonal and point cases.
- The VLine/HLine callee stubs and the `cur_bitmap` setup still need to be added to the T4 test. The test is incomplete until then.
