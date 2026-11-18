/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtShutdownMouse (0x31538): INT 33h ax=0 resets the driver, which also
 * removes MouseCallback.  Registered as an exit handler by EvtStartup only
 * when EvtInitMouse found a driver.
 */
#include <i86.h>

/* @0x31538 */
void EvtShutdownMouse(void)
{
    union REGS r;

    r.x.eax = 0;
    int386(0x33, &r, &r);
}
