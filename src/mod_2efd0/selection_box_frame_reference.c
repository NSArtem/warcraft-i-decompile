/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* SelectionBoxFrame (0x2f15c): the per-frame half of the drag selection -
 * track the mouse, convert the box to map pixels and select every live unit
 * of the local player inside it (a building or an enemy unit becomes the
 * single pick when the box holds no own units). */
#include "mod_2efd0.h"

/* @0x2f15c */
void SelectionBoxFrame(Event *ev)
{
    Unit *list[4];
    Unit *pick;
    Unit *u;
    unsigned short i;
    unsigned short n;
    short w;
    short h;
    int add;

    SelectionBoxTrack(ev);
    GameScreenInputInit();
    selection_box.visible = 0;
    selection_box.min_x += map_scroll_x * 16 - 0x48;
    selection_box.max_x += map_scroll_x * 16 - 0x48;
    selection_box.min_y += map_scroll_y * 16 - 0xc;
    selection_box.max_y += map_scroll_y * 16 - 0xc;
    add = (sel_mod_select_all != 0 || sel_mod_add != 0);
    n = 0;
    if (add && selection_local != 0) {
        for (u = SelectionFirst(); u != 0; u = SelectionNext())
            list[n++] = u;
    } else {
        memset(list, 0, 4 * sizeof(Unit *));
    }
    pick = 0;
    for (i = 200, u = unit_array; i != 0; i--, u++) {
        if (n >= 4)
            break;
        if ((u->flags.w & 0x207) != 0)
            continue;
        if ((u->flags.w & 0x8) != 0)
            continue;
        if ((u->flags2 & 0x100) != 0)
            continue;
        w = unit_pixel_size[u->type][0];
        h = unit_pixel_size[u->type][1];
        if (u->px > selection_box.max_x)
            continue;
        if (u->px + w < selection_box.min_x)
            continue;
        if (u->py > selection_box.max_y)
            continue;
        if (u->py + h < selection_box.min_y)
            continue;
        if (add && (u->flags.w & 0x40) != 0)
            continue;
        if (type_is_creature[u->type] == 0) {
            pick = u;
            continue;
        }
        if (u->owner != 0) {
            pick = u;
            continue;
        }
        list[n++] = u;
    }
    if (n == 0 && pick != 0) {
        list[0] = pick;
        n = 1;
    }
    SelectionSet(n, list);
}
