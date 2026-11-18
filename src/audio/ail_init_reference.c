/* codegen-flags: -s -od -4r -zp2
 * codegen-compiler: 10.0a
 *
 * AilInit (0x269f0), game sound layer above Miles AIL - reference C (T4).
 *
 * Starts AIL, points its general-timbre-library prefix at
 * <exe_dir>\drivers\warcraft, sets the driver preferences, stores the two
 * volumes and DPMI-locks the state and callbacks the AIL timer ISR touches.
 *
 * Not T3 because of the frame-slot order: the original puts its return-value
 * slot at -4 and the two parameters at -8/-0xc, Watcom 10.0a puts the
 * parameters at -8/-4 and the return slot at -0xc (audio.toml t3_blocker).
 * The code is otherwise the original's, instruction for instruction.
 */
#include "audio.h"

int AilInit(int sfx_volume, int music_volume)
{
    char path[256];

    AIL_startup();
    _makepath(path, 0, exe_dir, gtl_prefix_name, 0);
    AIL_set_GTL_filename_prefix(path);
    AIL_set_preference(7, 0);           /* mono */
    AIL_set_preference(1, 0x2b11);      /* 11025 Hz */
    AIL_set_preference(8, 0);           /* 8-bit */
    AIL_set_preference(4, 4);           /* DMA buffer length */
    AIL_set_preference(5, (short)sfx_volume);    /* default sample volume */
    AIL_set_preference(0xc, (short)music_volume);/* default sequence volume */
    snd_music_volume127 = (short)music_volume;
    snd_sfx_volume127 = (short)sfx_volume;
    DpmiLockRegion((void *)&snd_dig_active, 1);
    DpmiLockRegion((void *)&snd_mdi_active, 1);
    DpmiLockRegion((void *)&snd_fade_stop_all, 1);
    DpmiLockRegion((void *)snd_sequences, 6);
    DpmiLockRegion((void *)snd_channels, 0x20);
    DpmiLockRegion((void *)&snd_fade_timer, 4);
    DpmiLockRegion(SndLockStart,
                   (unsigned)SndLockEnd - (unsigned)SndLockStart + 1);
    return 0;
}
