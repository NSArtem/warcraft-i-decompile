/* codegen-compiler: 10.0a */
#include "war.h"

extern unsigned int MapScrollApplyDeltas(short dx, short dy); /* 0x25b54 calls 0x259d8; 0x25b59 stores EAX. */
extern void fn_2df9c(unsigned int *shape); /* 0x25b5e calls 0x2df9c with the local's address. */

unsigned int MapScrollUpdateWithoutEdges(void)
{
    unsigned int shape;

    shape = MapScrollApplyDeltas(0, 0);
    fn_2df9c(&shape);
    return shape;
}
