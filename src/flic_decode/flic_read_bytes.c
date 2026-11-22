/* codegen-compiler: 10.0a */
#include "playflic.h"
#include <stdio.h>

extern FILE *flic_file; /* 0x594e0, loaded into ECX at 0x19023 */
extern size_t FileRead(void *buf, size_t size, size_t n, FILE *fp); /* 0x31adc */

/* 0x19020: read byte-sized elements and compare the count at 0x1903a. */
short FlicReadBytes(void *dst, unsigned short count)
{
    return (size_t)count == FileRead(dst, 1, count, flic_file);
}
