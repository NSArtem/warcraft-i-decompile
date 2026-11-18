/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * ResourceReadHeaderBody (0x323e0), built from C: one function per object
 * (the neighbours 0x31920/0x32410 are not part of this area).
 */
#include "resources.h"

/* @0x323e0  read the 4-byte header of the current resource into hdr4, then
 * the rest of the resource into dest (allocating it when dest is 0) and store
 * the resulting body pointer at hdr4+4. */
void ResourceReadHeaderBody(void *hdr4, void *dest)
{
    ResourceRead(hdr4, 4);
    ((void **)hdr4)[1] = ResourceRead(dest, 0);
}
