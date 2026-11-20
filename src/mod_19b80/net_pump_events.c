/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_19b80_c.h"

extern unsigned short net_event_pending;
extern void UiInputInit(void);
extern void PlaceBoxCancel(void);
extern void StatusPanelLockClear(void);
extern void fn_2b390(void);
extern void MouseSetRange(short xmin, short ymin, short xmax, short ymax);

/* @0x19b80 */
void NetPumpEvents(void)
{
    unsigned short saved = net_event_pending;

    for (net_event_pending = 0; net_event_pending < 2; net_event_pending++) {
        PlaceBoxCancel();
        fn_2b390();
    }
    net_event_pending = saved;
    UiInputInit();
    MouseSetRange(0, 0, 0x13f, 0xc7);
    StatusPanelLockClear();
}
