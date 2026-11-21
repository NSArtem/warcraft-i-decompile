#ifndef MOD_1E9A0_H
#define MOD_1E9A0_H

/* Module mod_1e9a0 (0x1e9a0..0x1eba0): fog-of-war region update helpers. */

/* per-tile callback for TerrainWalkRegion; tile = index into fog_map */
void FogUpdateTile(int tile);                                   /* 0x1e9a0 */

/* set scan params (size NxN, shape table, FogUpdateTile) and walk region */
void FogUpdateArea5(short x, short y, unsigned short owner);    /* 0x1ea18 */
void FogUpdateArea6(short x, short y, unsigned short owner);    /* 0x1ea58 */
void FogUpdateArea7(short x, short y, unsigned short owner);    /* 0x1ea98 */
void FogUpdateArea8(short x, short y, unsigned short owner);    /* 0x1ead8 */
void FogUpdateArea9(short x, short y, unsigned short owner);    /* 0x1eb18 */
void FogUpdateArea11(short x, short y, unsigned short owner);   /* 0x1eb58 */

extern unsigned short fog_owner_mask[];        /* 0x51dde: field mask per owner */
extern unsigned short fog_owner_shift[];       /* 0x51de2: field shift per owner
                                                  (overlaps fog_owner_mask[2]) */
extern unsigned short fog_transition_table[];  /* 0x52598 */
extern unsigned short fog_shape_5[];           /* 0x5268a */
extern unsigned short fog_shape_6[];           /* 0x526bc */
extern unsigned short fog_shape_7[];           /* 0x52704 */
extern unsigned short fog_shape_8[];           /* 0x52766 */
extern unsigned short fog_shape_9[];           /* 0x527e6 */
extern unsigned short fog_shape_11[];          /* 0x52888 */
extern unsigned short fog_cur_owner;           /* 0x599d0 */

#endif
