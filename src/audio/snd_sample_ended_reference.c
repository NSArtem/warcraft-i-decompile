/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndSampleEndedCallback (0x27554), game sound layer above Miles AIL -
 * reference C (T4).  Clears the channel whose handle is the AIL sample that
 * ended.
 *
 * The hook is installed with ail_set_file_sample_end_hook (the +0x86c sample
 * hook) and AIL calls it as `push esi; call [hsample+0x86c]; add esp,4`
 * (ail_file_sample_done 0x3a604) - one stack argument.  The original reads it
 * at [ebp+0x10] after `push esi; push edi; push ebp`, which is Watcom's
 * __cdecl layout, so the function (and its link name,
 * _SndSampleEndedCallback) is cdecl; a watcall parameter would arrive in eax.
 *
 * Not T3: the original computes the channel address with
 * `lea edx, [eax*8 + 0x5a220]` while 10.0a uses `shl eax,3` and a memory
 * operand displacement (audio.toml t3_blocker), as in SndPlayData.
 */
#include "audio.h"

extern struct snd_chan snd_channels[4];            /* 0x5a220 */

void __cdecl SndSampleEndedCallback(void *hsample)
{
    volatile short i;

    for (i = 0; i < 4; i++)
        if (snd_channels[i].hsample == hsample)
            snd_channels[i].hsample = 0;
}
