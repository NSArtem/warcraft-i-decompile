/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileWrite (0x31b54), built from C: same retry structure as FileRead
 * (0x31adc) around the clib fwrite (0x3be4c).  One function per object.
 */
#include <stdio.h>
#include "resources.h"

/* @0x31b54  write n items of size bytes; on a DOS critical error the stream
 * is rewound to the position saved before the call and the write retried. */
size_t FileWrite(const void *buf, size_t size, size_t n, FILE *fp)
{
    size_t r;
    long pos;

    pos = FileTell(fp);
    for (;;) {
        crit_error_flag = 0;
        r = fwrite(buf, size, n, fp);
        if (r == n || crit_error_flag == 0)
            return r;
        CriticalErrorPrompt();
        FileSeek(fp, pos, 0);
    }
}
