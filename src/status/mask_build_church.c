/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27d04 - availability test of the 'build church/temple' button (records 0x53fc8/0x54040): needs the
 * prerequisite building and bit 0x200 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_mills[5];            /* 0x58e0a */

unsigned short CanBuildChurch(void)
{
    return player_mills[0] != 0 && (scenario_unit_mask & 0x200UL) != 0;
}
