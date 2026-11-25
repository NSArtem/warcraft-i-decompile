/* codegen-compiler: 10.0a */
#include "mod_12c70.h"

struct NetRingRecord;
extern struct NetRingRecord *NetFindSentRecord(unsigned short seq); /* 0x12e59 calls 0x12d2c */
extern void NetSendPacketChecksummed(unsigned char *pkt, unsigned short word); /* 0x12e70 and 0x12ede call 0x20a50 */

int NetProcessReceivedPacket(unsigned char *packet)
{
    unsigned char masked;
    unsigned char type;
    long work;
    short selector;
    unsigned short resend_seq;
    unsigned char *record;
    unsigned short received;
    unsigned short expected;
    unsigned short advanced;
    unsigned long received_wide;
    unsigned long successor;
    unsigned short received_eight;
    unsigned short expected_eight;
    unsigned long successor_eight;

    masked = packet[1] & 0x40;
    work = masked;
    if (work) {
        masked = packet[1] & 0x80;
        work = masked;
        selector = (short)(work >> 7);
        work = net_packet_selector_storage >> 16;
        work ^= (long)selector;
        if (work == 0)
            goto reject;
    }

    type = packet[1] & 0x3f;
    packet[1] = type;
    switch (type) {
    case 3:
        resend_seq = *(unsigned short *)(packet + 2);
        if (resend_seq < net_send_state[0]) {
            do {
                record = (unsigned char *)NetFindSentRecord(resend_seq);
                if (record != 0)
                    NetSendPacketChecksummed(record,
                        (unsigned short)(record[4] + 4));
                ++resend_seq;
            } while (resend_seq < net_send_state[0]);
        }
    reject:
        return 1;

    case 1:
    case 2:
    case 4:
    case 5:
    case 6:
    case 7:
        received = *(volatile unsigned short *)(packet + 2);
        expected = net_send_state[1];
        if (received == expected) {
            advanced = expected;
            ++advanced;
            net_send_state[1] = advanced;
            return 0;
        }
        successor = expected;
        received_wide = *(volatile unsigned short *)(packet + 2);
        ++successor;
        if (received_wide == successor) {
            net_resend_request_buffer.payload_length = 4;
            net_resend_request_buffer.packet_type = 3;
            net_resend_request_buffer.requested_sequence = net_send_state[1];
            NetSendPacketChecksummed((unsigned char *)&net_resend_request_buffer, 8);
            return 2;
        }
        if ((unsigned short)received_wide < net_send_state[1])
            goto reject;
        /* Fall through to 0x12ef6. */
    case 8:
        received_eight = *(volatile unsigned short *)(packet + 2);
        expected_eight = net_send_state[1];
        if (received_eight != expected_eight) {
            successor_eight = expected_eight;
            received_wide = *(volatile unsigned short *)(packet + 2);
            ++successor_eight;
            if (received_wide != successor_eight)
                goto reject;
        }
        return 0;

    default:
        goto reject;
    }
}
