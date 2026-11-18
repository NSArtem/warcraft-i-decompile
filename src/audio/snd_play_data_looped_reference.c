/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndPlayDataLooped (0x270dc), game sound layer above Miles AIL - reference C
 * (T4).  As SndPlayData but sets the sample to loop forever
 * (AIL_set_sample_loop_count(hsample, 0)) and uses its own round-robin
 * counter, snd_evict_next_looped (0x53430, tested through the dword at
 * 0x5342e >> 16).  Not T3: same channel-slot addressing difference
 * (audio.toml t3_blocker).
 */
#include "audio.h"

/* the dword that *ends* at the counter: 0x5342e holds snd_evict_next
 * (low word) and snd_evict_next_looped (high word) */
#define EVICT_LOOPED_WORD (*(int *)&snd_evict_next >> 16)

void SndPlayDataLooped(void *voc)
{
    void *hs;
    volatile short ch;

    if (!snd_dig_active)
        return;
    hs = AIL_allocate_file_sample(snd_hdig, voc, -1);
    if (hs == 0)
        return;
    for (ch = 0; ch < 4; ch++)
        if (snd_channels[ch].hsample == 0)
            break;
    if (ch == 4) {
        ch = snd_evict_next_looped++;
        if (EVICT_LOOPED_WORD >= 4)
            snd_evict_next_looped = 0;
        AIL_end_sample(snd_channels[ch].hsample);
    } else
        snd_evict_next_looped = 0;
    ail_set_file_sample_end_hook(hs, SndSampleEndedCallback);
    AIL_start_sample(hs);
    AIL_set_sample_loop_count(hs, 0);
    snd_channels[ch].hsample = hs;
    snd_channels[ch].data = voc;
}
