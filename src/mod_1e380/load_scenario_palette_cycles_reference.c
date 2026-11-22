/* codegen-compiler: 10.0a */
#include "mod_1e380_f1.h"

extern void PaletteCyclesClear(void);
extern void __cdecl PaletteCycleSetup(unsigned char id, unsigned char period, unsigned char first, unsigned char last, void *list, unsigned char count);
extern void __cdecl PaletteCycleEnable(unsigned char id);

unsigned char *LoadScenarioPaletteCycles(unsigned char *records)
{
    unsigned mask;
    int id;
    unsigned period;
    unsigned char first;
    unsigned char last;

    PaletteCyclesClear();
    mask = 1;
    id = 0;
    while ((period = *records++) != 0) {
        first = *records++;
        last = *records++;
        PaletteCycleSetup((unsigned char)id, (unsigned char)period, first, last, 0, 0);
        if (scenario_palette_cycle_enable_mask & mask)
            PaletteCycleEnable((unsigned char)id);
        mask += mask;
        ++id;
    }
    return records;
}
