/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

extern int fn_2e650(short x, short y, short type, unsigned short owner, void *size);

void PlaceCustomUnitCopies(unsigned owner, int count, Unit *anchor, int type)
{
    struct {
        unsigned long mask;
        long x;
        long y;
        short *size;
    } local;
    int i;

    if (count != 0 && owner == 0) {
        local.mask = scenario_unit_mask;
        if (type == 2 || type == 3)
            local.mask |= 0x2;
        else if (type == 0 || type == 1)
            local.mask |= 0x101;
        else if (type == 4 || type == 5)
            local.mask |= 0x5104;
        else if (type == 6 || type == 7)
            local.mask |= 0x7108;
        else if (type == 8 || type == 9)
            local.mask |= 0x1110;
        else if (type == 10 || type == 11)
            local.mask |= 0x1c5420UL;
        else if (type == 12 || type == 13)
            local.mask |= 0x39240UL;
        else
            FatalError(place_custom_error);
        scenario_unit_mask = local.mask;
    }

    local.x = *(long *)((char *)anchor + 0x08) >> 16;
    local.y = *(long *)((char *)anchor + 0x0a) >> 16;
    i = 1;
    if (i < count) {
        local.size = unit_type_size[type];
        do {
            fn_2e650((short)local.x, (short)local.y, (short)type,
                      (unsigned short)owner, local.size);
            ++i;
        } while (i < count);
    }
}
