/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileTell (0x319c4), built from C: retrying wrapper around the clib ftell
 * (0x3b9b1).  One function per object.
 */
#include <stdio.h>
#include "resources.h"

/* @0x319c4  current stream position; a DOS critical error while the clib
 * reads the position shows the abort/retry prompt and retries. */
long FileTell(FILE *fp)
{
    long pos;

    for (;;) {
        crit_error_flag = 0;
        pos = ftell(fp);
        if (pos != -1 && crit_error_flag == 0)
            return pos;
        CriticalErrorPrompt();
    }
}
