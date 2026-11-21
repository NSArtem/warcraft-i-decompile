/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

typedef struct Army {
    unsigned long d[0x13];
} Army;

typedef struct ArmyTmp {
    unsigned long d[0x13];
    char *s;
} ArmyTmp;

extern unsigned short scenario_race;
extern unsigned short scenario_race_enemy;
extern Army army_setup;
extern unsigned short setup_changed;
extern unsigned short preview_visible;
extern unsigned char setup_return_state;
extern int memcmp(const void *a, const void *b, unsigned n);
extern void PreviewRectReset(void);
extern void PreviewRectUpdate(void);
extern unsigned short DialogRun(unsigned int id, short x, short y, unsigned short layer, void **params);

/* @0x14e9c */
void ArmySetupDialog(void)
{
    ArmyTmp tmp;
    unsigned long *p;
    unsigned short id;
    unsigned long a, b, v;
    int i;

    *(Army *)&tmp = army_setup;
    p = tmp.d;
    if (dat_516ae != 0) {
        if (own_campaign != 0) {
            id = scenario_race * 2 + 0x18e + scenario_race_enemy;
        } else {
            id = scenario_race + (scenario_race_enemy * 2 + 0x18e);
        }
    } else {
        id = scenario_race + 0x192;
    }
    if (preview_visible != 0) {
        PreviewRectUpdate();
    }
    if (DialogRun(id, 0, 0x46, 0x10, (void **)&tmp) == 0) {
        if (memcmp(&army_setup, &tmp, 0x4c) != 0) {
            a = 0;
            for (i = 0; i < 7; i++, p++) {
                v = *p;
                if (v > 1) {
                    a += v - 1;
                }
            }
            b = 0;
            for (i = 0; i < 7; i++, p++) {
                v = *p;
                if (v > 1) {
                    b += v - 1;
                }
            }
            if (a == 0 || (dat_516ae != 0 && b == 0)) {
                tmp.s = str_army_total_zero;
                DialogRun(0x176, 0x11, 0x46, 0x10, (void **)&tmp.s);
            } else {
                army_setup = *(Army *)&tmp;
                setup_changed = 1;
            }
            setup_return_state = 5;
        }
    }
    PreviewRectReset();
}
