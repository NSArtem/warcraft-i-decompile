# mod_1c020_c: credit screen draw helpers

Four near-identical functions in mod_1c020 (0x1c1dc..0x1c2bc). Each draws one credit-screen sprite layer.

| Addr | Name | Layer id | GRP pointer (data) | Bitmap out (data) |
|---|---|---|---|---|
| 0x1c1dc | CreditDrawA | 14 | dat_59860 | dat_59838 |
| 0x1c214 | CreditDrawB | 15 | dat_59858 | dat_59840 |
| 0x1c24c | CreditDrawC | 16 | dat_5985c | dat_59848 |
| 0x1c284 | CreditDrawD | 17 | dat_59854 | dat_59830 |

Each one runs:

1. `LayerInvalidate(id)`.
2. `GrpFrameBitmap(grp, (unsigned char)frame, &bitmap)`.
3. `LayerInvalidate(id)`.
4. `ScreenUpdate()`.

## Data layouts
- GRP pointers (0x59854, 0x59858, 0x5985c, 0x59860) are dwords that point to loaded GRP data.
- Bitmap slots (0x59830, 0x59838, 0x59840, 0x59848) are 12-byte descriptors, each filled in by `GrpFrameBitmap`.

## Status
The reference C files are not T3 matches. The disassembly diff at the `mov eax, [grp_ptr]` instruction (for example 0x1c1f0) shows an unresolved relocation. Every other instruction is identical. The fix is to add `[[data]]` entries for the eight addresses above in Stage 1. The C does not need to change.

## T3/T4 notes
- `assert_t3_matches` has an empty file list for now.
- `assert_ref_mismatch` guards the four reference files.
- The T4 difftests stub `LayerInvalidate`, `GrpFrameBitmap` and `ScreenUpdate`. Stub addresses are looked up from the symbol DB by link name.
- The tests log eax for `LayerInvalidate`, and eax, edx and ebx for `GrpFrameBitmap`. `ScreenUpdate` is logged with no registers.
- Inputs are frame values 0, 1, 7, 0x7F and 0xFF, each with two different GRP pointer values.
- The functions are void, so `out_regs` is empty.
