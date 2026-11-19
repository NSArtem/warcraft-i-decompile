/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiWorkSiteAdvance 0x29778: move a unit
 * that has finished working one site on to the next work-site record.  The
 * table work_sites holds 3-word records {kind, x, y}; a 0xffff kind word ends
 * the list.  A spellcaster stops one record early.  Otherwise the next
 * record's x/y become the unit's work point and the unit is ordered there.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29778 */
void AiWorkSiteAdvance(Unit *u)
{
    unsigned short *p = work_sites + u->work_site;
    int type;

    if (p[3] == 0xffff) {
        u->order_flags = 4;
        u->work_site = 0;
        return;
    }
    if (p[6] == 0xffff) {
        type = u->type;
        if (type >= 0x0a && type <= 0x0e) {
            u->order_flags = 0;
            u->work_site = 0;
            return;
        }
    }
    u->work_site += 3;
    p = work_sites + u->work_site;
    u->work_x = p[1];
    u->work_y = p[2];
    UnitOrderTarget(u, u->work_x, u->work_y, 0, fn_20f30);
}
