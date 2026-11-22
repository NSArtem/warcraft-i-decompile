/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */

/* Both drawing calls receive sign-extended coordinates in full registers. */
#define BitmapBlitAll BitmapBlitAllShortDeclaration
#define DrawText DrawTextShortDeclaration
#include "mod_3d2b0.h"
#undef DrawText
#undef BitmapBlitAll

extern void BitmapBlitAll(int x, int y, const Bitmap *src);
extern void DrawText(int x, int y, const char *s);

void CritErrDrawButtons(short selected_index, CritErrButton *buttons,
                        unsigned char normal_color, unsigned char selected_color)
{
    unsigned int index;
    CritErrButton *button;
    const char *label;
    const Bitmap *bitmap;
    int width;
    int half_width;
    unsigned char color;

    cur_font = default_font;
    index = 0;
    button = buttons;
    if (((volatile CritErrButton *)button)->bitmap == 0)
        return;

    do {
        BitmapBlitAll(*(const long *)((const char *)&button->x - 2) >> 16,
                      *(const long *)((const char *)&button->y - 2) >> 16,
                      button->bitmap);
        label = button->label;
        if (label != 0) {
            bitmap = button->bitmap;
            width = *(const short *)bitmap;
            width -= (short)TextWidth(default_font, label);
            half_width = width / 2;
            button->label_x = (short)(half_width +
                (*(const long *)((const char *)&button->x - 2) >> 16));
            button->label_y = (short)(button->y + 3);
            if ((short)index == selected_index)
                color = selected_color;
            else
                color = normal_color;
            TextSetColorBase(color);
            DrawText(*(const long *)((const char *)&button->label_x - 2) >> 16,
                     *(const long *)((const char *)&button->label_y - 2) >> 16,
                     button->label);
        }
        ++index;
        ++button;
    } while (((volatile CritErrButton *)button)->bitmap != 0);
}
