#ifndef MOD_33B00_C_H
#define MOD_33B00_C_H

typedef struct Bitmap { short width; short height; } Bitmap;
typedef struct Rect { short left; short top; short right; short bottom; } Rect;
void BitmapBlitAll(short x, short y, const Bitmap *src);

#endif
