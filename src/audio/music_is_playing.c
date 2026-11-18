/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * MusicIsPlaying (0x26c70), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: 0 without a MIDI driver, else "the sequence is not done"
 * (AIL_sequence_status != 2).  The two return paths give the original's
 * return slot at -4 and the comparison temp at -8.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */

int MusicIsPlaying(void)
{
    if (!snd_mdi_active)
        return 0;
    return AIL_sequence_status(snd_sequences[0].hseq) != SND_SEQ_DONE;
}
