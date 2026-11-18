/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27c40 - availability test of the 'build road' button (records 0x54428/0x544a0): the scenario's
 * unit mask scenario_unit_mask has bit 0x200000 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanBuildRoad(void)
{
    return (scenario_unit_mask & 0x200000UL) != 0;
}
