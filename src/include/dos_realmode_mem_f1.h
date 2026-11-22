#ifndef DOS_REALMODE_MEM_F1_H
#define DOS_REALMODE_MEM_F1_H

/* DPMI real-mode memory block descriptor (10 bytes, GdsAlloc'd). */
typedef struct RealModeBlock {
    long err;                   /* +0  always 0 on success */
    unsigned short sel4;        /* +4  copy of selector */
    unsigned short sel;         /* +6  protected-mode selector (DX of AX=0100h) */
    unsigned short seg;         /* +8  real-mode segment (AX of AX=0100h) */
} RealModeBlock;

/* RealModeGetVector returns eax = segment, edx = offset (edx not visible in C). */
typedef struct RmVector {
    unsigned long seg;
    unsigned long off;
} RmVector;

RealModeBlock *RealModeAlloc(unsigned size);                 /* 0x23d10 */
void RealModeResize(RealModeBlock *b, unsigned size);        /* 0x23d88 */
void RealModeFree(RealModeBlock *b);                         /* 0x23dd8 */
unsigned long RealModeGetVector(unsigned char intno);           /* 0x23e10 */
void RealModeInt(unsigned char intno, void *rmregs);         /* 0x23e50 */

extern char str_rm_alloc_fail[];    /* 0x5789c */
extern char str_rm_resize_fail[];   /* 0x578c4 */

#endif
