/* codegen-compiler: 10.0a */
#include "audio.h"

/* @0x2674c */
void SndApplyOptions(const int *opts)
{
    SndSetSfxVolume((short)(((unsigned int)opts[2] * 127) / 100));
    SndSetMusicVolume((short)(((unsigned int)opts[1] * 127) / 100));
}
