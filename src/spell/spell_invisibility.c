/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "spell.h"

extern void fn_11ec0(void *u, int n);

/* @0x277a0 */
int SpellInvisibility(struct Unit *u, short cast)
{
    char *p = (char *)u;
    char *t;

    if (*(unsigned char *)(p + 0x1a) < 0x7d) {
        return 0;
    }
    if (cast != 0) {
        t = *(char **)(p + 0x52);
        *(unsigned char *)(p + 0x1a) -= 0x7d;
        *(unsigned short *)(t + 0x36) = 3000;
        fn_11ec0(t, 8);
    }
    return 1;
}
