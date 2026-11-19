/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiInitUnitOrder 0x29cf8: give a freshly
 * created AI unit its first behavioural state.  Called by UnitCreate 0x2e6f4
 * for every new unit of the computer player.  A town hall records the player's
 * home point and (for player 0) the AI attack point; buildings clear the 0x400
 * flag; summoned creatures attack in a linked game; the spellcaster/hero types
 * get an attack order; everything else either wakes a dormant scenario unit or
 * picks a work site.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern int AiWakeUnit(Unit *u);                /* 0x29a9c */
extern void AiPickWorkSite(Unit *u);           /* 0x29c58 */

/* @0x29cf8 */
void AiInitUnitOrder(Unit *u)
{
    int type = u->type;
    Point home;

    if (dat_5008c[u->owner] != 1)
        return;
    if (type == 2 || type == 3) {
        u->flags &= ~0x400;
        return;
    }
    if (type >= 0x20 && type <= 0x32) {
        if (type == 0x28 || type == 0x29) {
            home = player_home_point[u->owner];
            ai_sweep_point[u->owner] = home;
            ai_home_point[u->owner] = home;
            if (u->owner != 0)
                return;
            if (ai_attack_point.x != -1)
                return;
            ai_retarget_timer = 0x320;
            ai_attack_point.x = u->tx;
            ai_attack_point.y = u->ty;
            return;
        }
        if (type != 0x30 && type != 0x31)
            return;
        u->flags &= ~0x400;
        home = player_home_point[u->owner];
        ai_sweep_point[u->owner] = home;
        ai_home_point[u->owner] = home;
        if (u->owner != 0)
            return;
        if (ai_attack_point.x != -1)
            return;
        ai_retarget_timer = 0x320;
        ai_attack_point.x = u->tx;
        ai_attack_point.y = u->ty;
        return;
    }
    if (type >= 4 && type <= 5) {
        if (scenario_number == 0x8e || scenario_number == 0x8d)
            return;
        u->flags &= ~0x400;
        AiPickWorkSite(u);
        return;
    }
    if (type >= 0x13 && type <= 0x1f) {
        if (dat_5a7c2 != 0)
            u->order_flags = 8;
        else
            u->order_flags = 4;
        return;
    }
    if ((scenario_objectives & 1) != 0) {
        u->order_flags = 8;
        return;
    }
    if (dat_5a7c2 == 0) {
        if (AiWakeUnit(u)) {
            u->flags |= 0x400;
            return;
        }
    }
    AiPickWorkSite(u);
}
