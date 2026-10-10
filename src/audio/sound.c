/*
 * Game sound layer above Miles AIL: music sequence control, digital sound
 * channels and volume options (analysis/symbols/audio.toml).
 *
 * NOT matching: the original is unoptimised Watcom output with short jumps and
 * `sub esp,0` frames that OW2 -od cannot reproduce (see docs/subsystems/audio.md).
 * Kept as a readable reconstruction; not part of `make match-all` (src/*.c only).
 */
#include "audio.h"

/* 0x26b18 */
void SndShutdownAil(void)
{
    AIL_stop_all_timers();
    AIL_release_all_timers();
    AIL_shutdown();
}

/* 0x26d60 */
void MusicStop(void)
{
    if (snd_mdi_active && snd_music_data)
        AIL_end_sequence(snd_sequences[0].hseq);
}

/* 0x27320 */
int SndActiveCount(void)
{
    int n;
    if (!snd_dig_active)
        n = 0;
    else
        n = AIL_active_sample_count(snd_hdig);
    return n;
}
