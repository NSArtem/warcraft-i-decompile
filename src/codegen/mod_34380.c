/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module mod_34380 (0x34380..0x34390), video library, "DBG" style: a tiny leaf that still gets
 * `push ebp; mov ebp,esp ... pop ebp` -- only -d1+ produces this in OW2. */
#include "graphics.h"

/* @0x34380 */
void SetUiColorBase(unsigned char c)
{
    ui_color_base = c;
}
