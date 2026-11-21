# mod_3cb10 (area mod_3cb10_c)

## Functions

| Function | Conv | Status |
|----------|------|--------|
| RectClip | cdecl | T3 byte-match (`src/mod_3cb10/rect_clip.c`) |

## Data layouts

`Rect` (12 bytes, six shorts): `x`, `y`, `x2`, `y2`, `w`, `h`. Declared in `src/include/mod_3cb10_c.h`.

`int __cdecl RectClip(Rect *src, Rect *dst)` clips a rectangle.

## Testing notes

- T3: `rect_clip.c` is compiled with Watcom 10.0a and must match the original bytes. `tests/test_mod_3cb10_c.py` enforces this.
- T4: there are no reference (non-matching) functions in this module, so there are no differential tests. The near-miss guard list is empty.
