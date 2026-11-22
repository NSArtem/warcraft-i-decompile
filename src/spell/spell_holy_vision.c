/* codegen-compiler: 10.0a */
#include "spell.h"

extern void fn_2e9c4(int x, int y, int owner);
extern void fn_11e70(int x, int y, int type);          /* 0x11e70 bullet creator */

/* @0x27740 */
int SpellHolyVision(struct Unit *u, short cast)
{
    char *p = (char *)u;

    if (*(unsigned char *)(p + 0x1a) < 0x32) {
        return 0;
    }
    if (cast != 0) {
        *(unsigned char *)(p + 0x1a) -= 0x32;
        fn_2e9c4(*(long *)(p + 0x4c) >> 16, *(long *)(p + 0x4e) >> 16,
                 *(unsigned char *)(p + 0x1e));
        fn_11e70((*(long *)(p + 0x4c) >> 16) * 16 + 8,
                 (*(long *)(p + 0x4e) >> 16) * 16 + 8, 8);
    }
    return 1;
}
