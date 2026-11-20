/* codegen-compiler: 10.0a */
#include "playflic.h"

extern void fn_19048(long off, unsigned short whence);
extern short fn_192f0(void);
extern unsigned short dat_517c8;
extern long dat_59490;

/* @0x193fc */
short FlicRewind(void)
{
    if (dat_517c8 == 0) {
        return 0;
    }
    fn_19048(dat_59490, 0);
    return fn_192f0();
}
