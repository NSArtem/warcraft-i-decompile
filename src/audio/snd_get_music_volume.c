/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndGetMusicVolume (0x2743c), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: same shape as SndGetSfxVolume (a short global read for a
 * short result).
 */
#include "audio.h"

short SndGetMusicVolume(void)
{
    return snd_music_volume127;
}
