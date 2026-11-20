/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern char dat_572ec[];                /* 0x572ec "Unable to create unit." */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *));

/* @0x229c8 */
int PlaceBoxCreateBuilding(Unit *worker, Point p)
{
    Unit *nu;

    nu = UnitCreate((short)(p.x << 4), (short)(p.y << 4),
                    place_type[net_event_pending]);
    if (nu == 0) {
        if (net_event_pending == 0) {
            fn_19f70(dat_572ec, 0x24);
        }
        return 0;
    }
    if (net_event_pending == 0) {
        fn_1b9b8();
    }
    UnitOrderTarget(worker, 0, 0, nu, fn_210dc);
    return 1;
}
