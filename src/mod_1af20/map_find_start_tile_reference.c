/* codegen-compiler: 10.0a */
#include "mod_1af20.h"

/* 0x1b13b–0x1b17a: scan 200 records of size 0x5c, preferring types 0x28 and 0x29. */
void MapFindStartTile(int *x, int *y)
{
    unsigned char *choice;
    unsigned char *unit;
    int remaining;
    int type;

    choice = 0;
    unit = unit_array;
    remaining = 200;
    goto test_remaining;
    do {
        if ((unsigned short)(*(unsigned short *)(unit + 0x10) & 0x207U) == 0 &&
            unit[0x1e] == 0) {
            type = unit[0x1b];
            if (type >= 0x28 && type <= 0x29) {
                choice = unit;
                break;
            }
            if (choice == 0)
                choice = unit;
        }
        unit += 0x5c;
    test_remaining:
        --remaining;
    } while (remaining != -1);

    if (choice != 0) {
        *x = *(long *)(choice + 8) >> 16;
        *y = *(long *)(choice + 10) >> 16;
    }
}
