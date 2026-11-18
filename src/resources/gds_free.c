/* codegen-flags: -s -ot -ol -4r -d1+ -zp2
 * codegen-compiler: 10.0a
 * GdsFree (0x32780): the matching free of GdsAlloc (0x32558), which checks
 * the two "CHECKSIG" guards, poisons them and frees the raw block.
 * REFERENCE C (T4, tests/test_resources_files.py) - NOT built from C: the
 * original's extra 4-byte frame slot (sub esp,4) is not reproduced by 10.0a
 * (t3_blocker in the report; the symbol entry lives in graphics.toml, so this
 * file is not named *_reference.c yet).
 */
#include <stdlib.h>
#include "war.h"

#pragma aux GdsTrap = "int 3";

/* @0x32780  verify the 12-byte header (guard + tail pointer) and the tail
 * guard, poison both with the reversed signature and free the block. */
void GdsFree(void *p)
{
    char *b;
    char *tail;

    b = (char *)p - 12;
    tail = *(char **)(b + 8);
    if (b[0] != 'C' || tail[0] != 'C'
        || b[1] != 'H' || tail[1] != 'H'
        || b[2] != 'E' || tail[2] != 'E'
        || b[3] != 'C' || tail[3] != 'C'
        || b[4] != 'K' || tail[4] != 'K'
        || b[5] != 'S' || tail[5] != 'S'
        || b[6] != 'I' || tail[6] != 'I'
        || b[7] != 'G' || tail[7] != 'G') {
        GdsTrap();
        FatalError("GDS heap corrupt");
    }
    b[0] = tail[0] = 'G';
    b[1] = tail[1] = 'I';
    b[2] = tail[2] = 'S';
    b[3] = tail[3] = 'K';
    b[4] = tail[4] = 'C';
    b[5] = tail[5] = 'E';
    b[6] = tail[6] = 'H';
    b[7] = tail[7] = 'C';
    free(b);
}
