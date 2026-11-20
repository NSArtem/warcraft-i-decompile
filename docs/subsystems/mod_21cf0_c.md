# mod_21cf0_c

Module `mod_21cf0`, area `mod_21cf0_c`: layer/bitmap helpers.

## Functions

| Function | Source | Status |
|---|---|---|
| LayerAdd | src/mod_21cf0/layer_add.c | T3 byte-match |

There are no reference (non-matching) functions in this area.

## Data layouts (src/include/mod_21cf0_c.h)

- `Bitmap { short w; short h; void *data; }`
- `Rect { short x, y, r4, r6, w, h; }`
- `Layer { short active, x, y, w, h; Bitmap *bm; void (*blit)(); }`

## Testing

- T3: `tests/test_mod_21cf0_c.py::test_t3_files_match` recompiles `layer_add.c` and requires a MATCH against war.exe.
- T4: not needed. Every function is T3-matched, so there are no reference functions to difftest.
- The near-miss guard (`assert_ref_mismatch`) is not used, because the reference list is empty.
- The tests need `original/install/war.exe` and `$WATCOM`, and are skipped without them.
