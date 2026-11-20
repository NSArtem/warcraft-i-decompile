/* codegen-compiler: 10.0a */
#include "spell.h"

typedef struct SpUnit {
    char pad0[8];
    unsigned char owner8;   /* 0x08 */
    char pad1;
    short x;                /* 0x0a */
    short y;                /* 0x0c */
    char pad2[2];
    unsigned short flags;   /* 0x10 */
    char pad3[0x1a - 0x12];
    unsigned char mana;     /* 0x1a */
    unsigned char type;     /* 0x1b */
    char pad4[2];
    unsigned char owner;    /* 0x1e */
} SpUnit;

extern SpUnit *unit_array;
extern void *UnitCreate(short px, short py, unsigned char type, unsigned char owner);
extern void SndSummonAt(int px, int py);

/* @0x278ac */
int SpellRaiseDead(struct Unit *u, short cast)
{
    SpUnit *p = (SpUnit *)u;
    SpUnit *q;
    short i;
    short qx, qy;
    int dx, dy;

    if (p->mana < 0x46) {
        return 0;
    }
    if (cast != 0) {
        q = unit_array;
        for (i = 200; i--; q = (SpUnit *)((char *)q + 0x5c)) {
            if (p->mana < 0x46) {
                break;
            }
            if (q->type == 0x33
                && (q->flags & 2) != 0
                && (q->flags & 0x20d) == 0) {
                qx = q->x;
                qy = q->y;
                dx = (short)(p->x - qx);
                dy = (short)(p->y - qy);
                if (dx * dx + dy * dy <= 0x24) {
                    spell_summon_owner = q->owner8;
                    if (UnitCreate((short)(qx << 4), (short)(qy << 4), 0x1a,
                                   p->owner) != 0) {
                        p->mana -= 0x46;
                        SndSummonAt((unsigned short)qx, (unsigned short)qy);
                        *(unsigned char *)&q->flags |= 8;
                    }
                }
            }
        }
    }
    return 1;
}
