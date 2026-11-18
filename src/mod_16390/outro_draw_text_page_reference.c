/* codegen-compiler: 10.0a */
/* 0x18810: draw the next screenful (14 lines) of the credits text. */
#include "mod_16390.h"

const char *OutroDrawTextPage(Bitmap *bm, const char *text)
{
    char line[0x50];
    const char *p = text;
    const char *next;
    int n;

    cur_bitmap = bm;
    BitmapClear(0);
    n = 0;
    for (;;) {
        char *q;

        if (*p == 0)
            return next;
        q = line;
        while (*p != 0 && *p != '\n') {
            if (*p != '\r')
                *q++ = *p;
            p++;
        }
        *q = 0;
        if (*p == '\n')
            p++;
        if (n == 0)
            next = p;
        DrawText(0, ((Font *)cur_font)->rows * n, line);
        n++;
        if (n >= 0xe)
            return next;
    }
}
