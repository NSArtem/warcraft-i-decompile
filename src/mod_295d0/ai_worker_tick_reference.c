/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiWorkerTick 0x2b064: the AI's worker
 * AI.  Clears the worker's order flags and counters, sends a loaded worker to
 * the town hall to unload, otherwise (while the AI's busy count is below 2/3
 * of its workers) builds/repairs a building, then mines gold, scouts and
 * finally guards the start area.  Returns 1 when it gave the worker an order.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern Unit *AiChooseBuilding(Unit *u);        /* 0x2ad10 */
extern int AiBuildOrRepair(Unit *u, Unit *b);  /* 0x2ae24 */
extern int AiMineGold(Unit *u);                /* 0x2ac38 */
extern int AiScoutStep(Unit *u);               /* 0x2aefc */
extern int AiGuardStartArea(Unit *u);          /* 0x29f40 */

/* @0x2b064 */
int AiWorkerTick(Unit *u)
{
    int carry;
    int workers;
    int budget;
    Unit *b;

    if ((u->order_flags & 2) != 0) {
        ai_busy_count[u->owner]--;
        goto clear;
    }
    if ((u->order_flags & 1) != 0)
        ai_work_count[u->owner]--;
clear:
    u->order_flags &= 0xfc;
    carry = (u->b49 & 0x20);
    if (carry != 0) {
        Unit *hall = player_town_hall[u->owner];
        if (hall != 0) {
            UnitOrderTarget(u, 0, 0, hall, fn_2111c);
            return 1;
        }
    }
    workers = player_worker_count[u->owner] - 1;
    budget = (workers * 2) / 3;
    if (carry != 0 || budget > ai_busy_count[u->owner]) {
        do {
            b = AiChooseBuilding(u);
            if (b == 0)
                break;
            if (AiBuildOrRepair(u, b))
                return 1;
        } while (1);
        if (carry != 0)
            return 0;
    }
    if (u->attacker != 0 || workers > ai_work_count[u->owner]) {
        if (AiMineGold(u))
            return 1;
        if (u->attacker != 0)
            return 0;
    }
    if (AiScoutStep(u))
        return 1;
    return AiGuardStartArea(u);
}
