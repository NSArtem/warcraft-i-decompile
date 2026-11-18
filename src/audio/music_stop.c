/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * MusicStop (0x26d60), game sound layer above Miles AIL ("OD" style: OD frame,
 * all six registers saved, `sub esp,0`).  T3 under Watcom 10.0a.
 *
 * snd_sequences[0].hseq is read through a volatile lvalue: the original loads
 * it into eax before pushing (`mov eax,[0x5a24c]; push eax`, 0x26d82), which
 * 10.0a only emits for a volatile access - a plain struct member compiles to
 * `push dword [0x5a24c]`.  The state is shared with the AIL timer callbacks
 * (AilInit DPMI-locks exactly this array).
 */
#define WC1_AUDIO_LOCAL_STATE
#include "audio.h"

extern unsigned char snd_mdi_active;               /* 0x53415 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq_v snd_sequences[1];          /* 0x5a24c, volatile view */

void MusicStop(void)
{
    if (snd_mdi_active && snd_music_data)
        AIL_end_sequence(snd_sequences[0].hseq);
}
