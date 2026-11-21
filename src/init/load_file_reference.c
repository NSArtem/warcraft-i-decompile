/* codegen-compiler: 10.0a */
#include "war.h"

typedef struct _FILE FILE;

extern int FileClose(FILE *fp);
extern FILE *FileOpen(const char *name, const char *mode);
extern long FileTell(FILE *fp);
extern int FileSeek(FILE *fp, long offset, int whence);
extern unsigned FileRead(void *buf, unsigned size, unsigned n, FILE *fp);
extern void _makepath(char *path, const char *drive, const char *dir, const char *fname, const char *ext);
extern char *strcpy(char *dst, const char *src);
extern char dat_56c88[];
extern volatile short file_open_noprompt;

/* @0x1d330 */
short LoadFile(const char *name, void *buf, unsigned min_size, unsigned max_size, short in_exe_dir)
{
    FILE *fp;
    char path[0x90];
    unsigned size;
    short ok;

    if (in_exe_dir != 0) {
        _makepath(path, 0, exe_dir, name, 0);
    } else {
        strcpy(path, name);
    }
    file_open_noprompt++;
    fp = FileOpen(path, dat_56c88);
    file_open_noprompt--;
    if (fp == 0) {
        return 0;
    }
    FileSeek(fp, 0, 2);
    size = FileTell(fp);
    FileSeek(fp, 0, 0);
    if (size < min_size || size > max_size) {
        ok = 0;
    } else if (size != FileRead(buf, 1, size, fp)) {
        ok = 0;
    } else {
        ok = 1;
    }
    FileClose(fp);
    return ok;
}
