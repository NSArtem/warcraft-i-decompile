/*
 * Game sound layer above Miles AIL: codegen-study sample kept for
 * tools/wc1/codegen_refs.py, which sweeps it over flag sets to show why Open
 * Watcom 2 -od cannot reproduce the original's OD bytes (docs/subsystems/
 * codegen.md section 3).  The three functions are reconstructed and T3-matched
 * under Watcom 10.0a in their own files (src/audio/music_stop.c,
 * music_is_playing.c, snd_active_count.c); this file is NOT built.
 */
#include "audio.h"

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
