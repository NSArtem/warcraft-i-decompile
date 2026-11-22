/* codegen-compiler: 10.0a */
#include "mod_1eba0_f2.h"

extern void FillRect(int, int, unsigned int, unsigned int); /* 0x1ee71 */
extern void RectOutline(int, int, unsigned int, unsigned int); /* 0x1eeb3 */

/* Word reads at 0x1edcb, 0x1edf2 and 0x1ee06; stride 0x5c at 0x1ee76. */
struct MinimapUnitView {
    unsigned char prefix[0x0a];
    short x, y;
    volatile unsigned short flags_e, flags_10;
    unsigned char gap_12[9];
    unsigned char type;
    unsigned char gap_1c[2];
    unsigned char owner;
    unsigned char gap_1f[0x17];
    short state_36;
    unsigned char tail[0x24];
};

short MinimapRedraw(short force)
{
    struct MinimapUnitView *u;
    short x, y;
    unsigned short remaining, masked;
    unsigned short scroll_x, scroll_y, w, h;
    unsigned char type;

    if (force == 0 && --minimap_redraw_countdown != 0) {
        scroll_x = map_scroll_x;
        if (scroll_x == minimap_last_scroll_x) {
            scroll_y = map_scroll_y;
            if (scroll_y == minimap_last_scroll_y)
                return 0;
        }
    }
    if ((int)minimap_redraw_state < 4)
        return 0;

    minimap_redraw_countdown = 0x28;
    minimap_last_scroll_x = map_scroll_x;
    minimap_last_scroll_y = map_scroll_y;
    cur_bitmap = &minimap_panel_bitmap;
    MinimapDrawTerrain();
    u = (struct MinimapUnitView *)unit_array;
    remaining = 200;
    goto count_unit;
    do {
        masked = u->flags_10;
        masked &= 0x207;
        if ((int)masked != 0)
            goto next_unit;
        masked = u->flags_10;
        masked &= 8;
        if ((int)masked != 0)
            goto next_unit;
        masked = u->flags_e;
        masked &= 0x100;
        if ((int)masked != 0)
            goto next_unit;
        if (u->state_36 != 0 && u->owner != 0)
            goto next_unit;
        if ((void *)u == player_town_hall[0])
            draw_color = 0xdd;
        else
            draw_color = minimap_player_colors[u->owner];
        x = (short)(u->x + minimap_draw_rect[0]);
        y = (short)(u->y + minimap_draw_rect[1]);
        type = u->type;
        w = (unsigned short)unit_type_size[type][0];
        h = (unsigned short)unit_type_size[type][1];
        FillRect(x, y, w, h);
next_unit:
        ++u;
count_unit:
        --remaining;
    } while (remaining != (unsigned short)-1);
    draw_color = 0xdb;
    y = (short)(map_scroll_y + minimap_draw_rect[1]);
    x = (short)(map_scroll_x + minimap_draw_rect[0]);
    RectOutline(x, y, 0xf, 0xb);
    return 1;
}
