/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndReleaseAll (0x271f4), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: release every occupied digital channel (4 slots of
 * {hsample,data} at 0x5a220) unless no sample is playing.  The loop index is
 * a volatile short (the original loads it before the increment).
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_dig_active;               /* 0x53414 */
extern void *snd_hdig;                             /* 0x5a240 */
extern struct snd_chan snd_channels[4];            /* 0x5a220 */

void SndReleaseAll(void)
{
    volatile short i;

    if (!snd_dig_active)
        return;
    if (AIL_active_sample_count(snd_hdig) == 0)
        return;
    for (i = 0; i < 4; i++)
        if (snd_channels[i].hsample != 0) {
            AIL_release_sample_handle(snd_channels[i].hsample);
            snd_channels[i].hsample = 0;
        }
}
