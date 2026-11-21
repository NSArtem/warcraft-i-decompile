/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_16390.h"

extern unsigned short evt_mask;
extern void (*event_handlers[10])(Event *ev);

/* @0x18488 */
void UiInputInit(void)
{
    ui_button_bits = 0;
    evt_mask = 0x59f;
    memset(event_handlers, 0, 0x28);
    MouseSetRange(0, 0, 0x13f, 0xc7);
    EvtPump();
}
