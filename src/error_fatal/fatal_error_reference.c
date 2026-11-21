/* codegen-compiler: 10.0a */
/* codegen-flags: -s -ot -ol -4r -of+ -zp2 */
#include "error_fatal_c.h"
#include <stdarg.h>

extern void (*fatal_hook)(const char *fmt, va_list *args);
extern char str_error_hdr[];
extern char str_error_tail[];
extern void __run_atexit(int status);
extern int puts(const char *s);
extern int vprintf(const char *fmt, va_list args);
extern void __exit(int status);

void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

void FatalError(const char *fmt, ...)
{
    va_list ap;

    __run_atexit(1);
    va_start(ap, fmt);
    if (fatal_hook) {
        fatal_hook(fmt, &ap);
    }
    puts(str_error_hdr);
    vprintf(fmt, ap);
    va_end(ap);
    puts(str_error_tail);
    __exit(1);
}
