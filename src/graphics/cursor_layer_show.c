/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_32940 (0x32940..0x32970), DBG style. */
#include "graphics.h"

/* @0x32940 */
void CursorLayerShow(void)
{
    layers[cursor_layer_id].active = 1;
    LayerInvalidate(cursor_layer_id);
}
