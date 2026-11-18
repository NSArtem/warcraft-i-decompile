/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27c80 - availability test of the 'build lumber mill' button (records 0x53f28/0x53f78): the scenario's
 * unit mask scenario_unit_mask has bit 0x1000 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanBuildLumberMill(void)
{
    return (scenario_unit_mask & 0x1000UL) != 0;
}
