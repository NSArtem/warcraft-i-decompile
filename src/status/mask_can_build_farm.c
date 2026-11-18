/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27cc8 - availability test of the 'build farm' button (records 0x53f14/0x53f64): the scenario's
 * unit mask scenario_unit_mask has bit 0x80 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanBuildFarm(void)
{
    return (scenario_unit_mask & 0x80UL) != 0;
}
