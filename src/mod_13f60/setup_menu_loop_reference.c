/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern void DialogArtLoad(void);
extern void DialogArtFree(void);
extern void DialogSoundsLoad(void);
extern void DialogSoundsFree(void);
extern void *GdsAlloc(unsigned size);
extern void ResourceFreeBody(void *hdr);
extern void MusicStart(unsigned track);
extern void MusicClear(void);
extern void BitmapBlitTransparent(void);
extern unsigned long dat_51658[];
extern void *dat_5165c;
extern void (*dat_51718[])(void);
extern unsigned short intro_music_started;
extern unsigned char setup_state;
extern unsigned char setup_return_state;
extern short dat_5aba0;
extern short dat_5aba2;
extern short dat_5aba4;
extern short dat_5aba6;
extern void *dat_5aba8;
extern void *dat_5abac;

/* @0x162b0 */
void SetupMenuLoop(void)
{
    DialogArtLoad();
    dat_5165c = GdsAlloc(0x12c0);
    dat_5aba0 = 0;
    dat_5aba2 = 1;
    dat_5aba4 = 0x140;
    dat_5aba6 = 0xf;
    dat_5aba8 = dat_51658;
    dat_5abac = (void *)BitmapBlitTransparent;
    DialogSoundsLoad();
    if (intro_music_started != 0) {
        intro_music_started = 0;
    } else {
        MusicStart(0x10);
    }
    if (dat_516ae != 0) {
        screen_mode = own_campaign;
        setup_return_state = 5;
        setup_state = 5;
    } else {
        screen_mode = 1;
        setup_state = 0;
    }
    do {
        dat_51718[setup_state]();
    } while (setup_state != 0x10);
    ResourceFreeBody(dat_51658);
    DialogArtFree();
    DialogSoundsFree();
    MusicClear();
}
