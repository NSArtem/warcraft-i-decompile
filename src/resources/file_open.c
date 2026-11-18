/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileOpen (0x31964), built from C: retrying wrapper around the clib fopen
 * (0x33d2c) for DOS critical errors.  One function per object.
 */
#include <stdio.h>
#include "resources.h"

/* @0x31964  open a stream; on a DOS critical error (disk change, bad sector)
 * show the abort/retry prompt and try again.  While the optional-file probe
 * counter is set, a failure is returned quietly. */
FILE *FileOpen(const char *name, const char *mode)
{
    FILE *fp;

    for (;;) {
        crit_error_flag = 0;
        fp = fopen(name, mode);
        if (fp != 0 || file_open_noprompt != 0 || crit_error_flag == 0)
            return fp;
        CriticalErrorPrompt();
    }
}
