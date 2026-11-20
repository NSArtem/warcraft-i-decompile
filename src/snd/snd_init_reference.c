/* codegen-compiler: 10.0a */
#include "audio.h"

extern unsigned int opt_music_volume;
extern unsigned int opt_sfx_volume;
extern const char *dig_driver_files[7];
extern const char *mdi_driver_files[10];
extern unsigned short mdi_music_res_base[10];
extern unsigned char dat_555f8[];
extern char dat_57cb8[];
extern char dat_57cc0[];
extern char dat_57ce4[];
extern char dat_57cfc[];
extern unsigned short cfg_dig_driver;
extern unsigned short cfg_dig_io;
extern unsigned short cfg_dig_irq;
extern unsigned short cfg_dig_dma;
extern unsigned short cfg_dig_drq;
extern unsigned short cfg_mdi_driver;
extern unsigned short cfg_mdi_io;
extern unsigned short cfg_mdi_irq;
extern unsigned short cfg_mdi_dma;
extern unsigned short cfg_mdi_drq;
extern void *snd_music_buffer;
extern unsigned short snd_cur_track;
extern unsigned short snd_table_count;
extern unsigned short snd_saved_sfx_pct;
extern unsigned short snd_saved_music_pct;
extern void *GdsAlloc(unsigned size);
extern int fputs(const char *s, void *fp);
extern void exit(int status);
extern void FatalError(const char *fmt, ...);
#pragma aux FatalError "_*" parm caller [] modify [eax ebx ecx edx]

/* @0x263c0 */
void SndInit(void)
{
    char path[0x90];
    short err;
    int v;
    int m;

    if (cfg_dig_driver != 0xffff) {
        snd_saved_sfx_pct = 0x4e;
        if (opt_sfx_volume == (unsigned int)-1) {
            opt_sfx_volume = 0x4e;
        }
    } else {
        snd_saved_sfx_pct = 0;
        opt_sfx_volume = 0;
    }
    if (cfg_mdi_driver != 0xffff) {
        if (opt_music_volume == (unsigned int)-1 || opt_music_volume == 0) {
            if (cfg_mdi_driver == 9) {
                snd_saved_music_pct = 0x19;
            } else {
                if ((*(long *)((char *)mdi_music_res_base + cfg_mdi_driver * 2 - 2) >> 16) == 2) {
                    v = 100;
                } else {
                    v = 0x7f;
                }
                snd_saved_music_pct = (unsigned short)((int)((unsigned int)v * 100u) / 0x7f);
            }
            if (opt_music_volume == (unsigned int)-1) {
                opt_music_volume = snd_saved_music_pct;
            }
        }
    } else {
        snd_saved_music_pct = 0;
        opt_music_volume = 0;
    }
    m = (short)((opt_music_volume * 127) / 100);
    v = (short)((opt_sfx_volume * 127) / 100);
    AilInit(v, m);
    err = 0;
    snd_table_count = 0;
    snd_cur_track = 0;
    if (cfg_dig_driver != 0xffff) {
        if (cfg_dig_driver >= 7) {
            FatalError(dat_57cb8);
        }
        _makepath(path, 0, exe_dir, dig_driver_files[cfg_dig_driver], 0);
        if (SndInstallDigital(path, cfg_dig_io, cfg_dig_irq, cfg_dig_dma, cfg_dig_drq) != 0) {
            err = 1;
            fputs(dat_57cc0, dat_555f8);
        }
    }
    if (cfg_mdi_driver != 0xffff) {
        if (cfg_mdi_driver >= 10) {
            FatalError(dat_57cb8);
        }
        snd_music_buffer = GdsAlloc(30000);
        DpmiLockRegion(snd_music_buffer, 30000);
        _makepath(path, 0, exe_dir, mdi_driver_files[cfg_mdi_driver], 0);
        if (SndInstallMidi(path, cfg_mdi_io, cfg_mdi_irq, cfg_mdi_dma, cfg_mdi_drq) != 0) {
            err = 1;
            fputs(dat_57ce4, dat_555f8);
        }
    }
    if (err != 0) {
        fputs(dat_57cfc, dat_555f8);
        exit(1);
    }
}
