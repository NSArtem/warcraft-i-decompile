/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_31f70 (0x31f70..0x31f96), DBG style. */
#include "graphics.h"

/* @0x31f70 */
void LayerInvalidate(unsigned char id)
{
    if (layers[id].active)
        DirtyRectAddLayer(id);
}
