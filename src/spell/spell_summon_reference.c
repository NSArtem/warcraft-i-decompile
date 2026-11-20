/* codegen-compiler: 10.0a */
#include "spell.h"

typedef struct SpUnit {
    char pad0[8];
    long px;                /* 0x08 */
    long py;                /* 0x0c, only 0x0a..0x0d used via cast */
    char pad1[0x1a - 0x10];
    unsigned char mana;     /* 0x1a */
    unsigned char type;     /* 0x1b */
    char pad2[2];
    unsigned char owner;    /* 0x1e */
    unsigned char spell;    /* 0x1f */
} SpUnit;

extern short unit_type_size[52][2];
extern int fn_2e650(int x, int y, int type, int owner, short *size);

/* @0x279c0 */
int SpellSummon(struct Unit *u, short cast)
{
    SpUnit *p = (SpUnit *)u;
    unsigned short type;
    unsigned short cost;
    unsigned short i;

    if (p->spell == 0x16) {
        type = 0x1f;
        cost = 0xff;
    } else if (p->spell == 0x17) {
        type = 0x1c;
        cost = 0xff;
    } else {
        if (p->spell == 0x19) {
            type = 0x18;
        } else {
            type = 0x15;
        }
        cost = 0x3c;
    }
    if (p->mana < cost) {
        return 0;
    }
    if (cast != 0) {
        for (i = 0; i < 4; i++) {
            if (cost > p->mana) {
                break;
            }
            if (fn_2e650(*(long *)((char *)p + 8) >> 16,
                         *(long *)((char *)p + 0xa) >> 16, type,
                         p->owner, unit_type_size[p->type]) != 0) {
                p->mana -= (unsigned char)cost;
            }
        }
    }
    return 1;
}
