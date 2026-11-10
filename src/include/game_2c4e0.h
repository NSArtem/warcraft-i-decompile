/*
 * Shared declarations for the game-logic range 0x2c4e0..0x2efd0
 * (analysis/symbols/game_2c4e0.toml): pathfinding (0x2c4e0..0x2ced0) and the
 * unit array / draw list / per-tick unit update (0x2ced0..0x2efd0).
 * Layouts are derived from field accesses (docs/subsystems/game_2c4e0.md);
 * compile with -zp2.
 */
#ifndef GAME_2C4E0_H
#define GAME_2C4E0_H

typedef struct { short x, y; } Point;               /* tile coordinates (dword read as x | y<<16) */

/* The flags word at +0x10 is read as a word by most code and as two bytes by
 * the order setters (bit 7 of the high byte); the original object layout is
 * the same either way. */
typedef union Flags {
    unsigned short w;
    struct { unsigned char lo, hi; } b;
} Flags;

/* One entry of the unit array (0x59640, 200 * 0x5c bytes).  Offsets are the evidence; names are
 * descriptive.  Padding members stand for fields not yet understood. */
typedef struct Unit {
    short px, py;                    /* 0x00 pixel position (tile * 16) */
    unsigned short anim_ip;          /* 0x04 animation script offset */
    unsigned char anim_timer;        /* 0x06 */
    unsigned char frame;             /* 0x07 */
    unsigned char facing;            /* 0x08 */
    unsigned char b9;                /* 0x09 */
    short tx, ty;                    /* 0x0a tile position */
    unsigned short flags2;           /* 0x0e */
    Flags flags;                     /* 0x10 */
    unsigned char pad12[4];          /* 0x12 */
    unsigned short hp;               /* 0x16 */
    unsigned short ctr18;            /* 0x18 */
    unsigned char energy;            /* 0x1a damage/health fraction (0x2d0ac, 0x2d0e0) */
    unsigned char type;              /* 0x1b */
    unsigned char type2;             /* 0x1c */
    unsigned char sprite_set;        /* 0x1d */
    unsigned char owner;             /* 0x1e */
    unsigned char order;             /* 0x1f */
    unsigned char order_next;        /* 0x20 */
    unsigned char order_next2;       /* 0x21 */
    unsigned char path[20];          /* 0x22 */
    unsigned short timer36;          /* 0x36 */
    unsigned short timer38;          /* 0x38 */
    unsigned char pad3a[0x4c - 0x3a];
    unsigned char path_idx;          /* 0x4c (a word in some states) */
    unsigned char pad4d;
    Point dest;                      /* 0x4e */
    struct Unit *target;             /* 0x52 */
    unsigned long v54;               /* 0x54 */
    void *damage_sprite;             /* 0x58 */
} Unit;

#endif
