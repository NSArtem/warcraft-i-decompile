/*
 * Declarations for the sound-event object 0x1b800..0x1bf80
 * (analysis/symbols/mod_1b800.toml, docs/subsystems/mod_1b800.md).
 *
 * The module turns game events (unit selected, order acknowledged, unit
 * dying, building placed/destroyed, bullet launched/landed, enemy near the
 * town hall, ...) into sound ids and plays them through SndPlay, or, with the
 * sound effects switched off, prints the event's caption in the message strip.
 * It owns no unit logic; the callers are the unit, order, bullet and place-box
 * code.
 *
 * Unit and bullet records: only the fields this object touches are named
 * (layout of docs/subsystems/game_2c4e0.md).  Offsets are the evidence,
 * names are descriptive.  Compile with -zp2.
 */
#ifndef MOD_1B800_H
#define MOD_1B800_H

typedef struct { short x, y; } Point;   /* tile coordinates (read as one dword x | y<<16) */

typedef union Flags {
    unsigned short w;
    struct { unsigned char lo, hi; } b;
} Flags;

typedef struct Unit {
    short px, py;                    /* 0x00 pixel position (tile * 16) */
    unsigned char pad04[5];          /* 0x04 */
    unsigned char sound;             /* 0x09 pending sound id (played by the animation opcode 0x10457) */
    short tx, ty;                    /* 0x0a tile position */
    unsigned short flags2;           /* 0x0e secondary flags */
    Flags flags;                     /* 0x10 main flags */
    unsigned char pad12[6];          /* 0x12 */
    unsigned short alert_timer;      /* 0x18 under-attack alert cool-down (4000 after an alert) */
    unsigned char pad1a;             /* 0x1a */
    unsigned char type;              /* 0x1b unit type */
    unsigned char pad1c[2];          /* 0x1c */
    unsigned char owner;             /* 0x1e owner/player 0..4 */
    unsigned char pad1f[0x36 - 0x1f];/* 0x1f */
    unsigned short timer36;          /* 0x36 */
} Unit;

/* One bullet/missile record (BULLET.C); only the fields read here. */
typedef struct Bullet {
    unsigned char type;              /* 0x00 bullet type, index of bullet_sound[] */
    unsigned char pad01[2];          /* 0x01 */
    unsigned char damage;            /* 0x03 non-zero when the hit does damage */
    unsigned char pad04[0x1e - 4];   /* 0x04 */
    Unit *target;                    /* 0x1e unit the sound is positioned on */
} Bullet;

/* ---- data (symbol database names) ---- */
extern unsigned int opt_sfx_volume;                 /* 0x532bc */
extern unsigned short map_scroll_x, map_scroll_y;   /* 0x500d0/0x500d2 */
extern unsigned short scenario_race;                /* 0x50088 */
extern unsigned short scenario_race_enemy;          /* 0x5008a */
extern Unit **object_map;                           /* 0x58580 64x64 tile -> unit */
extern unsigned char hostility[25];                 /* 0x51883 owner x owner, 1 = enemy */
extern Unit *player_town_hall[5];                   /* 0x58db0 */
extern Point player_home_point[5];                  /* 0x50e68 */

extern const char *snd_event_caption[48];           /* 0x52028 */
extern const unsigned short *snd_event_table[2];    /* 0x520e8 per race */
extern unsigned short unit_attack_sound[];          /* 0x520f0 */
extern unsigned short bullet_sound[];               /* 0x52130 */

extern Unit *snd_last_selected;                     /* 0x59680 */
extern unsigned long snd_enemy_scan_timer;          /* 0x59684 */
extern unsigned short snd_enemy_near;               /* 0x59688 */
extern unsigned short snd_select_cooldown;          /* 0x5968a */
extern unsigned short snd_enemy_alt;                /* 0x5968c */
extern unsigned short snd_select_clicks;            /* 0x5968e */

/* ---- functions of other areas ---- */
extern int rand(void);                              /* 0x33b61 */
extern void SndPlay(unsigned id);                   /* 0x26958 */
extern void SndLoadTable(const unsigned short *ids);/* 0x267fc */
extern void fn_19edc(const char *text, unsigned short flag, unsigned short mode); /* 0x19edc message strip */

/* ---- this object ---- */
extern void SndEvent(unsigned short id, Unit *u);   /* 0x1b800 */

#endif
