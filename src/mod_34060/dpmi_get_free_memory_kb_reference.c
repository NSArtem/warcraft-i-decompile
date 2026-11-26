/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -5r -d1+ -zp2 */
#include <i86.h>
#include "mod_34060.h"

/* @0x34060  DPMI 0500h Get Free Memory Information */
unsigned long DpmiGetFreeMemoryKB(void)
{
    union REGS r;
    struct SREGS s;
    unsigned long buf[12];

    segread(&s);
    r.x.eax = 0x500;
    s.es = FP_SEG(buf);
    r.x.edi = (unsigned long)buf;
    int386x(0x31, &r, &r, &s);
    return buf[4] * 4;
}
