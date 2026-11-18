/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x280b8 - "build basic structure" (0x53e60/0x53eec): one unit selected and
 * at least one of farm (bit 7), lumber mill (bit 0xc) or barracks (bit 8)
 * buildable in this scenario. */
extern unsigned long scenario_unit_mask;           /* 0x50004 */
extern unsigned short OneUnitSelected(short is_unit);

unsigned short CanBuildBasicStructure(short is_unit)
{
    if (!OneUnitSelected(is_unit))
        return 0;
    if (scenario_unit_mask & 0x80UL)
        return 1;
    if (scenario_unit_mask & 0x1000UL)
        return 1;
    if (scenario_unit_mask & 0x100UL)
        return 1;
    return 0;
}
