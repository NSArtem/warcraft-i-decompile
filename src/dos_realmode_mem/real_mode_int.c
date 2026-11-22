/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "dos_realmode_mem_f1.h"
#include <i86.h>
#include <dos.h>
#include <string.h>

/* @0x23e50 */
void RealModeInt(unsigned char intno, void *rmregs)
{
    union REGS r;
    struct SREGS s;

    memset(&r, 0, sizeof(r));
    segread(&s);
    r.w.ax = 0x300;
    r.h.bl = intno;
    r.h.bh = 0;
    r.w.cx = 0;
    s.es = FP_SEG((void __far *)rmregs);
    r.x.edi = (unsigned long)rmregs;
    int386x(0x31, &r, &r, &s);
}
