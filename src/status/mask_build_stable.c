/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27cac - availability test of the 'build stable/kennel' button (records 0x53fdc/0x54054): needs the
 * prerequisite building and bit 0x2000 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_mills[5];            /* 0x58e0a */

unsigned short CanBuildStable(void)
{
    return player_mills[0] != 0 && (scenario_unit_mask & 0x2000UL) != 0;
}
