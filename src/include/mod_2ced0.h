#ifndef MOD_2CED0_H
#define MOD_2CED0_H

#include "war.h"

extern unsigned char dat_5008c[5]; /* 0x5008c: player resource class */
extern unsigned char dat_51df0[]; /* 0x51df0: resource decay period by unit type */
extern signed char tick_drift_storage[5]; /* 0x55281: dword views start at [0] and [1] (0x55282); signed components are [3] (0x55284) and [4] (0x55285). */
extern short perimeter_expand_dx[4]; /* 0x552b8 */
extern short perimeter_expand_dy[4]; /* 0x552c0 */
extern unsigned short perimeter_start_direction[2][2]; /* 0x552c8: [y_side][x_side] */
extern void *unit_array; /* 0x59640 */
extern unsigned short *fog_map; /* 0x58578 */
extern short step4_dx[4]; /* 0x5515c */
extern short step4_dy[4]; /* 0x55164 */

void UpdateUnitTimersAndResources(void); /* 0x2d2e0 */
int FogRectMatchesMask(const short *xy, const short *size, unsigned short mask, unsigned short expected); /* 0x2d5c8; pairs are x/y and width/height. */
/* Packed halves are signed shorts: width and target X in the low halves,
 * height and target Y in the high halves. x and y are changed only on success. */
int FindNearbyClearTile(short *x, short *y, unsigned long packed_size, unsigned long packed_target); /* 0x2e464 */

#endif
