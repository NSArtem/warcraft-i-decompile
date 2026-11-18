/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * Byte-matched function of module mod_24860 (the save-file loader/writer),
 * taken from C by the build (src = ... in analysis/symbols/mod_24860.toml).
 * One function per file, like ref_relocate.c, so the build can place it at
 * its own original address.
 */
#include <string.h>
#include "mod_24860.h"

/* @0x249a4  read `count` bytes from the loaded image into dst.
 *
 * The stream position is a raw pointer into the image (SaveLoadImage's
 * buffer) and the bytes-left counter is decremented by the 16-bit count;
 * returns the new position.  Only the low 16 bits of count are used (the
 * save blocks are all < 0x10000).
 */
unsigned char *SaveReadStream(void *dst, unsigned count, unsigned char *pos)
{
    save_stream_left -= (unsigned short)count;
    memcpy(dst, pos, (unsigned short)count);
    return pos + (unsigned short)count;
}
