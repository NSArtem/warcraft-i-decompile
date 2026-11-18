/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * REFERENCE C for the stored (codec 0) resource decoder: StoredBegin is a
 * no-op (built from src/codegen/mod_409a0.c) and StoredRead copies the
 * remaining bytes straight out of the archive FILE.  StoredRead is built
 * from C: T3 under Watcom 10.0a (under OW2 the DBG object's register
 * assignment differed and it was T4 only, wc1.cemu).
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
