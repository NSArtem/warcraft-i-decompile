# mod_3aac0_c

Module `mod_3aac0` (area `mod_3aac0_c`): a transparent, horizontally flipped bitmap blit.

## Functions

| Addr | Name | Status | Notes |
|---|---|---|---|
| 0x3aac0 | BitmapBlitTransparentFlipH | reference only (T4) | `x`=eax, `y`=edx, `src`=ebx, `srcrect`=ecx (watcall). It builds a source Rect and a destination Rect on the stack. It calls `RectClip(&s,&d)`. If that returns 0, it calls `RectCopyTransparentFlipH` with 6 cdecl stack args. |

## Data layouts

- `Rect`: six shorts, `x y a b w h` (12 bytes).
- `Bitmap`: `short w; short h; unsigned char *data` (8 bytes).
- `cur_bitmap`: global `Bitmap *`. It is the destination surface.

## Codegen blocker

The reference C compiles with `sub esp, 0x24`. The original has `sub esp, 0x28` at 0x3aac5. The frame is 4 bytes larger, so the original probably keeps an extra local or temporary. The near-miss guard `assert_ref_mismatch` keeps the reference file marked as non-matching.

## Tests

- T3: no files are matched yet (empty list).
- T4: `tests/test_mod_3aac0_c.py::test_bitmap_blit_transparent_fliph` compares the original at 0x3aac0 with the compiled reference. It uses stubbed `RectClip` and `RectCopyTransparentFlipH` callees. The stubs log Rect contents and the 6 stack args. They never log stack pointers.
- The stubbed clip callee can return nonzero, or shrink the source rect, to exercise both branches.
- Callee addresses are resolved at run time from the symbol DB by link name. Buffers are allocated only inside `init_emu`.
