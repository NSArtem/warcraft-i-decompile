/* codegen-compiler: 10.0a */
#include "war.h"
#include <stdio.h>

extern FILE runtime_stderr_stream;
extern const char startup_usage_text[];
extern void exit(int status);

/* 0x1d60b writes usage to stderr; 0x1d615 calls exit with status 1. */
void PrintUsageAndExit(void)
{
    fputs(startup_usage_text, &runtime_stderr_stream);
    exit(1);
}
