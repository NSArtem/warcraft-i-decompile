/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndCheckObjectives (0x2f540): the standard mission end conditions.
 *
 * Defeat: nothing left that can still fight or rebuild.  Victory: the
 * scenario_objectives bits - 0x10 "one enemy building left and no enemy
 * men", 0x02 "every other player is wiped out", 0x84 "the objective zone
 * requirement (ObjectiveUnitCount)". */
#include "mod_2efd0.h"

/* @0x2f540 */
void EndCheckObjectives(void)
{
    unsigned short i;

    if (cheat_flags.b[1] & 1)
        goto victory;
    if (cheat_flags.b[0] & 0x80)
        goto defeat;
    if (PlaceBoxActive() != 0)
        goto objectives;
    if (training_count[0] != 0)
        goto objectives;
    if (training_count[10] != 0)     /* 0x50d98 (dead_men+0xa) */
        goto objectives;
    if (player_active_men[0] == 0) {
        if (player_town_hall_count[0] == 0)
            goto defeat;
        if (dat_50074[0] >= 0x190)
            goto objectives;
        goto defeat;
    }
    if (player_active_men[0] != player_worker_count[0])
        goto objectives;
    if (player_town_hall[0] != 0)
        goto objectives;
    if (dat_50074[0] >= 0x190 && dat_50060[0] >= 0x190)
        goto objectives;
defeat:
    end_screen_action = DefeatDialog;
    return;
objectives:
    if (scenario_objectives & 0x10) {
        if (player_building_count[1] != 1)
            return;
        for (i = 1; i <= 3; i++)
            if (player_active_men[i] != 0)
                return;
        goto final;
    }
    if (scenario_objectives & 0x2) {
        for (i = 1; i <= 3; i++) {
            if (player_active_men[i] != 0)
                return;
            if (player_building_count[i] != 0)
                return;
        }
    }
final:
    if ((scenario_objectives & 0x84) == 0)
        goto victory;
    if (ObjectiveUnitCount() != 0)
        goto victory;
    return;
victory:
    end_screen_action = VictoryDialog;
}
