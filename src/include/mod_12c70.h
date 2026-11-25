#ifndef MOD_12C70_H
#define MOD_12C70_H

#include "war.h"

struct NetResendRequestBuffer {
    unsigned char prefix[4];
    unsigned char payload_length;
    unsigned char packet_type;
    unsigned short requested_sequence;
};

extern long net_packet_selector_storage; /* 0x52582; signed selector in upper word */
extern struct NetResendRequestBuffer net_resend_request_buffer; /* 0x585a0 */
extern unsigned short net_send_state[3]; /* 0x58d9c */

/* 0x585a4, 0x585a5, and 0x585a6 are payload_length, packet_type,
 * and requested_sequence in net_resend_request_buffer, respectively.
 * 0x58d9e is net_send_state[1], the next expected receive sequence.
 * 0x12dcc is a compiler-local switch table in the code segment. */

/* packet[1] may be modified in place. */
int NetProcessReceivedPacket(unsigned char *packet); /* 0x12dec, watcall */

#endif
