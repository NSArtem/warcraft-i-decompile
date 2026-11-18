/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileGetc (0x31a18), built from C: retrying wrapper around the clib fgetc
 * (0x3b9e1).  One function per object.
 */
#include <stdio.h>
#include "resources.h"

/* @0x31a18  read one byte; on a DOS critical error the stream is rewound to
 * the position saved before the call and the read is retried. */
int FileGetc(FILE *fp)
{
    int c;
    long pos;

    pos = FileTell(fp);
    for (;;) {
        crit_error_flag = 0;
        c = fgetc(fp);
        if (c != -1 || crit_error_flag == 0)
            return c;
        CriticalErrorPrompt();
        FileSeek(fp, pos, 0);
    }
}
