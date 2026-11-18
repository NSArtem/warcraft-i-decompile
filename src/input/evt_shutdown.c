/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtShutdown (0x31764): free the event ring allocated by EvtInit.  The
 * original's `sub esp,0` OD frame (no `mov esp,ebp` in the epilogue) is
 * reproduced by Watcom 10.0a only.
 */
#include "input.h"

void GdsFree(void *p);                  /* 0x32780 */

/* @0x31764 */
void EvtShutdown(void)
{
    GdsFree(evt_queue);
}
