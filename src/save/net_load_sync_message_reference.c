/* codegen-compiler: 10.0a */
#include "save_score.h"

extern void NetResetLink(void);
extern unsigned short ShowMessage(const char *text, unsigned short width, unsigned short height);
extern void NetSendPacketChecksummed(unsigned char *pkt, unsigned short word);
extern void ResetPacketId(void);
extern unsigned char *SaveReadStream(void *dst, unsigned count, unsigned char *pos);
extern void *memcpy(void *dst, const void *src, unsigned n);
extern unsigned short evt_pending;
extern unsigned short net_link_speed;
extern unsigned short net_sync_state[2];
extern unsigned short net_sync_reply;
extern unsigned char *net_stream_pos;
extern char txt_enemy_loaded[];
extern unsigned char net_send_ring[1360];
extern unsigned short net_ring_state[2];
extern unsigned short net_send_slot;
extern unsigned short net_send_state[3];
extern short screen_mode;
extern short game_mode;
extern NetRecord net_enemy_record;
extern NetSync net_sync_msg;
extern unsigned char net_load_state;
extern unsigned short net_event_pending;

/* @0x2445c */
void NetLoadSyncMessage(NetSync *msg)
{
    short saved;
    unsigned ofs;

    if (net_event_pending == 0)
        return;
    if ((*(long *)net_sync_state >> 16) == 2)
        return;
    if (net_sync_reply == 0) {
        saved = screen_mode;
        screen_mode = net_sync_reply;
        ShowMessage(txt_enemy_loaded, 0x176, 10);
        screen_mode = saved;
        game_mode = 4;
        net_load_state = 2;
        evt_pending = 0;
        return;
    }
    if (msg->now == net_sync_msg.now
        && msg->campaign != net_sync_msg.campaign
        && msg->side_flags == net_sync_msg.side_flags
        && WordInRange(msg->counter_other, (unsigned short)(net_sync_msg.counter - 10), net_sync_msg.counter)
        && WordInRange(net_sync_msg.counter_other, (unsigned short)(msg->counter - 10), msg->counter)) {
        NetResetLink();
        memcpy(net_send_state, &net_sync_msg.counter, 6);
        net_enemy_record = *(NetRecord *)&net_sync_msg;
        net_stream_pos = SaveReadStream(net_send_ring, 0x550, net_stream_pos);
        net_stream_pos = SaveReadStream(net_ring_state, 4, net_stream_pos);
        ResetPacketId();
        net_link_speed = net_enemy_record.side_flags;
        ofs = net_send_slot * 136;
        NetSendPacketChecksummed(net_send_ring + ofs, *(unsigned short *)(net_send_ring + ofs + 2));
        if (net_send_state[1] == (unsigned)net_send_state[2] - 1)
            net_send_state[2]--;
        net_load_state = 0;
        return;
    }
    GamesDifferDialog();
    net_load_state = 1;
}
