/* codegen-flags: -s -ot -ol -4r -zp2
 * Module mod_2ced0 (UNIT.C, 0x2ced0..0x2efd0), game code, "OPT" style.
 * UnitUpdateDamageFrame (0x2d0ac) - T3-matched; see
 * docs/subsystems/game_2c4e0.md.  The local mask variable is what makes OW2
 * emit the original's `mov dx,[u+0x10]; xor dh,dh; and dl,0x80; and
 * edx,0xffff` sequence (the flags word is an unsigned 32-bit value here). */
#include "game_2c4e0.h"

/* @0x2d0ac */
void UnitUpdateDamageFrame(Unit *u)
{
    unsigned f = u->flags.w & 0x80;

    if (f == 0) {
        int e = u->energy;

        if (e < 0x55)
            u->frame = 0;
        else if (e < 0xaa)
            u->frame = 1;
        else
            u->frame = 2;
    }
}
