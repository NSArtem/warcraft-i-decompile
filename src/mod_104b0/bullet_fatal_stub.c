/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module BULLET.C (0x119c0..0x123f0), game code, "OPT" style.
 * BulletFatalStub (0x123cc) is only referenced by the single handler pointer
 * at 0x51210: bullet state 6 has no handler and asserts the tag. */
#include "war.h"

extern const char bullet_fatal_tag[];   /* 0x569e0 "bullet:6" */

/* @0x123cc */
void BulletFatalStub(void)
{
    FatalError(bullet_fatal_tag);
}
