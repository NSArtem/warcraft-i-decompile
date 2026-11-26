#ifndef MOD_19470_H
#define MOD_19470_H

#include "war.h"

/* Only the first word of each 0x12-byte layer record is identified here. */
typedef struct Layer {
    unsigned short state;
    unsigned char opaque[16];
} Layer;

typedef union Mod19470CheatFlags {
    unsigned long w;
    unsigned char b[4];
} Mod19470CheatFlags;

extern unsigned long scenario_unit_mask;             /* 0x50004; start of scenario image */
extern unsigned short scenario_race;                 /* 0x50088 */
extern unsigned short scenario_race_enemy;           /* 0x5008a */
extern unsigned short scenario_music_track;          /* 0x500cc */
extern long dat_50d7c;                               /* 0x50d7c: LCG state; start of saved state block */
extern unsigned short minimap_redraw_state;          /* 0x50d80 */
extern unsigned short scenario_number;               /* 0x50d82 */
extern unsigned short custom_game;                   /* 0x50e4e */
extern unsigned short custom_map_index;              /* 0x50e50 */
extern unsigned short custom_map_group;              /* 0x50e52 */
extern Mod19470CheatFlags cheat_flags;                /* 0x51214 */
extern unsigned short demo_mode;                     /* 0x5152c */
extern unsigned long map_choice_params[0xb];         /* 0x5160c; 0x51620 is the low word of element 5 */
extern short custom_game_net_option;                 /* 0x516ae */
extern unsigned short load_not_cancelled;            /* 0x516b0 */
extern unsigned short dialog_enabled;                /* 0x517cc */
extern unsigned char packet_tick_intervals[7][5];   /* 0x517ce */
extern unsigned char game_tick_delays[][2];         /* 0x517f1 */
extern unsigned short player_visibility_mask[5];    /* 0x51de6; 0x51de8 is element 1 */
extern unsigned short own_campaign;                  /* 0x52584 */
extern unsigned short net_play_flag;                 /* 0x52586 */
extern unsigned short net_link_speed;                /* 0x52a5e */
extern long prefs_block[5];                          /* 0x532b4 */
extern const char scenario_size_error[7];            /* 0x56bf0 */
extern unsigned short movie_state;                   /* 0x58da4 */
extern short screen_mode;                            /* 0x593f6 */
extern long game_speed_cache;                        /* 0x594f0 */
extern unsigned short game_tick_delay_phase;         /* 0x594f4 */
extern unsigned short packet_tick_countdown;         /* 0x594f6 */
extern void *slot_file;                              /* 0x59610 */
extern unsigned short game_mode_dword_low;           /* 0x59614; dword read also spans game_mode */
extern short game_mode;                              /* 0x59616; high word of that read */
extern unsigned char *pending_save_image;            /* 0x599b0 */
extern unsigned short dat_5a7c2;                     /* 0x5a7c2: game init in progress */
extern unsigned char cursor_layer_id;                /* 0x5aa78 */
extern Layer layers[32];                             /* 0x5aa90 */
extern short crit_error_flag;                        /* 0x61ea0 */

void GameSetRandomSeed(long seed);
int  GameRandom(int id);                /* 0x19478: the LCG step (id unused) */
void GameResolveCustomScenario(void);
void GameInitSession(unsigned char *save_pos);
void GameUpdateFrame(short simulation_due, short packet_due);
void GameRunActiveLoop(void);
int GameHandlePendingLoad(void);
void GameRunSession(void);
void GameShutdownSession(void);

#endif
