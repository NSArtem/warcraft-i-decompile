/*
 * Graphics / input declarations (see analysis/symbols/graphics.toml and
 * input.toml for the evidence behind every name and address).
 */
#ifndef GRAPHICS_H
#define GRAPHICS_H

/* 8-byte bitmap descriptor used by the whole drawing library. */
typedef struct Bitmap {
    short w;                    /* +0 */
    short h;                    /* +2 */
    unsigned char *data;        /* +4, w*h bytes, row stride == w */
} Bitmap;

/* 12-byte rectangle: inclusive corners plus size. */
typedef struct Rect {
    short x1, y1, x2, y2;       /* +0..+6 */
    short w, h;                 /* +8, +0xa */
} Rect;

extern Bitmap *cur_bitmap;              /* 0x55438 */
extern unsigned char draw_color;        /* 0x5ad30 */
extern unsigned char ui_color_base;     /* 0x62880 */
extern short dirty_x1, dirty_y1, dirty_x2, dirty_y2;   /* 0x5acd0.. */
extern short dirty_w, dirty_h;          /* 0x5acd8, 0x5acda */

void HLine(short x, unsigned short y, unsigned short len);        /* 0x3ac10 */
void VLine(short x, unsigned short y, unsigned short len);        /* 0x32970 */
void BitmapClear(unsigned char color);                            /* 0x31fc0 */
void FillRect(short x, short y, unsigned short w, unsigned short h); /* 0x326a0 */
void DirtyRectAddBox(short x1, short y1, short x2, short y2);     /* 0x33a30 */
void DirtyRectUnion(const short *r);                              /* 0x328c0 */

#endif
