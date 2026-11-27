/* PACKET.C (0x214b0..0x21cf0): the command-packet layer of the two-player
 * link.  Declarations shared by the reconstructed C of src/packet/.
 * Layout, dispatch and evidence: docs/subsystems/packet.md; symbols:
 * analysis/symbols/packet.toml. */
#ifndef WC1_PACKET_H
#define WC1_PACKET_H

struct Unit;
typedef struct Unit Unit;
typedef struct { short x, y; } Point;

/* The packet body that crosses the link (the payload of the link layer's
 * type-4 data message, see docs/subsystems/save_score.md section 1):
 *   +0  unsigned char  type (1..0x11, the dispatch index)
 *   +1  unsigned short sync id (packet_id, stamped by PacketSend)
 *   +3  payload
 * The receive/record buffer is the 0x84-byte scratch the module keeps on the
 * stack (NetRecvDataMessage zeroes 0x80 of it). */
#define PKT_BUF 0x84

/* packet types (cd_215a8 jump table index) */
#define PKT_IDLE              0x01
#define PKT_SELECTION         0x03
#define PKT_PLACE_START       0x04
#define PKT_PLACE_CANCEL      0x05
#define PKT_PLACE_CONFIRM     0x06
#define PKT_TARGET_MODE       0x07
#define PKT_TARGET_CANCEL     0x08
#define PKT_ORDER             0x09
#define PKT_CANCEL_CONSTR     0x0a
#define PKT_START_RESEARCH    0x0b
#define PKT_START_TRAINING    0x0c
#define PKT_CANCEL_PRODUCTION 0x0d
#define PKT_CONTROL           0x0e
#define PKT_CHAT              0x0f
#define PKT_CHEAT_FLAGS       0x10
#define PKT_SYNC_BLOCK        0x11

/* 0x52b00: the outgoing packet id (net_link.toml) */
extern unsigned short packet_id;

/* 0x52586: the two-player flag (cmd_123f0.toml) */
extern unsigned short net_play_flag;
/* 0x517cc: set while the game screen is up (gamedlg.toml) */
extern unsigned short dialog_enabled;
/* 0x52584: which campaign/side this machine plays (save_score.toml) */
extern unsigned short own_campaign;
/* 0x5a11a: the player slot whose command is being executed (save_score.toml) */
extern unsigned short net_event_pending;
/* 0x51e24: a dialog is up (gamedlg.toml) */
extern unsigned short dialog_active;
/* 0x58d9c: outgoing / expected / consumed link sequence words */
extern unsigned short net_send_state[3];
/* 0x50d7c: the deterministic LCG state (codegen_promo.toml) */
extern long dat_50d7c;

/* 0x52b02: "a sync error was already reported" (packet.toml) */
extern unsigned short packet_sync_error;
/* 0x5a7c4: the order id waiting for its target (packet.toml) */
extern unsigned short pending_order;

/* 0x12d04: how many sent records are still outstanding */
extern int NetPendingMessageCount(void);
/* 0x24780: wrap and queue a payload as a link message */
extern void NetSendDataMessage(unsigned short len, void *data);
/* 0x131d8: stamp the sequence and hand the link message to the ring */
extern void NetSendMessage(unsigned char *msg);
/* 0x247d0: take one link message's payload, 1 if it was a data message */
extern int NetRecvDataMessage(short which, void *dst);
/* 0x214d4: the module's send entry (pacing + sync-id stamping) */
extern void PacketSend(unsigned short len, unsigned char *msg);
/* 0x29424/0x2941c: the status panel lock counter */
extern void StatusPanelLockAdjust(short on);
extern unsigned short StatusPanelLockGet(void);
/* 0x248e0: unit pointer <-> unit_array index */
extern int RefRelocate(int ref, int base, short to_offset);
extern Unit *unit_array;                        /* 0x59640 */
/* 0x30bf0: fatal error (prints and aborts) */
extern void __cdecl FatalError(const char *fmt, ...);
/* 0x31cef: string copy */
extern char *strcpy(char *dst, const char *src);
/* 0x2f0a8: send the pending order and reselect the cursor */
extern void fn_2f0a8(int a, int b, Unit *u);
/* 0x1b9b8: pick the map cursor for the next order */
extern void fn_1b9b8(Unit *u);
extern Unit *SelectionFirst(void);                     /* 0x25cc4 */
extern Unit *SelectionNext(void);                      /* 0x25c50 */
extern void UnitStartResearch(Unit *u, unsigned char row);   /* 0x11538 */
extern void UnitStartTraining(Unit *u, unsigned char type);  /* 0x115f4 */
extern void UnitCancelProduction(Unit *u);                   /* 0x104b0 area */
extern void SetCheatFlags(unsigned long flags);              /* 0x1284c */
extern void NetLoadSyncMessage(unsigned char *msg);           /* 0x2445c */

#endif
