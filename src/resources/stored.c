/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * REFERENCE C for the stored (codec 0) resource decoder: StoredBegin is a
 * no-op (built from src/codegen/mod_409a0.c) and StoredRead copies the
 * remaining bytes straight out of the archive FILE.  Not built: the DBG
 * object's register assignment differs (see the t3_blocker in
 * analysis/symbols/resources.toml); verified as T4 with wc1.cemu.
 */
#include "resources.h"

extern const char *archive_read_error;          /* 0x55820 */

/* @0x409a0  copy `count` bytes of the current resource to dest, decrementing
 * the unpacked-bytes counter; a short read is fatal. */
void StoredRead(void *dest, unsigned count)
{
    res_remaining -= count;
    if (FileRead(dest, count, 1, archive_file) != 1)
        FatalError((char *)archive_read_error);
}
