/* codegen-compiler: 10.0a */
#include <string.h>
#include "dos_realmode_mem_f1.h"
#include "mod_1dca0.h"

typedef struct {
    unsigned long edi, esi, ebp, res, ebx, edx, ecx, eax;
    unsigned short flags, es, ds, fs, gs, ip, cs, sp, ss;
} RealRegs;

/* @0x1de14 */
void IpxSendPacket(unsigned seg, unsigned off)
{
    RealRegs r;

    memset(&r, 0, 0x32);
    r.es = (unsigned short)seg;
    r.esi = (unsigned short)off;
    r.ebx = 3;
    RealModeInt(0x7a, &r);
}
