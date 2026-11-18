/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * Module mod_33040 (0x33040..0x330a0), DBG style: INT 33h functions 7/8
 * (set horizontal/vertical mouse range).  TOML entry in input.toml.
 */
#include <i86.h>
#include "graphics.h"

/* @0x33040 */
void MouseSetRange(unsigned short xmin, unsigned short ymin,
                   unsigned short xmax, unsigned short ymax)
{
    union REGS r;

    r.x.ecx = xmin * 2;
    r.x.edx = xmax * 2;
    r.x.eax = 7;
    int386(0x33, &r, &r);
    r.x.ecx = ymin;
    r.x.edx = ymax;
    r.x.eax = 8;
    int386(0x33, &r, &r);
}
