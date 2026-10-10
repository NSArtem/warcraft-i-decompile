/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module mod_3b360 (0x3b360..0x3b3a0), video library, "DBG" style. */
#include "graphics.h"

extern Bitmap backbuf_bm;               /* 0x5a870 */
extern unsigned char *dat_5a874;        /* pixel buffer, allocated just after the Bitmap header */
extern unsigned char *dat_5ad14;
extern void *fn_32558(unsigned size);   /* GDS malloc with CHECKSIG guard */

/* @0x3b360 */
void VidAllocBackbuffer(void)
{
    /* volatile: OW2 would merge the two adjacent 16-bit stores into one 32-bit store
       (`mov dword [..],0xc80140`); the original stores them separately. */
    *(volatile short *)&backbuf_bm.w = 320;
    *(volatile short *)&backbuf_bm.h = 200;
    backbuf_bm.data = fn_32558(0xfa00);
    dat_5ad14 = fn_32558(0x100);
}
