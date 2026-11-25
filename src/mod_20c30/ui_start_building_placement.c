/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void NetSendPlaceStart(unsigned char type); /* 0x212de calls 0x21ac8. */

void UiStartBuildingPlacement(unsigned char type)
{
    const char *msg;

    msg = fn_20d74(0, 1, type);
    if (msg != 0) {
        fn_19f70(msg, 0x24);
        return;
    }
    fn_20d74(0, 0, type);
    NetSendPlaceStart(type);
}
