#ifndef MOD_1C9C0_H
#define MOD_1C9C0_H

#include "war.h"

typedef struct Unit Unit;

extern unsigned short scenario_number;                        /* 0x50d82 */
extern unsigned short scenario_race;                          /* 0x50088 */
extern unsigned short scenario_race_enemy;                    /* 0x5008a */
extern unsigned char unit_type_graphics_map[][2];              /* 0x5180e: only column 0 is read here */
extern unsigned short session_graphics_resource_table[74];    /* 0x52214: race masks at indices 0 and 1; descriptors start at index 2 (0x52218) */
extern void *session_common_graphics[12];                      /* 0x522a8 */
extern void *session_side_graphics[144];                       /* 0x522d8: 72 interleaved enemy/player pairs, enemy first */

/* Register-call declarations use the target's default Watcom convention. */
void UnitUpdateGraphicsIndex(Unit *u);
void *CloneSpriteResource(const void *src, unsigned size);
int IsGraphicsResourceAllowedForScenario(unsigned short resource_id);
void LoadSessionGraphics(void);
void FreeSessionGraphics(void);

#endif
