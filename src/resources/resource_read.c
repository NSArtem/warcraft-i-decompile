/* codegen-flags: -s -ot -ol -4r -d1+ -zp1
 * codegen-compiler: 10.0a
 * ResourceRead (0x32740), built from C: T3 under Watcom 10.0a.  Split out of
 * src/resources/archive.c (reference C under OW2), whose declarations it repeats;
 * one function per object (wcc386 aligns the next function).
 */
#include <stdlib.h>
#include "resources.h"

extern unsigned long archive_count;             /* 0x62894 */
extern const char *archive_version_error;      /* 0x62890 */
extern const char *archive_read_error;          /* 0x55820 */
extern unsigned char res_codec;                 /* 0x5ad44 */

struct CodecDesc {
    unsigned char id;
    void (*alloc)(void);
    void (*begin)(void);
    void (*decode)(void *dest, unsigned count);
    void (*free)(void);
};
extern struct CodecDesc codec_table[8];         /* 0x56524 */

/* @0x32740  decode the current resource into dest (allocating it when dest
 * is 0, with count defaulting to the unpacked size); returns dest. */
void *ResourceRead(void *dest, unsigned count)
{
    if (count == 0)
        count = (unsigned)res_remaining;
    if (dest == 0)
        dest = GdsAlloc(count);
    codec_table[res_codec].decode(dest, count);
    return dest;
}
