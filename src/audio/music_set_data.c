/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * MusicSetData (0x26c10), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a.  Ends a running sequence, invalidates the sequence state word
 * (0x5a250 = 0xffff) and stores the XMIDI image; the handle is a volatile
 * read (see music_stop.c).
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */

int MusicSetData(void *xmidi)
{
    if (snd_mdi_active) {
        if (AIL_sequence_status(snd_sequences[0].hseq) != SND_SEQ_DONE)
            AIL_end_sequence(snd_sequences[0].hseq);
        snd_sequences[0].state = -1;
        snd_music_data = xmidi;
    }
    return 0;
}
