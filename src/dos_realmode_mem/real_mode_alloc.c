/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "dos_realmode_mem_f1.h"
#include <i86.h>
#include <dos.h>
#include "war.h"

/* @0x23d10 */
RealModeBlock *RealModeAlloc(unsigned size)
{
    union REGS r;
    RealModeBlock *b;
    long c;

    r.x.eax = 0x100;
    r.x.ebx = (long)((size & 0xffff) + 15) >> 4;
    int386(0x31, &r, &r);
    c = r.x.cflag;
    if (c == 0) {
        b = (RealModeBlock *)GdsAlloc(10);
        if (b != 0) {
            b->sel = (unsigned short)r.x.edx;
            b->seg = (unsigned short)r.x.eax;
            b->sel4 = b->sel;
            b->err = c;
            return b;
        }
    }
    FatalError(str_rm_alloc_fail);
    return 0;
}
