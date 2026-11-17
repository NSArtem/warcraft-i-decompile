/* codegen-flags: -s -ot -ol -4r -d1+ -zp1
 * REFERENCE C for RegisterCodec (module 0x3b980..0x3b9b1, "DBG" style),
 * the codec-table registration used by InitResources.  Not built: the body
 * matches byte for byte except the first push - OW2 keeps the codec id in
 * ecx where the original uses ebx (codegen.md V3), so this is T4 (wc1.cemu),
 * see docs/subsystems/resources.md.
 *
 * The -zp1 pack is needed because the descriptor is 17 bytes: id byte at +0,
 * then the four function pointers at +1/+5/+9/+0xd (analysis/symbols/
 * resources.toml, codec_table).
 */
#include <stdlib.h>
#include "resources.h"

typedef struct CodecDesc {
    unsigned char id;
    void (*alloc)(void);
    void (*begin)(void);
    void (*decode)(void);
    void (*free)(void);
} CodecDesc;

extern CodecDesc codec_table[8];       /* 0x56524 */

/* @0x3b980  copy a codec descriptor into its table slot (17 bytes, the
 * original inlines the copy as 4 movsd + 1 movsb), call the codec's alloc
 * hook, then register its free hook with atexit. */
void RegisterCodec(CodecDesc *desc)
{
    *(CodecDesc *)((unsigned char *)codec_table + desc->id * 17) = *desc;
    desc->alloc();
    atexit(desc->free);
}
