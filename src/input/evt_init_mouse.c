/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * EvtInitMouse (0x314a4): INT 33h ax=0 (driver reset), then install
 * MouseCallback for "movement + all four buttons" (ax=0Ch, cx=1Fh).  Returns
 * 0 when no mouse driver is present (ax != FFFFh after the reset).
 */
#include <i86.h>

#include "input.h"

void __far MouseCallback(void);                 /* 0x30fe0, INT 33h callback */
/* the callback is hand-written (far return), so its asm name carries no
 * underscore (analysis/symbols/input.toml conv = "asm") */
#pragma aux MouseCallback "MouseCallback"

/* @0x314a4 */
short EvtInitMouse(void)
{
    union REGS r;
    struct SREGS s;

    segread(&s);
    r.x.eax = 0;
    int386(0x33, &r, &r);
    if (r.w.ax != 0xffff)
        return 0;
    r.w.ax = 0x0c;
    r.w.cx = 0x1f;
    r.x.edx = FP_OFF(MouseCallback);
    s.es = FP_SEG(MouseCallback);
    int386x(0x33, &r, &r, &s);
    return 1;
}
