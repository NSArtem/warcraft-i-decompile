/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned short preview_visible;
extern short dat_5ab8c;
extern void PreviewRectReset(void);
extern void PreviewRectUpdate(void);
extern void LayerInvalidate(unsigned char id);

/* @0x14e48 */
void PreviewToggle(void)
{
    if (preview_visible != 0) {
        preview_visible = 0;
        LayerInvalidate(0xe);
        dat_5ab8c = 0;
        PreviewRectReset();
    } else {
        preview_visible = 1;
        dat_5ab8c = 1;
        LayerInvalidate(0xe);
        PreviewRectUpdate();
    }
}
