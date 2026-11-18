/* codegen-compiler: 10.0a */
/* 0x18890: blit one GRP frame of the credits art into the page bitmap. */
#include "mod_16390.h"

void OutroShowFrame(int frame, const unsigned char *grp, Bitmap *out)
{
    if (outro_is_orc != 0) {
        GrpFrameBitmap(grp, frame, out);
        LayerInvalidate(0xf);
    }
}
