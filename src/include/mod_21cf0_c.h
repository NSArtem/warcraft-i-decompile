#ifndef MOD_21CF0_C_H
#define MOD_21CF0_C_H

typedef struct Bitmap { short w; short h; void *data; } Bitmap;
typedef struct Rect { short x; short y; short r4; short r6; short w; short h; } Rect;
typedef struct Layer { short active; short x; short y; short w; short h; Bitmap *bm; void (*blit)(); } Layer;

#endif
