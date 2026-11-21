/* codegen-compiler: 10.0a */
#include "mod_1e9a0.h"

extern unsigned short *fog_map;
extern unsigned short *terrain_scan_table;

/* @0x1e9a0 */
void FogUpdateTile(int tile)
{
    unsigned short *p;
    unsigned short v;
    unsigned short n;
    unsigned short o;
    unsigned short (*tbl)[11];

    tbl = (unsigned short (*)[11])fog_transition_table;
    p = fog_map + tile;
    o = fog_cur_owner;
    v = *p & fog_owner_mask[o];
    if (v != 0) {
        n = *p ^ v;
        *p = n;
        *p = n | (tbl[v >> fog_owner_shift[o]][*terrain_scan_table] << fog_owner_shift[o]);
    }
}
