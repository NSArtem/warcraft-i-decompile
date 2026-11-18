/* codegen-flags: -s -od -4r -zp2 -d1+
 * codegen-compiler: 10.0a
 * FileClose (0x31940), built from C: one function per object (the wrappers
 * 0x31964..0x31bca are separate C files).  The original keeps fclose's
 * result in eax and does not copy it to a temporary, so the call's result is
 * discarded and the function returns whatever fclose left in eax.
 */
#include <stdio.h>
#include "resources.h"

/* @0x31940  close a stream; the thin wrapper the rest of the game calls. */
int FileClose(FILE *fp)
{
    fclose(fp);
}
