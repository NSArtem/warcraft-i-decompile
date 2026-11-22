/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

extern Unit *UnitCreate(short px, short py, short type, unsigned short owner);

unsigned char *LoadScenarioUnitRecords(unsigned char *records, const unsigned char *owner_map)
{
    struct {
        long y;
        long x;
    } coord;
    unsigned raw;
    unsigned type;
    unsigned owner;
    Unit *unit;
    unsigned long *amount;

    for (;;) {
        raw = *records;
        if (raw == 0xff)
            break;
        raw <<= 3;
        coord.x = raw;
        ++records;
        raw = *records;
        raw <<= 3;
        coord.y = raw;
        ++records;
        type = *records++;
        owner = owner_map[*records++];
        if (custom_game != 0 &&
            ((owner == 0 && scenario_race == 1) ||
             (owner == 1 && scenario_race_enemy == owner)))
            type = custom_unit_race_swap[type];

        unit = UnitCreate((short)coord.x, (short)coord.y,
                          (short)type, (unsigned short)owner);
        if (*records == 0xfe) {
            if (unit != 0)
                *(unsigned long *)((char *)unit + 0x54) = (unsigned long)records[1] << 8;
            records += 2;
        }
        if (unit != 0 && type == 0x32) {
            amount = (unsigned long *)((char *)unit + 0x54);
            *amount -= *amount % 100UL;
        }
    }
    return records + 2;
}
