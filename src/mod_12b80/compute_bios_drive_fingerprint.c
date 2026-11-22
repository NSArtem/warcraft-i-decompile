/* codegen-compiler: 10.0a */
#include "war.h"
#include <i86.h>
#include <string.h>

extern unsigned char bios_hard_drive_ids[3];   /* 0x51333, indexed at 0x12bad */
extern unsigned char bios_floppy_drive_ids[3]; /* 0x51330, indexed at 0x12c01 */

/* 0x12b80: INT 13h/AH=08h calls at 0x12bc4 and 0x12c18. */
unsigned ComputeBiosDriveFingerprint(void)
{
    union REGS regs;
    struct SREGS segs;
    unsigned fingerprint;
    int i;

    fingerprint = 0x67;
    for (i = 0; bios_hard_drive_ids[i] != 0xff; ++i) {
        segread(&segs);
        memset(&regs, 0, sizeof(regs));
        regs.h.ah = 8;
        regs.h.dl = bios_hard_drive_ids[i];
        int386x(0x13, &regs, &regs, &segs);
        fingerprint ^= regs.x.ecx;
        fingerprint ^= regs.x.edx;
    }
    for (i = 0; bios_floppy_drive_ids[i] != 0xff; ++i) {
        segread(&segs);
        memset(&regs, 0, sizeof(regs));
        regs.h.ah = 8;
        regs.h.dl = bios_floppy_drive_ids[i];
        int386x(0x13, &regs, &regs, &segs);
        fingerprint ^= regs.x.ebx;
        fingerprint ^= regs.x.ecx;
        fingerprint ^= regs.x.edx;
    }
    return (unsigned short)fingerprint;
}
