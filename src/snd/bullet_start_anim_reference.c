/* codegen-compiler: 10.0a */
#include "audio.h"

typedef struct Bullet Bullet;
extern unsigned short *anim_table;

/* @0x26390 */
void BulletStartAnim(Bullet *b, unsigned short anim)
{
    unsigned char *p = (unsigned char *)b;
    unsigned short base;
    unsigned short idx;

    base = anim_table[0x34 + p[0]];
    base = base >> 1;
    idx = (unsigned short)(base + anim);
    *(unsigned short *)(p + 0xa) = anim_table[idx];
    p[0xc] = 1;
}
