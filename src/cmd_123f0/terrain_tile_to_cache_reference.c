/* codegen-flags: -s -ot -oa -4r -zp2 */
/* CMD.C 0x1246c - see docs/subsystems/cmd_123f0.md and analysis/symbols/cmd_123f0.toml.
 * REFERENCE C (not built, no `src =` entry): OW2 assigns the fog_cell_table pointer and the
 * cache offset to the other registers and
 * hoists the four word loads (`and ch,7; mov bx,cx` vs `and ah,7; and eax,0xffff`) -
 * codegen.md V1/V3.
 * One function per object: wcc386 aligns each following function to 16 bytes, which
 * would otherwise put the neighbour's padding into the extent wc1.match compares. */
#include "cmd_123f0.h"
/* @0x1246c */
void TerrainTileToCache(unsigned short tile, unsigned short x, unsigned short y)
{
    unsigned short *quads = fog_cell_table[tile & 0x7ff];
    unsigned long off = (((unsigned long)y << 8) + x) << 4;

    MiniTileToCache(*quads++, (unsigned short)off);
    MiniTileToCache(*quads++, (unsigned short)(off + 8));
    MiniTileToCache(*quads++, (unsigned short)(off + 0x800));
    MiniTileToCache(*quads, (unsigned short)(off + 0x808));
}
