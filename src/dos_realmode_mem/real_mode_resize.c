/* codegen-compiler: 10.0a */
#include "dos_realmode_mem_f1.h"
#include <i86.h>
#include <dos.h>
#include "war.h"

/* @0x23d88 */
void RealModeResize(RealModeBlock *b, unsigned size)
{
    union REGS r;

    r.x.eax = 0x102;
    r.x.edx = b->sel;
    r.x.ebx = ((unsigned short)size + 15) >> 4;
    int386(0x31, &r, &r);
    if (r.x.cflag != 0) {
        FatalError(str_rm_resize_fail);
    }
}
