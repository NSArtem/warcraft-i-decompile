/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27fc0 - availability test of the 'cloud of poison/rain of fire' button: exactly one unit selected and
 * the spell's research row 4 is 1 (researched). */
extern unsigned short player_selection_count[2];  /* 0x5a110 */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short CanCastCloudOfPoison(void)
{
    unsigned long count = player_selection_count[0];
    unsigned long level;

    if (count == 1) {
        level = dat_50008[4][0];
        if (level == 1)
            return 1;
    }
    return 0;
}
