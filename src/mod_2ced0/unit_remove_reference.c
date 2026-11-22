/* codegen-compiler: 10.0a */

typedef struct Pt { short x; short y; } Pt;

typedef struct Unit {
    short x;
    short y;
    unsigned char pad4[2];
    unsigned char f6;
    unsigned char pad7;
    unsigned char f8;
    unsigned char pad9;
    Pt t;
    unsigned short flagsE;
    unsigned short flags;
    unsigned char pad12[4];
    short hp;
    unsigned char pad18[2];
    unsigned char f1a;
    unsigned char type;
    unsigned char f1c;
    unsigned char pad1d;
    unsigned char owner;
    unsigned char pad1f[0x1f];
    union {
        Pt dst;
        unsigned char b3e;
    } d;
    short s42;
    short s44;
    union {
        unsigned char *ptr46;
        struct {
            unsigned short w46;
            unsigned char b48;
            unsigned char pad49[3];
        } w;
    } p;
    short s4c;
    unsigned char pad4e[2];
    short s50;
    union {
        struct Unit *target;
        struct {
            unsigned short pad52;
            long l54;
        } s;
    } tg;
    unsigned char pad58[4];
} Unit;

extern void fn_25e58(void);
extern void fn_13c84(Unit *u);
extern void fn_13954(Unit *u);
extern void AiRemoveUnit(Unit *u);
extern void UnitSetOrder(Unit *u, unsigned char order);
extern void SndUnitDeath(Unit *u);
extern void SndBuildingDestroyed(void);
extern void BulletSpawnRuins(Unit *u);
extern void BulletSpawnBurst(Unit *u);
extern void MissionDefeat(void);
extern unsigned char dat_5008c[5];
extern unsigned short scenario_number;
extern unsigned short training_count[5];
extern unsigned short dat_50d98[5];
extern unsigned long ai_wave_timer;
extern unsigned short ai_site_count[5];
extern unsigned short ai_helper_count[5];
extern unsigned short *map_flags;
extern Unit *unit_array;
extern unsigned short status_dirty;
extern unsigned short dat_5a7c2;

/* @0x2e14c */
void UnitRemove(Unit *u)
{
    unsigned char pl;
    unsigned short idx;
    unsigned short n;
    unsigned short i;
    Unit *p;

    fn_25e58();
    AiRemoveUnit(u);
    UnitSetOrder(u, 1);
    u->flags |= 2;
    ((unsigned char *)&u->flags)[1] &= 0xe7;
    fn_13c84(u);
    if (u->type <= 0x1f) {
        if (u->type == 0x10 || (u->type == 0xf && u->owner == 4)) {
            u->flags &= 0xfffd;
            UnitSetOrder(u, 0);
            u->flags |= 0xc;
        }
        fn_13954(u);
        if (dat_5a7c2 == 0) {
            SndUnitDeath(u);
        }
        if (u->type == 0xf || u->type == 0x12) {
            MissionDefeat();
        } else if (u->type == 0x11) {
            ai_site_count[u->owner] = 0xffff;
            ai_wave_timer = 1;
        }
        return;
    }
    if (scenario_number == 0x82 && u->type == 0x26) {
        MissionDefeat();
    }
    if (u->type == 0x30 || u->type == 0x31) {
        BulletSpawnBurst(u);
    } else {
        SndBuildingDestroyed();
        BulletSpawnRuins(u);
    }
    pl = u->owner;
    if (pl == 0) {
        status_dirty = 1;
    } else if (dat_5008c[pl] == 1) {
        if (u->type == 0x30 || u->type == 0x31) {
            idx = 1;
            n = 3;
        } else {
            idx = pl;
            n = 1;
        }
        while (--n != 0xffff) {
            ai_site_count[idx] = 0xffff;
            ai_helper_count[idx] = 1;
            idx++;
        }
        ai_wave_timer = 1;
    }
    if ((u->flagsE & 0x10) != 0) {
        if (u->p.ptr46 != 0) {
            *u->p.ptr46 &= 0x7f;
        } else if (u->d.b3e == 0x35) {
            map_flags[(u->s44 << 6) + u->s42] &= 0xffef;
        } else {
            training_count[u->owner]--;
        }
    }
    if ((u->flags & 0x80) == 0) {
        dat_50d98[u->owner]--;
    }
    p = unit_array;
    i = 200;
    while (--i != 0xffff) {
        if ((p->flags & 0x207) == 0 && (p->flags & 8) != 0 && u == p->tg.target) {
            UnitRemove(p);
        }
        p++;
    }
}
