/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxShutdown (0x2254c): release the 48x48 placement-box scratch
 * bitmap that PlaceBoxInit allocated.  Called by the game teardown. */
#include "mod_20c30.h"

/* @0x2254c */
void PlaceBoxShutdown(void)
{
    if (place_box_bm.data != 0) {
        GdsFree(place_box_bm.data);
        place_box_bm.data = 0;
    }
}
