/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27ce8 - availability test of the 'build tower' button (records 0x53ff0/0x54068): needs the
 * prerequisite building and bit 0x400 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_blacksmiths[5];      /* 0x58e14 */

unsigned short CanBuildTower(void)
{
    return player_blacksmiths[0] != 0 && (scenario_unit_mask & 0x400UL) != 0;
}
