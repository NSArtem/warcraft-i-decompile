/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

extern unsigned char GameRandom(int n);

/* @0x13ff0 */
void UnitIdleTurn(OrderUnit *u)
{
    int r = GameRandom(0x1b);
    unsigned char a;
    unsigned char b;

    if (r == 0) {
        a = u->facing;
        a--;
        b = a;
        u->facing = b & 7;
    } else if (r <= 3) {
        a = u->facing;
        a++;
        b = a;
        u->facing = b & 7;
    }
}
