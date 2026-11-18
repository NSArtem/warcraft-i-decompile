/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * MusicFadeTimerCallback (0x275a8), game sound layer above Miles AIL.  T3
 * under Watcom 10.0a.
 *
 * The one-shot AIL timer callback armed by SndFadeOut/SndFadeOutAndStopAll.
 * The prologue `push esi; push edi; push ebp` is Watcom's __cdecl prologue (a
 * watcall function pushes all six registers), matching the AIL timer callback
 * type; the direct sequence-handle read is a volatile load while the indexed
 * loop access is a plain push, so this file declares the volatile view and
 * casts for the loop.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern unsigned char snd_fade_stop_all;            /* 0x5a256 */
extern int snd_fade_timer;                         /* 0x53418 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */

void __cdecl MusicFadeTimerCallback(void)
{
    volatile short i;

    AIL_stop_timer(snd_fade_timer);
    if (snd_mdi_active)
        AIL_end_sequence(snd_sequences[0].hseq);
    if (snd_fade_stop_all == 1) {
        for (i = 0; i < 1; i++) {
            if (AIL_sequence_status(((struct snd_seq *)snd_sequences)[i].hseq)
                    != SND_SEQ_DONE) {
                AIL_end_sequence(((struct snd_seq *)snd_sequences)[i].hseq);
                ((struct snd_seq *)snd_sequences)[i].state = -1;
            }
        }
        SndReleaseAll();
    }
}
