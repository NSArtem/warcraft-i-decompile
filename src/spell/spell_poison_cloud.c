/* codegen-compiler: 10.0a */
#include "spell.h"

extern void BulletSpawnPoisonCloud(struct Unit *caster);

/* @0x27824 */
int SpellPoisonCloud(struct Unit *u, short cast)
{
    char *p = (char *)u;

    if (*(unsigned char *)(p + 0x1a) < 0x32) {
        return 0;
    }
    if (cast != 0) {
        *(unsigned char *)(p + 0x1a) -= 0x32;
        BulletSpawnPoisonCloud(u);
    }
    return 1;
}
