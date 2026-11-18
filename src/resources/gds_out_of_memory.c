/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * GdsOutOfMemory (0x32540), built from C: the default GDS no-memory hook
 * (gds_nomem_handler 0x55440 is initialised with its address).  One function
 * per object.
 */
#include "war.h"

/* @0x32540  the game cannot continue without the block: fail fatally. */
void GdsOutOfMemory(void)
{
    FatalError("out of memory");
}
