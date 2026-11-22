/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

extern void ResourceFreeBody(Bitmap *bm); /* Tail jump at 0x1ec65; EAX set at 0x1ec60. */

void MinimapPanelFree(void)
{
    ResourceFreeBody(&minimap_panel_bitmap);
}
