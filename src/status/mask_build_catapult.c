/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x27bf0 - availability test of the 'build catapult' button (records 0x545cc/0x54644): needs the
 * prerequisite building and bit 0x4 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_blacksmiths[5];      /* 0x58e14 */
extern unsigned short player_mills[5];            /* 0x58e0a */

unsigned short CanBuildCatapult(void)
{
    return player_blacksmiths[0] != 0 && player_mills[0] != 0 && (scenario_unit_mask & 0x4UL) != 0;
}
