/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the bar painters of STATUS.C: HealthBarDraw 0x2864c,
 * HealthBarDrawSingle 0x28700 and ProgressBarDraw 0x28770.  They draw into the
 * panel bitmap through cur_bitmap (0x55438) at panel-relative coordinates.
 * The other painters are one function per file: button_available.c (T3),
 * button_draw_reference.c, status_panel_draw.c (T3). */
#include "status.h"

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
