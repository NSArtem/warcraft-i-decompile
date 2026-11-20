/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

/* @0x21e58 */
unsigned short UnitIsPassable(Unit *u)
{
    if ((u->flags.w & 0x207) != 0) {
        return ((unsigned char *)u)[0x1b] <= 0x1f;
    }
    if (((unsigned char *)u)[0x1f] != 3 && ((unsigned char *)u)[0x1f] != 0xc) {
        return 0;
    }
    if ((*(unsigned short *)((unsigned char *)u + 0xe) & 0xf000) != 0) {
        return 0;
    }
    if ((u->flags.w & 0x1000) != 0) {
        return 0;
    }
    return 1;
}
