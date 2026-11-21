/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "audio.h"

extern unsigned short *anim_table;
extern void GdsFree(void *p);

/* @0x26340 */
void AnimTableFree(void)
{
    if (anim_table != 0) {
        GdsFree(anim_table);
        anim_table = 0;
    }
}
