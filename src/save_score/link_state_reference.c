/* codegen-flags: -s -ot -ol -4r -zp2
 * REFERENCE C for the network state transition and the "not valid for two
 * players" dialog of SAVE.C (0x240f8 NetLinkExit, 0x243c4
 * NotValidTwoPlayerDialog).  Not built: register-allocation/order near
 * misses under OW2 (see the t3_blocker in analysis/symbols/save_score.toml);
 * verified as T4 against the original with wc1.cemu.
 *
 * NetSendRecord (0x20a50), NetClose (0x20b70) and Dat_517cc (0x517cc) live
 * outside this area and have no symbol entries yet; the T4 test supplies
 * their addresses through cemu's extra= map.
 */
#include <string.h>
#include "save_score.h"

extern unsigned short net_sync_state[2];   /* 0x5310c */
extern unsigned short net_play_flag;       /* 0x52586 */
extern unsigned short net_send_slot;       /* 0x58d9a */
extern unsigned char net_send_ring[];      /* 0x58848, 10 slots of 136 bytes */
extern unsigned short net_sync_counter;    /* 0x52a7e */
extern unsigned short dat_516ae;           /* 0x516ae */
extern unsigned short custom_game;          /* 0x50e4e */
extern unsigned short screen_mode;         /* 0x593f6 */
extern unsigned short own_campaign;        /* 0x52584 */
extern unsigned short net_event_pending;   /* 0x5a11a */
extern unsigned short evt_pending;         /* 0x516b2 */
extern short game_mode;                    /* 0x59616 */
extern unsigned char net_load_state;       /* 0x5a0a2 */
extern char net_msg_text[];                /* 0x59f00 */
extern char txt_you[];                     /* 0x57974 */
extern char txt_your_enemy[];              /* 0x57978 */
extern char txt_not_valid_2p[];            /* 0x53114 */

extern unsigned short dialog_enabled;           /* 0x517cc */
extern void NetSendPacketChecksummed(unsigned char *pkt, unsigned short word); /* 0x20a50 */
extern void NetDriverShutdown(void);                             /* 0x20b70 */
extern void Delay(int ms);                              /* 0x31784 */
extern void ShowMessage(const char *txt, int width, int height);  /* 0x1a894 */

/* @0x240f8  leave the two-player link: resend the last send-ring record
 * (bracketed by the +3/-3 packet counter), wait 0x12c ms, then clear every
 * link/game state word and close the transport. */
void NetLinkExit(void)
{
    if (net_sync_state[0] != 0) {
        unsigned char *rec = net_send_ring + (unsigned)net_send_slot * 136;
        unsigned short size = *(unsigned short *)(rec + 2);

        net_sync_counter += 3;
        NetSendPacketChecksummed(rec, size);
        net_sync_counter -= 3;
        Delay(0x12c);
    }
    dat_516ae = 0;
    net_play_flag = 0;
    own_campaign = 1;
    screen_mode = 1;
    custom_game = 0;
    net_sync_state[0] = 0;
    NetDriverShutdown();
}

/* @0x243c4  "not valid for two players": compose "You" or "Your enemy"
 * plus the fixed suffix, show it with the screen mode forced to the
 * pending-event state, restore the mode and drop the load state to 2. */
void NotValidTwoPlayerDialog(void)
{
    unsigned short save;

    if (net_event_pending == 0)
        memcpy(net_msg_text, txt_you, 4);
    else
        memcpy(net_msg_text, txt_your_enemy, 11);
    strcat(net_msg_text, txt_not_valid_2p);
    save = screen_mode;
    screen_mode = (net_event_pending == 0);
    ShowMessage(net_msg_text, 0x176, 10);
    screen_mode = save;
    if (dialog_enabled == 0)
        game_mode = 4;
    net_load_state = 2;
    evt_pending = 0;
}
