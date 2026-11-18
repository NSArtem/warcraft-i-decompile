/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 *
 * Module mod_13f60 (DGLS.C): the save-slot file checksum.
 * Reference C (not difftested: the original's FileRead/FileSeek go through the
 * segmented stdio of the 10.0a runtime).  The on-disk layout is
 * docs/subsystems/save_format.md section 1. */
#include "mod_13f60.h"

long FileSeek(FILE *fp, long offset, int whence);   /* 0x31a80 */
int FileRead(void *buf, unsigned size, unsigned n, FILE *fp);   /* 0x31adc */
int FileWrite(const void *buf, unsigned size, unsigned n, FILE *fp); /* 0x31b54 */
int FileClose(FILE *fp);                            /* 0x31940 */
FILE *FileOpen(const char *name, const char *mode); /* 0x31964 */

void SaveSlotPath(char *path, unsigned short slot);  /* 0x14740 */

/* @0x14670: seek to the image start (0x2c) and fold every dword of the file
 * into sum = (sum + dword) * 2, reading 200 bytes at a time. */
unsigned long SaveFileChecksum(FILE *fp)
{
    long buf[0x32];
    unsigned long sum = 0;
    int n;
    int i;

    FileSeek(fp, 0x2c, 0);
    for (;;) {
        n = FileRead(buf, 4, 0x32, fp);
        if (n == 0)
            break;
        if (n <= 0)
            continue;
        for (i = 0; i < n * 4; i += 4)
            sum = (sum + *(long *)((char *)buf + i)) * 2;
    }
    return sum;
}
