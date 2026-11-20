/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

typedef struct PUnit {
    char pad0[0x0e];
    unsigned short flags;               /* 0x0e */
    char pad10[0x1b - 0x10];
    unsigned char utype;                /* 0x1b */
    char pad1c[0x1e - 0x1c];
    unsigned char owner;                /* 0x1e */
    char pad1f[0x3e - 0x1f];
    unsigned char otype;                /* 0x3e */
} PUnit;

extern unsigned long dat_50060[5];
extern unsigned long dat_50074[5];
extern unsigned short training_count[5];
extern unsigned char score_value[];
extern unsigned char unit_lumber_cost[];
extern short unit_type_size[52][2];
extern unsigned short terrain_rect_mask_table[5];
extern char dat_56af4[];
extern unsigned short *map_flags;

short UnitWorkProgress(PUnit *u, int dirty);
void fn_19f70(const char *msg, unsigned code);
void SndTrainingComplete(PUnit *u);
int fn_20d74(unsigned short player, int pay, unsigned char type);
void TerrainApplyCellFlags(int x, int y, unsigned short flags);
int fn_2e650(short x, short y, unsigned char type, unsigned char owner, void *size);

/* @0x143cc */
int OrderUpdateProduce(PUnit *u)
{
    int ret;

    ret = UnitWorkProgress(u, 2);
    if (ret != 0) {
        if ((u->flags & 0x20) != 0) {
            u->flags &= ~0x20;
            dat_50074[u->owner] += ((int)score_value[u->otype] * 30) / 4;
            dat_50060[u->owner] += ((int)unit_lumber_cost[u->otype] * 30) / 4;
            if (u->otype == 0x35) {
                ((unsigned char *)map_flags)[((*(long *)((char *)u + 0x40) >> 16) + (*(long *)((char *)u + 0x42) >> 16) * 64) * 2] &= 0xef;
            }
        } else if (u->otype == 0x35) {
            TerrainApplyCellFlags((int)(*(long *)((char *)u + 0x40) >> 16), (int)(*(long *)((char *)u + 0x42) >> 16), terrain_rect_mask_table[u->owner]);
        } else {
            if (fn_2e650((short)(*(long *)((char *)u + 8) >> 16), (short)(*(long *)((char *)u + 10) >> 16), u->otype, u->owner, unit_type_size[u->utype]) == 0) {
                if (u->owner == 0)
                    fn_19f70(dat_56af4, 0x24);
                fn_20d74(u->owner, 0, u->otype);
            } else if (u->owner == 0) {
                SndTrainingComplete(u);
            }
        }
        if (u->otype != 0x35)
            training_count[u->owner]--;
        ret = 1;
    }
    return ret;
}
