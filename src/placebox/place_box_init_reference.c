/* codegen-compiler: 10.0a */
#include "mod_20c30.h"
#include "war.h"

extern void BitmapBlitTransparent();    /* 0x325d0 */
extern void *memset(void *dst, int c, unsigned n);

/* @0x224e0 */
void PlaceBoxInit(void)
{
    char *l = (char *)&layers[PLACE_LAYER];

    ((void **)&place_box_bm)[1] = GdsAlloc(0x900);
    *(unsigned short *)(l + 2) = 0;
    *(unsigned short *)(l + 4) = 0;
    *(unsigned short *)(l + 6) = 0;
    *(unsigned short *)(l + 8) = 0;
    *(void **)(l + 10) = &place_box_bm;
    *(void (**)())(l + 14) = BitmapBlitTransparent;
    memset(place_active, 0, 2);
}
