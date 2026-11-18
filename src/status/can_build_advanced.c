/* codegen-flags: -s -ot -ol -4r -zp2 */
/* 0x280e8 - "build advanced structure" (0x53e74/0x53f00): one unit selected
 * and at least one advanced structure buildable (blacksmith, church/temple,
 * stable/kennel, tower or a town hall to rebuild). */
extern unsigned short CanBuildBlacksmith(short is_unit);
extern unsigned short CanBuildChurch(short is_unit);
extern unsigned short CanBuildStable(short is_unit);
extern unsigned short CanBuildTower(short is_unit);
extern unsigned short CanRebuildTownHall(short is_unit);
extern unsigned short OneUnitSelected(short is_unit);

unsigned short CanBuildAdvancedStructure(short is_unit)
{
    if (!OneUnitSelected(is_unit))
        return 0;
    if (CanBuildBlacksmith(is_unit))
        return 1;
    if (CanBuildChurch(is_unit))
        return 1;
    if (CanBuildStable(is_unit))
        return 1;
    if (CanBuildTower(is_unit))
        return 1;
    if (CanRebuildTownHall(is_unit))
        return 1;
    return 0;
}
