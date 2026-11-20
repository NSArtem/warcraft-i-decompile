#ifndef MOD_2B8E0_H
#define MOD_2B8E0_H

struct Unit;

/* resource loading / freeing of terrain transition tables */
void TerrainTableLoad(unsigned short id, void **out, unsigned short *hdr); /* 0x2b8e0 */
void TerrainTablesInit(void);                                  /* 0x2b91c */
void TerrainTablesFree(void);                                  /* 0x2ba08 */

/* tile rewrite callbacks (called per cell by the region walker 0x2b1b0) */
void TerrainTileAdvanceB(int idx);                             /* 0x2ba50 */
void TerrainStartRegionB(struct Unit *u);                      /* 0x2bb38 */
int  TerrainTileIsClear(short *pt);                            /* 0x2bb7c */
void TerrainTileAdvanceA(int idx);                             /* 0x2bd00 */
void TerrainStartRegionA(struct Unit *u);                      /* 0x2bdd4 */

/* autotiling */
int  TerrainFlagTest(unsigned x, unsigned y, int idx);         /* 0x2bf30 */
void TerrainAutotileCell(unsigned x, unsigned y, unsigned short flags); /* 0x2bf64 */
void TerrainAutotileCross(int x, int y, unsigned short flags); /* 0x2c0bc */
void TerrainApplyCellFlags(int x, int y, unsigned short flags);/* 0x2c14c */
void TerrainFillRectOwnerMask(unsigned char *rect, unsigned owner); /* 0x2c1e8 */
void TerrainFillRectMask(unsigned char *rect, unsigned kind);  /* 0x2c208 */

int TerrainFindClearTile(unsigned short *p);                   /* 0x2bbe4 */

void TerrainRoadCell(int x, int y, unsigned short mask);   /* 0x2c100 */
void TerrainWallCell(int x, int y);                        /* 0x2c268 */
void TerrainWallAdvance(int x, int y);                     /* 0x2c2c4 */

#endif
