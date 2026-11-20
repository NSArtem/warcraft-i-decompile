# mod_13dd0_c: cursor shape selection

## Functions

| Addr | Name | Status |
|---|---|---|
| 0x13dd0 | SetCursorShape(unsigned char id) | reference only (no T3 match) |

SetCursorShape compares `id` with the current-shape byte at 0x58f10. If they differ, it stores `id` there and calls `CursorSetImage(&dat_58e50[id])`. Each descriptor is 12 bytes, three dwords, at 0x58e50. The call passes the descriptor pointer in eax.

## Blocker

The reference C compiles, but the compare against `[0x58f10]` comes out as `cmp al, [0]`. The original has the 0x58f10 fixup at offset 0x13dd1 and the reference has none there. This is a codegen/relocation difference in OP/STRUCT. `assert_ref_mismatch` guards that the reference still fails to match.

## Tests

- T3: no files are matched yet.
- T4: `test_set_cursor_shape` runs the original and the compiled C side by side. It uses cases where the new id equals the current one, differs from it, and sits at the 0 and 0xFF edges. The `CursorSetImage_` stub logs eax. The byte at 0x58f10 is watched. Neither the original nor the compiled C has a return value to compare.
