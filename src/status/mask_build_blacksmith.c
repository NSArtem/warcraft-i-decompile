/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27c90 - availability test of the 'build blacksmith' button (records 0x53fb4/0x5402c): needs the
 * prerequisite building and bit 0x4000 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_mills[5];            /* 0x58e0a */

unsigned short CanBuildBlacksmith(void)
{
    return player_mills[0] != 0 && (scenario_unit_mask & 0x4000UL) != 0;
}
