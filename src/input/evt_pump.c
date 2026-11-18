/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtPump (0x31568): drain the queue, handing every event to EvtProcess
 * (which updates the key state and discards the event).  One 12-byte Event
 * lives on the stack.
 */
#include "input.h"

void EvtProcess(Event *ev);             /* 0x32b40 */

/* @0x31568 */
void EvtPump(void)
{
    Event ev;

    while ((short)EvtGet(&ev))
        EvtProcess(&ev);
}
