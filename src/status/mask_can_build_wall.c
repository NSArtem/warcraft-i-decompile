/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27c50 - availability test of the 'build wall' button (records 0x5443c/0x544b4): the scenario's
 * unit mask scenario_unit_mask has bit 0x400000 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanBuildWall(void)
{
    return (scenario_unit_mask & 0x400000UL) != 0;
}
