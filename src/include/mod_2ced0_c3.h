#ifndef MOD_2CED0_C3_H
#define MOD_2CED0_C3_H

#include "mod_13b30_f1.h"

typedef struct Unit {
    unsigned char pad0[7];
    unsigned char b7;
    unsigned char pad8[8];
    unsigned short flags;
    unsigned char pad12[8];
    unsigned char b1a;
    unsigned char type;
    unsigned char b1c;
    unsigned char pad1d;
    unsigned char owner;
    unsigned char pad1f[0x2d];
    short s4c;
    short s4e;
    short s50;
    short s52;
    unsigned char pad54[8];
} Unit;

extern short unit_type_size[52][2];
extern void *unit_array;
extern unsigned short status_dirty;
extern void SndConstructionTick(Unit *u);
extern void SndWorkComplete(Unit *u);
extern void fn_26360(Unit *u, unsigned sound);
extern void UnitUpdateGraphicsIndex(Unit *u);
extern int HarvestDepositCargo(Unit *u);
extern int fn_2e5c8(Unit *u, short *size);
void UnitStartDeath(Unit *u);

#endif
