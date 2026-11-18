/* codegen-flags: -s -ot -ol -4r -d1+ -zp1
 * The 17-byte codec descriptors are packed 1 (id byte + four pointers), so
 * this file uses -zp1.
 *
 * REFERENCE C for the archive side of DATA.WAR (modules res_archive
 * 0x34440..0x34583 and res_begin/read): OpenArchive and ResourceBegin
 * (CloseArchive and ResourceRead are T3 under Watcom 10.0a and built from
 * close_archive.c / resource_read.c).  Not built: DBG objects whose codegen
 * differs in register assignment / operand order from OW2 (see the per
 * function t3_blocker in analysis/symbols/resources.toml); verified as T4
 * against the original (wc1.cemu, tests/test_resources_lzss.py).
 */
#include <stdlib.h>
#include "resources.h"

extern unsigned long archive_count;             /* 0x62894 */
extern const char *archive_version_error;      /* 0x62890 */
extern const char *archive_read_error;          /* 0x55820 */
extern unsigned char res_codec;                 /* 0x5ad44 */

struct CodecDesc {
    unsigned char id;
    void (*alloc)(void);
    void (*begin)(void);
    void (*decode)(void *dest, unsigned count);
    void (*free)(void);
};
extern struct CodecDesc codec_table[8];         /* 0x56524 */

/* @0x34480  adopt an open data archive: register the exit handler, check
 * the version dword, read the entry count, allocate and read the offset
 * table. */
void OpenArchive(FILE *fp)
{
    unsigned long v;

    archive_file = fp;
    atexit(CloseArchive);
    FileRead(&v, 4, 1, archive_file);
    if (v != archive_version)
        FatalError((char *)archive_version_error);
    FileRead(&archive_count, 4, 1, archive_file);
    archive_offsets = GdsAlloc(archive_count * 4);
    if (FileRead(archive_offsets, archive_count * 4, 1, archive_file) != 1)
        FatalError((char *)archive_read_error);
}

/* @0x34440 CloseArchive: built from C (T3 under Watcom 10.0a) in src/resources/close_archive.c. */

/* @0x31870  start reading a resource: seek to its entry, report the packed
 * length, read the 4-byte header (unpacked size in the low 29 bits, codec
 * in the top 3), run the codec's begin hook and return the unpacked size. */
unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len)
{
    unsigned long header;
    unsigned long packed;

    packed = ResourceSeek((unsigned short)id);
    if (packed_len != 0)
        *packed_len = packed;
    if (FileRead(&header, 4, 1, archive_file) != 1)
        FatalError((char *)archive_read_error);
    res_codec = (unsigned char)((header >> 29) & 7);
    res_remaining = header & 0x1fffffffUL;
    codec_table[res_codec].begin();
    return res_remaining;
}

/* @0x32740 ResourceRead: built from C (T3 under Watcom 10.0a) in src/resources/resource_read.c. */
