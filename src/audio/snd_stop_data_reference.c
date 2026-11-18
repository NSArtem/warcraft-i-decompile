/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndStopData (0x27278), game sound layer above Miles AIL - reference C (T4).
 * Releases the channel that is playing the given VOC/WAV image (the data
 * pointer recorded in snd_channels[i].data, 0x5a224 + i*8).  Not T3: same
 * channel-slot addressing difference as SndPlayData 0x26fd4 (audio.toml).
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
        if (snd_channels[i].hsample == 0)
            continue;
        if (snd_channels[i].data != voc)
            continue;
        AIL_release_sample_handle(snd_channels[i].hsample);
        snd_channels[i].hsample = 0;
        break;
    }
}
