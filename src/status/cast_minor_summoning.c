/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27f9c - availability test of the 'summon scorpions/spiders' button: exactly one unit selected and
 * the spell's research row 3 is 1 (researched). */
extern unsigned short player_selection_count[2];  /* 0x5a110 */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short CanCastMinorSummon(void)
{
    unsigned long count = player_selection_count[0];
    unsigned long level;

    if (count == 1) {
        level = dat_50008[3][0];
        if (level == 1)
            return 1;
    }
    return 0;
}
