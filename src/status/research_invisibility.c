/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27f80 - availability test of the 'research invisibility/unholy armor' button: the spell's research row 8
 * is still 0 and bit 0x20000 of the scenario unit mask is set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned char dat_50008[10][5];            /* 0x50008 player_upgrade */

unsigned short CanResearchInvisibility(void)
{
    return dat_50008[8][0] == 0 && (scenario_unit_mask & 0x20000UL) != 0;
}
