/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * MouseButtonEvent (0x30fa8): fill the button template with (type, sub) and
 * queue it.  Called by MouseCallback for the four button bits with
 * (2,4) (4,5) (8,6) (16,7).
 */
#include "input.h"

/* @0x30fa8 */
void MouseButtonEvent(unsigned short type, unsigned short sub)
{
    evt_button.type = type;
    evt_button.sub = sub;
    EvtPost(&evt_button);
}
