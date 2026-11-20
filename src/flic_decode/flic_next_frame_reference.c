/* codegen-compiler: 10.0a */
#include "playflic.h"

extern unsigned short dat_517c8;   /* 0x517c8 flic open flag */
extern short fn_192f0(void);       /* 0x192f0 decode next frame */

/* @0x19450 */
short FlicNextFrame(void)
{
    if (dat_517c8 == 0) {
        return 0;
    }
    return fn_192f0();
}
