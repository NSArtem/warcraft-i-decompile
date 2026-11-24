/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short dat_5ab8c;
extern unsigned short dat_5ab9e;
extern void *cur_bitmap;
extern void *cur_font;
extern char alt_font[];
extern const char str_your[];
extern const char str_enemy[];
extern char *strcpy(char *dst, const char *src);
extern char *strcat(char *dst, const char *src);
extern void DrawText(short x, short y, const char *s);
extern void LayerInvalidate(unsigned char id);
extern void BitmapClear(unsigned char color);
extern void TextSetColorBase(unsigned char c);
extern int TextWidth(const void *font, const char *s);

/* @0x15244 */
void ControlTitleDraw(void)
{
    char buf[0x40];
    short w;

    if (dat_516ae == 0 || dat_51658.body == 0) {
        dat_5ab8c = 0;
        return;
    }
    cur_bitmap = &dat_51658;
    BitmapClear(0);
    if (screen_mode != 0) {
        strcpy(buf, str_your);
    } else {
        strcpy(buf, str_enemy);
    }
    strcat(buf, str_system_has_control);
    if (screen_mode == 0) {
        strcat(buf, str_ctrl_esc_disconnect);
    }
    cur_font = alt_font;
    TextSetColorBase(0xf3);
    w = (short)TextWidth(cur_font, buf);
    DrawText((short)((0x140 - w) / 2), 0, buf);
    dat_5ab9e = 1;
    LayerInvalidate(0xf);
}
