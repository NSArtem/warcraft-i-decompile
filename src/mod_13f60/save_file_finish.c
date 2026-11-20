/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

unsigned long SaveFileChecksum(FILE *fp);
void SaveSlotPath(char *path, unsigned short slot);
int FileClose(FILE *fp);
int FileSeek(FILE *fp, long offset, int whence);
size_t FileWrite(const void *buf, size_t size, size_t n, FILE *fp);
int remove(const char *path);

/* @0x146cc */
void SaveFileFinish(FILE *fp, short del)
{
    char path[0x90];
    unsigned long sum;

    if (del != 0) {
        FileClose(fp);
        SaveSlotPath(path, save_slot);
        remove(path);
    } else {
        sum = SaveFileChecksum(fp);
        FileSeek(fp, 0x20, 0);
        FileWrite(&sum, 4, 1, fp);
        FileClose(fp);
    }
}
