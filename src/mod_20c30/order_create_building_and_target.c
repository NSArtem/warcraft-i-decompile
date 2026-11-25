/* codegen-compiler: 10.0a */
#define UnitCreate UnitCreateThreeArgDecl
#include "mod_20c30.h"
#undef UnitCreate

extern Unit *UnitCreate(short x, short y, unsigned char type,
                        unsigned char owner); /* 0x213ce–0x213d9: owner in ECX. */
extern const char msg_cannot_create_unit[19]; /* 0x213ed loads 0x57248. */
extern void UnitSetNextOrder(void *u, unsigned char order); /* 0x21377. */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target,
                            void (*fn)(Unit *)); /* 0x21417. */

void OrderCreateBuildingAndTarget(Unit *u)
{
    unsigned int building_type;
    unsigned char type;
    const char *msg;
    Unit *building;
    short x, y;

    UnitSetNextOrder(u, 2);
    building_type = (unsigned char)
        ((((const unsigned char *)u)[0x1b] & 1) != 0);
    building_type += 0x28U;
    type = (unsigned char)building_type;
    msg = fn_20d74(((const unsigned char *)u)[0x1e], 1, type);
    if (msg != 0) {
        if (((const unsigned char *)u)[0x1e] == 0)
            fn_19f70(msg, 0x24);
    } else {
        x = (short)(*(const short *)((const char *)u + 0x4e) * 16);
        y = (short)(*(const short *)((const char *)u + 0x50) * 16);
        building = UnitCreate(x, y, type, ((const unsigned char *)u)[0x1e]);
        if (building == 0) {
            if (((const unsigned char *)u)[0x1e] == 0)
                fn_19f70(msg_cannot_create_unit, 0x24);
            fn_20d74(((const unsigned char *)u)[0x1e], 0, type);
        } else {
            UnitOrderTarget(u, 0, 0, building, fn_210dc);
        }
    }
}
