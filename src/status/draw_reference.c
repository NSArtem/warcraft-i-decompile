/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's painters of STATUS.C: ButtonAvailable 0x28434,
 * ButtonDraw 0x284a8, HealthBarDraw 0x2864c, HealthBarDrawSingle 0x28700,
 * ProgressBarDraw 0x28770, StatusPanelCacheUnitState 0x287f0,
 * UnitPanelDraw 0x28824 and StatusPanelDraw 0x28894.  All of them draw into the panel bitmap through
 * cur_bitmap (0x55438) at panel-relative coordinates. */
#include "status.h"

/* 0x28434 ButtonAvailable: built from C (T3 under Watcom 10.0a) in
 * button_available.c. */

/* 0x284a8 - draw one command button: background (normal/pressed bitmap at
 * command_button_rect[b->icon]) and the icon frame b->face of unit_icon_grp
 * on top of it.  The info line (status_info_button, 0x53aec) uses its own
 * background at (3,0x74).  Unavailable buttons are not drawn. */
void ButtonDraw(const CommandButton *b, short pressed)
{
    Bitmap icon;
    const Bitmap *bg;
    short x;
    short y;

    if (b == &status_info_button) {
        bg = pressed ? &status_info_bm_pressed : &status_info_bm_normal;
        BitmapBlit(3, 0x74, bg, &status_info_src_rect);
        return;
    }
    if (!ButtonAvailable(b))
        return;
    y = command_button_rect[b->icon].y1 - 0x48;
    bg = pressed ? &status_button_bm_pressed : &status_button_bm_normal;
    BitmapBlitAll(command_button_rect[b->icon].x1, y, bg);
    x = command_button_rect[b->icon].x1 + 2;
    y = y + 2 + (pressed != 0);
    GrpFrameBitmap(unit_icon_grp, b->face, &icon);
    BitmapBlitAll(x, y, &icon);
}

/* 0x2864c - a 3-high health bar at (x, y): length 27 * hp / max, colour from
 * bar_color_table picked with 100 * hp / max (green 0xdf above 75 %, yellow
 * 0xdd above 50 %, red 0xde below).  Nothing is drawn when the percentage
 * rounds to 0. */
void HealthBarDraw(short x, short y, const Unit *u)
{
    unsigned long hp;
    unsigned long max_hp;
    unsigned long value;
    unsigned long len;
    unsigned long i;

    hp = u->hp;
    max_hp = unit_max_hp[u->type];
    value = 100 * hp / max_hp;
    if (value == 0)
        return;
    i = 0;
    while (value < bar_color_table[i][0])
        i++;
    draw_color = bar_color_table[i][1];
    len = 27 * hp / max_hp;
    if (len > 0xff)
        len = 0xff;
    if (len == 0)
        len = 1;
    FillRect(x, y, len, 3);
}

/* 0x28700 - the state-1 bar at (0x25, 9): 27 * unit+0x1a / 255 wide, 3 high,
 * colour 0xdf. */
void HealthBarDrawSingle(void)
{
    unsigned long value;
    unsigned long len;

    value = status_unit->damage;
    if (value == 0)
        return;
    len = 27 * value / 0xff;
    if (len > 0xff)
        len = 0xff;
    if (len == 0)
        len = 1;
    draw_color = 0xdf;
    FillRect(0x25, 9, len, 3);
}

/* 0x28770 - the state-2 bar at (4, 0x25): 62 * unit+0x1a / 255 wide, 5 high,
 * colour 0xdf, with the bar icon (0x53520) on top. */
void ProgressBarDraw(void)
{
    unsigned long value;
    unsigned long len;

    value = status_unit->damage;
    if (value == 0)
        return;
    len = 62 * value / 0xff;
    if (len > 0xff)
        len = 0xff;
    if (len == 0)
        len = 1;
    draw_color = 0xdf;
    FillRect(4, 0x25, len, 5);
    BitmapBlitTransparentAll(0xf, 0x25, &status_bar_icon_bm);
}

/* 0x28824 - draw the command card: every button (pressed only for the armed
 * one), then the card's extra lines when the displayed unit has flags bit
 * 0x80 (the farm's food usage, the gold mine's gold left). */
void UnitPanelDraw(const UnitPanel *panel)
{
    const CommandButton *b;
    unsigned long i;
    unsigned short armed;

    b = panel->buttons;
    for (i = 0; i < panel->nbuttons; i++) {
        armed = (status_visible && b == status_button && status_pressed);
        ButtonDraw(b, armed);
        b++;
    }
    if (panel->draw != 0 && (status_unit->flags & 0x80))
        panel->draw();
}

/* 0x28894 - paint the whole panel for the displayed unit.  The "state" decides
 * the layout: 0/1 = one unit (1 also gets the small health bar), 2 = a
 * building under construction, 3..5 = a group of 2..4 units (the group
 * portrait plus the members' head icons and health bars).  The state is also
 * the portrait frame; the type's name table entry must exist. */
void StatusPanelDraw(void)
{
    Unit *u;
    Bitmap frame;
    unsigned short state;
    unsigned long type;

    u = status_unit;
    if (u == 0)
        return;
    type = u->type;
    if (unit_names[type].face == 0xffff)
        return;
    state = unit_names[type].flags;
    if (player_selection_count[0] > 1)
        state = player_selection_count[0] + 1;
    else if (u->owner != 0)
        state = 0;
    else if (type >= 0x20)
        if ((u->flags & 0x80) || !(u->sflags & 0x10))
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
        GrpFrameBitmap(unit_icon_grp, unit_names[type].face, &frame);
        BitmapBlitAll(6, 4, &frame);
        cur_font = score_font;
        TextSetColorBase(0xf3);
        DrawText(6, 0x1a, unit_names[type].name);
        if (state == 2)
            ProgressBarDraw();
        if (state == 1)
            HealthBarDrawSingle();
        HealthBarDraw(0x25, 0x14, u);
    }
    if (status_unit != 0) {
        StatusPanelCacheUnitState();
        if (status_unit->type >= 0x20)
            status_work_state = status_unit->dest;
    }
    if (state < 3 && type >= 2 && type <= 3 && (u->work.b.state & 0x20)) {
        if (u->work.b.state & 0x80)
            BitmapBlitTransparentAll(0x2a, 3, &status_carry_bm[0]);
        else
            BitmapBlitTransparentAll(0x2a, 3, &status_carry_bm[1]);
    }
    if (u->owner == 0 || u->type == 0x32)
        UnitPanelDraw(&unit_panel_table[status_unit_type]);
}
