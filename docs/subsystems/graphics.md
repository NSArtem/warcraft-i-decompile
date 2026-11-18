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

## Blitter conventions (0x32410..0x32740, 0x3cb10..0x3ccb2, 0x400e4)

`BitmapBlit` / `BitmapBlitTransparent` take `(x, y, src, srcrect)`; `x,y` is the
*screen* position of the source rectangle's top-left corner and `srcrect` is in
the source bitmap's own coordinates.  Both build a second `Rect` on the stack as
the destination bounds - `x1 = x, y1 = y, w = cur_bitmap->w, h = cur_bitmap->h`
(the `x2/y2` fields are left uninitialised; `RectClip` overwrites them, which is
why a "fix" that sets them changes nothing) - and call `RectClip(src, dst)`.
`RectClip` (cdecl, 0x3cb10) rejects a rectangle that is entirely outside
(`src->x1 >= src->w || src->y1 >= src->h || src->x2 < 0 || src->y2 < 0`), clamps
`src` to its own bitmap, moves `dst->x1/y1` by the same amount, clamps the
result to `dst->w/h` and recomputes `src->w/h`; it returns 1 when nothing is
visible (the blitters then return without drawing).

The actual copy is one of the cdecl helpers
`RectCopy` 0x3cc5e / `RectCopyTransparent` 0x3ccb2 / `RectCopyTransparentFlipH`
0x400e4 with `(src, dst, src->w - w, dst->w - w, w, h)`: the skip values advance
the pointers by whole rows, so a row is `w` bytes.  The transparent variant
skips source bytes equal to 0 (colour 0), the FlipH one reads each source row
backwards (mirrored sprites, facings 5..7 of the 8-entry blitter table at
0x55288).  `BitmapBlitTransparentAll` 0x326f0 just fills a Rect `{0,0,w-1,h-1,w,h}`
from the source bitmap and calls the transparent blitter, and `FillRect`
0x326a0 is `h` calls of `HLine(x, y+i, w)`.

## Layer / dirty-rectangle model (0x31f70, 0x321e8, 0x328c0, 0x33aa0, 0x349f0)

32 layers of 18 bytes at 0x5aa90 (`Layer {u16 active; short x,y,w,h; void *data;
void (*callback)(short,short,Rect*,void*)}`).  Layer 0 is the mouse cursor
(`cursor_layer_id` 0x5aa78 is never written, so it is always 0; init 0x1dbca
sets layer 0 up with `x = -hot_x`, `y = -hot_y`, `data = &cursor_bitmap` (from
the *source* descriptor's bitmap at 0x5aa70) and `callback = BitmapBlitTransparent`), layer 2 is the full-screen background
(`LayerInitFullScreen(2)`, callback `LayerFillCallback` = `draw_color = 0` plus a
`FillRect` over the dirty rectangle; `PaletteFadeIn/Out` toggle its `active`
bit - the "fade flag" 0x5aab4 in older notes *is* `layers[2].active`, and
0x5aab6 is its `x` field).

Drawing is deferred through the dirty-rectangle accumulator 0x5acd0
(`dirty_x1,y1,x2,y2,w,h`): `DirtyRectAddBox` (T3, `src/codegen/mod_33a30.c`) and
`DirtyRectUnion` grow it, `LayerInvalidate` adds a layer's rectangle when the
layer is active.  `ScreenUpdate` clips the accumulator to 320x200 (the guards
read `dirty_x1 >= 320 || dirty_y1 >= 200`, clamp `dirty_x2` to 319 and
`dirty_y2` to 199, and bail out on `dirty_w/h < 1` - the original's own tests,
kept verbatim), takes `cur_bitmap = &backbuf_bm`, and walks i = 31..0:
for every active layer it builds `r = {dirty_x1 - layer.x, dirty_y1 - layer.y,
..., dirty_w, dirty_h}`, calls `CursorSaveUnder()` before layer 0 and then
`layer->callback(dirty_x1, dirty_y1, &r, layer->data)` (so the callback draws at
the screen position and reads the shifted rectangle from its own bitmap), then
`DirtyRectAlignAndPresent` (rounds x1/down and w/up to multiples of 4 and calls
`VidPresentRect` 0x3d560), `CursorRestoreUnder()` when layer 0 is active, and
finally resets the accumulator to `{0x7fff,0x7fff,-0x8000,-0x8000,0,0}` and
restores `cur_bitmap`.

## Cursor save-under (0x320f0, 0x32188, 0x330a0, 0x317b0)

`cursor_save_bm` 0x5ad10 is a 16x16 bitmap whose data comes from
`VidAllocBackbuffer` (`GdsAlloc(0x100)`); `cursor_save_rect` 0x5ad18 is the
rectangle beside it.  `CursorSaveUnder` copies the cursor layer's `x,y,w,h` into
both, computes `x2/y2`, switches `cur_bitmap` to `cursor_save_bm`, calls
`BitmapBlit(0,0,&backbuf_bm,&cursor_save_rect)` and restores `cur_bitmap`
(this is the one function of the group that matches byte for byte, see below).
`CursorRestoreUnder` only rewrites `x1,y1,x2,y2` (0,0,w-1,h-1) - it relies on
the `w/h` fields left by `CursorSaveUnder` - and blits `cursor_save_bm` back to
`(layers[0].x, layers[0].y)`.  `CursorMoveTo` invalidates, sets
`layers[0].x/y = x/y - hotspot`, invalidates again and stores `mouse_x/mouse_y`.
`CursorSetImage` copies the 12-byte descriptor (hotspot words + Bitmap) into
`cursor_hotspot_x/y` + `cursor_bitmap` at 0x5aa60..0x5aa6b, points layer 0's
`data` at the *descriptor's* bitmap (`desc+4`, not `&cursor_bitmap`), copies w/h
into the layer, and calls
`CursorMoveTo(mouse_raw_x, mouse_raw_y)` when the raw mouse position disagrees
with `layer position + hotspot`; it invalidates the layer on both sides.

## Text metrics and state (0x31dcc, 0x32060, 0x3ca30)

`DrawText` first copies the font header into a scratch block that the glyph
routine shares with it: `cur_font` 0x5acf0 (pointer), `text_dest` 0x5acf4
(current destination, advanced by the glyph routine), `text_max_x` 0x5acf8
(`cur_bitmap->w - bytes_per_row*4`, the last column a glyph may start at),
`text_glyph_table` 0x5acfa, `text_glyph_bytes` 0x5acfe (`bytes_per_row*rows`),
`text_bytes_per_row` 0x5ad00, `text_rows` 0x5ad01, `text_first_char` 0x5ad06;
`text_colors[4]` 0x5ad02 and `text_glyph_fn` 0x5ad07 sit inside the same block
and `text_esc_colors[2]` 0x5ad0b right after it.  Per character: `\n` advances
`y` by `rows + text_line_gap` (0x5543e) and restores the starting `x`, `\t`
rounds `x` up to the next multiple of `text_tab_width` (0x5543c) measured from
the starting `x` (and marks the line as moved), `@1`/`@2` reload
`text_colors[1..3]` from `text_esc_colors[0]/[1]` as `c, c+1, c+2`, `@@` draws a
literal `@`, everything else calls `text_glyph_fn(ch)` and adds its returned
width to `x`.  The destination pointer is only recomputed when `x`/`y` changed.
`TextWidth` returns the *widest line*: it sums the glyph widths (byte 2 of the
3-byte record at `table + (ch - first)*3`), resets on `\n`, adds
`text_tab_width` on `\t` and skips the `@1`/`@2`/`@@` escapes exactly like
`DrawText`.

## Codegen status of this library (2026-11-19)

The area is not one compiler configuration.  With `-s -ot -ol -4r -d1+ -zp2`
and Watcom 10.0a the following match byte for byte (`wc1.match`, one function
per file unless noted):

| Function | Address | File |
|---|---|---|
| PaletteCycleEnable | 0x31920 | `src/graphics/palette_cycle_enable.c` (cdecl) |
| VidSetMode13 / VidRestoreTextMode | 0x31d40 / 0x31d94 | `src/graphics/vid_mode.c` |
| LayerInvalidate | 0x31f70 | `src/graphics/layer_invalidate.c` |
| CursorSaveUnder | 0x320f0 | `src/graphics/cursor_save_under.c` |
| DirtyRectUnion | 0x328c0 | `src/graphics/dirty_rect_union.c` |
| CursorLayerShow | 0x32940 | `src/graphics/cursor_layer_show.c` |
| PaletteFadeIn | 0x32e80 | `src/graphics/palette_fade_in.c` |
| LayerInitFullScreen | 0x32f4c | `src/graphics/layer_init_full_screen.c` |
| PaletteFadeOut | 0x32fb0 | `src/graphics/palette_fade_out.c` |
| GrpFrameBitmap | 0x33110 | `src/graphics/grp_frame_bitmap.c` |
| KeyStateClear/KeyModClear/KeyModSet/KeyModToggle | 0x32a80.. | `src/graphics/key_state.c` (`-s -od -4r -zp2`, entries in input.toml) |
| MouseSetRange | 0x33040 | `src/graphics/mouse_set_range.c` (entry in input.toml) |

`EvtProcess` (0x32b40, the keyboard translator of mod_32a80) is reference C in
`src/graphics/evt_process.c` - its TOML entry lives in `analysis/symbols/input.toml`
(input area), which still needs `ref = "src/graphics/evt_process.c"`,
`ref_verified_by = "difftest: tests/test_graphics_lib.py::test_t4_evt_process"`
and a `t3_blocker`; the behaviour is difftested here.

`VidSetMode13` shows how the BIOS calls are reproduced: `#pragma aux` bodies
(`mov ah,0x0f; int 0x10` / `int 0x10` with `parm [ax]`) plus ordinary C.
The rest of the range is reference C (`ref = ...` in `analysis/symbols/graphics.toml`)
verified against the original by `tests/test_graphics_lib.py`; its T3 blockers
are word sign-extension idioms (`mov reg,dword [addr-2]; sar reg,0x10` instead
of `movsx`), inline-asm loop frames and register-allocation order.  These are
properties of the *compiler version* that built these objects, not of the
flags: the same 10.0a reproduces neighbouring objects exactly, so the video
library was probably built by an older Watcom (9.5/10.0 GA) - the same
conclusion the module layout suggests for the rest of the library.

## Open questions
* Exact meaning of `PaletteFadeOut`'s final `PaletteSet` (restores the palette after fading).
* Fog-of-war naming (0x1af90) is inferred from draw order only.
* Which Watcom built the DBG objects of this library: `-d1+` reproduces some
  functions exactly and others differ only in the word sign-extension idiom /
  register allocation, suggesting 10.0 GA (or 9.5) rather than 10.0a for those
  objects (docs/subsystems/compiler.md rules out 10.0 GA for *game* code).
* `CursorSaveUnder` assumes the cursor layer is at most 16x16 (the save buffer
  is 0x100 bytes); a bigger cursor image would overflow it.  Resource 0x109 is
  16x16, so this is not reachable in v1.22h.
* `PaletteCycleStepList` increments `palette_cycles[id].current` once before the
  loop and then only in a register - the advanced index is *not* written back,
  so consecutive calls start from the same +1 position (an original bug, kept
  in the reference C).
* `memmove` (0x3cefc) moves DS into ES before its `rep movsd`, so Unicorn cannot
  run it; the tests install a flat model (like the built-in `memcpy` stub).
  A built-in `memmove` stub in `wc1.emu` would save each test that needs it.
