/*
 * Declarations for the computer-opponent AI object 0x295d0..0x2b1b0
 * (analysis/symbols/mod_295d0.toml, docs/subsystems/mod_295d0.md).
 *
 * The module is the single-player AI: the per-player AI state reset and tick,
 * the work-site (mine/forest) assignment of the AI's workers, the AI's
 * production/rebuild choice, and the automatic target/spell behaviour of the
 * AI's spellcasters.  It is called from the unit order layer (UnitIdleTick,
 * UnitRetaliate, UnitRemove, UnitCreate, OrderUpdateStop) and from the
 * scenario start 0x195ac.
 *
 * The unit record is the 0x5c-byte one of docs/subsystems/game_2c4e0.md; the
 * fields this module uses that area leaves as padding are named here
 * (+0x12 order flags, +0x14 work site, +0x3c..+0x50 work point/production
 * area).  Offsets are the evidence, names are descriptive.  Compile with -zp2.
 */
#ifndef MOD_295D0_H
#define MOD_295D0_H

typedef struct { short x, y; } Point;   /* tile coordinates (read as one dword x | y<<16) */

/* One entry of the unit array (0x59640, 200 * 0x5c bytes). */
typedef struct Unit {
    short px, py;                    /* 0x00 pixel position (tile * 16) */
    unsigned short anim_ip;          /* 0x04 animation script offset */
    unsigned char anim_timer;        /* 0x06 */
    unsigned char frame;             /* 0x07 */
    unsigned char facing;            /* 0x08 direction 0..7 */
    unsigned char anim_start;        /* 0x09 */
    short tx, ty;                    /* 0x0a tile position */
    unsigned short flags2;           /* 0x0e secondary flags */
    unsigned short flags;            /* 0x10 main flags (0x207 off map, 0x200 hidden) */
    unsigned short order_flags;      /* 0x12 order flags: 1 work, 2 busy, 4 return, 8 attack, 0x10 at site */
    unsigned short work_site;        /* 0x14 work-site index; 0x4000/0x8000 state bits */
    unsigned short hp;               /* 0x16 */
    unsigned short ctr18;            /* 0x18 */
    unsigned char energy;            /* 0x1a damage fraction / spellcaster mana */
    unsigned char type;              /* 0x1b unit type 0..0x33 */
    unsigned char type2;             /* 0x1c type copy */
    unsigned char sprite_set;        /* 0x1d */
    unsigned char owner;             /* 0x1e owner/player 0..4 */
    unsigned char order;             /* 0x1f current order */
    unsigned char order_next;        /* 0x20 next order */
    unsigned char order_next2;       /* 0x21 next order argument */
    unsigned char path[20];          /* 0x22 path steps */
    unsigned short timer36;          /* 0x36 */
    unsigned short timer38;          /* 0x38 */
    struct Unit *attacker;           /* 0x3a last unit that hit this one */
    short work_x, work_y;            /* 0x3e/0x40 work point (tile) */
    unsigned char pad42[4];          /* 0x42 */
    unsigned short word46;           /* 0x46 type copy (word) */
    unsigned char b48;               /* 0x48 */
    unsigned char b49;               /* 0x49 carry bits 0x20/0x40/0x80 */
    unsigned short word4a;           /* 0x4a production word */
    unsigned char path_idx;          /* 0x4c */
    unsigned char pad4d;             /* 0x4d */
    short dest_x, dest_y;            /* 0x4e/0x50 destination tile */
    struct Unit *target;             /* 0x52 target unit */
    unsigned short pad56;            /* 0x56 */
    void *damage_sprite;             /* 0x58 */
} Unit;

/* ---- globals (addresses are the evidence; see the area TOML) ---- */
extern Unit *unit_array;                       /* 0x59640 */
extern Unit **object_map;                      /* 0x58580 64x64 tile -> unit */
extern unsigned char hostility[25];            /* 0x51883 5x5, 1 = enemy */
extern unsigned short unit_max_hp[];           /* 0x51978 */
extern unsigned char unit_sight_range[];       /* 0x51c6c */
extern unsigned char target_priority[];        /* 0x51d28 */
extern unsigned short spell_order;             /* 0x5a7c0 */
extern unsigned short scenario_number;         /* 0x50d82 */
extern unsigned short scenario_objectives;     /* 0x50092 mission-condition word */
extern unsigned char dat_5008c[];              /* 0x5008c player type by owner (1 = computer) */
extern unsigned char spell_available[6][5];    /* 0x50017 the six spell rows, by player */
extern unsigned long dat_50060[];              /* 0x50060 lumber per player */
extern unsigned long dat_50074[];              /* 0x50074 gold per player */
extern Unit *player_town_hall[5];              /* 0x58db0 */
extern unsigned short player_worker_count[5];  /* 0x58dd8 */

/* AI state (this module) */
extern unsigned short ai_retarget_timer;       /* 0x50de8 */
extern Point ai_attack_point;                  /* 0x50dea pixel coordinates */
extern Point ai_home_point[5];                 /* 0x50e0c */
extern Point ai_sweep_point[5];                /* 0x50e20 */
extern unsigned long ai_wave_timer;            /* 0x50e4a */
extern unsigned short ai_site_count[5];        /* 0x50e54 */
extern unsigned short ai_helper_count[5];      /* 0x50e5e */
extern unsigned short ai_tick_count;           /* 0x50e56 */
extern Point player_home_point[5];             /* 0x50e68 town-hall tile per player */
extern unsigned short ai_busy_count[5];        /* 0x50df8 */
extern unsigned short ai_work_count[5];        /* 0x50dee */
extern unsigned short ai_site_limit;           /* 0x500a6 */
extern unsigned short ai_site_reset;           /* 0x500b0 */
extern unsigned short ai_site_cycle;           /* 0x500ba */
extern unsigned short ai_site_max;             /* 0x500c4 */
extern unsigned short *work_sites;             /* 0x599c0 pointer to the map work-site table */
extern unsigned char building_priority_down[]; /* 0x55100 base; table content at +0x20 */
extern unsigned char building_priority_up[];   /* 0x55113 base; table content at +0x20 */
extern short step4_dx[4];                      /* 0x5515c four-direction dx */
extern short step4_dy[4];                      /* 0x55164 four-direction dy */
extern unsigned short dat_5a7c2;               /* 0x5a7c2 linked-game flag */
extern signed char dir_dx[8];                  /* 0x50f80 */
extern signed char dir_dy[8];                  /* 0x50f88 */

/* ---- callees ---- */
extern void UnitOrderTarget(Unit *u, short x, short y, Unit *target, void (*fn)(Unit *));
extern void UnitSetOrder(Unit *u, int order);
extern void UnitSetNextOrder(Unit *u, int order);
extern void UnitSetNextOrders(Unit *u, int order, int order2);
extern int GameRandom(int id);                   /* 0x19478 random */
extern unsigned fn_13270(short *p, Unit *u);   /* 0x13270 distance (tile point) */
extern int fn_13990(short tx, short ty, int type);      /* 0x13990 placement test */
extern int fn_2bb7c(Point *p);                 /* 0x2bb7c tile walkability */
extern int fn_20d74(unsigned short player, int pay, int type);   /* 0x20d74 pay/refund */
extern Unit *UnitCreate(short px, short py, int type, int owner);  /* 0x2e6f4 */
extern void *memset(void *dst, int c, unsigned n);

void ClipBox(int *x, int *y, int *w, int *h, int size);
Unit *AiBestTarget(short *origin, short range, short pref_dist, unsigned char *enemy_row);

/* order callbacks (mod_20c30 / mod_2ced0) */
extern void fn_20eb4(Unit *u);                 /* 0x20eb4 move */
extern void fn_20f30(Unit *u);                 /* 0x20f30 attack/move (player) */
extern void fn_21094(Unit *u);                 /* 0x21094 arrive-and-work */
extern void fn_210dc(Unit *u);                 /* 0x210dc repair a building target */
extern void fn_2111c(Unit *u);                 /* 0x2111c return goods */
extern void fn_21168(Unit *u);                 /* 0x21168 cast the queued spell */

#endif
