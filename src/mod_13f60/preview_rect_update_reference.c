/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern short dat_5ab8e;
extern short dat_5ab90;
extern short dat_5ab92;
extern short dat_5ab94;

/* @0x14ca8 */
void PreviewRectUpdate(void)
{
    preview_rect[0] = dat_5ab8e;
    preview_rect[1] = dat_5ab90;
    preview_rect[4] = dat_5ab92;
    preview_rect[5] = dat_5ab94;
    preview_rect[2] = (short)(preview_rect[0] + preview_rect[4] - 1);
    preview_rect[3] = (short)(preview_rect[1] + preview_rect[5] - 1);
}
