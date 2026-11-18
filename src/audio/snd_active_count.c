/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndActiveCount (0x27320), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: number of playing samples, 0 without a digital driver.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_dig_active;               /* 0x53414 */
extern void *snd_hdig;                             /* 0x5a240 */

int SndActiveCount(void)
{
    if (!snd_dig_active)
        return 0;
    return AIL_active_sample_count(snd_hdig);
}
