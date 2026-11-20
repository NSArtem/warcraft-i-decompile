/* codegen-compiler: 10.0a */
#include "audio.h"

extern unsigned int opt_music_volume;
extern unsigned short snd_saved_music_pct;

/* @0x26684 */
void SndToggleMusic(void)
{
    if (opt_music_volume != 0) {
        snd_saved_music_pct = (unsigned short)opt_music_volume;
        opt_music_volume = 0;
    } else {
        opt_music_volume = snd_saved_music_pct;
    }
    SndSetMusicVolume((short)(opt_music_volume != 0 ? (snd_saved_music_pct * 127) / 100 : 0));
}
