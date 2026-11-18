/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DGLS.C): the map-preview hit rectangle of the 'Set Army'
 * screen.  See docs/subsystems/mod_13f60.md. */
#include "mod_13f60.h"

/* @0x14c74 */
void PreviewRectReset(void)
{
    preview_rect[0] = -1;
    preview_rect[1] = -1;
    preview_rect[2] = -1;
    preview_rect[3] = -1;
    preview_rect[4] = -1;
    preview_rect[5] = -1;
}
