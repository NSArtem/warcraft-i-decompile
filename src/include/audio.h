/* Audio: Miles AIL 3.x (cdecl) and the game's sound layer. See docs/subsystems/audio.md */
#ifndef WC1_AUDIO_H
#define WC1_AUDIO_H

/* AIL entry points (code 0x34d83-0x3aac0 in war.exe), C calling convention. */
extern void __cdecl AIL_stop_all_timers(void);
extern void __cdecl AIL_release_all_timers(void);
extern void __cdecl AIL_shutdown(void);
extern int  __cdecl AIL_sequence_status(void *hseq);
extern void __cdecl AIL_end_sequence(void *hseq);
extern int  __cdecl AIL_active_sample_count(void *hdig);
extern void __cdecl AIL_release_sample_handle(void *hsample);

extern unsigned char snd_dig_active;
extern unsigned char snd_mdi_active;
extern void *snd_hdig;
extern void *snd_music_data;
extern struct { void *hseq; short state; } snd_sequences[1];

#define SND_SEQ_DONE 2

void SndShutdownAil(void);
void MusicStop(void);
int  MusicIsPlaying(void);
int  SndActiveCount(void);
#endif
