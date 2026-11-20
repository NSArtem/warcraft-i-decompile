# mod_33aa0 (area mod_33aa0_c)

## Functions

| Addr | Name | Status |
|------|------|--------|
| 0x33aa0 | DirtyRectAlignAndPresent | reference only (not T3 match) |

## Behaviour
Aligns the dirty rectangle to 4-pixel boundaries, then presents it:
- Low 2 bits of `dirty_x1` (read at 0x5acd0) are `a`. If nonzero, `dirty_w += a` and `dirty_x1 -= a`.
- Low 2 bits of `dirty_w` are `a`. If nonzero, `dirty_w += 4 - a`.
- `dirty_x2 = dirty_x1 + dirty_w - 1`.
- It then calls `VidPresentRect()`, which takes no arguments.

## Data
`dirty_x1`, `dirty_x2` and `dirty_w` are 16-bit globals from the symbol DB.

## T3/T4 notes
- The reference C compiles but does not match. The original pushes ebx/ecx/edx around the ebp frame. At 0x33aa6 it uses `mov ax, word [0x5acd0]; xor ah, ah`. Our output uses a byte load.
- The near-miss guard asserts the reference still mismatches.
- The T4 difftest compares the reference C with the original in the emulator. It uses several x1/w inputs, and the `VidPresentRect` stub logs each call.
