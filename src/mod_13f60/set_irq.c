/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern int NetSerialPortIrq(int index);

/* @0x1550c */
void SetIrq(struct Control *c)
{
    int *p = (int *)c;
    int r;

    if (p[7] != p[2]) {
        p[7] = p[2];
        r = NetSerialPortIrq(p[2]);
        if (r == 3) {
            p[3] = 1;
        } else if (r == 4) {
            p[3] = 2;
        } else {
            FatalError(tag_setirq);
        }
    }
}
