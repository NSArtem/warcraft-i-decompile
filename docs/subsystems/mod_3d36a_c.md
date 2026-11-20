# mod_3d36a_c: video present

Module `mod_3d36a`, area `mod_3d36a_c`.

## Functions

| Addr | Name | Status |
|---|---|---|
| 0x3d560 | VidPresentRect | reference only (not matched) |

### VidPresentRect (0x3d560)
Copies the dirty rectangle from the back buffer pointed to by `dat_5a874` to VGA memory at 0xa0000, with a stride of 320 (0x140). Inputs are the shorts `dirty_x1`, `dirty_y1`, `dirty_w` and `dirty_h`. Width is copied as dwords (`w>>2`) per row, and both pointers then advance by `320-w`.

Evidence: the original is hand-written asm. It saves eax..ebp and uses `mov ax,0x140; imul word [dirty_y1]`, which C cannot emit. The reference C therefore first differs at 0x3d560 (`push eax` in the original, `push ebx` in the C output).

## Data
- `dat_5a874`: pointer to the 320x200 8bpp back buffer.
- `dirty_x1`, `dirty_y1`, `dirty_w`, `dirty_h`: 16-bit rectangle values.

## Tests
- T3: there are no matched files yet.
- Near-miss guard: `vid_present_rect_reference.c` must still fail to match.
- T4: `tests/test_mod_3d36a_c.py::test_vid_present_rect` is a differential test. It compares the VGA window at 0xa0000 for the original and the compiled C, using w as a multiple of 4 and h of at least 1. The back buffer is allocated in `init_emu`.
