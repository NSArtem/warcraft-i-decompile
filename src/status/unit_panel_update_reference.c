/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x29450 UnitPanelUpdate (STATUS.C), the panel's per-frame
 * update called from the game loop fn_197b0.  One function per file so the
 * painters, the input restore and the card callback are external (the T4
 * difftest stubs them). */
#include "status.h"

void UnitPanelUpdate(void)
{
    unsigned short prev_type;
    Rect save;

    prev_type = status_unit_type;
    if (status_lock)
        return;
    if (status_unit_req == status_unit) {
        if (status_unit == 0)
            return;
        /* the original calls the card callback through the table
         * (0x29495 `call [eax*2+0x549ca]`), so index it directly */
        if (unit_panel_table[status_unit_req->type_copy].changed())
            goto redraw;
        if (status_sel_count != player_selection_count[0])
            goto redraw;
        if (!status_dirty)
            return;
        status_dirty = 0;
    }
redraw:
    save = *(const Rect *)&dirty_x1;
    dirty_x1 = 0x7fff;
    dirty_y1 = 0x7fff;
    dirty_x2 = -0x8000;
    dirty_y2 = -0x8000;
    dirty_w = 0;
    dirty_h = 0;
    cur_bitmap = &status_panel_bm;
    BitmapBlitAll(0, 0, &status_panel_art);
    DirtyRectAddBox(0, 0x48, 0x47, 0xc7);
    status_sel_count = player_selection_count[0];
    status_unit = status_unit_req;
    if (status_unit != 0) {
        status_unit_type = status_unit->type_copy;
        StatusPanelCacheUnitState();
    } else {
        status_unit_type = 0xffff;
    }
    if (status_visible) {
        if (prev_type != status_unit_type ||
            (status_button != &status_info_button && !ButtonAvailable(status_button))) {
            status_visible = 0;
            GameScreenInputInit();
        }
    }
    StatusTextForUnit();
    StatusPanelDraw();
    ScreenUpdate();
    *(Rect *)&dirty_x1 = save;
}
