/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern unsigned char hostility[25];
extern unsigned char dat_55264[];

/* @0x2e9f4 */
unsigned int UnitTargetRelation(Unit *u)
{
    unsigned char a;
    unsigned char t;

    a = dat_55264[*((unsigned char *)u + 0x1f)];
    if (a != 0) {
        t = a & 2;
        if (t != 0) {
            if (u->u52.p == 0)
                return 0;
            return hostility[u->owner * 5 + u->u52.p->owner];
        }
        a &= 1;
    }
    return a;
}
