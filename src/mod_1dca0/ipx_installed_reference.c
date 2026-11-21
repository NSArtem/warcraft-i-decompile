/* codegen-compiler: 10.0a */
#include <string.h>

typedef struct {
    unsigned long edi, esi, ebp, res, ebx, edx, ecx, eax;
    unsigned short flags, es, ds, fs, gs, ip, cs, sp, ss;
} RealRegs;

extern void fn_23e50(unsigned int n, RealRegs *r);

/* @0x1dca0 */
unsigned short IpxInstalled(void)
{
    RealRegs r;

    memset(&r, 0, 0x32);
    r.eax = 0x7a00;
    fn_23e50(0x2f, &r);
    return (r.eax & 0xff) == 0xff;
}
