/* codegen-flags: -s -ot -ol -4r -d1+ -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_34350.h"

/* @0x34350 read 4 bytes into hdr4, then a body pointer stored at hdr4+4 */
void ResourceReadHeaderBody2(void *hdr4, void *dest)
{
    ResourceRead(hdr4, 4);
    *(void **)((char *)hdr4 + 4) = ResourceRead(dest, 0);
}
