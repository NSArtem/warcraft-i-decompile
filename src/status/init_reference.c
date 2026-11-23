/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for the panel's life cycle of STATUS.C.  StatusPanelSetUnit
 * 0x290f8 stays here; StatusPanelInit 0x29120 and StatusPanelFree 0x292a4 are
 * one function per file (the T3-matched status_panel_init.c and
 * status_panel_free.c).  The panel graphics are DATA.WAR resources (0x16b icon
 * grp, 0x169+race portrait grp, 0x16c..0x16f button backgrounds, 0x19a/0x19b
 * carry icons, 0xe4+race the panel artwork, 0x19c the bar icon) plus the layer
 * created from the artwork. */
#include "status.h"

/* 0x290f8 - remember which unit the panel should show next and hide the old
 * panel (called by the selection module whenever the selection changes). */
void StatusPanelSetUnit(Unit *u)
{
    if (status_visible) {
        status_visible = 0;
        GameScreenInputInit();
    }
    status_unit_req = u;
}
