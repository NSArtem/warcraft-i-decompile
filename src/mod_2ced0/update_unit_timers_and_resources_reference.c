/* codegen-compiler: 10.0a */
#include "mod_2ced0.h"

extern int GameRandom(int arg); /* 0x2d2e5–0x2d2ea. */
struct Unit;
extern void UnitRemove(struct Unit *u); /* 0x2d483–0x2d485. */

typedef struct {
    unsigned char pad00[0x10];
    unsigned short flags;
    unsigned char pad12[4];
    unsigned short health;
    unsigned char pad18[2];
    unsigned char resource;
    unsigned char type;
    unsigned char pad1c[2];
    unsigned char player;
    unsigned char pad1f[0x17];
    short timer36;
    short timer38;
    unsigned char pad3a[0x0e];
    unsigned char timer48;
    unsigned char pad49[0x13];
} TimerUnitView;

void UpdateUnitTimersAndResources(void)
{
    TimerUnitView *u;
    short n;
    short timer36;
    short timer38;
    unsigned char timer;
    unsigned char resource;
    int type;
    int health;
    int delta;

    if ((GameRandom(5) & 0xf) == 0) {
        if (GameRandom(6) & 1) {
            delta = GameRandom(7) % 3;
            tick_drift_storage[3] = (signed char)((*(volatile long *)&tick_drift_storage[0] >> 24) + --delta);
        } else {
            delta = GameRandom(8) % 3;
            tick_drift_storage[4] = (signed char)((*(volatile long *)&tick_drift_storage[1] >> 24) + --delta);
        }
        if ((*(volatile long *)&tick_drift_storage[0] >> 24) < -2)
            tick_drift_storage[3] = -2;
        if ((*(volatile long *)&tick_drift_storage[0] >> 24) > 2)
            tick_drift_storage[3] = 2;
        if ((*(volatile long *)&tick_drift_storage[1] >> 24) < -2)
            tick_drift_storage[4] = -2;
        if ((*(volatile long *)&tick_drift_storage[1] >> 24) > 2)
            tick_drift_storage[4] = 2;
    }

    u = unit_array;
    n = 200;
    if ((short)--n == (short)-1)
        return;
    do {
        if ((unsigned short)(u->flags & 0x207) != 0)
            goto next_unit;
        timer36 = u->timer36;
        if (timer36 != 0)
            u->timer36 = (short)(timer36 - 1);
        timer38 = u->timer38;
        if (timer38 != 0)
            u->timer38 = (short)(timer38 - 1);
        type = u->type;
        if (type >= 10 && type <= 14) {
            if (u->resource == 255)
                goto next_unit;
            timer = u->timer48;
            u->timer48 = --timer;
            if ((unsigned char)timer != 0)
                goto next_unit;
            if (dat_5008c[u->player] == 1)
                u->timer48 = 60;
            else
                u->timer48 = 40;
            ++u->resource;
            goto next_unit;
        }
        if (dat_51df0[u->type] == 0)
            goto next_unit;
        if ((unsigned short)(u->flags & 0x400) != 0)
            goto next_unit;
        timer = u->timer48;
        u->timer48 = --timer;
        if ((unsigned char)timer != 0)
            goto next_unit;
        resource = u->resource;
        if ((unsigned char)resource != 0) {
            u->resource = (unsigned char)(resource - 1);
        } else {
            health = u->health;
            if (health < 5)
                UnitRemove((struct Unit *)u);
            else
                u->health = (unsigned short)(health - 5);
        }
        u->timer48 = dat_51df0[u->type];
next_unit:
        ++u;
    } while ((short)--n != (short)-1);
}
