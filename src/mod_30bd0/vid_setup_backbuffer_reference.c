/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
#include "mod_30bd0_f1.h"

extern void VidAllocBackbuffer(unsigned a, unsigned b);
extern void VidResetLayers(void);

/* @0x30bd0 */
void VidSetupBackbuffer(unsigned short arg)
{
    VidAllocBackbuffer(0, arg);
    VidResetLayers();
}
