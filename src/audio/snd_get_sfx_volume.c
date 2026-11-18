/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndGetSfxVolume (0x27360), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: the short return type is what produces the original's
 * `mov ax, word [0x5a252]; mov [ebp-4],eax` (a short global read for a short
 * result; an int return would sign-extend with movsx).
 */
#include "audio.h"

short SndGetSfxVolume(void)
{
    return snd_sfx_volume127;
}
