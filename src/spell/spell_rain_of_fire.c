/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "spell.h"

extern void UnitSetNextOrder(void *u, unsigned char order);
extern void BulletSpawnRainOfFire(struct Unit *caster, int n);

/* @0x2784c */
int SpellRainOfFire(struct Unit *u, short cast)
{
    char *p = (char *)u;

    if (*(unsigned char *)(p + 0x1a) < 0x32) {
        UnitSetNextOrder(u, 2);
        return 0;
    }
    if (cast != 0) {
        *(unsigned char *)(p + 0x1a) -= 0x32;
        BulletSpawnRainOfFire(u, 0);
        BulletSpawnRainOfFire(u, 1);
        BulletSpawnRainOfFire(u, 2);
        BulletSpawnRainOfFire(u, 3);
    }
    return 1;
}
