/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * LzssFreeRing (0x41800), built from C: T3 under Watcom 10.0a.  Split out of
 * src/resources/lzss.c (reference C under OW2), whose declarations it repeats;
 * one function per object (wcc386 aligns the next function).
 */
#include "resources.h"

extern unsigned char *lzss_ring;                    /* 0x5677c */
extern unsigned short lzss_match_src;               /* 0x635d0 */
extern unsigned short lzss_ring_pos;                /* 0x635d2 */
extern unsigned short lzss_match_left;              /* 0x635d4 */
extern unsigned short lzss_flags;                   /* 0x635d6 */
extern unsigned long res_remaining;                 /* 0x5ad40 */

/* @0x41800  free the decode window (registered as the codec's "free" slot,
 * run at exit). */
void LzssFreeRing(void)
{
    GdsFree(lzss_ring);
    lzss_ring = 0;
}
