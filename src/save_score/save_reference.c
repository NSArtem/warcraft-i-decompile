/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for SAVE.C (0x23ec0..0x24860) - not built, no src = entry.
 *
 * The two-player link half of saving/loading.  These functions route every
 * message through the link primitives NetSendMessage 0x131d8 (send: takes the 16-byte
 * net_msg buffer, stamps the sequence word and hands the record to the
 * dispatch layer) and fn_12f24 (record poll: returns 0 and stores the
 * record pointer at [edx] when one is available, non-zero otherwise), both
 * outside this area and still unnamed - that alone keeps them from being
 * byte-matched, and OW2's register allocation differs on top.  The logic is
 * verified differentially in tests/test_save_score.py; the guard test
 * test_reference_c_stays_a_near_miss asserts they stay non-matching.
 * See docs/subsystems/save_score.md.
 */
#include "save_score.h"

extern unsigned char net_msg[0x10];                /* 0x5a000 */
extern unsigned short net_sync_state[2];           /* 0x5310c: [0] link active */
extern unsigned char net_sync_msg[0x12];          /* 0x5a090 */
extern unsigned char net_load_state;              /* 0x5a0a2 */
extern unsigned short net_sync_reply;              /* 0x5310e */
extern unsigned char *net_stream_pos;              /* 0x53110 */
extern unsigned short net_play_flag;               /* 0x52586 (cmd_123f0) */
extern unsigned short net_sync_counter;            /* 0x52a7e (unnamed) */
extern unsigned short game_mode_dword_low;         /* 0x59614; game_mode at +2 */

extern int EvtGet(void *out);                      /* 0x31598 (input.toml) */
extern void *memcpy(void *dst, const void *src, unsigned n);
extern void *memset(void *s, int c, unsigned n);

/* link primitives outside this area (see the header comment) */
extern void NetSendMessage(unsigned char *msg);    /* 0x131d8: send net_msg */
extern short fn_12f24(short which, unsigned char **out); /* 0x12f24: poll record */
extern void delay(unsigned ms);                    /* 0x31784 */
extern void *fn_249a4(void *dst, unsigned short n, unsigned char *pos);
                                                   /* 0x249a4: stream read */
extern unsigned char *fn_249c8(unsigned short n, unsigned char *pos);
                                                   /* 0x249c8: stream skip */
extern void SaveVersionDialog(void);                        /* old-version dialog */
extern void TwoPlayerComputerDialog(void);                        /* save mismatch dialog */
extern void NetSendSyncMessage(void *msg);                   /* PACKET.C sync check */
extern void NetSendControlPacket(unsigned short id); /* 0x21c20 */
extern void PacketTick(void);                        /* PACKET.C wait tick */

/* @0x241a4  validate a loaded save image's header: the 0x43 ('C') record,
 * then two zero bytes (single player) or an 18-byte sync block (two
 * player), then 0x566 bytes of scenario data are skipped.  The link branch
 * ends in a wait loop that polls net_load_state while the game state stays
 * 3 or 5; the single-player paths are what the difftest covers. */
unsigned char *SaveStreamValidate(unsigned char *pos)
{
    unsigned short w1, w2;

    if (net_play_flag == 0) {
        if (pos == 0)
            return 0;
        pos = fn_249a4(&w1, 2, pos);
        if (w1 != 0x43) {
            SaveVersionDialog();
            return 0;
        }
        pos = fn_249a4(&w2, 2, pos);
        if (w2 != 0) {
            TwoPlayerComputerDialog();
            return 0;
        }
        return fn_249c8(0x566, pos);
    }
    if (pos != 0) {
        pos = fn_249a4(&w1, 2, pos);
        if (w1 == 0x43) {
            pos = fn_249a4(&w2, 2, pos);
            if (w2 != 0) {
                pos = fn_249a4(net_sync_msg, 0x12, pos);
                net_sync_counter += 3;
                NetSendSyncMessage(net_sync_msg);
                net_sync_reply = 1;
                net_stream_pos = pos;
                net_sync_counter -= 3;
                goto wait;
            }
        }
    }
    NetSendControlPacket(0xc);
    net_sync_reply = 2;
wait:
    net_load_state = 3;
    for (;;) {
        /* The original reads a dword at 0x59614 before testing its high word. */
        int mode = (*(const int *)(const void *)&game_mode_dword_low) >> 16;
        if (mode != 3 && mode != 5)
            break;
        PacketTick();
        if (net_load_state == 0) {
            net_sync_reply = 0;
            return net_stream_pos;
        }
        if (net_load_state <= 2)
            break;
    }
    net_sync_reply = 0;
    return 0;
}

/* @0x2461c  wait for the partner's save/load event: send the empty type-1
 * query, take a type-5 answer's 12-byte payload.  Without a link this is a
 * plain EvtGet. */
int NetQueryRemoteEvent(void *buf)
{
    unsigned char *p;

    if (net_sync_state[0] == 0) {
        EvtGet(buf);
        return 0;
    }
    delay(0x14);
    if (fn_12f24(0, &p) != 0)
        return 0;
    if (fn_12f24(1, &p) != 0)
        return 0;
    net_msg[0] = 4;
    net_msg[1] = 1;
    NetSendMessage(net_msg);
    if ((p[1] & 0x3f) == 5) {
        memcpy(buf, p + 4, 0xc);
        return 1;
    }
    return 0;
}

/* @0x246b4  report our own save/load event as a type-5 message (or the
 * empty type-1 query when nothing happened), then read the reply like
 * NetQueryRemoteEvent does. */
int NetSendLocalEvent(void *buf)
{
    unsigned char *p;

    if (net_sync_state[0] == 0) {
        EvtGet(buf);
        return 0;
    }
    delay(0x14);
    if (fn_12f24(1, &p) != 0)
        return 0;
    if (fn_12f24(0, &p) != 0)
        return 0;
    if (EvtGet(buf) != 0) {
        net_msg[0] = 0x10;
        net_msg[1] = 5;
        memcpy(net_msg + 4, buf, 0xc);
    } else {
        net_msg[0] = 4;
        net_msg[1] = 1;
    }
    NetSendMessage(net_msg);
    if ((p[1] & 0x3f) == 5) {
        memcpy(buf, p + 4, 0xc);
        return 1;
    }
    return 0;
}

/* 0x24780 NetSendDataMessage is built from C now (T3 under Watcom 10.0a):
 * src/save_score/net_send_data_message.c. */

/* @0x247d0  read a type-4 data message into dst (0x80 bytes); a poll that
 * finds nothing overwrites the stale record's type with 1 ("nothing"),
 * which fails the type test and zeroes dst instead. */
int NetRecvDataMessage(short which, void *dst)
{
    unsigned char *msg;

    if (net_sync_state[0] != 0) {
        if (fn_12f24(which, &msg) != 0)
            msg[1] = 1;
    } else {
        msg = net_msg;
    }
    if ((msg[1] & 0x3f) == 4) {
        memcpy(dst, msg + 4, msg[0] - 4);
        if (net_sync_state[0] == 0)
            memset(net_msg, 0, 0x80);
        return 1;
    }
    memset(dst, 0, 0x80);
    return 0;
}
