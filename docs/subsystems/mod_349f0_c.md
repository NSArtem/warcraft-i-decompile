# mod_349f0 (area mod_349f0_c)

Module covering 0x349f0: dirty-rectangle accumulation.

## Functions
| Addr | Name | Status |
|---|---|---|
| 0x349f0 | DirtyRectAddLayer(unsigned char id) | reference only; fails match (extra `push ebx` prologue, codegen/register-allocation difference) |

## Data layout
- `dat_5aa92`: array of 9-short (18-byte) layer records. Fields used: [0]=x, [1]=y, [2]=w, [3]=h.
- `dirty_x1, dirty_y1, dirty_x2, dirty_y2`: signed short accumulated bounds.
- `dirty_w, dirty_h`: derived as `x2-x1+1`, `y2-y1+1`.

Behaviour: expands the dirty rect to include layer `id` (min of x/y, max of x+w-1 / y+h-1) and then recomputes w/h.

## Tests
- T3: no files matched yet (empty list).
- Near-miss guard: `dirty_rect_add_layer_reference.c` must still fail to match.
- T4: `tests/test_mod_349f0_c.py::test_dirty_rect_add_layer` runs the reference C against the original in the emulator with edge and seeded random layer/rect values. It compares the six dirty globals and the layer table. The function returns void, so `out_regs=()`.
