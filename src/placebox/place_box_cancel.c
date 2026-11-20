/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void __cdecl PaletteCycleDisable(unsigned char id);

/* @0x22930 */
void PlaceBoxCancel(void)
{
    if (place_active[net_event_pending] != 0) {
        place_active[net_event_pending] = 0;
        fn_20c6c();
        fn_20d74(net_event_pending, 0, place_type[net_event_pending]);
        if (net_event_pending == 0) {
            ((void (*)(int))fn_20c4c)(0);
            map_cursor_flags &= 0xfe;
            PaletteCycleDisable(0xf);
            *(unsigned short *)&layers[PLACE_LAYER] = 0;
            map_release_handler = MapReleaseDefault;
            map_press_handler = MapPressDefault;
            fn_25b6c(0);
            fn_19f70(0, 0);
            *(unsigned char *)&map_cursor_shape = 0;
        }
    }
}
