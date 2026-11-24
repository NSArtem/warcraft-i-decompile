/* codegen-compiler: 10.0a */
#include "mod_1af20.h"
#include "mod_25820.h"
#include <string.h>

extern void MapReleaseDefault(void *evt); /* 0x1b1af: release-handler assignment. */
extern void MapPressDefault(void *evt); /* 0x1b1b9: press-handler assignment. */
extern int fn_25b6c(int on); /* 0x1b1c5: called with eax = 0. */
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len); /* 0x1b289: ID in eax, null edx. */
extern void *ResourceRead(void *dest, unsigned count); /* 0x1b295: destination in eax, zero edx. */
extern void PaletteSet(unsigned char first, unsigned short count, const unsigned char *rgb); /* 0x1b2ff: eax = 0, edx = 0x100, ebx = palette. */
extern void MapViewInitLimits(void); /* 0x1b304: call before viewport setup. */
extern void ViewportLayerCallback(); /* 0x1b335: viewport callback assignment. */
extern unsigned char *SaveReadStream(void *dst, unsigned count, unsigned char *pos); /* 0x1b358: eax/edx/ebx, cursor returned in eax. */
extern void SaveRelocObjectMap(int *map); /* 0x1b38c: object_map in eax. */
extern void FogMapObscure(void); /* 0x1b418: call when demo_mode is zero. */
extern void MapViewSetScroll(int x, int y); /* 0x1b423 and 0x1b42b already sign-extend both arguments. */

unsigned char *MapInitBuffers(unsigned char *save_pos)
{
    *(unsigned char *)&map_cursor_shape = 0;
    map_input_state_word = 0;
    map_release_handler = MapReleaseDefault;
    map_press_handler = MapPressDefault;
    fn_25b6c(0);
    MapScrollSetMouseRepeat(0);

    fog_cell_table = GdsAlloc(0x4000);
    tile_map = GdsAlloc(0x2000);
    object_map = GdsAlloc(0x4000);
    map_cost = GdsAlloc(0x2000);
    fog_map = GdsAlloc(0x2000);
    map_flags = GdsAlloc(0x2000);
    minitile_pixels = GdsAlloc(0x10000);
    terrain_cache = GdsAlloc(0x10000);
    object_array = GdsAlloc(0xed8);
    memset(object_array, 0, 0xed8);
    unit_array = GdsAlloc(0x47e0);
    memset(unit_array, 0, 0x47e0);

    ResourceBegin(scenario_tileset_id, 0);
    ResourceRead(minitile_pixels, 0);
    ResourceBegin(scenario_fog_cell_resource_id, 0);
    ResourceRead(fog_cell_table, 0);
    ResourceBegin(scenario_palette_resource_id, 0);
    ResourceRead(palette, 0);
    ResourceBegin((unsigned short)(scenario_race + 0xd4), 0);
    ResourceRead(palette + 0x180, 0);
    PaletteSet(0, 0x100, palette);

    MapViewInitLimits();
    map_viewport_left = 0x48;
    map_viewport_top = 0xc;
    map_viewport_width = 0xf0;
    map_viewport_height = 0xb0;
    map_viewport_aux = 0;
    map_viewport_callback = ViewportLayerCallback;
    map_viewport_enabled = 1;

    if (save_pos != 0) {
        save_pos = SaveReadStream(tile_map, 0x2000, save_pos);
        save_pos = SaveReadStream(map_flags, 0x2000, save_pos);
        save_pos = SaveReadStream(object_map, 0x4000, save_pos);
        SaveRelocObjectMap((int *)object_map);
        save_pos = SaveReadStream(fog_map, 0x2000, save_pos);
    } else {
        ResourceBegin(scenario_tile_map_resource_id, 0);
        ResourceRead(tile_map, 0);
        ResourceBegin(scenario_map_flags_resource_id, 0);
        ResourceRead(map_flags, 0);
        _fmemset((void __far *)object_map, 0, 0x4000);
        _fmemset((void __far *)fog_map, 0, 0x2000);
        map_scroll_x >>= 1;
        map_scroll_y >>= 1;
        if (demo_mode == 0)
            FogMapObscure();
    }
    MapViewSetScroll(*(long *)&map_scroll_x_low_word >> 16,
                     *(long *)&map_scroll_x >> 16);
    return save_pos;
}
