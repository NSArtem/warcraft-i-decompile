/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * Module mod_3b360 (0x3b360..0x3b3a0), video library, "DBG" style. */
#include "war.h"
#include "graphics.h"

extern Bitmap backbuf_bm;               /* 0x5a870 */
extern Bitmap cursor_save_bm;           /* 0x5ad10 */

/* @0x3b360 */
void VidAllocBackbuffer(void)
{
    /* volatile: OW2 would merge the two adjacent 16-bit stores into one 32-bit store
       (`mov dword [..],0xc80140`); the original stores them separately. */
    *(volatile short *)&backbuf_bm.w = 320;
    *(volatile short *)&backbuf_bm.h = 200;
    backbuf_bm.data = GdsAlloc(0xfa00);
    cursor_save_bm.data = GdsAlloc(0x100);
}
