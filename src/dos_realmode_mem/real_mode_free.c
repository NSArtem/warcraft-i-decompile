/* codegen-compiler: 10.0a */
#include "dos_realmode_mem_f1.h"
#include <i86.h>
#include <dos.h>
#include "war.h"

/* @0x23dd8 */
void RealModeFree(RealModeBlock *b)
{
    union REGS r;

    r.x.eax = 0x101;
    r.x.edx = b->sel;
    int386(0x31, &r, &r);
    GdsFree(b);
}
