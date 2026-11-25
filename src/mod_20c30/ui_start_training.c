/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void NetSendStartTraining(unsigned char type); /* 0x2135e calls 0x21bc4. */

void UiStartTraining(unsigned char type)
{
    const char *msg;

    msg = fn_20d74(0, 1, type);
    if (msg != 0) {
        fn_19f70(msg, 0x24);
        return;
    }
    fn_20d74(0, 0, type);
    NetSendStartTraining(type);
}
