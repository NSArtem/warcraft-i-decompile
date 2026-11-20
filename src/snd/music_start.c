/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
extern unsigned short cfg_mdi_driver;
extern unsigned short mdi_music_res_base[10];
extern void *snd_music_buffer;
extern unsigned short snd_cur_track;
extern unsigned long ResourceBegin(unsigned short id, unsigned long *packed_len);
extern void *ResourceRead(void *dest, unsigned count);
extern int MusicSetData(void __far *xmidi);
extern int MusicPlayTrack(int seq_num);

/* @0x26784 */
void MusicStart(unsigned track)
{
    if (cfg_mdi_driver != 0xffff) {
        if ((unsigned short)track != snd_cur_track) {
            snd_cur_track = (unsigned short)track;
            ResourceBegin((unsigned short)(track + (mdi_music_res_base[cfg_mdi_driver] - 2)), 0);
            ResourceRead(snd_music_buffer, 0);
        }
        MusicSetData((void __far *)snd_music_buffer);
        MusicPlayTrack(0);
    }
}
