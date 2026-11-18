/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_33110 (0x33110..0x33150), OPT-style leaf (no ebp frame). */
#include "graphics.h"

/* @0x33110 */
void GrpFrameBitmap(const unsigned char *grp, unsigned char frame, Bitmap *out)
{
    const unsigned char *e = grp + 4 + frame * 8;
    out->w = e[2];
    out->h = e[3];
    out->data = (unsigned char *)grp + *(const unsigned int *)(e + 4);
}
