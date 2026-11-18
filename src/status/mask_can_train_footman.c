/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27be0 - availability test of the 'train footman/grunt' button (records 0x545a4/0x5461c): the scenario's
 * unit mask scenario_unit_mask has bit 0x1 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanTrainFootman(void)
{
    return (scenario_unit_mask & 0x1UL) != 0;
}
