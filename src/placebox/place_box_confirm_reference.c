/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

/* @0x22ae4 */
void PlaceBoxConfirm(Point p)
{
    unsigned short code;
    Unit *u;
    unsigned short ok;
    long idx;
    unsigned char t;
    unsigned short *fp;

    code = PlaceBoxCheck(p, place_type[net_event_pending]);
    if (code != 0) {
        if (net_event_pending == 0) {
            fn_19f70(place_error[code], 0x24);
        }
        return;
    }
    PlaceBoxCancel();
    u = SelectionFirst();
    if (u == 0)
        return;
    t = *((unsigned char *)u + 0x1b);
    if (t >= 2 && t <= 3) {
        idx = (*(long *)((char *)u + 8) >> 16) +
              ((*(long *)((char *)u + 10) >> 16) << 6);
        ((unsigned char *)map_flags)[idx * 2 + 1] &= 0xfe;
    }
    t = place_type[net_event_pending];
    if (t <= 0x32) {
        ok = PlaceBoxCreateBuilding(u, p);
    } else if (t == 0x34) {
        ok = PlaceBoxRoad(p);
    } else if (t == 0x35) {
        ok = PlaceBoxWall(u, p);
    }
    t = *((unsigned char *)u + 0x1b);
    if (t >= 2 && t <= 3) {
        fp = map_flags + idx;
        if ((*fp & 0x200) == 0) {
            ((unsigned char *)fp)[1] |= 1;
        }
    }
    if (ok != 0) {
        fn_20d74(net_event_pending, 1, place_type[net_event_pending]);
        if (place_type[net_event_pending] == 0x34) {
            if (fn_20d74(net_event_pending, 1, 0x34) == 0) {
                fn_20d74(net_event_pending, 0, 0x34);
                PlaceBoxStart(0x34);
            }
        }
    }
}
