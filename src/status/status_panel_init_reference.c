/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2 */
/* Reference C for 0x29120 StatusPanelInit (STATUS.C): load the panel graphics
 * and create its layer.  One function per file so the resource/layer callees
 * are external symbols (the T4 difftest stubs them).
 *
 * The graphics are DATA.WAR resources: 0x16b icon grp, 0x169/0x16a by race
 * the portrait grp, 0x16c..0x16f the button backgrounds, 0x19a/0x19b the
 * carry icons, 0xe4+race the panel artwork, 0x19c the bar icon. */
#include "status.h"

extern unsigned short scenario_race;             /* 0x50088 */

void StatusPanelInit(void)
{
    status_unused_d2 = 0;
    status_unit_type = 0xffff;
    status_lock = 0;
    status_unit = 0;
    status_unit_req = 0;

    ResourceBegin(0x16b, 0);
    unit_icon_grp = ResourceRead(0, 0);
    /* 0x2916c-0x2917c: `cmp eax,1; setne al; and eax,0xff; add eax,0x169`
     * - the ternary is the spelling that reproduces 10.0a's code (the
     * `0x169 + (scenario_race != 1)` form emits `xor ah,ah` instead) */
    ResourceBegin(scenario_race == 1 ? 0x169 : 0x16a, 0);
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
