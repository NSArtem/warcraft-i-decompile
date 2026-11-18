/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndLockEnd (0x2764c), game sound layer above Miles AIL.  T3 under Watcom
 * 10.0a.  Empty end marker of the DPMI-locked callback range (see
 * snd_lock_start.c); the code after it is alignment filler.
 */
#include "audio.h"

void SndLockEnd(void)
{
}
