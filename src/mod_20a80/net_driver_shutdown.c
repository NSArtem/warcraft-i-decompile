/* codegen-flags: -s -ot -oa -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
#include "mod_20a80.h"

extern void (*net_driver[6])(void);

/* @0x20b70 */
void NetDriverShutdown(void)
{
    if (net_driver_stop != 0) {
        net_driver_stop();
        net_driver[0] = 0;
        net_driver_connect = 0;
        net_driver_stop = 0;
        net_driver_receive = 0;
        net_driver_send = 0;
        net_driver_drain = 0;
    }
}
