/*
 * Declarations for the resource archive layer (analysis/symbols/resources.toml).
 * File I/O goes through the library's retrying wrappers (FileOpen 0x31964,
 * FileSeek 0x31a80, FileRead 0x31adc, ...), not directly through the clib.
 */
#ifndef RESOURCES_H
#define RESOURCES_H

#include <stdio.h>
#include "war.h"

extern FILE *archive_file;              /* 0x5581c */
extern unsigned long *archive_offsets;  /* 0x55828 */
extern unsigned long archive_count;     /* 0x62894 */
extern unsigned long archive_version;   /* 0x55824 */
extern unsigned long res_remaining;     /* 0x5ad40 (unpacked bytes left) */

void OpenArchive(FILE *fp);                          /* 0x34480 */
void CloseArchive(void);                             /* 0x34440 */
unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len); /* 0x31870 */
void *ResourceRead(void *dest, unsigned count);      /* 0x32740 */

int FileClose(FILE *fp);                                        /* 0x31940 */
int FileSeek(FILE *fp, long offset, int whence);                /* 0x31a80 */
size_t FileRead(void *buf, size_t size, size_t n, FILE *fp);    /* 0x31adc */
int FileGetc(FILE *fp);                                         /* 0x31a18 */

long ResourceSeek(unsigned short id);   /* 0x3452c */

#endif
