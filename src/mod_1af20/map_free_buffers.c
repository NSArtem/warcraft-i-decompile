/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

/* 0x1b075..0x1b111: free each buffer before clearing its pointer. */
void MapFreeBuffers(void)
{
    GdsFree(minitile_pixels);
    minitile_pixels = 0;
    GdsFree(terrain_cache);
    terrain_cache = 0;
    GdsFree(fog_cell_table);
    fog_cell_table = 0;
    GdsFree(fog_map);
    fog_map = 0;
    GdsFree(map_flags);
    map_flags = 0;
    GdsFree(tile_map);
    tile_map = 0;
    GdsFree(object_map);
    object_map = 0;
    GdsFree(map_cost);
    map_cost = 0;
    GdsFree(unit_array);
    unit_array = 0;
    GdsFree(object_array);
    object_array = 0;
}
