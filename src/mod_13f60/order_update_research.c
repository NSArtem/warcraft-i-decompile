/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

typedef struct RUnit {
    char pad0[0x0e];
    unsigned short flags;               /* 0x0e */
    char pad10[0x1e - 0x10];
    unsigned char owner;                /* 0x1e */
    char pad1f[0x3e - 0x1f];
    unsigned char otype;                /* 0x3e */
    char pad3f[0x46 - 0x3f];
    unsigned char *work;                /* 0x46 */
} RUnit;

extern unsigned long dat_50074[5];
extern unsigned short status_dirty;

short UnitWorkProgress(RUnit *u, int dirty);
unsigned short ResearchCost(unsigned short player, unsigned char row, const unsigned char **level);

/* @0x14534 */
int OrderUpdateResearch(RUnit *u)
{
    unsigned char *p;

    if (UnitWorkProgress(u, 2) != 0) {
        p = u->work;
        if ((*p & 0x80) != 0) {
            *p &= 0x7f;
            if ((u->flags & 0x20) != 0) {
                u->flags &= ~0x20;
                dat_50074[u->owner] += ((int)ResearchCost(u->owner, u->otype, (const unsigned char **)&p) * 3) / 4;
            } else {
                status_dirty = 1;
                (*p)++;
            }
        }
    }
    return 1;
}
