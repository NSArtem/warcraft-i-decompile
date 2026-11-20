/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
#include "mod_3d260_c.h"

extern Bitmap *cur_bitmap;
extern Font *default_font;
extern Font *cur_font;
void DrawText(short x, short y, const char *s);
void TextSetColorBase(unsigned char c);
int TextWidth(const Font *font, const char *s);

void DrawTextCentered(short y, const char *s, unsigned char color)
{
    short w;

    cur_font = default_font;
    TextSetColorBase(color);
    w = (short)TextWidth(default_font, s);
    DrawText((short)((cur_bitmap->width - w) / 2), y, s);
}
