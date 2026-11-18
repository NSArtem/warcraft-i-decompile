/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's per-frame update of STATUS.C: UnitPanelUpdate
 * 0x29450 (called from the game loop fn_197b0) and
 * StatusPanelTextRefresh 0x28e88 (the info line's hover text, called from the
 * status chart fn_1a168). */
#include "status.h"

/* 0x29450 - the panel update.  Everything is skipped while the panel is
 * locked (a remote dialog is open).  When the requested unit is already on
 * show and nothing changed (card callback, selection count, redraw request)
 * the function returns; otherwise it repaints the whole panel out of the
 * artwork bitmap, adopts the requested unit and, if the info line is
 * affected, redraws text and buttons around ScreenUpdate. */
void UnitPanelUpdate(void)
{
    unsigned short prev_type;
    Rect save;
    const UnitPanel *panel;

    prev_type = status_unit_type;
    if (status_lock)
        return;
    if (status_unit_req == status_unit) {
        if (status_unit_req == 0)
            return;
        panel = &unit_panel_table[status_unit_req->type_copy];
        if (panel->changed())
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
            MapInputRestore();
        }
    }
    StatusTextForUnit();
    StatusPanelDraw();
    ScreenUpdate();
    *(Rect *)&dirty_x1 = save;
}

/* 0x28e88 - the info line's hover text for the point (x, y): the info-line
 * text when the point is over the info line, otherwise the label of the first
 * available command button whose rect contains the point.  For build/train
 * buttons it also fills in the gold/lumber cost, for research buttons the
 * research cost of the button's row. */
void StatusPanelTextRefresh(short x, short y)
{
    Unit *u;
    const Rect *r;
    const UnitPanel *panel;
    const CommandButton *b;
    const unsigned char *level;
    unsigned long i;

    u = status_unit;
    StatusTextForUnit();
    if (x >= status_info_rect.x1 && x <= status_info_rect.x2 &&
        y >= status_info_rect.y1 && y <= status_info_rect.y2) {
        status_button = &status_info_button;
        status_button_rect = &status_info_rect;
        SetHelpText(status_info_button.label);
        return;
    }
    if (status_unit_type == 0xffff)
        goto nothing;
    if (u->owner != 0)
        goto nothing;
    panel = &unit_panel_table[status_unit_type];
    if (panel->buttons == 0)
        goto nothing;
    b = panel->buttons;
    for (i = 0; i < panel->nbuttons; i++) {
        r = &command_button_rect[b->icon];
        status_button_rect = r;
        status_button = b;
        if (!ButtonAvailable(b))
            goto next;
        if (x < r->x1 || x > r->x2 || y < r->y1 || y > r->y2)
            goto next;
        SetHelpText(b->label);
        status_help_kind = b->kind;
        if (b->kind == 1) {
            status_help_gold = score_value[b->arg] * 10;
            status_help_lumber = unit_lumber_cost[b->arg] * 10;
        } else if (status_help_kind == 2) {
            status_help_lumber = 0;
            status_help_gold = ResearchCost(u->owner, b->arg, &level);
        }
        return;
    next:
        b++;
    }
nothing:
    status_button = 0;
}
