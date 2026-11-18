/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * DpmiLockRegion (0x312f0): lock a linear region for interrupt-time use
 * (DPMI int 31h ax=600h, bx:cx = address, si:di = size).  "OD" style.
 *
 * The address is latched in one local (`lin`) declared before the register
 * union: Watcom 10.0a allocates stack slots in declaration order, and the
 * original's frame is REGS (-0x28), size (-0xc), addr (-8), lin (-4).  The
 * register block is filled through the word view (`r.w.ax` ... `r.w.di`),
 * which is what makes the original's word stores at +0/+4/+8/+0x10/+0x14.
 * Failure of the DPMI call is fatal ("evt lock", 0x57e54).
 */
#include <i86.h>

#include "input.h"

void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

/* @0x312f0 */
void DpmiLockRegion(void *addr, unsigned size)
{
    unsigned lin = (unsigned)addr;
    union REGS r;

    r.w.ax = 0x600;
    r.w.bx = lin >> 16;
    r.w.cx = lin;
    r.w.si = size >> 16;
    r.w.di = size;
    int386(0x31, &r, &r);
    if (r.x.cflag)
        FatalError("evt lock");
}
