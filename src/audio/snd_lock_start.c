/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndLockStart (0x2753c), game sound layer above Miles AIL.  T3 under Watcom
 * 10.0a.  An empty function that only marks the start of the DPMI-locked
 * interrupt-time callback range: AilInit passes
 * [SndLockStart, SndLockEnd - SndLockStart + 1) to DpmiLockRegion (0x312f0).
 * The original still has the full six-register OD frame.
 */
#include "audio.h"

void SndLockStart(void)
{
}
