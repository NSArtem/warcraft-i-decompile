/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern short UnitRetaliate(OrderUnit *u);
extern void UnitSetNextOrder(void *u, unsigned char order);
extern union CheatFlags { unsigned long w; unsigned char b[4]; } cheat_flags;
extern unsigned short status_dirty;

/* @0x14334 */
int UnitWorkProgress(OrderUnit *u, int dirty)
{
    unsigned char *p = (unsigned char *)u;
    unsigned char a;
    unsigned char b;

    UnitRetaliate(u);
    if ((*(unsigned short *)(p + 0xe) & 0x20) != 0) {
        status_dirty = 1;
    } else {
        if ((cheat_flags.w & 2) == 0) {
            if (--p[0x3f] != 0) {
                return 0;
            }
        }
        a = p[0x40];
        b = p[0x41];
        if (a > b) {
            p[0x1a] = 0;
            p[0x40] = 0;
        } else {
            if (a == b) {
                p[0x1a] = 0xff;
            } else {
                p[0x1a] = (unsigned char)((int)(a * 255) / (int)b);
            }
            p[0x40]++;
            p[0x3f] = (unsigned char)dirty;
            return 0;
        }
    }
    *(unsigned short *)(p + 0xe) &= 0xef;
    UnitSetNextOrder(u, 2);
    return 1;
}
