/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
extern unsigned short snd_cur_track;
extern void MusicStop(void);
extern int MusicSetData(void __far *xmidi);

/* @0x267e0 */
void MusicClear(void)
{
    MusicStop();
    MusicSetData((void __far *)0);
    snd_cur_track = 0;
}
