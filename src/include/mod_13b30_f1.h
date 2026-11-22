#ifndef MOD_13B30_F1_H
#define MOD_13B30_F1_H

/* mod_13b30 (0x13b30..0x13d03): per-player unit/building counters.
 * All functions are __watcall (default); the owner player is u->owner (byte at +0x1e),
 * the unit type is the byte at +0x1b. */
struct Unit;

/* per-unit-type "count changed" callback table, 0x34 entries, NULL = none.
 * Entries are called as cb(u, +1/-1) from UnitCountAdd/UnitCountRemove. */
extern void (*unit_count_callback[0x34])(struct Unit *u, short delta);  /* 0x51408 */

/* per-player counters (indexed by player 0..4) */
extern unsigned short player_stat_50d98[5];   /* 0x50d98 */
extern unsigned short player_stat_50dac[5];   /* 0x50dac */
extern unsigned short player_stat_50db6[5];   /* 0x50db6 */
/* 0x50e6a is the interior y field of player_home_point[0] (0x50e68, Point[5], stride 4);
 * documented separately only so the address has a name. */
extern short player_home_point_y[];           /* 0x50e6a, stride 4 shorts-bytes (same storage as player_home_point[i].y) */
extern unsigned short player_stat_58e32[5];   /* 0x58e32 */

void CountMenDelta(struct Unit *u, short delta);            /* 0x13b30 */
void CountBuildingDelta(struct Unit *u, short delta);       /* 0x13b4c */
void CountFoodBuildingDelta(struct Unit *u, short delta);   /* 0x13b7c */
void CountTownHallDelta(struct Unit *u, short delta);       /* 0x13b9c */
void CountTownHallFullDelta(struct Unit *u, short delta);   /* 0x13bb4 */
void UnitCountAdd(struct Unit *u);                          /* 0x13c04 */
void UnitCountRemove(struct Unit *u);                       /* 0x13c84 */
void PlayerStatsReset(int keep_totals);                     /* 0x13d04 */

#endif
