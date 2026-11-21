/* codegen-compiler: 10.0a */
#include <i86.h>
#include "mod_20a80.h"

/* @0x20ba8 */
unsigned NetDriverReceiveChecked(void *buf_off, unsigned buf_seg)
{
    unsigned r;
    unsigned short __far *p;

    r = ((unsigned (*)(void))net_driver_receive)();
    p = (unsigned short __far *)MK_FP(buf_seg, (unsigned)buf_off);
    if ((unsigned short)r != 0 && (unsigned short)r != p[1])
        return 0xffff;
    return r;
}
