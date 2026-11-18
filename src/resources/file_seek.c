/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileSeek (0x31a80), built from C: like its neighbours a retrying wrapper,
 * but a failed fseek (0x3bb86) is fatal ("file seek error (%d)\n", 0x57e6c)
 * instead of prompting.  One function per object.
 */
#include <stdio.h>
#include <errno.h>
#include "resources.h"

/* @0x31a80  seek; the caller's errno is cleared first so the fatal message
 * reports only this call's failure. */
int FileSeek(FILE *fp, long offset, int whence)
{
    int r;

    errno = 0;
    r = fseek(fp, offset, whence);
    if (r == -1)
        FatalError("file seek error (%d)\n", errno);
    return r;
}
