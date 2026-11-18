/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * MusicPlayTrack (0x26cc8), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a.  The track number is an int parameter used as `(short)`:
 * the original promotes it with `movsx eax, word [ebp-8]` at 0x26d0e, and
 * passing the int unchanged moves the frame slots.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */
extern short snd_music_volume127;                  /* 0x5a254 */

int MusicPlayTrack(int seq_num)
{
    if (snd_mdi_active && snd_music_data) {
        if (AIL_sequence_status(snd_sequences[0].hseq) != SND_SEQ_DONE)
            AIL_end_sequence(snd_sequences[0].hseq);
        if (!AIL_init_sequence(snd_sequences[0].hseq, snd_music_data, (short)seq_num))
            return 1;
        if (snd_music_volume127 != 0)
            AIL_start_sequence(snd_sequences[0].hseq);
    }
    return 0;
}
