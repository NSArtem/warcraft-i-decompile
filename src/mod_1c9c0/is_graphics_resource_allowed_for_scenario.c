/* codegen-compiler: 10.0a */
#include "mod_1c9c0.h"

/* 0x1cb05 snapshots the scenario; 0x1cb87 stores it on both return paths. */
int IsGraphicsResourceAllowedForScenario(unsigned short resource_id)
{
    unsigned short scenario = scenario_number;
    int allowed;

    switch (resource_id) {
    case 0x128:
    case 0x129:
        if (scenario == 0x7d)
            goto allow;
        allowed = 0;
        break;
    case 0x127:
        if (scenario == 0x85)
            goto allow;
        allowed = 0;
        break;
    case 0x12a:
        if (scenario == 0x7e || scenario == 0x86)
            goto allow;
        allowed = 0;
        break;
    case 0x145:
    case 0x146:
        if (scenario <= 0x8e && scenario >= 0x8d)
            goto allow;
        allowed = 0;
        break;
    default:
    allow:
        allowed = 1;
        break;
    }
    scenario_number = scenario;
    return allowed;
}
