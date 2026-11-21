/* codegen-compiler: 10.0a */
#include "war.h"

typedef struct _FILE FILE;

extern FILE *FileOpen(const char *name, const char *mode);
extern int sprintf(char *buf, const char *fmt, ...);
extern void _makepath(char *path, const char *drive, const char *dir, const char *fname, const char *ext);
extern int setvbuf(FILE *fp, char *buf, int mode, unsigned size);
extern char dat_56c88[];
extern char dat_56c8c[];
extern volatile short file_open_noprompt;

/* @0x1d410 */
FILE *FindDataFile(const char *name)
{
    char fname[0x90];
    char path[0x90];
    FILE *fp;

    sprintf(fname, dat_56c8c, name);
    _makepath(path, 0, exe_dir, fname, 0);
    file_open_noprompt++;
    fp = FileOpen(path, dat_56c88);
    if (fp == 0) {
        _makepath(path, 0, cd_path, fname, 0);
        fp = FileOpen(path, dat_56c88);
    }
    file_open_noprompt--;
    if (fp != 0) {
        setvbuf(fp, 0, 0x100, 0x4000);
    }
    return fp;
}
