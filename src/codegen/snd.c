/* codegen-flags: -s -ot -ol -4r -zp2
 * Module SND.C (0x26320..0x269f0), game code, "OPT" style: the three sound-id wrappers. */

extern unsigned short cfg_dig_driver;
extern int opt_sfx_volume;
extern void *snd_data_ptrs[];
void SndPlayData(void *data);
void SndPlayDataLooped(void *data);
void SndStopData(void *data);

/* @0x26958 SndPlay; SndPlayLooped is @0x26988 and SndStop @0x269b8 (same shape).  The driver id is copied into a local first: the
 * original compares the zero-extended value as a 32-bit int (cmp edx,0xffff),
 * which OW2 only does for a named local; comparing the global directly gives
 * the narrowed `cmp word [..],-1`.
 */
void SndPlay(unsigned id)
{
    unsigned d = cfg_dig_driver;

    if (d != 0xffff && opt_sfx_volume)
        SndPlayData(snd_data_ptrs[(unsigned short)id]);
}

/* @0x26988 */
void SndPlayLooped(unsigned id)
{
    unsigned d = cfg_dig_driver;

    if (d != 0xffff && opt_sfx_volume)
        SndPlayDataLooped(snd_data_ptrs[(unsigned short)id]);
}

/* @0x269b8 */
void SndStop(unsigned id)
{
    unsigned d = cfg_dig_driver;

    if (d != 0xffff && opt_sfx_volume)
        SndStopData(snd_data_ptrs[(unsigned short)id]);
}
