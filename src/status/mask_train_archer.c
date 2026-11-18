/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27bc4 - availability test of the 'train archer/spearman' button (records 0x545b8/0x54630): needs the
 * prerequisite building and bit 0x10 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_mills[5];            /* 0x58e0a */

unsigned short CanTrainArcher(void)
{
    return player_mills[0] != 0 && (scenario_unit_mask & 0x10UL) != 0;
}
