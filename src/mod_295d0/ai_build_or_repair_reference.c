/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiBuildOrRepair 0x2ae24: give a worker
 * a building to (re)build.  A destroyed building (flag 0x200) is paid for
 * (fn_20d74), its site checked (fn_13990) and re-created (fn_2e6f4); any other
 * building just gets the worker.  The worker is then marked busy and ordered
 * there with callback fn_210dc.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x2ae24 */
int AiBuildOrRepair(Unit *u, Unit *b)
{
    if ((b->flags & 0x200) != 0) {
        Unit *n;
        if (b->type != 0x28 && b->type != 0x29) {
            if (fn_20d74(u->owner, 1, b->type) != 0) {
                b->word4a = 0xff;
                return 0;
            }
        }
        if (fn_13990(b->tx, b->ty, b->type) == 0) {
            fn_20d74(u->owner, 0, b->type);
            b->word4a = 0xff;
            return 0;
        }
        b->flags = 1;
        n = UnitCreate(b->px, b->py, b->type, b->owner);
        n->flags |= 0x400;
    }
    u->order_flags |= 2;
    ai_busy_count[u->owner]++;
    UnitOrderTarget(u, 0, 0, 0, fn_210dc);
    return 1;
}
