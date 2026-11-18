/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * DpmiUnlockRegion (0x31360): the mirror of DpmiLockRegion (int 31h
 * ax=601h); failure is fatal with "evt unlock" (0x57e60).  Same frame and
 * word-view register stores as 0x312f0.
 */
#include <i86.h>

#include "input.h"

void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

/* @0x31360 */
void DpmiUnlockRegion(void *addr, unsigned size)
{
    unsigned lin = (unsigned)addr;
    union REGS r;

    r.w.ax = 0x601;
    r.w.bx = lin >> 16;
    r.w.cx = lin;
    r.w.si = size >> 16;
    r.w.di = size;
    int386(0x31, &r, &r);
    if (r.x.cflag)
        FatalError("evt unlock");
}
