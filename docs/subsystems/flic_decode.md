# flic_decode (war.exe 0x19020..0x19470)

FLIC movie decoder object. Public entry points are called from the playflic object (`playflic.h`). Evidence is the disassembly at the listed addresses and the reference-file blockers.

## Functions

| Addr | Name | Notes |
|------|------|-------|
| 0x19020 | fn_19020 | Reads n bytes into a buffer. FlicOpen calls it with (0x59440, 0x80) to read the header. |
| 0x19048 | fn_19048 | Seek (offset, whence). Rewind and restart call it with whence 0. |
| 0x192f0 | fn_192f0 | Decodes the next frame. Called by FlicRewind, FlicRestart and FlicNextFrame. |
| 0x1933c | FlicOpen | Stores chunk, image, first and last. Sets palette_on to 1 and frames to 0. Opens the file with FindDataFile. Reads the header and checks it. |
| 0x193dc | FlicClose | If the open flag is set: clears it and calls FileClose on the file handle. |
| 0x193fc | FlicRewind | Returns 0 if not open. Otherwise seeks to the offset at 0x59490, then decodes. |
| 0x19420 | FlicRestart | Same as FlicRewind, but the offset is at 0x59494. |
| 0x19444 | FlicPaletteOff | T3 matched (`flic_palette_off.c`). |
| 0x19450 | FlicNextFrame | Returns 0 if not open. Otherwise returns the result of fn_192f0. |

## Data

- 0x517c8: open flag, word. FlicOpen stores the validity result in it.
- 0x594d0: first. 0x594d4: image. 0x594d8: chunk. 0x594dc: last. 0x594e0: file handle.
- 0x59440: 0x80-byte header buffer.
  - +4 = magic, expected 0xaf12.
  - +0xc = 8.
  - +0xe = 3.
  - +0x14 = 0.
- 0x59446: frames. 0x59448: width. 0x5944a: height.
- 0x59490: rewind offset. 0x59494: restart offset.
- 0x594ea: palette-on flag.

## Testing

- T3: `flic_palette_off.c` must still match.
- The five reference files are near-miss guards. Each currently differs only by raw-address versus symbolic globals (`dat_*` placeholders). `assert_ref_mismatch` keeps them from silently matching.
- T4 tests in `tests/test_flic_decode.py` compare the original against the compiled reference with `run_spec`. Callees are stubbed and their register arguments are logged.
  - FlicOpen uses a stack argument for `last`. It covers every header-field mismatch plus the find and read failure paths.
  - The FindDataFile and FileClose stub addresses are looked up in the symbol DB at test time. A test skips if the symbol is missing.
