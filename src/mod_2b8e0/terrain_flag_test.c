/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned short *map_flags;
extern unsigned short terrain_flag_mask;

/* @0x2bf30 */
int TerrainFlagTest(unsigned x, unsigned y, int idx)
{
    if (x >= 0x40 || y >= 0x40) {
        return 0;
    }
    if ((map_flags[idx] & terrain_flag_mask) == 0) {
        return 0;
    }
    return 1;
}
