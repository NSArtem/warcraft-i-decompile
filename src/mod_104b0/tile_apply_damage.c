/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Module mod_104b0 (0x104b0..0x110a0), unit combat code, "OPT" style.
 * TileApplyDamage (0x105d0): damage a terrain feature (a wall, a tree, a mine)
 * at tile (x, y); the tile's graphic is advanced when its amount field (bits
 * 11..15 of the tile word) drops to zero.  See docs/subsystems/mod_104b0.md. */
#include "mod_104b0.h"

extern unsigned short *tile_map;               /* 0x58570 */
extern unsigned short fn_13348(short x, short y, unsigned mask);   /* 0x13348 */
extern void TerrainWallAdvance(short x, short y); /* 0x2c2c4 tile graphic advance */

/* @0x105d0 */
void TileApplyDamage(unsigned short x, unsigned short y, unsigned char damage)
{
    unsigned char amount;

    if (x >= 0x40 || y >= 0x40)
        return;
    if (fn_13348(x, y, 0xc) == 0)
        return;
    amount = (damage >> 1) + 1;
    if (amount > 0x14)
        amount = 0x14;
    {
        unsigned off = y * 0x40 + x;
        int have = (tile_map[off] & 0xffff) >> 11;

        have -= amount;
        if (have <= 0) {
            TerrainWallAdvance(x, y);
            have += 0x14;
        }
        tile_map[off] = (tile_map[off] & 0x7ff) | (have << 11);
    }
}
