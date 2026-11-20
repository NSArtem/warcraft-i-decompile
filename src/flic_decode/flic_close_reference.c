/* codegen-compiler: 10.0a */
#include "playflic.h"

extern int FileClose(void *fp);
extern unsigned short dat_517c8;
extern void *dat_594e0;

/* @0x193dc */
void FlicClose(void)
{
    if (dat_517c8 != 0) {
        dat_517c8 = 0;
        FileClose(dat_594e0);
    }
}
