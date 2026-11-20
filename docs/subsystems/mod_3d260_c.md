# mod_3d260_c — centered text drawing

Module `mod_3d260` (0x3d260), area `mod_3d260_c`.

## Functions

| Addr | Name | Prototype | Status |
|------|------|-----------|--------|
| 0x3d260 | DrawTextCentered | `void DrawTextCentered(short y, const char *s, unsigned char color)` | reference only (T4) |

## Behaviour
1. `cur_font = default_font`.
2. `TextSetColorBase(color)`.
3. `w = (short)TextWidth(default_font, s)`.
4. `DrawText((cur_bitmap->width - w) / 2, y, s)`.

Registers (watcall): y=eax, s=edx, color=ebx. Callees: DrawText (eax, edx, ebx), TextSetColorBase (eax), TextWidth (eax, edx).

## Data layouts
- `cur_bitmap`: pointer to `Bitmap { short width; short height; }`.
- `default_font`, `cur_font`: `Font *` globals.

## T3 / T4 notes
- No T3 (matching) files yet.
- `draw_text_centered_reference.c` is behaviourally equivalent but does not byte-match: the original has a `movsx esi, si` at 0x3d27c that the compiled output lacks (OP/STRUCT). The near-miss guard asserts it keeps failing to match.
- T4 test `test_draw_text_centered` stubs all three callees and compares call logs plus the `cur_font` write. Cases cover zero width, a width wider than the bitmap (negative result), odd differences, short truncation of the width, and garbage in the upper bits of the y register.
- Buffers are allocated in `init_emu`. Callee and data addresses are resolved from the symbol DB at test time.
