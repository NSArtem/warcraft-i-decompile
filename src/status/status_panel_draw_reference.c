/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x28894 StatusPanelDraw (STATUS.C), the panel painter.  One
 * function per file so every callee is an external symbol (the T4 difftest
 * stubs the graphics primitives and the bar painters).
 *
 * The state (0/1 = one unit, 2 = a building under construction, 3..5 = a group
 * of 2..4 units) is also the portrait frame.  The state-2 test is the
 * original's: a building is "under construction" when it is NOT finished
 * (flags 0x80 clear) or it is busy (sflags 0x10) - 0x288fe `and edx,0xffff`,
 * 0x28904 `je 0x28915`, 0x28913 `je 0x2891a`. */
#include "status.h"

void StatusPanelDraw(void)
{
    Bitmap frame;
    unsigned short state;

    if (status_unit == 0)
        return;
    if (unit_names[status_unit->type].face == 0xffff)
        return;
    state = unit_names[status_unit->type].flags;
    if (player_selection_count[0] > 1)
        state = player_selection_count[0] + 1;
    else if (status_unit->owner != 0)
        state = 0;
    else if (status_unit->type >= 0x20)
        if (!(status_unit->flags & 0x80) || (status_unit->sflags & 0x10))
            state = 2;
    if (state >= 3) {
        GrpFrameBitmap(unit_portrait_grp, state, &frame);
        BitmapBlitAll(2, 0, &frame);
        GrpFrameBitmap(unit_icon_grp, unit_names[SelectionFirst()->type].face, &frame);
        BitmapBlitAll(4, 1, &frame);
        GrpFrameBitmap(unit_icon_grp, unit_names[SelectionNext()->type].face, &frame);
        BitmapBlitAll(0x26, 1, &frame);
    } else {
        GrpFrameBitmap(unit_portrait_grp, state, &frame);
        BitmapBlitAll(2, 0, &frame);
    }
    if (state >= 4) {
        GrpFrameBitmap(unit_icon_grp, unit_names[SelectionNext()->type].face, &frame);
        BitmapBlitAll(4, 0x17, &frame);
    }
    if (state == 5) {
        GrpFrameBitmap(unit_icon_grp, unit_names[SelectionNext()->type].face, &frame);
        BitmapBlitAll(0x26, 0x17, &frame);
    }
    if (state >= 3) {
        GrpFrameBitmap(unit_portrait_grp, state + 3, &frame);
        BitmapBlitTransparentAll(3, 0x10, &frame);
        HealthBarDraw(4, 0x11, SelectionFirst());
        HealthBarDraw(0x26, 0x11, SelectionNext());
    }
    if (state >= 4)
        HealthBarDraw(4, 0x27, SelectionNext());
    if (state == 5)
        HealthBarDraw(0x26, 0x27, SelectionNext());
    if (state < 3) {
        GrpFrameBitmap(unit_icon_grp, unit_names[status_unit->type].face, &frame);
        BitmapBlitAll(6, 4, &frame);
        cur_font = score_font;
        TextSetColorBase(0xf3);
        DrawText(6, 0x1a, unit_names[status_unit->type].name);
        if (state == 2)
            ProgressBarDraw();
        if (state == 1)
            HealthBarDrawSingle();
        HealthBarDraw(0x25, 0x14, status_unit);
    }
    if (status_unit != 0) {
        StatusPanelCacheUnitState();
        if (status_unit->type >= 0x20)
            status_work_state = status_unit->dest;
    }
    if (state < 3 && status_unit->type >= 2 && status_unit->type <= 3 &&
        (status_unit->work.b.state & 0x20)) {
        if (status_unit->work.b.state & 0x80)
            BitmapBlitTransparentAll(0x2a, 3, &status_carry_bm[0]);
        else
            BitmapBlitTransparentAll(0x2a, 3, &status_carry_bm[1]);
    }
    if (status_unit->owner == 0 || status_unit->type == 0x32)
        UnitPanelDraw(&unit_panel_table[status_unit_type]);
}
