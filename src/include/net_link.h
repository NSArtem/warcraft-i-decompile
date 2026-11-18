/*
 * The two-player link ring layer (module mod_12c70, 0x12c70..0x13270).
 * Names and evidence: analysis/symbols/net_link.toml; prose:
 * docs/subsystems/save_score.md section 1 (the ring and message layout).
 *
 * A ring record is 136 (0x88) bytes: a 4-byte transport header written by
 * fn_20a50 (checksum at +0, length at +2), then the 16-byte link message
 * (size at +4, type at +5, sequence at +6, payload at +8).  The send ring has
 * 10 slots at 0x58848, the receive ring 4 slots at 0x58628.
 */
#ifndef NET_LINK_H
#define NET_LINK_H

struct NetRingRecord {
    unsigned short checksum;        /* +0x00 fn_20a50 */
    unsigned short length;          /* +0x02 fn_20a50 */
    unsigned char size;             /* +0x04 message total size */
    unsigned char type;             /* +0x05 message type (low 6 bits) */
    unsigned short seq;             /* +0x06 sender sequence number */
    unsigned char payload[0x80];    /* +0x08 */
};

#define NET_SEND_SLOTS 10
#define NET_RECV_SLOTS 4

extern unsigned char net_send_ring[];               /* 0x58848 */
extern unsigned char net_recv_ring[];               /* 0x58628 */
extern unsigned short net_ring_state[2];            /* 0x58d98: [0] recv slot */
extern unsigned short net_send_slot;                /* 0x58d9a */
extern unsigned short net_send_state[3];            /* 0x58d9c: seq, expect, done */
extern unsigned short net_reply_pending;            /* 0x58da2 */
extern unsigned short dat_516ae;                    /* 0x516ae: link mode word */

void NetResetLink(void);                            /* 0x12c70 */
unsigned short NetNextRecvSlot(unsigned short *counter);  /* 0x12cd4 */
unsigned short NetNextSendSlot(unsigned short *counter);  /* 0x12cec */
int NetPendingMessageCount(void);                    /* 0x12d04 */
struct NetRingRecord *NetFindSentRecord(unsigned short seq);      /* 0x12d2c */
struct NetRingRecord *NetFindReceivedRecord(unsigned short seq);  /* 0x12d7c */

#endif /* NET_LINK_H */
