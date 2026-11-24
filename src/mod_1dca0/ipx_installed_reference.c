/* codegen-compiler: 10.0a */
#include <string.h>
#include "dos_realmode_mem_f1.h"
#include "mod_1dca0.h"

typedef struct {
    unsigned long edi, esi, ebp, res, ebx, edx, ecx, eax;
    unsigned short flags, es, ds, fs, gs, ip, cs, sp, ss;
} RealRegs;

/* @0x1dca0 */
unsigned short IpxInstalled(void)
{
    RealRegs r;

    memset(&r, 0, 0x32);
    r.eax = 0x7a00;
    RealModeInt(0x2f, &r);
    return (r.eax & 0xff) == 0xff;
}
