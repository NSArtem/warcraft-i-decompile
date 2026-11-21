/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern void SaveSlotPath(char *path, unsigned short slot);
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
extern int FileClose(FILE *fp);
extern FILE *FileOpen(const char *name, const char *mode);
extern size_t FileWrite(const void *buf, size_t size, size_t n, FILE *fp);
extern int *__get_errno_ptr(void);
extern size_t strlen(const char *s);
extern void fn_147a8(void);
extern char dat_592e8[];
extern char dat_592e9[];
extern char dat_56b40[];
extern char dat_56b48[];

/* @0x14ad8 */
FILE *SaveSlotCreate(unsigned short layer, unsigned short id, short *cancelled)
{
    char path[0x90];
    void *params[2] = { (void *)fn_147a8, 0 };
    long zero1;
    long zero2;
    long magic;
    short r;
    int i;
    FILE *fp;

    magic = 0x31726157L;
    zero1 = 0;
    zero2 = 0;
    *cancelled = 0;
    slot_remote = 0;
    r = DialogRun(id, 0x34, 0x17, layer, params);
    i = r;
    if (dat_516ae != 0 && screen_mode == 0) {
        if (i >= 7) {
            *cancelled = 1;
        }
        return 0;
    }
    if (i >= 7) {
        *cancelled = 1;
        return 0;
    }
    if (dat_592e8[i * 0x20] == 0) {
        *(long *)&dat_592e8[i * 0x20] = *(long *)dat_56b40;
        *(long *)&dat_592e8[i * 0x20 + 4] = *(long *)(dat_56b40 + 4);
    }
    SaveSlotPath(path, (unsigned short)i);
    save_slot = (unsigned short)i;
    *__get_errno_ptr() = 0;
    fp = FileOpen(path, dat_56b48);
    if (fp == 0) {
        return fp;
    }
    dat_592e9[i * 0x20 + strlen(&dat_592e8[i * 0x20])] = 0x1a;
    if (FileWrite(&dat_592e8[i * 0x20], 0x20, 1, fp) == 0 ||
        FileWrite(&zero1, 4, 1, fp) == 0 ||
        FileWrite(&zero2, 4, 1, fp) == 0 ||
        FileWrite(&magic, 4, 1, fp) == 0) {
        FileClose(fp);
        return 0;
    }
    return fp;
}
