/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned char dat_5008c[];

/* @0x21040 */
void *UnitGetTargetIfType50(void *u)
{
    char *p = (char *)u;
    char *t;
    unsigned c;

    t = *(char **)(p + 0x52);
    if (t != 0) {
        p = t;
        c = *(unsigned char *)(p + 0x1b);
        if (c == 0x32)
            return p;
        return 0;
    }
    if (dat_5008c[*(unsigned char *)(p + 0x1e)] != 0)
        return 0;
    t = (char *)object_map[(*(long *)(p + 0x4c) >> 16) + ((*(long *)(p + 0x4e) >> 16) << 6)];
    if (t != 0 && *(unsigned char *)(t + 0x1b) == 0x32)
        return t;
    return 0;
}
