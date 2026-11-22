#include "mod_1e100.h"

/* C decoration supplies the second leading underscore in __STOSB. */
extern void __cdecl _STOSB(void *dst, unsigned long pattern, unsigned count);
#pragma aux _STOSB parm [eax] [edx] [ecx] modify exact [eax edx ecx]

void InitNewCampaign(void)
{
    scenario_number = scenario_race + 0x77;
    /* The original fill includes the word immediately after player_score. */
    _STOSB(player_score, 0x012c012cUL, 10);
}
