/* codegen-compiler: 10.0a */
#include "mod_3ac10_c.h"

typedef struct Bitmap {
    short width;
    short height;
    unsigned char *data;
} Bitmap;

extern Bitmap *cur_bitmap;
extern unsigned char draw_color;

void HLine(short x, unsigned short y, unsigned short len)
{
    unsigned char *p;
    unsigned short i;
    volatile int yy;

    yy = y;
    p = cur_bitmap->data + (cur_bitmap->width * yy + x);
    for (i = 0; i < len; i++) {
        *p++ = draw_color;
    }
}
