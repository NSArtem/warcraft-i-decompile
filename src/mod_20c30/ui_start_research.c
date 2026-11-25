/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern int fn_20d14(unsigned short player, int pay, unsigned char row, unsigned char **cost); /* 0x212fd passes the stack slot in ecx. */
extern void NetSendStartResearch(unsigned char row); /* 0x2131f calls 0x21b94. */

void UiStartResearch(unsigned char row)
{
    unsigned char *cost;
    int result;

    result = fn_20d14(0, 1, row, &cost);
    if (result != 0) {
        fn_19f70((const char *)result, 0x24);
    } else {
        fn_20d14(0, 0, row, &cost);
        NetSendStartResearch(row);
    }
}
