/* codegen-compiler: 10.0a */
#include "mod_2b400_c.h"
#include <stdio.h>
#include <string.h>

typedef struct Bitmap Bitmap;
typedef struct Font Font;

extern unsigned short demo_mode;
extern const char *status_text;
extern Bitmap *cur_bitmap;
extern Font *cur_font;
extern unsigned char score_font[8];
extern const char dat_57df8[];
extern unsigned char dat_5a370[];
extern unsigned char dat_5a378[];
extern char dat_5a380[];
extern unsigned char dat_5a408[];
extern unsigned char dat_5a410[];
extern unsigned short status_help_gold;
extern unsigned short status_help_lumber;

extern void DrawText(short x, short y, const char *s);
extern void TextSetColorBase(unsigned char c);
extern void BitmapBlitTransparentAll(short x, short y, const Bitmap *src);
extern void BitmapBlitAll(short x, short y, const Bitmap *src);
extern void DirtyRectAddLayer(unsigned char id);

void StatusBarDrawText(const char *text, unsigned char show_costs)
{
    char buf[12];
    Bitmap *saved_bitmap;

    if (demo_mode != 0)
        return;
    if (text == 0)
        text = status_text;
    if (text == 0) {
        text = buf;
        buf[0] = '\0';
    }
    if (strcmp(text, dat_5a380) == 0)
        return;

    strcpy(dat_5a380, text);
    saved_bitmap = cur_bitmap;
    cur_bitmap = (Bitmap *)dat_5a408;
    BitmapBlitAll(0, 0, (const Bitmap *)dat_5a378);
    cur_bitmap = saved_bitmap;

    if (*text != '\0') {
        cur_bitmap = (Bitmap *)dat_5a408;
        cur_font = (Font *)score_font;
        TextSetColorBase(0xf3);
        DrawText(1, 5, text);
        if (show_costs != 0) {
            BitmapBlitTransparentAll(0xa3, 3, (const Bitmap *)dat_5a410);
            sprintf(buf, dat_57df8, (int)status_help_lumber);
            DrawText(0xb3, 5, buf);
            BitmapBlitTransparentAll(0xc8, 5, (const Bitmap *)dat_5a370);
            sprintf(buf, dat_57df8, (int)status_help_gold);
            DrawText(0xda, 5, buf);
        }
    }
    DirtyRectAddLayer(0xf);
}
