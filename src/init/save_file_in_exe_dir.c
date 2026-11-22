/* codegen-compiler: 10.0a */
#include "war.h"
#include <stdio.h>

extern const char binary_write_mode[]; /* 0x1d2cf */
extern volatile short file_open_noprompt; /* 0x1d2c2..0x1d2e4 */
extern void _makepath(char *path, const char *drive, const char *dir, const char *fname, const char *ext); /* 0x1d2bd */
extern size_t FileWrite(const void *buf, size_t size, size_t n, FILE *fp); /* 0x1d2fe */
extern int FileClose(FILE *fp); /* 0x1d310 */
extern int unlink(const char *path); /* 0x1d31c */

/* 0x1d2a0 */
short SaveFileInExeDir(const char *name, const void *buf, unsigned size)
{
    char path[0x90];
    FILE *fp;
    short ok;

    _makepath(path, NULL, exe_dir, name, NULL);
    file_open_noprompt++;
    fp = fopen(path, binary_write_mode);
    file_open_noprompt--;
    if (fp == NULL)
        return 0;

    ok = (short)(size == FileWrite(buf, 1, size, fp));
    FileClose(fp);
    if (!ok)
        unlink(path);
    return ok;
}
