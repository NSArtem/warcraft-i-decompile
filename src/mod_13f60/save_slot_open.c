/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern void SaveSlotsScan(Control *d);
extern void SaveSlotPath(char *path, unsigned short slot);
extern unsigned long SaveFileChecksum(FILE *fp);
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);
extern int FileClose(FILE *fp);
extern FILE *FileOpen(const char *name, const char *mode);
extern int FileSeek(FILE *fp, long offset, int whence);
extern size_t FileRead(void *buf, size_t size, size_t n, FILE *fp);

/* @0x1498c */
FILE *SaveSlotOpen(int layer, int dialog_id, short *cancelled)
{
    char path[0x90];
    unsigned long sum;
    unsigned long magic;
    void *params[1];
    int slot;
    FILE *fp;

    params[0] = (void *)SaveSlotsScan;
    slot_remote = 1;
    slot = (short)DialogRun((unsigned int)(unsigned short)dialog_id, 0x34, 0x17, (unsigned short)layer, params);
    if (slot >= 7) {
        *cancelled = 1;
        return 0;
    }
    *cancelled = 0;
    if (dat_516ae != 0 && screen_mode == 0)
        return 0;
    if (edit_buffer2[0x58 + (slot << 5)] == 0)
        return 0;
    SaveSlotPath(path, (unsigned short)slot);
    fp = FileOpen(path, str_read_binary);
    if (fp == 0)
        return 0;
    if (FileSeek(fp, 0x20, 0) == 0 &&
        FileRead(&sum, 4, 1, fp) == 1 &&
        FileSeek(fp, 4, 1) == 0 &&
        FileRead(&magic, 4, 1, fp) == 1 &&
        magic == 0x31726157UL &&
        SaveFileChecksum(fp) == sum &&
        FileSeek(fp, 0x2c, 0) == 0)
        return fp;
    FileClose(fp);
    return 0;
}
