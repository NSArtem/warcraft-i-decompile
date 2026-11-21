/* codegen-compiler: 10.0a */
#include <string.h>
#include "mod_1dca0.h"

typedef struct {
    unsigned long edi, esi, ebp, res, ebx, edx, ecx, eax;
    unsigned short flags, es, ds, fs, gs, ip, cs, sp, ss;
} RealRegs;

extern void fn_23e50(unsigned int n, RealRegs *r);

/* @0x1dd5c */
void IpxGetInternetworkAddress(unsigned seg, unsigned off)
{
    RealRegs r;

    memset(&r, 0, 0x32);
    r.es = (unsigned short)seg;
    r.esi = (unsigned short)off;
    r.ebx = 9;
    fn_23e50(0x7a, &r);
}
