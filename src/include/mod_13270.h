#ifndef MOD_13270_H
#define MOD_13270_H

#include "war.h"

typedef struct Unit Unit;

extern short unit_type_size[52][2]; /* 0x51abc: width at [type][0], height at [type][1]; 0x51abe is &unit_type_size[0][1]. */
extern unsigned short unit_map_class_masks[]; /* 0x51dd4 */
extern unsigned short *map_flags; /* 0x5857c */
extern void **object_map; /* 0x58580: pointer to 4096 object slots, not an inline array. */

/* Default Watcom 386 register calling convention (__watcall). */
void MarkUnitFootprint(Unit *u);
void ClearUnitFootprint(Unit *u);
int CanPlaceUnitFootprint(short tile_x, short tile_y, unsigned char type);
int HasJoinCandidateNearby(Unit *u);

/* Unit prefix used by mod_13270. Member offsets are evidenced by
 * 0x137a6/0x137aa (coordinates), 0x13ad6 (flags), and
 * 0x137bd/0x137d5 (type and map class). */
struct Unit {
    unsigned char pad_00[0x0a];
    short tile_x;
    short tile_y;
    unsigned char pad_0e[2];
    unsigned short flags;
    unsigned char pad_12[9];
    unsigned char type;
    unsigned char pad_1c[2];
    unsigned char map_class;
};

#endif
