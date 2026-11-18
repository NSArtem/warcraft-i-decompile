/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x280a4 - exactly one unit is selected: the panel then shows that unit and
 * the "build basic/advanced structure" buttons become available
 * (0x280b8/0x280e8). */
extern unsigned short player_selection_count[2];   /* 0x5a110 */

unsigned short OneUnitSelected(short is_unit)
{
    unsigned long count = player_selection_count[0];

    return count == 1;
}
