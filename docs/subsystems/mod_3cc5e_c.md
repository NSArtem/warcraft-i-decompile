# mod_3cc5e_c: rectangle copy blitters

Two hand-written asm routines (cdecl, ebp frame, `[ebp+N]` stack args; they save and restore ebx/ecx/edx/esi/edi/ebp) that copy a width x height byte rectangle with separate source and destination row skips.

| Addr | Name | Prototype | Notes |
|---|---|---|---|
| 0x3cc5e | RectCopy | `void RectCopy(src, dst, src_skip, dst_skip, width, height)` | Copies words (`shr ecx,1`). A carry (odd width) copies one trailing byte. Then it adds the skips and loops on height. |
| 0x3ccb2 | RectCopyTransparent | same | Copies bytes. Source bytes equal to 0 are skipped (`or al,al`) and the destination is left untouched. |

## Data layout
No globals. Skips are added after each row. Width and height must be at least 1, because the loops are do-while.

## T3 / T4
- No T3 (byte-exact) files yet. The original is hand-written asm, so the C references cannot reproduce the ebp frame or the carry branch. `assert_ref_mismatch` guards both reference files, `rect_copy_reference.c` and `rect_copy_transparent_reference.c`.
- T4 difftests (`tests/test_mod_3cc5e_c.py`) run the compiled reference against the original in the emulator. They use `cdecl=True`, no output registers, and a watched destination buffer. The buffers are allocated in `init_emu`. They cover odd and even widths, several heights and nonzero skips. The transparent test also uses sources with many zero bytes.
