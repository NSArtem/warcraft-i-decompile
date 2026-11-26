/* codegen-flags: -s -ot -ol -4r -zp2
 *
 * Module mod_19470 (0x19470..0x19b80), game code, "OPT" style.
 * The original was built with OW2: 10.0a selects another register for the
 * state reload and emits the multiply differently. */
#include "mod_19470.h"

/* @0x19478: linear congruential generator; the single dword state
 * dat_50d7c is carried with GameSetRandomSeed 0x19470 and the save image.
 * Every caller supplies an argument (a stream/limit id) that the original
 * does not read. */
int GameRandom(int id)
{
    dat_50d7c = dat_50d7c * 0x15a4e35L + 1;
    return (int)(dat_50d7c >> 16) & 0x7fff;
}
