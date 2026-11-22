#ifndef MOD_12B80_H
#define MOD_12B80_H

#include "war.h"

extern char dos_block_marker_tail[8];                 /* 0x512b5: "OSBLOCK" */
extern unsigned char bios_floppy_drive_ids[3];        /* 0x51330: 00 01 ff */
extern unsigned char bios_hard_drive_ids[3];          /* 0x51333: 80 81 ff */
extern char dos_block_check_error[8];                 /* 0x56a80: "CHECK:1" */

unsigned short ComputeBiosDriveFingerprint(void);   /* 0x12b80 */
void CheckDosBlockMarker(void);                      /* 0x12c48 */

#endif
