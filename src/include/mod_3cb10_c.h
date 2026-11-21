#ifndef MOD_3CB10_C_H
#define MOD_3CB10_C_H

typedef struct Rect {
    short x;
    short y;
    short x2;
    short y2;
    short w;
    short h;
} Rect;

int __cdecl RectClip(Rect *src, Rect *dst);

#endif
