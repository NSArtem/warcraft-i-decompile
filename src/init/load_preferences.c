/* codegen-compiler: 10.0a */
#include "war.h"

extern const char preferences_filename[];
extern short preferences_load_failed;
extern long prefs_block[5];
extern unsigned int opt_music_volume;
extern unsigned int opt_sfx_volume;
extern unsigned int opt_mouse_scroll;
extern unsigned int opt_key_scroll;

/* 0x1d597 records failure; 0x1d5a4..0x1d5f2 applies defaults even on failure. */
void LoadPreferences(void)
{
    preferences_load_failed = (short)(LoadFile(preferences_filename, prefs_block, sizeof(prefs_block), sizeof(prefs_block), 1) == 0);
    if ((unsigned long)prefs_block[0] > 6UL)
        prefs_block[0] = 3;
    if (opt_mouse_scroll > 4U)
        opt_mouse_scroll = 2;
    if (opt_key_scroll > 4U)
        opt_key_scroll = 2;
    if (opt_sfx_volume == 0)
        opt_sfx_volume = (unsigned int)-1;
    if (opt_music_volume == 0)
        opt_music_volume = (unsigned int)-1;
}
