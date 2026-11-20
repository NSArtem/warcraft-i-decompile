/* codegen-compiler: 10.0a */
#include "mod_1af20_c1.h"

extern unsigned short map_scroll_x;
extern unsigned short map_scroll_y;
extern void NetSendPlaceConfirm(unsigned long cell);
extern void fn_1a388(int arg);

/* @0x1b4dc */
void PlaceBoxRelease(void *evt)
{
    short pos[2];

    pos[0] = *(short *)((char *)evt + 4) - 0x48;
    if ((unsigned short)pos[0] < 0xf0) {
        pos[1] = *(short *)((char *)evt + 6) - 0xc;
        if ((unsigned short)pos[1] < 0xb0) {
            pos[0] = pos[0] >> 4;
            pos[1] = pos[1] >> 4;
            pos[0] = pos[0] + map_scroll_x;
            pos[1] = pos[1] + map_scroll_y;
            NetSendPlaceConfirm(*(unsigned long *)pos);
            fn_1a388(0);
        }
    }
}
