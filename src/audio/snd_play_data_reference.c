/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndPlayData (0x26fd4), game sound layer above Miles AIL - reference C (T4).
 *
 * Allocates an AIL file sample for a VOC/WAV image, picks a free channel of
 * the four slots, evicts round-robin with AIL_end_sample when all are busy,
 * installs the end hook and starts it.
 *
 * Not T3: the original computes the channel-slot addresses as
 * `movsx eax, word [ebp-4]; lea edx, [eax*8 + base]`, 10.0a emits
 * `movsx edx, ...; shl edx,3` (audio.toml t3_blocker).
 *
 * The round-robin counter is a word (snd_evict_next 0x5342e) whose successor
 * is tested through the dword at 0x5342c (`mov eax,[0x5342c]; sar eax,0x10`),
 * so the source keeps a long view of that word; SFX_VOLUME shows the same
 * idiom for the volume in snd_set_sfx_volume.c.
 */
#include "audio.h"

#define EVICT_WORD (*(int *)((char *)&snd_evict_next - 2) >> 16)

void SndPlayData(void *voc)
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
        ch = snd_evict_next++;
        if (EVICT_WORD >= 4)
            snd_evict_next = 0;
        AIL_end_sample(snd_channels[ch].hsample);
    } else
        snd_evict_next = 0;
    ail_set_file_sample_end_hook(hs, SndSampleEndedCallback);
    AIL_start_sample(hs);
    snd_channels[ch].hsample = hs;
    snd_channels[ch].data = voc;
}
