# mod_33b00_c: BitmapBlitAll

| Addr | Name | Notes |
|---|---|---|
| 0x33b00 | BitmapBlitAll(short x, short y, const Bitmap *src) | Builds a local rect {0,0,w-1,h-1,w,h} from the bitmap header, then calls BitmapBlit(x, y, src, &rect). |

## Data layouts
- Bitmap: `short width; short height;`
- Rect: `short left, top, right, bottom;`
- Local BlitRect (12 bytes on stack): Rect followed by `w`, `h`.

## T3
No T3-matching files yet. The reference file is `src/mod_33b00/bitmap_blit_all_reference.c`. Its blocker: the compiled output has an extra `mov eax, dword ptr [ebp-4]` at +0x1b (a struct/op difference). `assert_ref_mismatch` guards that it still fails to match.

## T4
`test_bitmap_blit_all` runs the compiled reference against 0x33b00 in the emulator. The bitmap header is allocated in `init_emu`. A `BitmapBlit` stub logs eax, edx, ebx and ecx, which holds x, y, src and the rect pointer. Stack-pointer values are not logged. The rect contents are not watched, so they aren't compared.
