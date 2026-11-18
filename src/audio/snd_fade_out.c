/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndFadeOut (0x26d98), game sound layer above Miles AIL.  T3 under Watcom
 * 10.0a.  Ramps the music down (AIL_set_sequence_volume(seq, 0, ms)) and arms
 * the one-shot fade timer; (unsigned short)ms is the promotion the original
 * uses (`xor eax,eax; mov ax, word [ebp-4]`).  snd_fade_timer is a plain
 * global here: the original pushes it directly (`push dword [0x53418]`).
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern unsigned char snd_fade_stop_all;            /* 0x5a256 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */
extern int snd_fade_timer;                         /* 0x53418 */

void SndFadeOut(int ms)
{
    snd_fade_stop_all = 0;
    if (snd_mdi_active && snd_music_data) {
        AIL_set_sequence_volume(snd_sequences[0].hseq, 0, (unsigned short)ms);
        if (snd_fade_timer == -1) {
            snd_fade_timer = AIL_register_timer(MusicFadeTimerCallback);
            if (snd_fade_timer == -1) {
                MusicStop();
                return;
            }
        }
        AIL_set_timer_period(snd_fade_timer, (unsigned short)ms * 1000);
        AIL_start_timer(snd_fade_timer);
    }
}
