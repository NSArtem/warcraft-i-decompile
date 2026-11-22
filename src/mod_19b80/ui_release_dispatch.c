/* codegen-compiler: 10.0a */
#include "mod_19b80.h"

extern unsigned short demo_mode;
extern void (*ui_release_handler)(void);
extern void NetSendControlPacket(unsigned short id);

/* @0x1a130 */
void UiReleaseDispatch(void)
{
    if (demo_mode != 0) {
        NetSendControlPacket(1);
        return;
    }
    ui_release_handler();
}
