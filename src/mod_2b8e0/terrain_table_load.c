/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_2b8e0.h"

extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *GdsAlloc(unsigned size);
extern void *ResourceRead(void *dest, unsigned count);

/* @0x2b8e0 */
void TerrainTableLoad(unsigned short id, void **out, unsigned short *hdr)
{
    unsigned long len;

    len = ResourceBegin(id, 0);
    *out = GdsAlloc((unsigned short)len - 4);
    ResourceRead(hdr, 4);
    hdr[1]--;
    ResourceRead(*out, 0);
}
