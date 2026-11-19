/*
 * NETWORK.C: the two-player link's transport drivers (module NETWORK.C,
 * 0x1f050..0x209e0, docs/subsystems/network.md).
 *
 * Two drivers behind the six-entry dispatch vtable net_driver 0x59b90
 * (installed by the dispatch layer fn_20a80 0x20a80 from connection_type
 * 0x516ac): the IPX driver 0x1f050..0x1f62c (NetIpx...) and the serial/modem
 * driver 0x1f62c..0x209e0 (NetSerial..., NetModem...).  Every offset below is a
 * field access listed as evidence in analysis/symbols/network.toml; compile
 * with -zp2 (structure packing 2, docs/subsystems/codegen.md).
 *
 * File layout: one function per object (src/network/<name>.c), because the
 * neighbours are not all built from C; the two interrupt handlers share their
 * EOI tail in the original and therefore live in one file
 * (net_serial_isr.c).  Reference C (not byte-matched) ends in _reference.c and
 * is verified differentially (T4) by tests/test_network.py.
 */
#ifndef NETWORK_H
#define NETWORK_H

/* ------------------------------------------------------------ data symbols
 * Addresses are the ones in analysis/symbols/network.toml (and mod_13f60.toml
 * for the settings written by the dialogs). */

extern unsigned short connection_type;   /* 0x516ac 0 sp, 1 modem, 2 ipx, 3 direct */
extern unsigned short own_campaign;      /* 0x52584 */
extern unsigned short net_node_number;   /* 0x52a7c */
extern unsigned short net_sync_counter;  /* 0x52a7e duplicate sends per record */
extern unsigned long  modem_baud;        /* 0x52990 */
extern unsigned short modem_port;        /* 0x52994 */
extern unsigned short modem_irq;         /* 0x52996 */
extern char           modem_init1[];     /* 0x52998 "ATZ" */
extern char           modem_init2[];     /* 0x529c8 "AT &K0 M1 S46=0 &D2" */
extern char           modem_hangup[];    /* 0x529f8 "AT H0" */
extern char           phone_number[];    /* 0x52a28 */
extern unsigned char  dial_pulse;        /* 0x52a51 */
extern unsigned long  serial_baud;       /* 0x52a52 */
extern unsigned short serial_port;       /* 0x52a56 */
extern unsigned short serial_irq;        /* 0x52a58 */

extern char net_signature[];             /* 0x52984 "WARCRAFT" + 2 zero bytes */
extern unsigned short net_modem_link;    /* 0x52a5a */
extern unsigned short net_direct_link;   /* 0x52a5c */
extern unsigned short net_link_speed;    /* 0x52a5e */
extern unsigned short net_link_speed_set;/* 0x52a60, -1 = auto */
extern unsigned short net_port_base[];   /* 0x52a62 {0xffff,0x3f8,0x2f8,0x3e8,0x2e8} */
extern unsigned short net_port_irq[];    /* 0x52a6c {4,3,4,3} */
extern unsigned short net_rx_length;     /* 0x52a74 */
extern unsigned short net_rx_escape;     /* 0x52a76 */
extern unsigned short net_rx_frame_done; /* 0x52a78 */

extern void          *net_ipx_buf;       /* 0x59a00 RmBlock * */
extern char           net_response[];    /* 0x59a10 modem response line, 0x50 */
extern void          *net_uart_buf;      /* 0x59a60 RmBlock * */
extern void          *net_irq_buf;       /* 0x59a64 RmBlock * */
extern unsigned long  net_old_isr_off;   /* 0x59a68 */
extern unsigned long  net_vector_table;  /* 0x59a6c */
extern void          *net_uart;          /* 0x59a70 NetUart * (linear) */
extern unsigned short net_old_vector_seg;/* 0x59a74 */
extern unsigned short net_old_isr_sel;   /* 0x59a76 */
extern unsigned short net_irq_vector;    /* 0x59a78 */
extern unsigned short net_old_vector_off;/* 0x59a7a */
extern unsigned char  net_uart_fifo;     /* 0x59a7c */
extern unsigned char  net_tx_frame[];    /* 0x59a7d, 0x113 bytes (0x88*2+2+1) */
extern char           net_error_text[];  /* 0x59ba8 */
extern unsigned short key_down_table[];  /* 0x5a8d4 (input.toml) */

/* The module's string table (0x570c0..0x57157 and the handshake words): the
 * modem commands and result strings the drivers compare against. */
extern char net_rsp_busy[];        /* 0x570c0 "BUSY" */
extern char net_rsp_error[];       /* 0x570c8 "ERROR" */
extern char net_rsp_no_carrier[];  /* 0x570d0 "NO CARRIER" */
extern char net_rsp_no_dialtone[]; /* 0x570dc "NO DIALTONE" */
extern char net_rsp_no_answer[];   /* 0x570e8 "NO ANSWER" */
extern char net_cr[];              /* 0x570f4 "\r" */
extern char net_rsp_ok[];          /* 0x570f8 "OK" */
extern char net_err_reset[];       /* 0x570fc "Error resetting modem." */
extern char net_err_init_string[]; /* 0x57114 "Error in modem init string." */
extern char net_cmd_atdp[];        /* 0x57130 "ATDP%s" */
extern char net_cmd_atdt[];        /* 0x57138 "ATDT%s" */
extern char net_rsp_connect[];     /* 0x57140 "CONNECT" */
extern char net_rsp_ring[];        /* 0x57148 "RING" */
extern char net_cmd_answer[];      /* 0x57150 "ATA" */
extern char net_cmd_escape[];      /* 0x57154 "+++" */
extern char net_cmd_listen[];      /* 0x1f600 "listen" */
extern char net_cmd_talk[];        /* 0x1f607 "talk" */
extern char net_cmd_waiting[];     /* 0x1f60c "waiting" */
extern char net_cmd_ack[];         /* 0x1f614 "ack" */
extern char *net_result_table[];   /* 0x1f618 five result-string pointers */

/* --------------------------------------------------------- shared layouts */

#define NET_ECB_COUNT 10
#define NET_ECB_SIZE  0xd0
#define NET_PAYLOAD   0x80          /* payload bytes behind the 0x26-byte header */
#define NET_FRAME_MAX 0x88          /* longest link record the drivers accept */
#define NET_RING      0x800         /* rx and tx ring size of the UART */

/* One ring record of the link layer (net_link.toml): 136 bytes, the drivers
 * carry it as their payload. */
#define NET_RECORD    136

/* The IPX event control block, 0xd0 bytes: the standard 0x2a-byte ECB
 * followed by this module's own packet area (slot+0x2a). */
typedef struct NetEcb {
    unsigned long  link;         /* +0x00 */
    unsigned long  esr;          /* +0x04 */
    unsigned char  inuse;        /* +0x08 */
    unsigned char  completion;   /* +0x09 */
    unsigned short socket;       /* +0x0a */
    unsigned char  ipx_work[4];  /* +0x0c */
    unsigned char  driver_work[12]; /* +0x10 */
    unsigned char  node[6];      /* +0x1c source node (filled by IPX) */
    unsigned short frag_count;   /* +0x22 */
    unsigned short frag_off;     /* +0x24 real-mode offset of frag_seg:frag_off */
    unsigned short frag_seg;     /* +0x26 */
    unsigned short frag_size;    /* +0x28 */
    unsigned char  data[0xa6];   /* +0x2a packet header + payload */
} NetEcb;

/* Fields inside NetEcb.data (packet area, slot+0x2a). */
typedef struct NetPacket {
    unsigned char  pad[0x12];    /* +0x00 */
    unsigned char  header[12];   /* +0x12 */
    unsigned long  id;           /* +0x1e */
    unsigned short cmd;          /* +0x22 */
    unsigned short length;       /* +0x24 */
    unsigned char  payload[NET_PAYLOAD]; /* +0x26 */
} NetPacket;

/* The 0x842-byte IPX state: a header and the ten ECBs. */
typedef struct NetIpxState {
    unsigned short socket;       /* +0x00 */
    unsigned long  session;      /* +0x02 */
    unsigned char  node[6];      /* +0x06 own node (own-packet filter) */
    unsigned short word0c;       /* +0x0c */
    unsigned char  rx_header[12];/* +0x0e header of the last received packet */
    unsigned short cmd;          /* +0x1a command stamped into every packet */
    unsigned short peer_cmd;     /* +0x1c command of the last received packet */
    unsigned long  packet_id;    /* +0x1e decremented per send */
    NetEcb         ecb[NET_ECB_COUNT]; /* +0x22, slot 0 = transmit */
} NetIpxState;

/* The 0x1076-byte UART state (docs/subsystems/network.md section 3). */
typedef struct NetUart {
    unsigned short io_base;      /* +0x0000 */
    unsigned short irq;          /* +0x0002 */
    unsigned short port;         /* +0x0004 COM1..COM4 */
    unsigned long  baud;         /* +0x0006 */
    short          rx_head;      /* +0x000a */
    short          rx_tail;      /* +0x000c */
    short          rx_count;     /* +0x000e */
    unsigned char  rx_buf[NET_RING];  /* +0x0010 */
    short          tx_head;      /* +0x0810 */
    short          tx_tail;      /* +0x0812 */
    short          tx_count;     /* +0x0814 */
    unsigned char  tx_buf[NET_RING];  /* +0x0816 */
    unsigned short modem_status; /* +0x1016 */
    unsigned short line_status;  /* +0x1018 */
    unsigned long  cts_count;    /* +0x101a */
    unsigned long  dcd_count;    /* +0x101e */
    unsigned long  ri_count;     /* +0x1022 */
    unsigned long  dsr_count;    /* +0x1026 */
    unsigned long  tx_ints;      /* +0x102a */
    unsigned long  rx_ints;      /* +0x102e */
    unsigned long  tx_overflow;  /* +0x1032 */
    unsigned long  rx_bytes;     /* +0x1036 */
    unsigned long  rx_frames;    /* +0x103a */
    unsigned long  rx_max;       /* +0x103e */
    unsigned long  rx_min;       /* +0x1042 */
    unsigned long  rx_overrun;   /* +0x1046 */
    unsigned long  rx_total;     /* +0x104a */
    unsigned long  rx_too_long;  /* +0x104e */
    unsigned long  rx_longest;   /* +0x1052 */
    unsigned long  rx_long_run;  /* +0x1056 */
    unsigned long  word105a;     /* +0x105a */
    unsigned long  tx_frames;    /* +0x105e */
    unsigned long  tx_max;       /* +0x1062 */
    unsigned long  tx_min;       /* +0x1066 */
    unsigned long  tx_total;     /* +0x106a */
    unsigned long  tx_too_long;  /* +0x106e */
    unsigned long  tx_longest;   /* +0x1072 */
} NetUart;

/* A DPMI 'allocate DOS memory' descriptor (fn_23d10 in dos_realmode_mem):
 * +0 far pointer to the block (offset 0), +6 selector again, +8 the real-mode
 * segment. */
typedef struct RmBlock {
    unsigned char __far *base;   /* +0x00, selector at +0x04 */
    unsigned short       sel;    /* +0x06 */
    unsigned short       seg;    /* +0x08 */
} RmBlock;

/* ---------------------------------------------------------------- IPX API
 * The int 2Fh/int 7Ah wrappers of module mod_1dca0 (0x1dca0..0x1de60, no
 * symbol entries yet - the T4 tests supply their addresses through cemu's
 * extra= map; docs/subsystems/network.md section 2).  The ECB calls take the
 * real-mode address as two words: segment in eax, offset in edx. */
int  IpxInstalled(void);                            /* 0x1dca0 */
unsigned short IpxOpenSocket(unsigned short sock);  /* 0x1dce0 */
void IpxCloseSocket(unsigned short sock);           /* 0x1dd20 */
void IpxListen(unsigned short seg, unsigned short off); /* 0x1ddd0 */
void IpxSend(unsigned short seg, unsigned short off);   /* 0x1de14 */
void IpxRelinquish(void);                           /* 0x1dda0 */
void IpxSetup(unsigned short seg, unsigned short off);  /* 0x1dd5c */

/* DPMI block allocator, module dos_realmode_mem 0x23d10..0x23ec0. */
void *NetAllocReal(unsigned size);                  /* 0x23d10 */
void NetResizeReal(void *block, unsigned size);     /* 0x23d88 */
void NetFreeReal(void *block);                      /* 0x23dd8 */

/* ------------------------------------------------------- module functions */
int  NetIpxStart(void);                             /* 0x1f050 */
int  NetIpxConnect(void);                           /* 0x1f230 */
void NetIpxStop(void);                              /* 0x1f3c8 */
unsigned short NetIpxReceive(void __far *msg);      /* 0x1f424 */
void NetIpxDrain(void);                             /* 0x1f564 */
void NetIpxSend(void __far *msg, unsigned len);     /* 0x1f580 */
int  NetSerialConnect(void);                        /* 0x1f62c */
int  NetSerialStart(void);                          /* 0x1f854 */
void NetSerialStop(void);                           /* 0x1fb0c */
void NetSerialDrain(void);                          /* 0x1fb54 */
void NetSerialQueueBytes(const unsigned char *src, unsigned len); /* 0x1fb60 */
int  NetSerialReceive(void __far *msg);             /* 0x1fbc8 */
void NetSerialSend(void __far *msg, unsigned len);  /* 0x1fd30 */
void NetSerialFixPort(void);                        /* 0x1fe04 */
void NetSerialUartInit(void);                       /* 0x1fe48 */
void NetSerialUartStop(void);                       /* 0x200e8 */
int  NetSerialGetByte(void);                        /* 0x201c0 */
void NetSerialPutByte(unsigned char c);             /* 0x2020c */
void NetSerialPushBytes(const unsigned char *src, unsigned len); /* 0x20258 */
void NetSerialIsrAnchor(void);                      /* 0x202bc */
void __interrupt NetSerialIsr(void);                /* 0x202c0 */
void __interrupt NetSerialIsrFifo(void);            /* 0x20448 */
void NetSerialKickTx(void);                         /* 0x2061c */
void NetModemCommand(const char *cmd);              /* 0x206c8 */
int  NetModemReadByte(const char *expect, int len); /* 0x2070e */
int  NetModemInit(void);                            /* 0x207c0 */
int  NetModemDial(void);                            /* 0x20884 */
int  NetModemAnswer(void);                          /* 0x208d4 */
int  NetModemWaitResponse(const char *expect);      /* 0x20900 */
void NetModemHangup(void);                          /* 0x2094c */
int  NetSerialPortIrq(int index);                   /* 0x209d4 */

#endif
