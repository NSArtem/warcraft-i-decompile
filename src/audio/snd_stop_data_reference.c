/* codegen-compiler: 10.0a */
/* codegen-flags: -s -od -4r -zp2 */
/* SndStopData (0x27278), game sound layer above Miles AIL - T3 (built from C).
 * Releases the channel that is playing the given VOC/WAV image (the data
 * pointer recorded in snd_channels[i].data, 0x5a224 + i*8).  Was reference C
 * (T4); the single positive `&&` guard (instead of two `continue`s) gives the
 * original's near `je rel32` loop exit - recovered by wc1.wave4 (2026-11-23).
 * The file name is kept: the T4 difftest still loads it.
 */
#include "audio.h"

void SndStopData(void *voc)
{
    volatile short i;

    if (!snd_dig_active)
        return;
    if (AIL_active_sample_count(snd_hdig) == 0)
        return;
    for (i = 0; i < 4; i++) {
        if (snd_channels[i].hsample != 0 && snd_channels[i].data == voc) {
            AIL_release_sample_handle(snd_channels[i].hsample);
            snd_channels[i].hsample = 0;
            break;
        }
    }
}
