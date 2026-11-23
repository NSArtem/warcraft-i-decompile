#ifndef FLIC_DECODE_STATE_H
#define FLIC_DECODE_STATE_H

#include <stdio.h>

/* The 0x80-byte file header read by FlicOpen. The three dimension/count
 * fields also have original-address labels used by other decoder objects. */
typedef struct FlicFileHeader {
    unsigned long size;
    unsigned short magic, frames, width, height;
    unsigned short depth, flags;
    unsigned char reserved_10[4];
    unsigned short reserved_14;
    unsigned char reserved_16[0x3a];
    long rewind_offset, restart_offset;
    unsigned char reserved_58[0x28];
} FlicFileHeader;

extern FlicFileHeader flic_file_header;  /* 0x59440, offsets used at +0x50/+0x54 */
extern FILE *flic_file;                   /* 0x594e0 */
extern unsigned short flic_decoder_open; /* 0x517c8 (not the intro's 0x52c60 flag) */

#endif
