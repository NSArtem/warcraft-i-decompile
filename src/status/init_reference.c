/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's life cycle of STATUS.C: StatusPanelSetUnit
 * 0x290f8, StatusPanelInit 0x29120 and StatusPanelFree 0x292a4.  The panel
 * graphics are DATA.WAR resources (0x16b icon grp, 0x169+race portrait grp,
 * 0x16c..0x16f button backgrounds, 0x19a/0x19b faction flags, 0xe4+race the
 * panel artwork, 0x19c the bar icon) plus the layer created from the artwork. */
#include "status.h"

extern unsigned short scenario_race;             /* 0x50088 */

/* 0x290f8 - remember which unit the panel should show next and hide the old
 * panel (called by the selection module whenever the selection changes). */
void StatusPanelSetUnit(Unit *u)
{
    if (status_visible) {
        status_visible = 0;
        MapInputRestore();
    }
    status_unit_req = u;
}

/* 0x29120 - load the panel graphics and create its layer (id 0x13). */
void StatusPanelInit(void)
{
    status_unused_d2 = 0;
    status_unit_type = 0xffff;
    status_lock = 0;
    status_unit = 0;
    status_unit_req = 0;

    ResourceBegin(0x16b, 0);
    unit_icon_grp = ResourceRead(0, 0);
    ResourceBegin(0x169 + (scenario_race != 1), 0);
    unit_portrait_grp = ResourceRead(0, 0);
    ResourceBegin(0x16c, 0);
    ResourceReadHeaderBody(&status_info_bm_normal, 0);
    ResourceBegin(0x16d, 0);
    ResourceReadHeaderBody(&status_info_bm_pressed, 0);
    ResourceBegin(0x16e, 0);
    ResourceReadHeaderBody(&status_button_bm_normal, 0);
    ResourceBegin(0x16f, 0);
    ResourceReadHeaderBody(&status_button_bm_pressed, 0);
    ResourceBegin(0x19a, 0);
    ResourceReadHeaderBody(&status_carry_bm[0], 0);
    ResourceBegin(0x19b, 0);
    ResourceReadHeaderBody(&status_carry_bm[1], 0);
    ResourceBegin(0xe4 + scenario_race, 0);
    ResourceReadHeaderBody(&status_panel_art, 0);
    ResourceBegin(0x19c, 0);
    ResourceReadHeaderBody(&status_bar_icon_bm, 0);

    LayerAdd(&status_panel_bm, &status_panel_rect, 0x13, 0xffff, (void (*)())BitmapBlit);
    cur_bitmap = &status_panel_bm;
    BitmapBlitAll(0, 0, &status_panel_art);
    LayerInvalidate(0x13);
}

/* 0x292a4 - free the layer and every graphic the init loaded. */
void StatusPanelFree(void)
{
    LayerFree(&status_panel_bm);
    GdsFree((void *)unit_icon_grp);
    unit_icon_grp = 0;
    GdsFree((void *)unit_portrait_grp);
    unit_portrait_grp = 0;
    GdsFree(status_info_bm_normal.data);
    status_info_bm_normal.data = 0;
    GdsFree(status_info_bm_pressed.data);
    status_info_bm_pressed.data = 0;
    GdsFree(status_button_bm_normal.data);
    status_button_bm_normal.data = 0;
    GdsFree(status_button_bm_pressed.data);
    status_button_bm_pressed.data = 0;
    GdsFree(status_carry_bm[0].data);
    status_carry_bm[0].data = 0;
    GdsFree(status_carry_bm[1].data);
    status_carry_bm[1].data = 0;
    GdsFree(status_panel_art.data);
    status_panel_art.data = 0;
    GdsFree(status_bar_icon_bm.data);
    status_bar_icon_bm.data = 0;
}
