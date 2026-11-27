/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_11530 (0x11530..0x119c0), building production, "OPT" style.
 * BuildingAutoTrain (0x116c4): the barracks' production callback - pick one
 * of the four trainable combat types the scenario allows, weighted by
 * 4/6/2/8 and gated on a blacksmith and a mill, and start training it.  See
 * docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned short custom_game;             /* 0x50e4e (save_score area) */
extern unsigned short scenario_unit_mask;      /* 0x50004 */
extern unsigned short player_blacksmiths[];    /* 0x58e14 */
extern unsigned short player_mills[];          /* 0x58e0a */
extern signed char train_priority_odd[];       /* 0x11530 {1,9,5,7} */
extern signed char train_priority_even[];      /* 0x11534 {0,8,4,6} */

extern int GameRandom(unsigned id);                              /* 0x19478 LCG */
extern void UnitStartTraining(Unit *u, unsigned char type);    /* 0x115f4 */

/* @0x116c4 */
void BuildingAutoTrain(Unit *u)
{
    unsigned mask = (custom_game != 0) ? 0xffffffff : scenario_unit_mask;
    unsigned w[4];
    unsigned total;
    unsigned i;
    int n;

    n = 1;
    if (player_blacksmiths[1] == 0) {
        for (i = 2; i <= 6; i += 2) {
            n++;
            if (player_blacksmiths[i >> 1] != 0)
                break;
        }
    }
    if (n > 3)
        mask &= ~0xc;
    n = 1;
    if (player_mills[1] == 0) {
        for (i = 2; i <= 6; i += 2) {
            n++;
            if (player_mills[i >> 1] != 0)
                break;
        }
    }
    if (n > 3)
        mask &= ~0x10;
    w[0] = (mask & 1) ? 4 : 0;
    w[1] = (mask & 0x10) ? 6 : 0;
    w[2] = (mask & 4) ? 2 : 0;
    w[3] = (mask & 8) ? 8 : 0;
    total = w[0] + w[1] + w[2] + w[3];
    if (total == 0)
        return;
    {
        int r = GameRandom(0x10) % (int) total;

        for (i = 0; i < 4; i++) {
            r -= w[i];
            if (r < 0)
                break;
        }
    }
    {
        unsigned t = u->type - 0x20;
        unsigned char type = (t & 1) ? train_priority_odd[i] : train_priority_even[i];

        UnitStartTraining(u, type);
    }
}
