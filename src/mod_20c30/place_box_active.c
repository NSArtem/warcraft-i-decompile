/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * PlaceBoxActive (0x22538): is the local network player placing right now?
 * The map input dispatcher and the per-frame map updates ask this to give the
 * mouse to the placement box. */
#include "mod_20c30.h"

/* @0x22538 */
unsigned short PlaceBoxActive(void)
{
    return place_active[net_event_pending];
}
