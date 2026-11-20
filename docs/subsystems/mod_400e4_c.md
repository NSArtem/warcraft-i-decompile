# mod_400e4 (area mod_400e4_c)

## Functions
| Addr | Name | Link | Status |
|---|---|---|---|
| 0x400e4 | RectCopyTransparentFlipH | `_RectCopyTransparentFlipH` | reference only (does not match) |

## Behavior
Stack-convention (cdecl-like) copy of a `width` x `height` byte rectangle. Each row is read right-to-left, starting at `src + width - 1`. Zero source bytes are transparent and skipped. After each row, `src += src_skip` and `dst += dst_skip`. The loops are do-while, so width and height must be at least 1.

Arguments: `src, dst, src_skip, dst_skip, width, height`.

## Why it is not T3
The original at 0x400e4 is a hand-written asm frame. It runs `push ebp; mov ebp,esp; push ebx; push ecx; push edx; push esi; push edi`, saves ecx and edx, and tests with `or al,al`. Watcom C emits `push esi; push edi; push ebp` with esp-relative loads, so the reference cannot match byte-for-byte.

## Tests
- T3: no files match. `assert_ref_mismatch` guards `rect_copy_transparent_flip_h_reference.c`, which must keep failing to match.
- T4: `test_rect_copy_transparent_flip_h` runs the reference against the original in the emulator. Buffers are allocated in `init_emu`. Cases vary width, height and skips with a seeded pattern that includes zero bytes. The destination buffer is watched.
