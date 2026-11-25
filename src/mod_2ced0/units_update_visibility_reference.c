/* codegen-compiler: 10.0a */
#include "mod_2ced0_c7.h"

extern void *unit_array;
extern short unit_type_size[52][2];
extern union { unsigned long w; unsigned char b[4]; } cheat_flags;
extern int FogRectMatchesMask(const short *xy, const short *size, unsigned short mask, unsigned short expected);

void UnitsUpdateVisibility(void)
{
    struct Unit *u;
    const short *xy;
    const short *size;
    short left;
    unsigned masked;
    unsigned offset;

    u = unit_array;
    left = 200;
    xy = u->tile_xy;
    goto test_count;

next_record:
    *(volatile unsigned char *)&u->visibility |= 3;
    masked = *(volatile unsigned short *)&u->flags & 0x020dU;
    if ((unsigned short)masked == 0) {
        if (cheat_flags.w & 1UL) {
            *(volatile unsigned char *)&u->visibility &= 0xfc;
        } else {
            offset = u->type;
            offset <<= 2;
            size = (const short *)((const char *)unit_type_size + offset);
            if ((short)FogRectMatchesMask(xy, size, 0x001f, 0x000a) == 0)
                *(volatile unsigned char *)&u->visibility &= 0xfe;
            offset = u->type;
            offset <<= 2;
            size = (const short *)((const char *)unit_type_size + offset);
            if ((short)FogRectMatchesMask(xy, size, 0x1f00, 0x0a00) == 0)
                *(volatile unsigned char *)&u->visibility &= 0xfd;
        }
    }
    xy = (const short *)((const char *)xy + sizeof(*u));
    ++u;

test_count:
    if (--left != -1)
        goto next_record;
}
