# Graphics subsystem (war.exe 1.22h)

Evidence is in `analysis/symbols/graphics.toml`; this page is the overview.

## Video
* `VidSetMode13` (0x31d40): `int 10h ah=0Fh` saves the mode, `int 10h ax=13h`, then
  `vga_bm = {320,200,0xa0000}`; fatal error "VGA required" otherwise. `VidRestoreTextMode`
  (0x31d94) is registered as exit handler.
* All drawing goes to a 64000-byte back buffer `backbuf_bm` (0x5a870, allocated by 0x3b360);
  `VidPresentRect` (0x3d560) copies the dirty rectangle to 0xa0000 with dword moves.
* Palette: `VgaSetPaletteRange` (0x331be, ports 0x3c8/0x3c9, 6-bit values), `PaletteSet` (0x33150)
  keeps `palette_base`/`palette_cur`, `PaletteLerp` + `PaletteFadeIn/Out` implement fades,
  `palette_cycles` (16 x 12 bytes, 0x628a0) drive colour cycling updated once per frame.

## Library conventions
`Bitmap {short w,h; u8 *data}`, `Rect {x1,y1,x2,y2,w,h}`; `cur_bitmap` (0x55438) is the implicit
destination; `draw_color` (0x5ad30). Primitives: HLine/VLine/Line/FillRect/RectOutline,
BitmapBlit(+Transparent, +TransparentFlipH), RectClip. Colour 0 is transparent in sprite blits.

## Layers and the cursor
32 screen layers (`layers`, 0x5aa90, 18 bytes each: active,x,y,w,h,data,callback). `ScreenUpdate`
(0x321e8) draws active layers 31..0 into the back buffer for the accumulated dirty rectangle, saves
the background under the cursor (layer 0, drawn with `BitmapBlitTransparent`), presents, then restores.
Cursor image = DATA.WAR resource 0x109 (2 hotspot words + Bitmap).

## Text
Font resource (e.g. 0xd7): byte0 first char, byte1 bytes per glyph row, byte2 rows, byte3 ?,
then 3-byte glyph records {u16 offset, u8 width} and 2 bits-per-pixel glyph data (4 px per byte,
low bits first, 0 transparent, 1..3 -> `TextSetColorBase` colours). `DrawText` understands `\n`, `\t`,
`@1`, `@2` (colour sets) and `@@`. Verified against the real font in `tests/test_graphics_text.py`.

## Map viewport
240x176 px at (72,12) of the back buffer. Terrain comes from a 64 KB wrap-around cache built from
8x8 minitiles (tile word: index<<5 | vflip<<1 | hflip); `FogDrawViewport` overlays transparent
minitiles. Unit sprites are GRP frames (`GrpFrameInfo`: 4-byte header, 8-byte frame entries
xoff,yoff,w,h,u32 offset) blitted by the facing-indexed table at 0x55288.

## Open questions
* Exact meaning of `PaletteFadeOut`'s final `PaletteSet` (restores the palette after fading).
* Fog-of-war naming (0x1af90) is inferred from draw order only.
* The library is compiled by an older Watcom than OW2; OW2 does not reproduce its code bytes
  (tried -ot, -od, -of+), so no T3 matches exist for this area.
