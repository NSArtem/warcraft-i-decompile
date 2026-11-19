/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndCheckSurvive (0x2f694): the scenario objective "build up" (objectives
 * bit 0x1) - win by reaching the unit cap with two town halls, lose when
 * every unit is gone and no town hall is left or affordable. */
#include "mod_2efd0.h"

/* @0x2f694 */
void EndCheckSurvive(void)
{
    if ((cheat_flags.b[1] & 1) != 0)
        goto victory;
    if ((cheat_flags.b[0] & 0x80) != 0)
        goto defeat;
    if (player_unit_cap[0] >= 6 && player_town_hall_count[0] >= 2 &&
            player_town_hall[0] != 0)
        goto victory;
    if (PlaceBoxActive() != 0)
        return;
    if (training_count[0] != 0)
        return;
    if (player_unit_count[0] != 0)
        return;
    if (player_town_hall[0] != 0) {
        if (player_worker_count[0] != 0)
            return;
        if (dat_50074[0] >= 0x190)
            return;
        goto defeat;
    }
    if (player_worker_count[0] == 0)
        goto defeat;
    if (dat_50074[0] < 0x190)
        goto defeat;
    if (dat_50060[0] < 0x190)
        return;
defeat:
    MissionDefeat();
    return;
victory:
    end_screen_action = VictoryDialog;
}
