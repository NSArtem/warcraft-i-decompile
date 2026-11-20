/* codegen-compiler: 10.0a */
#include "audio.h"

extern unsigned int opt_sfx_volume;
extern unsigned short snd_saved_sfx_pct;

/* @0x266e4 */
void SndToggleSfx(void)
{
    if (opt_sfx_volume != 0) {
        snd_saved_sfx_pct = (unsigned short)opt_sfx_volume;
        opt_sfx_volume = 0;
        SndReleaseAll();
    } else {
        opt_sfx_volume = snd_saved_sfx_pct;
    }
    SndSetSfxVolume((short)(opt_sfx_volume != 0 ? (snd_saved_sfx_pct * 127) / 100 : 0));
}
