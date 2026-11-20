# mod_3abb0_c — GRP frame info

## Functions

| Addr | Name | Status |
|---|---|---|
| 0x3abb0 | `GrpFrameInfo_` | Reference only (`grp_frame_info_reference.c`); near miss |

## Behaviour

`GrpFrameInfo(grp, frame, out, xoff, yoff, maxw, maxh)` (watcall: grp=eax, frame=edx, out=ebx, xoff=ecx, remaining three on the stack, callee-popped).

GRP layout:
- Bytes 2 and 3 of the header: max width and max height.
- The frame table starts at offset 4, with 8-byte entries.
- Entry bytes 0 and 1: x and y offsets.
- Entry bytes 2 and 3: width and height.
- Entry bytes 4–7: dword offset of the pixel data from the start of the GRP.
- The frame index is masked with 0xff.

The `Bitmap` output is `{short w; short h; unsigned char *data}`, where data is `grp + offset`.

## Notes

- T3: the reference is not matched. The blocker is at 0x3abc4, where the original uses `xor dh,dh` and the build emits `movzx dx, byte ptr [eax]` (+0x14). `assert_ref_mismatch` guards it so the file keeps failing to match.
- T4: `test_grp_frame_info` runs the reference C against the original in the emulator. It uses a random GRP buffer (allocated in `init_emu`) and frames 0, 1, 2, 127, 255, 0x100, 0x1ff and a high-bits value to check the mask. It watches the Bitmap and the four shorts. There are no callees, so no stubs.
