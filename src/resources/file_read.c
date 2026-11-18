/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileRead (0x31adc), built from C: retrying wrapper around the clib fread
 * (0x3bc82).  One function per object.
 */
#include <stdio.h>
#include "resources.h"

/* @0x31adc  read n items of size bytes; on a DOS critical error the stream
 * is rewound to the position saved before the call and the read retried.
 * A short read without that flag (EOF) is returned as is. */
size_t FileRead(void *buf, size_t size, size_t n, FILE *fp)
{
    size_t r;
    long pos;

    pos = FileTell(fp);
    for (;;) {
        crit_error_flag = 0;
        r = fread(buf, size, n, fp);
        if (r == n || crit_error_flag == 0)
            return r;
        CriticalErrorPrompt();
        FileSeek(fp, pos, 0);
    }
}
