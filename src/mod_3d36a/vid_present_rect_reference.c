/* codegen-compiler: 10.0a */
#include "mod_3d36a_c.h"

extern char *dat_5a874;
extern short dirty_x1;
extern short dirty_y1;
extern short dirty_w;
extern short dirty_h;

/* @0x3d560 */
void VidPresentRect(void)
{
    unsigned off;
    unsigned long *src;
    unsigned long *dst;
    unsigned w;
    unsigned h;
    unsigned n;
    unsigned skip;

    off = (unsigned short)(dirty_y1 * 0x140 + dirty_x1);
    src = (unsigned long *)(dat_5a874 + off);
    dst = (unsigned long *)(off + 0xa0000);
    w = (unsigned short)dirty_w;
    skip = 0x140 - w;
    h = (unsigned short)dirty_h;
    do {
        n = w >> 2;
        do {
            *dst++ = *src++;
        } while (--n != 0);
        src = (unsigned long *)((char *)src + skip);
        dst = (unsigned long *)((char *)dst + skip);
    } while (--h != 0);
}
