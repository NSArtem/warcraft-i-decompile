/* codegen-compiler: 10.0a */
#include "war.h"
#include <stdio.h>

typedef struct BannerStreamPrefix {
    unsigned char *cursor;
} BannerStreamPrefix;

extern const unsigned char cd_version_banner[27]; /* 0x1d862: start address */
extern void NoOp(void); /* 0x1d867, 0x1d95f: exclusive end */
extern BannerStreamPrefix runtime_stdout_stream; /* 0x1d8a1, 0x1d8b5 */
extern unsigned runtime_stdout_buffer_used; /* 0x1d886 */
extern unsigned char runtime_stdout_flags_high; /* 0x1d893 */
extern unsigned runtime_stdout_buffer_size; /* 0x1d880 */
extern unsigned char _IsTable[257]; /* 0x1d8fa */

/* 0x1d854 */
void PrintExitBanner(char status)
{
    const unsigned char *p;
    unsigned char *cursor;
    unsigned used;
    unsigned room;
    unsigned c;
    unsigned char flags;

    if (status != 0)
        return;

    p = cd_version_banner;
    if ((unsigned long)p < (unsigned long)NoOp) {
        do {
            c = *p++;
            if (c == 0)
                break;

            room = runtime_stdout_buffer_size;
            used = runtime_stdout_buffer_used;
            room -= used;
            if (c == '@') {
                if (!(*(unsigned long *)(void *)&runtime_stdout_flags_high & 4UL) && room > 1U) {
                    cursor = runtime_stdout_stream.cursor;
                    *cursor = '\n';
                    c = *(volatile unsigned char *)cursor;
                    if (c == '\n') {
                        fputc(c, (FILE *)(void *)&runtime_stdout_stream);
                    } else {
                        runtime_stdout_flags_high |= 0x10;
                        runtime_stdout_buffer_used = used + 1U;
                        ++runtime_stdout_stream.cursor;
                    }
                } else {
                    fputc('\n', (FILE *)(void *)&runtime_stdout_stream);
                }
            } else if (_IsTable[(unsigned char)(c + 1U)] & 8) {
                flags = runtime_stdout_flags_high;
                if (!(flags & 4) && room > 1U) {
                    cursor = runtime_stdout_stream.cursor;
                    *cursor = (unsigned char)c;
                    c = (unsigned char)c;
                    if (c == '\n') {
                        fputc(c, (FILE *)(void *)&runtime_stdout_stream);
                    } else {
                        runtime_stdout_flags_high = (unsigned char)(flags | 0x10);
                        ++runtime_stdout_buffer_used;
                        runtime_stdout_stream.cursor = cursor + 1;
                    }
                } else {
                    fputc(c, (FILE *)(void *)&runtime_stdout_stream);
                }
            }
        } while ((unsigned long)p < (unsigned long)NoOp);
    }

    if ((*(unsigned long *)(void *)&runtime_stdout_flags_high & 4UL) ||
        runtime_stdout_buffer_size - runtime_stdout_buffer_used <= 1U) {
        fputc('\n', (FILE *)(void *)&runtime_stdout_stream);
        return;
    }

    cursor = runtime_stdout_stream.cursor;
    *cursor = '\n';
    c = *(volatile unsigned char *)cursor;
    if (c == '\n') {
        fputc(c, (FILE *)(void *)&runtime_stdout_stream);
        return;
    }
    runtime_stdout_flags_high |= 0x10;
    ++runtime_stdout_buffer_used;
    ++runtime_stdout_stream.cursor;
}
