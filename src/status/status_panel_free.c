/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x292a4 StatusPanelFree: free the panel's offscreen bitmap data and every
 * graphic StatusPanelInit loaded, clearing each pointer. */
#include "status.h"

extern void ResourceFreeBody(void *hdr);         /* 0x21cf0 */

void StatusPanelFree(void)
{
    ResourceFreeBody(&status_panel_bm);
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
