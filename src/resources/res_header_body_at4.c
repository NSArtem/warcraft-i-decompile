/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * ResourceReadHeaderBodyAt4 (0x318f0), built from C: one function per object
 * (the neighbours 0x31870/0x31920 belong to other areas or are not C yet).
 */
#include "resources.h"

/* @0x318f0  read the first 4 bytes of the current resource into p, then a
 * 4-byte header + body pair into p+4 (an 8-byte header structure). */
void ResourceReadHeaderBodyAt4(void *p, void *dest)
{
    ResourceRead(p, 4);
    ResourceReadHeaderBody((char *)p + 4, dest);
}
