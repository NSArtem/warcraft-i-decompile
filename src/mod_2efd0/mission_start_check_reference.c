/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* MissionStartCheck (0x2f788): install the mission-end condition the
 * scenario asks for and start its poll. */
#include "mod_2efd0.h"

/* @0x2f788 */
void MissionStartCheck(void)
{
    void (*fn)(void);

    end_check_timer = 1;
    if (demo_mode != 0)
        fn = EndCheckDemo;
    else if ((scenario_objectives & 1) != 0)
        fn = EndCheckSurvive;
    else if ((scenario_objectives & 0x20) != 0)
        fn = EndCheckElimination;
    else
        fn = EndCheckObjectives;
    if ((scenario_objectives & 0x80) != 0)
        *(unsigned short *)palette_cycles = 1;
    end_screen_action = fn;
}
