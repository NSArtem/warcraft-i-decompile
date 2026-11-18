/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27bb4 - availability test of the 'train peasant/peon' button (records 0x54414/0x5448c): the scenario's
 * unit mask scenario_unit_mask has bit 0x2 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanTrainWorker(void)
{
    return (scenario_unit_mask & 0x2UL) != 0;
}
