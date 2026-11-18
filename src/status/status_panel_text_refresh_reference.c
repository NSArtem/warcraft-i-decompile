/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x28e88 StatusPanelTextRefresh, the info line's hover text.
 *
 * The point is passed as ONE 4-byte value: the caller (the status chart
 * fn_1a168, 0x1a1f2) loads the dword 0x59428 - the cursor position the UI
 * event layer publishes, x at +0, y at +2 - into eax and calls.  The original
 * spills that dword to [esp+4] (0x28e95) and reads the two words at +4/+6
 * (0x28e9e/0x28eb4), i.e. the parameter is a packed {short x, short y}; an
 * earlier version of this C used two short parameters, which is a different
 * ABI (x in eax, y in edx) and can never match.  status.h still has the old
 * two-short prototype; rename it here (reported as a change request) so this
 * file can define the real one. */
#define StatusPanelTextRefresh StatusPanelTextRefresh_stale_proto
#define unit_lumber_cost unit_lumber_cost_stale_proto
#include "status.h"
#undef StatusPanelTextRefresh
#undef unit_lumber_cost

/* 0x51a84: a BYTE per unit type - 0x28fc6 `mov al,[eax+unit_lumber_cost]`,
 * 0x28fcc `xor ah,ah`; status.h's `unsigned short[]` is wrong (change
 * request).  The symbol is the database's `_unit_lumber_cost`. */
extern const unsigned char unit_lumber_cost[];

typedef struct Point {
    short x;
    short y;
} Point;

void StatusPanelTextRefresh(Point pt)
{
    Unit *u;
    const Rect *r;
    const UnitPanel *panel;
    const CommandButton *b;
    const unsigned char *level;
    unsigned long i;

    StatusTextForUnit();
    if (pt.x >= status_info_rect.x1 && pt.x <= status_info_rect.x2 &&
        pt.y >= status_info_rect.y1 && pt.y <= status_info_rect.y2) {
        status_button = &status_info_button;
        status_button_rect = &status_info_rect;
        SetHelpText(status_info_button.label);
        return;
    }
    if (status_unit_type == 0xffff)
        goto nothing;
    u = status_unit;
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
        if (pt.x < r->x1 || pt.x > r->x2 || pt.y < r->y1 || pt.y > r->y2)
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
    /* the original's two "no button" exits share one tail call to SetHelpText
     * with eax = 0 (0x29039-0x29043): the info line is blanked */
    SetHelpText(0);
}
