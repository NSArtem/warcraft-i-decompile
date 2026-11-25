/* codegen-flags: -s -ot -oa -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern Point player_home_point[5]; /* 0x21458 and 0x2145f load the two words of entry zero. */
extern const char msg_town_square_occupied[28]; /* 0x21480: message at 0x5725c. */
extern unsigned short pending_order; /* 0x21490 stores 0x1e. */
extern int CanPlaceUnitFootprint(short tile_x, short tile_y, unsigned char type); /* 0x21471 calls 0x13990. */
extern void IssueOrderAt(short x, short y, Unit *target); /* 0x2149f calls 0x2f0a8. */

void UiIssueTownSquareOrder(unsigned char type)
{
    const char *msg;
    short y;
    short x;

    msg = fn_20d74(0, 1, type);
    if (msg != 0) {
        fn_19f70(msg, 0x24);
    } else {
        fn_20d74(0, 0, type);
        x = player_home_point[0].x;
        y = player_home_point[0].y;
        if ((unsigned short)CanPlaceUnitFootprint(x, y, type) == 0) {
            fn_19f70(msg_town_square_occupied, 0x24);
            return;
        }
        pending_order = 0x1e;
        IssueOrderAt(x, y, 0);
    }
}
