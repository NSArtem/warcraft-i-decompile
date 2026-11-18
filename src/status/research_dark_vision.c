/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27f64 - availability test of the 'research dark vision/far seeing' button: the spell's research row 7
 * is still 0 and bit 0x10000 of the scenario unit mask is set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short CanResearchDarkVision(void)
{
    return dat_50008[7][0] == 0 && (scenario_unit_mask & 0x10000UL) != 0;
}
