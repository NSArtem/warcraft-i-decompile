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

extern void fn_1379c(Unit *u);
extern void fn_13928(Unit *u);
extern short fn_13990(short tx, short ty, unsigned char type);
extern void fn_13c04(Unit *u);
extern int fn_19478(int n);
extern void fn_1c9c0(Unit *u);
extern void AiInitUnitOrder(Unit *u);
extern void DrawListInsert(void *u);
extern void UnitSetOrder(Unit *u, unsigned char order);
extern void UnitSetNextOrder(void *u, unsigned char order);
extern void *memset(void *s, int c, unsigned n);
extern unsigned short dat_50d98[];
extern unsigned short unit_max_hp[0x36];
extern unsigned char dat_519e0[];
extern unsigned char unit_train_time[];
extern unsigned char dat_51df0[];
extern unsigned short net_play_flag;
extern Unit *unit_array;
extern unsigned short dat_5a7c2;
extern unsigned char spell_summon_owner;

/* @0x2e6f4 */
Unit *UnitCreate(short px, short py, short type, unsigned char owner)
{
    Unit *u;
    unsigned short i;
    unsigned char b;

    u = unit_array;
    for (i = 200; --i != 0xffff; u++) {
        if ((u->flags & 1) != 0) {
            break;
        }
    }
    if (i == 0xffff) {
        u = 0;
    } else {
        memset(u, 0, 0x5c);
        px &= 0xfff0;
        py &= 0xfff0;
        u->x = px;
        u->y = py;
        px >>= 4;
        py >>= 4;
        u->t.x = px;
        u->t.y = py;
        if (fn_13990(px, py, type) == 0) {
            u->flags = 1;
            u = 0;
            return u;
        }
        u->type = type;
        u->f1c = type;
        u->flags = 0;
        u->flagsE = 0x300;
        u->hp = unit_max_hp[type];
        u->f1a = dat_519e0[type];
        DrawListInsert(u);
        u->owner = owner;
        b = dat_51df0[u->type];
        if (b != 0 && dat_5a7c2 == 0) {
            u->p.w.b48 = b;
            u->f1a = 0xff;
            if (type == 0x1a) {
                u->f8 = spell_summon_owner;
                UnitSetOrder(u, 0x1c);
                UnitSetNextOrder(u, 2);
            }
        } else if (u->type <= 0x1f) {
            u->f8 = fn_19478(9) & 7;
        }
        UnitSetOrder(u, 2);
        u->f6 = 1;
        if (dat_5a7c2 != 0) {
            u->flags |= 0x480;
        }
        if (type >= 0x20) {
            if (dat_5a7c2 == 0) {
                dat_50d98[u->owner]++;
            }
            if (type == 0x32) {
                if (net_play_flag == 0) {
                    u->tg.s.l54 = (fn_19478(10) & 0x1fff) + 0x6590;
                } else {
                    u->tg.s.l54 = 40000;
                }
            }
            u->s50 = unit_train_time[type];
            u->s4c = 10;
            fn_1379c(u);
        } else {
            if (u->type >= 10 && u->type <= 14) {
                u->p.w.b48 = 0x28;
                u->f1a = 0x55;
            }
            u->d.dst = u->t;
            u->p.w.w46 = u->type;
            fn_13928(u);
            u->flags |= 0x80;
            if (u->owner == 4) {
                u->hp = 5;
                UnitSetOrder(u, 0x1d);
            }
        }
        fn_1c9c0(u);
        fn_13c04(u);
        AiInitUnitOrder(u);
        u->f6 += fn_19478(0x27) & 7;
    }
    return u;
}
