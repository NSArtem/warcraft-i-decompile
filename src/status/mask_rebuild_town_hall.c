/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x27b98 - availability test of 'rebuild the town hall' (records 0x54004/
 * 0x5407c): only when the player has no town hall left and bit 0xb of the
 * scenario unit mask is set. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern void *player_town_hall[5];                 /* 0x58db0 */

unsigned short CanRebuildTownHall(void)
{
    return player_town_hall[0] == 0 && (scenario_unit_mask & 0x800UL) != 0;
}
