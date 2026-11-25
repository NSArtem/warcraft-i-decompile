/* codegen-compiler: 10.0a */
#include "mod_2b400_c.h"

typedef struct Bitmap Bitmap;
typedef struct Font Font;

extern unsigned short demo_mode;
extern Bitmap *cur_bitmap;
extern Font *cur_font;
extern unsigned char score_font[8];
extern unsigned long dat_50060[5];
extern unsigned long dat_50074[5];
extern const char dat_57dfc[];
extern const char dat_57e0c[];
extern unsigned char dat_5a360[];
extern unsigned char dat_5a368[];
extern int dat_5a418;
extern int dat_5a41c;

extern void DrawAnimatedResourceCounter(const char *format, short x, short y, int *displayed_count, int target_count);
extern void TextSetColorBase(unsigned char c);
extern void BitmapBlitAll(short x, short y, const Bitmap *src);
extern void DirtyRectAddLayer(unsigned char id);

void ResourceCountersUpdate(void)
{
    if (demo_mode == 0 &&
        ((unsigned long)dat_5a418 != dat_50060[0] ||
         (unsigned long)dat_5a41c != dat_50074[0])) {
        Bitmap *dest = (Bitmap *)dat_5a360;

        cur_bitmap = dest;
        BitmapBlitAll(0, 0, (const Bitmap *)dat_5a368);
        cur_bitmap = dest;
        cur_font = (Font *)score_font;
        TextSetColorBase(0xf3);
        DrawAnimatedResourceCounter(dat_57dfc, 0x17, 2, &dat_5a418, (int)dat_50060[0]);
        DrawAnimatedResourceCounter(dat_57e0c, 0x87, 2, &dat_5a41c, (int)dat_50074[0]);
        DirtyRectAddLayer(0xe);
    }
}
