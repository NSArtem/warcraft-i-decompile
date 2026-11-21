/* codegen-compiler: 10.0a */
#include "graphics.h"
#include "mod_13f60.h"

/* @0x14ca8 */
void PreviewRectUpdate(void)
{
    preview_rect[0] = layers[14].x;
    preview_rect[1] = layers[14].y;
    preview_rect[4] = layers[14].w;
    preview_rect[5] = layers[14].h;
    preview_rect[2] = (short)(preview_rect[0] + preview_rect[4] - 1);
    preview_rect[3] = (short)(preview_rect[1] + preview_rect[5] - 1);
}
