#ifndef MOD_1C020_H
#define MOD_1C020_H

#include "war.h"

struct Bitmap;
struct Font;
struct Rect;

extern char *wrapped_text_lines[100]; /* 0x596a0 */
extern char *wrap_text_buffer;        /* 0x59850 */
extern struct Font *cur_font;        /* 0x5acf0 */

/* Use the default Watcom register convention selected by -4r. */
void WrapTextInPlace(int max_width);
void BlitTransparentInTextBand(short x, short y, const struct Bitmap *src, struct Rect *src_rect);
void FreeWrapTextBuffer(void);

#endif
