/* codegen-compiler: 10.0a */
#include "audio.h"

typedef struct Unit Unit;
extern unsigned short *anim_table;

/* @0x26360 */
void fn_26360(Unit *u, unsigned char anim)
{
    unsigned char *p = (unsigned char *)u;
    unsigned short base;
    unsigned short idx;

    base = anim_table[p[0x1b]];
    base = base >> 1;
    idx = (unsigned short)(base + anim);
    *(unsigned short *)(p + 4) = anim_table[idx];
    p[6] = 1;
}
