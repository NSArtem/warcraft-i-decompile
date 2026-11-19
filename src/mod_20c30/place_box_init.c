/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxInit (0x224e0): allocate the 48x48 placement-box scratch bitmap,
 * register it as layer 21 and clear both players' "placing" flags.  Called
 * from the scenario/game start fn_195ac. */
#include "mod_20c30.h"

/* The original clears the two place_active bytes through the runtime
 * __STOSB (0x34390) with its asm argument convention (dst=eax, val=edx,
 * count=ecx); a normal C declaration or the compiler's __STOSB builtin puts
 * the count in ebx and calls __STOSB_, so the convention is spelled out. */
void fit_stosb(unsigned char *dst, unsigned char val, unsigned count);
#pragma aux fit_stosb "__STOSB" parm [eax] [edx] [ecx] modify [eax edx ecx];

/* @0x224e0 */
void PlaceBoxInit(void)
{
    place_box_bm.data = GdsAlloc(0x900);
    layers[PLACE_LAYER].x = 0;
    layers[PLACE_LAYER].y = 0;
    layers[PLACE_LAYER].w = 0;
    layers[PLACE_LAYER].h = 0;
    layers[PLACE_LAYER].data = &place_box_bm;
    layers[PLACE_LAYER].callback = (void (*)())BitmapBlitTransparent;
    fit_stosb((unsigned char *)place_active, 0, 2);
}
