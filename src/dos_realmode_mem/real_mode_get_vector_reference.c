/* codegen-compiler: 10.0a */
#include <i86.h>
#include <dos.h>
#include <string.h>
#include "dos_realmode_mem_f1.h"

/* Watcom 10.0a has no 64-bit return; the original returns eax = segment and
   edx = offset, so load edx with an empty aux function just before returning. */
extern void SetEdx(unsigned long v);
#pragma aux SetEdx = "" parm [edx] modify exact [];

/* @0x23e10 */
unsigned long RealModeGetVector(unsigned char intno)
{
    union REGS r;
    unsigned long seg;

    memset(&r, 0, sizeof(r));
    r.w.ax = 0x200;
    r.h.bl = intno;
    int386(0x31, &r, &r);
    seg = r.w.dx;
    SetEdx(r.x.ecx);
    return seg;
}
