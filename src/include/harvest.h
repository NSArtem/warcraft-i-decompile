#ifndef HARVEST_H
#define HARVEST_H

#include "war.h"

typedef struct Unit Unit;

/* Watcom register convention: compile with -4r. */
void HarvestQueueBuildingEntry(Unit *u); /* 0x1cd50 */
int OrderUpdateHarvest(Unit *u, int is_human); /* 0x1cd90 */
int OrderUpdateHarvestReturn(Unit *u, int is_human); /* 0x1cf5c */
int HarvestDepositCargo(Unit *u); /* 0x1cf94 */
int OrderUpdateHarvestEnterBuilding(Unit *u); /* 0x1d034 */
int OrderUpdateHarvestExitBuilding(Unit *u); /* 0x1d1e0 */

extern unsigned long player_lumber[5]; /* 0x50060 */
extern unsigned long player_gold[5]; /* 0x50074 */
extern unsigned char player_controller_type[5]; /* 0x5008c */
extern unsigned long harvested_gold[5]; /* 0x50dc0 */
extern unsigned long harvested_lumber[5]; /* 0x50dd4 */
extern unsigned short player_score[4]; /* 0x50e34 */
extern unsigned short player_home_point_preceding_word; /* 0x50e66 */
extern short player_home_point[5][2]; /* 0x50e68: packed x,y pairs */
extern signed char dir_dx[8]; /* 0x50f80 */
extern signed char dir_dy[8]; /* 0x50f88 */
extern short unit_type_size[52][2]; /* 0x51abc */
extern unsigned char harvest_sound_ids[]; /* 0x53296 */
extern char harvest_invalid_state_msg[10]; /* 0x56c78 */
extern void **object_map; /* 0x58580: pointer to the 64 x 64 tile slots */
extern void *player_town_hall[5]; /* 0x58db0 */

/* 0x1d240 loads two bytes before player_home_point[owner][0], then
 * 0x1d289 extracts the signed high word. The preceding word symbol
 * describes the relocation base, not a second array of coordinates. */

void fn_21094(Unit *u);
void UiOrderSetNext3_11(Unit *u);

/* Unit layout used by HARVEST.C. Keep two-byte packing (-zp2). */
typedef union HarvestPointView {
    long packed;
    short xy[2];
    unsigned short words[2];
} HarvestPointView;

struct Unit {
    unsigned long position_prefix; /* 0x00: copied at 0x1d0d2 */
    unsigned char entry_flags;     /* 0x04: 0x1d0bb */
    unsigned char pad05;
    unsigned char entry_timer;     /* 0x06: 0x1d0fa */
    unsigned char pad07;
    unsigned char direction;       /* 0x08: 0x1cd6c, 0x1d093 */
    unsigned char pad09;
    HarvestPointView position;     /* 0x0a: 0x1ce71, 0x1d0cc */
    unsigned short building_flags; /* 0x0e: 0x1d189 */
    unsigned short state_flags;    /* 0x10: 0x1cdba, 0x1d101 */
    unsigned char pad12[9];
    unsigned char type;            /* 0x1b: 0x1cd76, 0x1cf99 */
    unsigned char pad1c[2];
    unsigned char owner;           /* 0x1e: 0x1ceb4, 0x1d012 */
    unsigned char pad1f[0x1f];
    HarvestPointView saved_point;  /* 0x3e: 0x1ce9e, 0x1d280 */
    Unit *saved_target;            /* 0x42: 0x1cea4, 0x1d27d */
    unsigned char pad46[2];
    unsigned char work_ticks;      /* 0x48: 0x1ce62, 0x1cef2 */
    unsigned char harvest_flags;   /* 0x49: 0x1cd6f, 0x1d1e6 */
    unsigned char pad4a[4];
    HarvestPointView target_point; /* 0x4e: 0x1ce4f; low byte reused at 0x1d112 */
    union {
        Unit *target;              /* 0x52: 0x1cd73, 0x1d040 */
        struct {
            unsigned short pad52;
            unsigned long remaining; /* 0x54: 0x1d14b, 0x1d1ad */
        } deposit;
    } work;
};

#endif
