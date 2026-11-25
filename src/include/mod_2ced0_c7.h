#ifndef MOD_2CED0_C7_H
#define MOD_2CED0_C7_H

/* 0x2d6e5 and 0x2ed31 establish the 0x5c-byte record stride. */
struct Unit {
    short pixel_x;                  /* 0x2e032 */
    short pixel_y;                  /* 0x2e055 */
    unsigned char pad04[6];
    short tile_xy[2];               /* 0x2d665, 0x2d6aa */
    unsigned char pad0e;
    unsigned char visibility;       /* 0x2d66d */
    unsigned short flags;           /* 0x2d671, 0x2e999 */
    unsigned char pad12[6];
    unsigned short tick_timer;      /* 0x2ec70 */
    unsigned char pad1a;
    unsigned char type;             /* 0x2d694, 0x2e9a1 */
    unsigned char pad1c[2];
    unsigned char owner;            /* 0x2e976, 0x2ecb1 */
    unsigned char order;            /* 0x2ed16 */
    unsigned char pad20[0x29];
    unsigned char tick_bits;        /* 0x2ecc3 */
    unsigned short gone_timer;      /* 0x2e9ae, 0x2ec57 */
    unsigned char pad4c[0x10];
};

void UnitsUpdateVisibility(void);
void MapPickOrderTarget(unsigned short *cursor_shape);
void UnitFinalizeGone(struct Unit *u);
void SimulationTick(void);

#endif
