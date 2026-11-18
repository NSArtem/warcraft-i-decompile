/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * SndSetMusicVolume (0x27460), game sound layer above Miles AIL.  T3 under
 * Watcom 10.0a: clamp to 0..127, store it, AIL_set_preference(0xc, vol),
 * apply it to the (single) sequence, then restart the track when going from
 * silence to sound or stop it when muted.  The indexed sequence access is a
 * plain push, the loop index a volatile short.
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq snd_sequences[1];            /* 0x5a24c, plain view */
extern short snd_music_volume127;                  /* 0x5a254 */

void SndSetMusicVolume(int vol)
{
    short old;
    volatile short i;

    old = snd_music_volume127;
    if (!snd_mdi_active)
        return;
    if ((short)vol < 0)
        vol = 0;
    if ((short)vol > 0x7f)
        vol = 0x7f;
    snd_music_volume127 = (short)vol;
    AIL_set_preference(0xc, (short)vol);
    if (snd_music_data == 0)
        return;
    for (i = 0; i < 1; i++)
        AIL_set_sequence_volume(snd_sequences[i].hseq, (short)vol, 0);
    if (old == 0 && (short)vol != 0)
        MusicPlayTrack(0);
    else if (old != 0 && (short)vol == 0)
        MusicStop();
}
