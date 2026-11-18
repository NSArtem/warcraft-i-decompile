/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27c60 - availability test of the 'train conjurer/warlock' button (records 0x54694/0x54720): the scenario's
 * unit mask scenario_unit_mask has bit 0x20 set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */

unsigned short CanTrainConjurer(void)
{
    return (scenario_unit_mask & 0x20UL) != 0;
}
