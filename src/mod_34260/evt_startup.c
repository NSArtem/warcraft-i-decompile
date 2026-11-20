/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_34260_c.h"

extern void EvtHookKeyboard(void);
extern short EvtInitMouse(void);
extern void EvtInit(unsigned short queue_size);
extern int atexit(void (*fn)(void));
extern void EvtShutdown(void);
extern void EvtUnhookKeyboard(void);
extern void EvtShutdownMouse(void);

/* @0x34260 */
void EvtStartup(void)
{
    atexit(0);
    EvtInit(0x20);
    atexit(EvtShutdown);
    EvtHookKeyboard();
    atexit(EvtUnhookKeyboard);
    if (EvtInitMouse() != 0) {
        atexit(EvtShutdownMouse);
    }
}
