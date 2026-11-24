/* codegen-compiler: 10.0a */
#include "save_score.h"

extern short fn_20b2c(void);
extern short fn_12f24(short which, unsigned char **out);
extern void fn_19470(unsigned long v);
extern void NetResetLink(void);
extern void NetSendMessage(unsigned char *msg);
extern void VersionMismatchDialog(void);
extern unsigned short ShowMessage(const char *text, unsigned short width, unsigned short height);
extern void delay(unsigned ms);
extern void *memcpy(void *dst, const void *src, unsigned n);
extern long time(long *t);
extern long prefs_block[5];
extern unsigned short own_campaign;
extern unsigned char cd_present;
extern unsigned short net_link_speed;
extern unsigned short net_sync_state[2];
extern char txt_need_cd[];
extern short screen_mode;
extern unsigned char net_msg[0x10];
extern NetRecord net_enemy_record;
extern unsigned short key_down_table[128];
extern short dat_5a9b6;

/* @0x23edc */
short NetLinkHandshake(void)
{
    NetRecord rec;
    unsigned char *reply;
    short i;

    if (fn_20b2c() == 0)
        return 0;
    NetResetLink();
    i = 0;
    for (;;) {
        if (i != (short)key_down_table[1]) {
            if (i != (short)key_down_table[0x1d] || (short)key_down_table[0x1d] != dat_5a9b6)
                return 0;
        }
        rec.local_time = prefs_block[0];
        rec.now = time(0);
        rec.campaign = (unsigned char)own_campaign;
        rec.cd_present = cd_present;
        rec.version = 0x25;
        rec.side_flags = (unsigned char)net_link_speed;
        net_msg[1] = 2;
        net_msg[0] = 0x10;
        memcpy(&net_msg[4], &rec, 12);
        NetSendMessage(net_msg);
        delay(20);
        if (fn_12f24(i, &reply) != 0) {
            memcpy(&rec, &net_msg[4], 12);
            return 0;
        }
        if (fn_12f24(1, &reply) != 0)
            return 0;
        if (reply[1] != 2)
            return 0;
        memcpy(&net_enemy_record, reply + 4, 12);
        if (rec.version != net_enemy_record.version) {
            VersionMismatchDialog();
            return 0;
        }
        if (net_enemy_record.campaign == own_campaign) {
            if (rec.now == net_enemy_record.now)
                continue;
            own_campaign = (rec.now > net_enemy_record.now);
            net_enemy_record.campaign = (own_campaign == 0);
        }
        break;
    }
    if (own_campaign == 0) {
        prefs_block[0] = net_enemy_record.local_time;
        net_link_speed = net_enemy_record.side_flags;
    } else {
        net_enemy_record.now = rec.now;
        net_enemy_record.side_flags = (unsigned char)net_link_speed;
    }
    fn_19470(net_enemy_record.now);
    cd_present |= net_enemy_record.cd_present;
    if (cd_present == 0) {
        screen_mode = 1;
        ShowMessage(txt_need_cd, 0x176, 10);
        return 0;
    }
    net_sync_state[0] = 1;
    net_msg[1] = 1;
    net_msg[0] = 4;
    NetSendMessage(net_msg);
    return 1;
}
