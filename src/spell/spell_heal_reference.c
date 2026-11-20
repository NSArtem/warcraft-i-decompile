/* codegen-compiler: 10.0a */
#include "spell.h"

typedef struct SpUnit {
    char pad0[0x16];
    unsigned short hp;      /* 0x16 */
    char pad1[2];
    unsigned char mana;     /* 0x1a */
    unsigned char type;     /* 0x1b */
    char pad2[0x52 - 0x1c];
    struct SpUnit *target;  /* 0x52 */
} SpUnit;

extern unsigned short unit_max_hp[];
extern void fn_11ec0(void *u, int n);

/* @0x27670 */
int SpellHeal(struct Unit *u, short cast)
{
    SpUnit *p = (SpUnit *)u;
    SpUnit *t = p->target;
    unsigned short n;

    if (t->type >= 0x20 && t->type <= 0x32) {
        return 0;
    }
    if (cast != 0) {
        if (t->type == 0x1c) {
            n = t->hp;
        } else {
            n = unit_max_hp[t->type] - t->hp;
        }
        if (n != 0 && p->mana != 0) {
            if (n > 0x28) {
                n = 0x28;
            }
            if ((unsigned)n * 3 > p->mana) {
                n = p->mana / 3;
            }
            if (t->type == 0x1c) {
                t->hp -= n;
            } else {
                t->hp += n;
            }
            p->mana -= (unsigned char)n * 3;
        }
        fn_11ec0(t, 8);
        return 1;
    }
    return p->mana;
}
