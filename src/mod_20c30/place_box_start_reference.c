/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxStart (0x22798, PLACEBOX.C): the build/place command.  Checks and
 * pays the cost, marks the player as placing, sets up the box bitmap and
 * layer, installs the placement mouse handlers and starts the palette cycle.
 * Shows 'Select location' (0x572dc); on a failed cost check it shows the
 * message fn_20d74 returned and stops. */
#include "mod_20c30.h"

void fn_20cc0(void);                                   /* 0x20cc0 */
void fn_20c30(unsigned id);                            /* 0x20c30 */
void fn_25b6c(int on);                                 /* 0x25b6c */
void PlaceBoxUpdate(void);                             /* 0x2261c */

/* @0x22798 */
void PlaceBoxStart(unsigned char type)
{
    Unit *w;
    unsigned short wpx, hpx;

    if (place_active[net_event_pending] != 0)
        return;
    w = SelectionFirst();
    if (w == 0)
        return;
    {
        const char *err = fn_20d74(net_event_pending, 1, type);

        if (err != 0) {
            if (net_event_pending != 0)
                return;
            fn_19f70(err, 0x24);
            return;
        }
    }
    place_type[net_event_pending] = type;
    place_active[net_event_pending] = 1;
    fn_20cc0();
    if (net_event_pending != 0)
        return;
    fn_20c30(0x3a);
    place_valid = 0;
    map_cursor_flags |= 1;
    wpx = unit_type_size[type * 2] * 16;
    hpx = unit_type_size[type * 2 + 1] * 16;
    place_box_bm.w = wpx;
    place_box_bm.h = hpx;
    cur_bitmap = &place_box_bm;
    draw_color = 0;
    FillRect(1, 1, wpx - 2, hpx - 2);
    draw_color = 0xda;
    RectOutline(0, 0, wpx, hpx);
    layers[PLACE_LAYER].w = wpx;
    layers[PLACE_LAYER].h = hpx;
    layers[PLACE_LAYER].active = 1;
    map_release_handler = PlaceBoxRelease;
    map_press_handler = PlaceBoxPress;
    fn_25b6c(1);
    fn_19f70("Select location", 0);
    PaletteCycleSetup(0xf, 1, 0xda, 0xda, place_colors_bad, 0x20);
    PaletteCycleEnable(0xf);
    PlaceBoxUpdate();
    map_cursor_shape = 0;
}
