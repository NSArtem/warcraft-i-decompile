/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * GdsAlloc (0x32558), built from C: the game's checked malloc.  One function
 * per object (GdsFree 0x32780 and GdsOutOfMemory 0x32540 are separate files).
 */
#include <stdlib.h>
#include "war.h"

extern void (*gds_nomem_handler)(void);      /* 0x55440 */

/* @0x32558  malloc the block plus a 12-byte header and an 8-byte tail guard,
 * write "CHECKSIG" at both ends, store the tail pointer in the header and
 * return block+12.  A NULL malloc goes through the no-memory hook.
 * The parenthesised `(size + 12)` is the original's spelling: plain
 * `p + size + 12` folds into a three-operand lea and does not match. */
void *GdsAlloc(unsigned size)
{
    char *p;
    char *tail;

    p = malloc(size + 20);
    if (p == 0)
        gds_nomem_handler();
    tail = p + (size + 12);
    p[0] = tail[0] = 'C';
    p[1] = tail[1] = 'H';
    p[2] = tail[2] = 'E';
    p[3] = tail[3] = 'C';
    p[4] = tail[4] = 'K';
    p[5] = tail[5] = 'S';
    p[6] = tail[6] = 'I';
    p[7] = tail[7] = 'G';
    *(char **)(p + 8) = tail;
    return p + 12;
}
