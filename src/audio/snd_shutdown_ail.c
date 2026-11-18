/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 * SndShutdownAil (0x26b18), game sound layer above Miles AIL, "OD" style
 * (unoptimised: all registers saved, `sub esp,0` frame).  Watcom 10.0a
 * reproduces the frame byte for byte (OW2 emits `sub esp,4`), so this one is
 * built from C; the rest of the layer is the readable reconstruction in
 * sound.c.  One function per object (wcc386 aligns the next function).
 */
#include "audio.h"

/* @0x26b18 */
void SndShutdownAil(void)
{
    AIL_stop_all_timers();
    AIL_release_all_timers();
    AIL_shutdown();
}
