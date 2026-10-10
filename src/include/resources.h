/*
 * Declarations for the resource archive layer (analysis/symbols/resources.toml).
 * Library primitives are declared with the standard names; their addresses are
 * named by clib.toml.
 */
#ifndef RESOURCES_H
#define RESOURCES_H

#include <stdio.h>

extern FILE *archive_file;              /* 0x5581c */
extern unsigned long *archive_offsets;  /* 0x55828 */

void fatal_error(const char *fmt, ...); /* 0x30bf0: printf-like, does not return */

long ResourceSeek(unsigned short id);   /* 0x3452c */

#endif
