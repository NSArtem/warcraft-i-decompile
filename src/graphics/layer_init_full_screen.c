/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_32f10 (0x32f4c..0x32fb0), DBG style. */
#include "graphics.h"

/* @0x32f4c */
void LayerInitFullScreen(unsigned char id)
{
    layers[id].x = 0;
    layers[id].y = 0;
    layers[id].w = 320;
    layers[id].h = 200;
    layers[id].data = 0;
    layers[id].callback = LayerFillCallback;
    layers[id].active = 1;
}
