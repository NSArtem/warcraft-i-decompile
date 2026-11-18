/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27cd8 - availability test of the 'build barracks' button (records 0x53f3c/0x53f8c): the scenario's
 * unit mask scenario_unit_mask has bit 0x100 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanBuildBarracks(void)
{
    return (scenario_unit_mask & 0x100UL) != 0;
}
