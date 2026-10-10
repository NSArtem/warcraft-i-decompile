/* codegen-flags: -s -ot -ol -4r -zp2
 * Module BULLET.C (0x119c0..0x123f0), game code, "OPT" style (no frame pointer). */
#include "codegen.h"

/* @0x123cc  push ebx/ecx/edx; push &"bullet:6"; call FatalError; add esp,4; pop..; ret */
void fn_123cc(void)
{
    FatalError("bullet:6");
}
