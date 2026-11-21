/* codegen-compiler: 10.0a */
#include "mod_13f60.h"
#include <string.h>

extern void SaveSlotPath(char *path, unsigned short slot);
extern int FileClose(FILE *fp);
extern FILE *FileOpen(const char *name, const char *mode);
extern int FileSeek(FILE *fp, long offset, int whence);
extern size_t FileRead(void *buf, size_t size, size_t n, FILE *fp);

/* @0x147a8 */
void SaveSlotsScan(Control *d)
{
    char path[0x90];
    char *p = d->text;
    int i;
    int off;
    FILE *fp;
    long magic;

    if (dat_516ae != 0 && screen_mode == 0) {
        i = 0;
        off = 0;
        for (;;) {
            if (slot_remote != 0) {
                sprintf(p, fmt_slot_number, i + 1, str_remote_slot);
                p += 0x17;
            } else {
                strcpy(p, str_remote_slot);
                p += 0x13;
            }
            edit_buffer2[0x58 + off] = 0;
            off += 0x20;
            i++;
            if (i >= 7)
                break;
        }
    } else {
        i = 0;
        off = 0;
        do {
            SaveSlotPath(path, (unsigned short)i);
            fp = FileOpen(path, str_read_binary);
            if (fp != 0) {
                if (FileRead(&edit_buffer2[0x58 + off], 0x20, 1, fp) == 1 &&
                    FileSeek(fp, 8, 1) == 0 &&
                    FileRead(&magic, 4, 1, fp) == 1 &&
                    magic == 0x31726157L) {
                    if (slot_remote != 0)
                        sprintf(p, fmt_slot_number, i + 1, &edit_buffer2[0x58 + off]);
                    else
                        strcpy(p, &edit_buffer2[0x58 + off]);
                }
                FileClose(fp);
            } else {
                edit_buffer2[0x58 + off] = 0;
            }
            if (slot_remote != 0)
                p += 0x17;
            else
                p += 0x13;
            off += 0x20;
            i++;
        } while (i < 7);
    }
}
