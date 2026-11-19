/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* FormatNumber (0x2f830): sprintf the value, then copy the digits into the
 * destination with a leading space and a ',' after every third digit. */
#include "mod_2efd0.h"

/* @0x2f830 */
char *FormatNumber(char *buf, long value, char *out)
{
    short n;

    sprintf(buf, "%ld", value);
    n = strlen(buf);
    *out++ = ' ';
    while (--n != -1) {
        *out++ = *buf++;
        if (n == 3 || n == 6)
            *out++ = ',';
    }
    *out = 0;
    return out;
}
