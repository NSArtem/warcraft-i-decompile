/* codegen-compiler: 10.0a */
#include "mod_348c0_c.h"

extern void VLine(int x, int y, int len);
extern void HLine(int x, int y, int len);

/* @0x348c0 */
void RectOutline(short x, short y, unsigned short w, unsigned short h)
{
    long sx;
    long sy;

    sy = *(long *)((char *)&y - 2) >> 16;
    sx = *(long *)((char *)&x - 2) >> 16;
    HLine(sx, sy, w);
    HLine(sx, (short)(y + h - 1), w);
    VLine(sx, sy, h);
    VLine((short)(x + w - 1), sy, h);
}
