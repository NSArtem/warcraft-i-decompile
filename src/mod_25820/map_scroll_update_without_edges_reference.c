/* codegen-compiler: 10.0a */
#include "war.h"

extern unsigned int MapScrollApplyDeltas(short dx, short dy); /* 0x25b54 calls 0x259d8; 0x25b59 stores EAX. */
extern void MapPickOrderTarget(unsigned short *cursor_shape); /* 0x25b5e: the local's address; 0x2df9c writes its low word only. */

unsigned int MapScrollUpdateWithoutEdges(void)
{
    unsigned int shape;

    shape = MapScrollApplyDeltas(0, 0);
    MapPickOrderTarget((unsigned short *)&shape);
    return shape;
}
