/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "audio.h"

extern unsigned short *anim_table;
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *ResourceRead(void *dest, unsigned count);

/* @0x26320 */
void AnimTableLoad(void)
{
    ResourceBegin(0xd6, 0);
    anim_table = (unsigned short *)ResourceRead(0, 0);
}
