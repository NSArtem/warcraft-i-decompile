/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndSetSfxVolume (0x27384), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: clamp to 0..127 into 0x5a252, AIL_set_preference(5, volume)
 * and the same volume on every active sample.
 *
 * The original's stores are plain word stores to 0x5a252, but the three reads
 * go through the dword at 0x5a250 (`mov eax,[0x5a250]; sar eax,0x10` at
 * 0x273ab/0x273d4/0x27411) - the source kept a long view of the volume word;
 * spelled here as the dword that ends at the short.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_dig_active;               /* 0x53414 */
extern short snd_sfx_volume127;                    /* 0x5a252 */
extern struct snd_chan snd_channels[4];            /* 0x5a220 */

#define SFX_VOLUME (*(int *)((char *)&snd_sfx_volume127 - 2) >> 16)

void SndSetSfxVolume(int vol)
{
    volatile short i;

    if (!snd_dig_active)
        return;
    snd_sfx_volume127 = (short)vol;
    if (SFX_VOLUME > 0x7f)
        snd_sfx_volume127 = 0x7f;
    if (snd_sfx_volume127 < 0)
        snd_sfx_volume127 = 0;
    AIL_set_preference(5, SFX_VOLUME);
    for (i = 0; i < 4; i++)
        if (snd_channels[i].hsample != 0)
            AIL_set_sample_volume(snd_channels[i].hsample, SFX_VOLUME);
}
