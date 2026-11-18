/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27f2c - availability test of the 'research major summoning' button: the spell's research row 5
 * is still 0 and bit 0x100000 of the scenario unit mask is set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short CanResearchMajorSummoning(void)
{
    return dat_50008[5][0] == 0 && (scenario_unit_mask & 0x100000UL) != 0;
}
