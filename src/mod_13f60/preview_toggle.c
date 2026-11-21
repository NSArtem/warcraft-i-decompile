/* codegen-compiler: 10.0a */
#include "graphics.h"
#include "mod_13f60.h"

extern unsigned short preview_visible;
extern void PreviewRectReset(void);
extern void PreviewRectUpdate(void);

/* @0x14e48 */
void PreviewToggle(void)
{
    if (preview_visible != 0) {
        preview_visible = 0;
        LayerInvalidate(0xe);
        layers[14].active = 0;
        PreviewRectReset();
    } else {
        preview_visible = 1;
        layers[14].active = 1;
        LayerInvalidate(0xe);
        PreviewRectUpdate();
    }
}
