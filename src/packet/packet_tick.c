/* codegen-flags: -s -ot -ol -4r -zp2
 * codegen-compiler: 10.0a
 * PacketTick (0x21844): the command layer's once-per-tick pump.
 *   1. sanity check of the link sequence words (PKT:7 %d %d),
 *   2. take the two directions' packets (0 = the local/loopback direction,
 *      1 = the partner's),
 *   3. two-player: generate the sync id when the queue is empty, send the idle
 *      packet,
 *   4. execute both directions - the local one with net_event_pending = 0 and
 *      the partner's with 1, in an order fixed by own_campaign so that both
 *      machines execute the two players' commands in the same order,
 *   5. clear dialog_active and compare the two sync stamps.
 * Calls: fn_197b0 0x197d1 (game loop), fn_19908 0x1990d, fn_1e158 0x1e230 /
 * 0x1e242, SaveStreamValidate 0x242b4, fn_2fac4 0x2fb7d. */
#include "packet.h"

/* @0x21844 */
void PacketTick(void)
{
    unsigned char buf1[PKT_BUF];
    unsigned char buf0[PKT_BUF];

    if (net_play_flag != 0 && net_send_state[2] != net_send_state[1])
        FatalError("PKT:7 %d %d", net_send_state[2], net_send_state[1]);
    NetRecvDataMessage(0, buf1);
    if (net_play_flag != 0)
        NetRecvDataMessage(1, buf0);
    if (net_play_flag != 0 && dialog_enabled != 0 &&
        NetPendingMessageCount() == 0)
        PacketGenerateId();
    if (net_play_flag != 0)
        PacketSendIdle();
    if (own_campaign != 0) {
        PacketDispatch(buf1);
        if (net_play_flag != 0) {
            net_event_pending = 1;
            PacketDispatch(buf0);
            net_event_pending = 0;
        }
    } else {
        if (net_play_flag != 0) {
            net_event_pending = 1;
            PacketDispatch(buf0);
            net_event_pending = 0;
        }
        PacketDispatch(buf1);
    }
    dialog_active = 0;
    PacketCheckSync(buf1, buf0);
}
