/* codegen-compiler: 10.0a */
/* mod_1b800.  SndBulletEvent 0x1bbcc: the sound of a bullet event, by bullet
 * type (table bullet_sound; bit 0x8000 = only for a damaging hit).  Called by
 * the bullet handlers 0x11fa8, 0x12240 and 0x12338.  See
 * docs/subsystems/mod_1b800.md. */
#include "mod_1b800.h"

/* @0x1bbcc */
void SndBulletEvent(Bullet *b)
{
    unsigned short id = bullet_sound[b->type];

    if (id == 0)
        return;
    if ((id & 0x8000) != 0) {
        if (b->damage == 0)
            return;
        id &= 0x7fff;
    }
    SndEvent(id, b->target);
}
