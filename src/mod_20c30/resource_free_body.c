/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -zp2
 * mod_21cf0 (0x21cf0..0x21df0): the layer registry helpers.  ResourceFreeBody
 * frees the pixel body of an 8-byte resource header ({w,h} then the body
 * pointer).  status.h calls the same function LayerFree.  It is named by
 * playflic.toml (0x21cf0), so no symbol entry is repeated here; the C is
 * reported for the owner to wire. */
#include "mod_20c30.h"

/* @0x21cf0 */
void ResourceFreeBody(Bitmap *hdr)
{
    if (hdr->data != 0) {
        GdsFree(hdr->data);
        hdr->data = 0;
    }
}
