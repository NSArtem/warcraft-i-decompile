/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndFadeOutAndStopAll (0x26e3c), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a.  Same ramp as SndFadeOut but for every sequence (the loop
 * index doubles as the volume argument: `AIL_set_sequence_volume(
 * snd_sequences[i].hseq, i, ms)`), then the timer path, which also runs
 * without a MIDI driver as long as a digital driver is active, and on
 * timer-allocation failure stops the music and releases every sample.
 *
 * The indexed access is a plain push in the original
 * (`push dword [eax+0x5a24c]`), so the array is seen non-volatile here; the
 * loop index is a volatile short (`mov eax,[ebp-4]; inc dword [ebp-4]`).
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern unsigned char snd_dig_active;               /* 0x53414 */
extern unsigned char snd_fade_stop_all;            /* 0x5a256 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq snd_sequences[1];            /* 0x5a24c, plain view */
extern int snd_fade_timer;                         /* 0x53418 */

void SndFadeOutAndStopAll(int ms)
{
    volatile short i;

    snd_fade_stop_all = 1;
    if (snd_mdi_active && snd_music_data) {
        for (i = 0; i < 1; i++)
            AIL_set_sequence_volume(snd_sequences[i].hseq, i, (unsigned short)ms);
    }
    if (snd_mdi_active || snd_dig_active) {
        if (snd_fade_timer == -1) {
            snd_fade_timer = AIL_register_timer(MusicFadeTimerCallback);
            if (snd_fade_timer == -1) {
                MusicStop();
                SndReleaseAll();
                return;
            }
        }
        AIL_set_timer_period(snd_fade_timer, (unsigned short)ms * 1000);
        AIL_start_timer(snd_fade_timer);
    }
}
