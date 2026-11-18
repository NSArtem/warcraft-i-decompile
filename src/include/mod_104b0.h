/*
 * Shared declarations for the early game-code range
 * 0x104b0..0x119c0 (analysis/symbols/mod_104b0.toml):
 *   mod_104b0 0x104b0..0x110a0  unit combat / damage / target acquisition
 *   mod_110a0 0x110a0..0x11530  the attack order handlers
 *   mod_11530 0x11530..0x119c0  building production, training and research
 *
 * The unit record layout is the one established by the game_2c4e0 area
 * (docs/subsystems/game_2c4e0.md); this header repeats it with the fields the
 * combat code uses, including the ones that area leaves as padding:
 * +0x3a last attacker, +0x3e..+0x46 production state, +0x4a production word.
 * Field names are descriptive; offsets are the evidence.  Compile with -zp2.
 */
#ifndef MOD_104B0_H
#define MOD_104B0_H

typedef struct { short x, y; } Point;   /* tile coordinates (read as one dword x | y<<16) */

typedef union Flags {
    unsigned short w;
    struct { unsigned char lo, hi; } b;
} Flags;

/* cheat_flags (0x51214) is read as a dword, as bytes and through bit tests;
 * Watcom 10.0a emits `test byte [cheat_flags],imm` only for a bitfield
 * (compiler.md section 2), so the low byte is a bitfield here. */
typedef union CheatFlags {
    unsigned long w;
    unsigned char b[4];
    struct {
        unsigned char f1 : 1;            /* 0x1 */
        unsigned char fast : 1;          /* 0x2 fast build/research (0x115b8) */
        unsigned char dev : 1;           /* 0x4 developer mode (0x104b7) */
        unsigned char b3 : 1;
        unsigned char b4 : 4;
        unsigned char hi[3];
    } f;
} CheatFlags;

typedef struct Unit {
    short px, py;                    /* 0x00 pixel position (tile * 16) */
    unsigned short anim_ip;          /* 0x04 animation script offset */
    unsigned char anim_timer;        /* 0x06 */
    unsigned char frame;             /* 0x07 */
    unsigned char facing;            /* 0x08 direction 0..7 */
    unsigned char anim_start;        /* 0x09 animation start index (0x1bb90) */
    short tx, ty;                    /* 0x0a tile position */
    unsigned short flags2;           /* 0x0e secondary flags: 0x10 busy, 0x20 cancel */
    Flags flags;                     /* 0x10 main flags: 0x80 dead, 0x207 not a map unit */
    unsigned char f12;               /* 0x12 bit 3 (0x08) = has a target */
    unsigned char f13;               /* 0x13 */
    unsigned char pad14[2];          /* 0x14 */
    unsigned short hp;               /* 0x16 hit points */
    unsigned short ctr18;            /* 0x18 */
    unsigned char energy;            /* 0x1a damage/health fraction */
    unsigned char type;              /* 0x1b unit type 0..0x33 */
    unsigned char type2;             /* 0x1c type copy at death */
    unsigned char sprite_set;        /* 0x1d */
    unsigned char owner;             /* 0x1e owner/player 0..4 */
    unsigned char order;             /* 0x1f current order */
    unsigned char order_next;        /* 0x20 next order */
    unsigned char order_next2;       /* 0x21 next order argument */
    unsigned char path[20];          /* 0x22 path steps */
    unsigned short timer36;          /* 0x36 */
    unsigned short timer38;          /* 0x38 */
    struct Unit *attacker;           /* 0x3a last unit that hit this one */
    unsigned char build_type;        /* 0x3e unit type / research row being produced */
    unsigned char b3f;               /* 0x3f production state (2 = running) */
    unsigned char b40;               /* 0x40 */
    unsigned char build_time;        /* 0x41 left to produce */
    unsigned char pad42[4];          /* 0x42 */
    void *build_cost;                /* 0x46 resource record being paid */
    unsigned short word4a;           /* 0x4a production word */
    unsigned char path_idx;          /* 0x4c path index (also a dword with dest) */
    unsigned char pad4d;
    short dest_x, dest_y;            /* 0x4e/0x50 destination tile */
    struct Unit *target;             /* 0x52 current target unit */
    unsigned long v54;               /* 0x54 */
    void *damage_sprite;             /* 0x58 */
} Unit;

#endif
