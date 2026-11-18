/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * REFERENCE C for the LZSS codec of DATA.WAR (module 0x41550..0x4181e,
 * "DBG" style): LzssDecode.  LzssReset and LzssFreeRing are T3 under Watcom
 * 10.0a and built from lzss_reset.c / lzss_free_ring.c.  LzssDecode is not
 * built: the T3 comparison fails on the register that holds the zero
 * constant / ring indices (codegen.md V2/V3, not steerable),
 * so this is verified as T4 against the original (wc1.cemu), see
 * docs/subsystems/resources.md and tests/test_resources_lzss.py.
 *
 * The original always inlines the stdio getc macro (FILE count at +4,
 * pointer at +0, flags at +0xc) with the 0x31a18 slow path; this C calls the
 * wrapper `FileGetc` for every byte instead, which is the same operation
 * (the macro's fast path is an optimisation).  The T4 test drives both with
 * an empty FILE buffer, i.e. through the slow path, so the I/O effects are
 * identical.
 */
#include "resources.h"

extern unsigned char *lzss_ring;                    /* 0x5677c */
extern unsigned short lzss_match_src;               /* 0x635d0 */
extern unsigned short lzss_ring_pos;                /* 0x635d2 */
extern unsigned short lzss_match_left;              /* 0x635d4 */
extern unsigned short lzss_flags;                   /* 0x635d6 */
extern unsigned long res_remaining;                 /* 0x5ad40 */

/* @0x417cc LzssReset: built from C (T3 under Watcom 10.0a) in src/resources/lzss_reset.c. */

/* @0x41550  decode `count` bytes (or until the resource's unpacked size is
 * used up) from the archive FILE into dest.
 *
 * The stream is a flag byte (8 items, LSB first; bit 0 = literal byte,
 * bit 1 = a 16-bit match word whose low 12 bits are the absolute ring
 * position and whose high 4 bits + 3 are the match length) interleaved with
 * the data.  Every output byte is also written to the ring, so matches may
 * overlap the write position.  A match split by the count/unpacked-size
 * limit keeps its remainder in lzss_match_left / lzss_match_src for the next
 * call. */
void LzssDecode(unsigned char *dest, unsigned count)
{
    unsigned char c;

    for (;;) {
        if (lzss_match_left == 0) {
            lzss_flags >>= 1;
            /* bit 8 is the "another item left in this flag byte" marker:
             * a refill stores byte|0xff00, one shift consumes one item */
            if ((lzss_flags & 0x100) == 0)
                lzss_flags = (unsigned char)FileGetc(archive_file) | 0xff00;
            if (lzss_flags & 1) {                   /* literal byte */
                c = (unsigned char)FileGetc(archive_file);
                lzss_ring[lzss_ring_pos] = c;
                *dest++ = c;
                if (++lzss_ring_pos == 0x1000)
                    lzss_ring_pos = 0;
                if (--res_remaining == 0)
                    return;
                if (--count == 0)
                    return;
                continue;
            }
            /* match word: low byte, then high byte */
            lzss_match_src = (unsigned char)FileGetc(archive_file);
            lzss_match_src |= (unsigned char)FileGetc(archive_file) << 8;
            lzss_match_left = (lzss_match_src >> 12) + 3;
            lzss_match_src &= 0x0fff;
        }
        /* copy the pending match, one byte at a time (it may wrap and may
         * overlap the write position) */
        while (lzss_match_left != 0) {
            c = lzss_ring[lzss_match_src];
            lzss_ring[lzss_ring_pos] = c;
            *dest++ = c;
            if (++lzss_ring_pos == 0x1000)
                lzss_ring_pos = 0;
            if (++lzss_match_src == 0x1000)
                lzss_match_src = 0;
            lzss_match_left--;
            if (--res_remaining == 0)
                return;
            if (--count == 0)
                return;
        }
    }
}

/* @0x41800 LzssFreeRing: built from C (T3 under Watcom 10.0a) in src/resources/lzss_free_ring.c. */
