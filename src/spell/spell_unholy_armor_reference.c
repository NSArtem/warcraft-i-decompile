/* codegen-compiler: 10.0a */
#include "spell.h"

extern void fn_11ec0(void *u, int n);

/* @0x277d4 */
int SpellUnholyArmor(struct Unit *u, short cast)
{
    char *p = (char *)u;
    char *t;
    int hp;

    if (*(unsigned char *)(p + 0x1a) < 0x7d) {
        return 0;
    }
    if (cast != 0) {
        t = *(char **)(p + 0x52);
        *(unsigned char *)(p + 0x1a) -= 0x7d;
        *(unsigned short *)(t + 0x38) = 1000;
        hp = *(unsigned short *)(t + 0x16);
        if (hp <= 0x1e) {
            *(unsigned short *)(t + 0x16) = 1;
        } else {
            *(unsigned short *)(t + 0x16) = (unsigned short)hp >> 1;
        }
        fn_11ec0(t, 8);
    }
    return 1;
}
