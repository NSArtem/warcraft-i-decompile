/* codegen-compiler: 10.0a */
#include "playflic.h"
#include <stdio.h>

extern FILE *flic_file; /* 0x594e0, loaded at 0x1904f */
extern int FileSeek(FILE *fp, long offset, int whence); /* 0x31a80 */

/* 0x19048: widen whence and discard the result of the call at 0x19059. */
void FlicSeek(long offset, unsigned short whence)
{
    FileSeek(flic_file, offset, whence);
}
