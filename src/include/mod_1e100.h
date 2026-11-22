#ifndef MOD_1E100_H
#define MOD_1E100_H

#include "war.h"

extern unsigned short scenario_race;             /* 0x50088 */
extern unsigned short map_scroll_x_low_word;     /* 0x500ce */
extern unsigned short scenario_number;           /* 0x50d82 */
extern unsigned short player_score[4];           /* 0x50e34 */
extern unsigned short custom_game;               /* 0x50e4e */
extern unsigned short demo_mode;                 /* 0x5152c */
extern unsigned short load_not_cancelled;         /* 0x516b0 */
extern unsigned short evt_pending;                /* 0x516b2 */
extern unsigned short setup_quit;                 /* 0x5176a */
extern unsigned short net_play_flag;              /* 0x52586 */
extern short preferences_load_failed;            /* 0x52588 */
extern unsigned long archive_version;             /* 0x55824 */
extern const char archive_version_error_message[]; /* 0x56f38 */
extern void *slot_file;                           /* 0x59610 */
extern unsigned short game_mode_dword_low;        /* 0x59614; dword reads also span game_mode */
extern short game_mode;                           /* 0x59616 */
extern unsigned char *pending_save_image;         /* 0x599b0 */
extern const char *archive_version_error;         /* 0x62890 */

/* Both functions use the default Watcom register convention. */
void InitNewCampaign(void);                       /* 0x1e100 */
void RunGameModeLoop(void);                       /* 0x1e158 */

#endif
