/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x1284c - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): SetCheatFlags stores the flag word and
 * applies the one-shot effects.  Not T3: the six tables it writes (0x50008, 0x50060,
 * 0x50074, 0x5008c, 0x5a7c2, 0x59614/0x59616) belong to other subsystems and only have
 * placeholder names here, and OW2 lays the four tests out differently (279 bytes against
 * the original 269, 140 of them different).
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"

/* @0x1284c */
void SetCheatFlags(unsigned long flags)
{
    unsigned long old = cheat_flags.w;
    unsigned char p;

    cheat_flags.w = flags;
    if (flags & 0x8) {                      /* eye of newt: all spells */
        for (p = 0; p < 2; p++)
            if (dat_5008c[p] == 0) {
                dat_50008[3][p] = 1;
                dat_50008[6][p] = 1;
                dat_50008[4][p] = 1;
                dat_50008[7][p] = 1;
                dat_50008[5][p] = 1;
                dat_50008[8][p] = 1;
            }
    }
    if (cheat_flags.b[0] & 0x10) {          /* iron forge: all technology */
        for (p = 0; p < 2; p++)
            if (dat_5008c[p] == 0) {
                dat_50008[2][p] = 2;
                dat_50008[1][p] = 2;
                dat_50008[0][p] = 2;
                dat_50008[9][p] = 2;
            }
    }
    p = (unsigned char)cheat_flags.w;
    if (p & 0x20) {                         /* pot of gold, once */
        cheat_flags.b[0] = p & 0xdf;
        for (p = 0; p < 5; p++) {
            dat_50060[p] += 5000;
            dat_50074[p] += 10000;
        }
    }
    if (cheat_flags.b[0] & 0x40) {          /* ides of march */
        if (net_play_flag == 0)
            game_mode = 10;
    } else if (dat_5a7c2 == 0 && game_mode == 3) {
        fn_19edc(old > cheat_flags.w ? cheat_disabled_msg : cheat_enabled_msg, 0, 0x24);
    }
}
