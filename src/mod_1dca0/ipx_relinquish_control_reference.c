/* codegen-compiler: 10.0a */
#include <string.h>
#include "mod_1dca0.h"

typedef struct {
    unsigned long edi, esi, ebp, res, ebx, edx, ecx, eax;
    unsigned short flags, es, ds, fs, gs, ip, cs, sp, ss;
} RealRegs;

extern void fn_23e50(unsigned int n, RealRegs *r);

/* @0x1dda0 */
void IpxRelinquishControl(void)
{
    RealRegs r;

    memset(&r, 0, 0x32);
    r.ebx = 10;
    fn_23e50(0x7a, &r);
}
