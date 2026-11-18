/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27c70 - availability test of the 'train cleric/necrolyte' button (records 0x547ac/0x54838): the scenario's
 * unit mask scenario_unit_mask has bit 0x40 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanTrainCleric(void)
{
    return (scenario_unit_mask & 0x40UL) != 0;
}
