/* codegen-compiler: 10.0a */
#include "mod_1c9c0.h"

extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len); /* 0x1cbab, 0x1cc60 */
extern void *ResourceRead(void *dest, unsigned count); /* 0x1cbb4, 0x1cc6b */

void LoadSessionGraphics(void)
{
    unsigned short common_index;
    unsigned short side_index;
    unsigned short id;
    unsigned short enemy_mask;
    unsigned short player_mask;
    unsigned short entry;
    unsigned short scenario_flag;
    int mask;
    const unsigned short *descriptor;
    void **side;
    unsigned long size;
    void *sprite;
    void *enemy_sprite;

    for (common_index = 0, id = 0x15d; (int)common_index < 12;
         ++id, ++common_index) {
        ResourceBegin(id, 0);
        session_common_graphics[common_index] = ResourceRead(0, 0);
    }

    enemy_mask = session_graphics_resource_table[scenario_race_enemy] | 0x2000;
    player_mask = session_graphics_resource_table[scenario_race];
    descriptor = &session_graphics_resource_table[2];
    side = session_side_graphics;
    side_index = 0;
    goto test_side;
    do {
        mask = (int)enemy_mask | (int)player_mask;
        entry = *descriptor;
        if (((int)entry & mask) == 0) {
            side[0] = side[1] = 0;
            goto next_side;
        }
        scenario_flag = (unsigned short)(entry & 0x1000);
        if ((int)scenario_flag != 0 &&
            !IsGraphicsResourceAllowedForScenario(entry & 0x0fff))
            goto next_side;

        size = ResourceBegin(*descriptor & 0x0fff, 0);
        sprite = ResourceRead(0, 0);
        entry = *descriptor;
        if (((int)entry & (int)enemy_mask) != 0) {
            enemy_sprite = sprite;
            if (((int)entry & (int)player_mask) != 0)
                enemy_sprite = CloneSpriteResource(sprite, size);
            side[0] = enemy_sprite;
        } else {
            side[0] = 0;
        }
        entry = *descriptor;
        if (((int)entry & (int)player_mask) != 0)
            side[1] = sprite;
        else
            side[1] = 0;
    next_side:
        ++side_index;
        side += 2;
        ++descriptor;
    test_side:
        ;
    } while ((int)side_index < 72);
}
