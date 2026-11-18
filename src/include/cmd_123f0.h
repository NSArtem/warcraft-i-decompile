/*
 * Declarations for the CMD.C range 0x123f0..0x12b80
 * (analysis/symbols/cmd_123f0.toml, docs/subsystems/cmd_123f0.md).
 *
 * The object holds two groups:
 *   0x123f0..0x127ff - the scrolled terrain cache (the map view),
 *   0x12800..0x12b80 - the typed command / cheat-code parser.
 *
 * Names owned by other areas (fog_map, fog_cell_table, map_scroll_x/y,
 * MiniTileToCache) and the clib helpers are repeated here so this header is
 * self-contained; keep them in sync with analysis/symbols/.
 *
 * Codegen: this object needs `-s -ot -oa -4r -zp2` (docs/subsystems/cmd_123f0.md
 * section 3) - the project default OPT set does not reproduce it.
 */
#ifndef CMD_123F0_H
#define CMD_123F0_H

/* ------------------------------------------------ other areas ------------ */
extern unsigned short *fog_map;                   /* 0x58578 (graphics.toml) */
extern unsigned short (*fog_cell_table)[4];       /* 0x5858c (graphics.toml) */
extern unsigned short map_scroll_x;               /* 0x500d0 (graphics.toml) */
extern unsigned short map_scroll_y;               /* 0x500d2 (graphics.toml) */

void MiniTileToCache(unsigned short tile, unsigned dst_off);   /* 0x1007c */

/* ------------------------------------------------ this area: terrain cache */
extern unsigned short *tile_map;                  /* 0x58584 */
extern unsigned short tile_cache_top;             /* 0x58590 */
extern unsigned short tile_cache_left;            /* 0x58592 */
extern unsigned short map_scroll_y_max;           /* 0x58594 (53) */
extern unsigned short map_scroll_x_max;           /* 0x58596 (49) */

void MapViewInitLimits(void);                             /* 0x123f0 */
void FogMapClear(void);                                   /* 0x12404 */
void FogMapObscure(void);                                 /* 0x12438 */
void TerrainTileToCache(unsigned short tile, unsigned short x,
                        unsigned short y);                /* 0x1246c */
void TerrainCacheRunX(unsigned short *row, unsigned short x,
                      unsigned short y);                  /* 0x124e8 */
void TerrainCacheRunY(unsigned short *col, unsigned short x,
                      unsigned short y);                  /* 0x12524 */
void TerrainCacheRow(unsigned short y);                   /* 0x12564 */
void TerrainCacheColumn(unsigned short x);                /* 0x12594 */
void MapViewScrollUp(unsigned short n);                   /* 0x125c4 */
void MapViewScrollDown(unsigned short n);                 /* 0x12620 */
void MapViewScrollLeft(unsigned short n);                 /* 0x12688 */
void MapViewScrollRight(unsigned short n);                /* 0x126e4 */
void MapViewSetScroll(short x, short y);                  /* 0x1274c */

/* ------------------------------------------------ this area: commands ----- */
/*
 * The cheat flag word is read as a dword (SetCheatFlags, 0x196cd) and a byte at
 * a time (0x128da, 0x12a40, 0x2f4c0), hence the union.  Bit 31 is the
 * developer-mode bit ("corwin of amber"); the original tests it with
 * `test byte [cheat_flags+3],0x80`, which Watcom 10.0a emits for a bitfield
 * (it promotes a plain unsigned-char byte compare to int: compiler.md).
 */
typedef union CheatFlags {
    unsigned long w;
    unsigned char b[4];
    struct {
        unsigned char b0, b1, b2;
        unsigned char low : 7;
        unsigned char dev : 1;           /* bit 31: developer mode */
    } f;
} CheatFlags;

extern CheatFlags cheat_flags;                    /* 0x51214 */
extern char cheat_code_text[];                    /* 0x51218 obfuscated phrases */
extern char race_command_text[];                  /* 0x512a6 "orc" / "human" */
extern char cheat_enabled_msg[];                  /* 0x569ec */
extern char cheat_disabled_msg[];                 /* 0x56a70 */

extern unsigned short scenario_race;              /* 0x50088 */
extern unsigned short scenario_number;            /* 0x50d82 */
extern short game_mode;                           /* 0x59616 */
extern unsigned short net_play_flag;              /* 0x52586 */

/* Game state that other subsystems own; placeholder names from
 * analysis/symbols/cmd_123f0.toml (SetCheatFlags writes records of it). */
extern unsigned char dat_50008[10][5];            /* per-player spell/upgrade rows */
extern unsigned long dat_50060[5];                /* per-player resource 0..4 */
extern unsigned long dat_50074[5];                /* per-player resource 0..4 */
extern unsigned char dat_5008c[5];                /* per-player gate for the cheats */
extern unsigned short dat_5a7c2;                  /* scenario is (re)starting */
void fn_19edc(char *text, unsigned short flag, unsigned short mode);   /* 0x19edc */

int CheatCodeMatch(char *text, char *code);               /* 0x12800 */
void SetCheatFlags(unsigned long flags);                  /* 0x1284c */
short CheatScenarioCommand(char *text, unsigned char *flags);   /* 0x1295c */
short CheatCodeCommand(char *text, unsigned char *flags);       /* 0x12a2c */
short CmdProcessText(char *text, unsigned char *flags);         /* 0x12b50 */

#endif /* CMD_123F0_H */
