/* codegen-compiler: 10.0a */
/* mod_295d0 REFERENCE C (not built).  AiWorkSiteStep 0x298a0: the per-tick
 * step of a unit that is working a site.  Called from the stop order's body
 * (OrderUpdateStop 0x14030) to finish the harvest swing: a unit with no
 * pending order and standing on its work point either toggles into the site
 * (and releases the site when it is full) or moves on to the next record.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern void AiWorkSiteAdvance(Unit *u);        /* 0x29778 */
extern void AiWorkSiteRelease(int site);       /* 0x29818 */

/* @0x298a0 */
void AiWorkSiteStep(Unit *u)
{
    unsigned site;

    if (u->order_next != 0x1f)
        return;
    if (u->order_next2 != 0x1f)
        return;
    if (fn_13270(&u->work_x, u) > 4) {
        UnitOrderTarget(u, u->work_x, u->work_y, 0, fn_20f30);
        return;
    }
    if ((u->work_site & 0x8000) != 0) {
        u->work_site ^= 0xc000;
        site = u->work_site & 0x3fff;
        if (++work_sites[site] >= ai_site_limit)
            AiWorkSiteRelease(site);
        return;
    }
    if ((u->work_site & 0x4000) == 0)
        AiWorkSiteAdvance(u);
}
