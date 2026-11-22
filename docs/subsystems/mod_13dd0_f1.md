# Cursor shapes (`mod_13dd0_f1`)

This part of `mod_13dd0` covers cursor-shape initialization and storage. Addresses and declarations below come from `src/include/mod_13dd0_f1.h`; no instruction listing or callers were supplied, so the initialization sequence and record encoding are not documented here.

## Function

| Address | Function | Evidence |
| --- | --- | --- |
| `0x13dfc` | `void InitCursorShapes(void)` | Address and signature in the subsystem header; implemented in `src/mod_13dd0/init_cursor_shapes.c`. |

## Data layout

| Address | Symbol | Layout and evidence |
| --- | --- | --- |
| `0x58e50` | `cursor_shape_table` | Header declares 16 records of 12 bytes. The resulting `0xc0`-byte span ends immediately before `0x58f10`; subsequent records are elements of the same array. |
| `0x58f10` | `current_cursor_shape_id` | Header declares one unsigned byte, immediately after the table. |
| `0x5aa6c` | `default_cursor_shape` | Header declares a separate 12-byte array, the same size as one table record. |

## Tests

`tests/test_mod_13dd0_f1.py::test_t3_matches` checks that `init_cursor_shapes.c` still matches the original under its declared compiler. There are no reference files in this area, so no near-miss guard or T4 differential test is needed. The test requires the original executable and `$WATCOM`; it was not run here.
