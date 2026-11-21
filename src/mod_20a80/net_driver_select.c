/* codegen-compiler: 10.0a */
#include "mod_20a80.h"

extern unsigned short connection_type;
extern void (*net_driver[6])(void);
extern void NetSerialStart(void);
extern void NetSerialConnect(void);
extern void NetSerialStop(void);
extern void NetSerialReceive(void);
extern void NetSerialSend(void);
extern void NetSerialDrain(void);
extern void NetIpxStart(void);
extern void NetIpxConnect(void);
extern void NetIpxStop(void);
extern void NetIpxReceive(void);
extern void NetIpxSend(void);
extern void NetIpxDrain(void);

/* @0x20a80 */
int NetDriverSelect(void)
{
    switch (connection_type) {
    case 1:
    case 3:
        net_driver[0] = NetSerialStart;
        net_driver_connect = NetSerialConnect;
        net_driver_stop = NetSerialStop;
        net_driver_receive = NetSerialReceive;
        net_driver_send = NetSerialSend;
        net_driver_drain = NetSerialDrain;
        return ((int (*)(void))net_driver[0])();
    case 2:
        net_driver[0] = NetIpxStart;
        net_driver_connect = NetIpxConnect;
        net_driver_stop = NetIpxStop;
        net_driver_receive = NetIpxReceive;
        net_driver_send = NetIpxSend;
        net_driver_drain = NetIpxDrain;
        return ((int (*)(void))net_driver[0])();
    }
    return 0;
}
