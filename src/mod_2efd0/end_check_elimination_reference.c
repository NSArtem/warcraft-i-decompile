/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* EndCheckElimination (0x2f4c0): the "destroy the enemy" objective
 * (scenario_objectives bit 0x20). */
#include "mod_2efd0.h"

/* @0x2f4c0 */
void EndCheckElimination(void)
{
    if (cheat_flags.b[1] & 1)
        goto victory;
    if (cheat_flags.b[0] & 0x80)
        goto defeat;
    if (player_active_men[1] != 0 || player_building_count[1] != 0)
        goto own;
victory:
    if (game_mode == 3)
        NetSendControlPacket(0xa);
    else
        game_mode = 6;
own:
    if (player_active_men[0] != 0 || player_building_count[0] != 0)
        return;
defeat:
    if (game_mode == 3)
        NetSendControlPacket(0xa);
    else
        game_mode = 7;
}
