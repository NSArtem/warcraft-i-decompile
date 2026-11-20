/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "audio.h"

extern void *snd_music_buffer;
extern void DpmiUnlockRegion(void *addr, unsigned size);
extern void GdsFree(void *p);

/* @0x26654 */
void SndShutdown(void)
{
    MusicStop();
    SndShutdownAil();
    if (snd_music_buffer != 0) {
        DpmiUnlockRegion(snd_music_buffer, 30000);
        GdsFree(snd_music_buffer);
    }
}
