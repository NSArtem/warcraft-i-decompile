/* Audio: Miles AIL 3.x (cdecl) and the game's sound layer. See docs/subsystems/audio.md.
 *
 * AIL entry points use the C calling convention (stack arguments, caller
 * pops); the game layer is Watcom register code ("OD" style, unoptimised:
 * `sub esp,0` frames).  The state below is shared with the AIL timer callbacks
 * (AilInit DPMI-locks exactly these objects); the original reads the objects
 * that the callbacks touch through a volatile-qualified lvalue, which Watcom
 * 10.0a compiles to `mov eax,[m]; push eax` instead of `push dword [m]`
 * (evidence: MusicStop 0x26d60 and MusicSetData 0x26c10 match only with the
 * qualifier).  A file that needs the volatile view defines WC1_AUDIO_LOCAL_STATE
 * before including this header and declares it itself, because the same module
 * also reads some of those objects through a *plain* view (`snd_sequences[i]`
 * inside a loop compiles to `push dword [eax+_snd_sequences]`, not a volatile
 * load; e.g. SndFadeOutAndStopAll 0x26e3c, SndSetMusicVolume 0x27460).
 */
#ifndef WC1_AUDIO_H
#define WC1_AUDIO_H

/* AIL entry points (code 0x34d83-0x3aac0 in war.exe), C calling convention. */
extern void __cdecl AIL_startup(void);
extern void __cdecl AIL_shutdown(void);
extern void __cdecl AIL_stop_all_timers(void);
extern void __cdecl AIL_release_all_timers(void);
extern int  __cdecl AIL_set_preference(unsigned number, int value);
extern void __cdecl AIL_set_GTL_filename_prefix(const char *prefix);
extern void * __cdecl AIL_install_MDI_driver_file(const char *fname, void *io);
extern void * __cdecl AIL_install_DIG_driver_file(const char *fname, void *io);
extern void * __cdecl AIL_allocate_sequence_handle(void *mdi);
extern int  __cdecl AIL_sequence_status(void *hseq);
extern int  __cdecl AIL_init_sequence(void *hseq, void *xmidi_data, int seq_num);
extern void __cdecl AIL_start_sequence(void *hseq);
extern void __cdecl AIL_end_sequence(void *hseq);
extern void __cdecl AIL_set_sequence_volume(void *hseq, int volume, int ms);
extern int  __cdecl AIL_register_timer(void (__cdecl *callback)(void));
extern void __cdecl AIL_set_timer_period(int timer, unsigned usec);
extern void __cdecl AIL_start_timer(int timer);
extern void __cdecl AIL_stop_timer(int timer);
extern void * __cdecl AIL_allocate_file_sample(void *hdig, void *file_image, int block);
extern int  __cdecl AIL_active_sample_count(void *hdig);
extern void __cdecl AIL_release_sample_handle(void *hsample);
extern void __cdecl AIL_set_sample_volume(void *hsample, int volume);
extern void __cdecl AIL_set_sample_loop_count(void *hsample, int count);
extern void __cdecl AIL_start_sample(void *hsample);
extern void __cdecl AIL_end_sample(void *hsample);
extern void * __cdecl ail_set_file_sample_end_hook(void *hsample, void *cb);

struct snd_seq {                   /* plain view of snd_sequences (see the comment) */
    void *hseq;
    short state;
};
struct snd_seq_v {                 /* volatile view, used by the files that need it */
    void * volatile hseq;
    short volatile state;
};
struct snd_chan {                  /* the four digital sound channels */
    void *hsample;
    void *data;
};

#ifndef WC1_AUDIO_LOCAL_STATE
/* Game sound layer state (addresses in audio.toml). */
extern unsigned char snd_dig_active;               /* 0x53414 */
extern unsigned char snd_mdi_active;               /* 0x53415 */
extern unsigned char snd_fade_stop_all;            /* 0x5a256 */
extern void *snd_hdig;                             /* 0x5a240 */
extern void *snd_hmdi;                             /* 0x5a248 */
extern void *snd_music_data;                       /* 0x5a244 */
extern struct snd_seq snd_sequences[1];            /* 0x5a24c */
extern struct snd_chan snd_channels[4];            /* 0x5a220 */
extern short snd_sfx_volume127;                    /* 0x5a252 */
extern short snd_music_volume127;                  /* 0x5a254 */
extern int snd_fade_timer;                         /* 0x53418 */
extern short snd_evict_next;                       /* 0x5342e */
extern short snd_evict_next_looped;                /* 0x53430 */
#endif

/* clib / startup helpers used by the layer. */
extern char gtl_prefix_name[];                     /* 0x5341c */
extern char exe_dir[];                             /* startup area */
extern void _makepath(char *path, const char *drive, const char *dir,
                      const char *fname, const char *ext);
extern void DpmiLockRegion(void *addr, unsigned size);  /* 0x312f0 (input) */

#define SND_SEQ_DONE 2

int  AilInit(int sfx_volume, int music_volume);
void SndShutdownAil(void);
int  SndInstallMidi(const char *path, unsigned short io, unsigned short irq,
                    unsigned short dma, unsigned short drq);
int  MusicSetData(void *xmidi);
int  MusicIsPlaying(void);
int  MusicPlayTrack(int seq_num);
void MusicStop(void);
void SndFadeOut(int ms);
void SndFadeOutAndStopAll(int ms);
int  SndInstallDigital(const char *path, unsigned short io, unsigned short irq,
                       unsigned short dma, unsigned short drq);
void SndPlayData(void *voc);
void SndPlayDataLooped(void *voc);
void SndReleaseAll(void);
void SndStopData(void *voc);
int  SndActiveCount(void);
short SndGetSfxVolume(void);
short SndGetMusicVolume(void);
void SndSetSfxVolume(int vol);
void SndSetMusicVolume(int vol);
void SndLockStart(void);
void __cdecl SndSampleEndedCallback(void *hsample);  /* cdecl (link _SndSampleEndedCallback) */
void __cdecl MusicFadeTimerCallback(void);       /* cdecl (link _MusicFadeTimerCallback) */
void SndLockEnd(void);
#endif
