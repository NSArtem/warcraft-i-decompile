/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27c18 - availability test of the 'train knight/raider' button (records 0x545e0/0x54658): needs the
 * prerequisite building and bit 0x8 of the scenario unit mask. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short player_stables[5];          /* 0x58e3c */
extern unsigned short player_blacksmiths[5];      /* 0x58e14 */

unsigned short CanTrainKnight(void)
{
    return player_stables[0] != 0 && player_blacksmiths[0] != 0 && (scenario_unit_mask & 0x8UL) != 0;
}
