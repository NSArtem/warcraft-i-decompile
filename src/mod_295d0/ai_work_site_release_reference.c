/* codegen-compiler: 10.0a */
/* mod_295d0.  AiWorkSiteRelease 0x29818: take one work site away from the
 * unit working it.  Finds the unit whose work-site index is the argument,
 * clears its "working" state, decrements the site's count and lets the unit
 * advance to its next site; then steps the site-cycle counter (wrapping at
 * ai_site_reset) and raises the per-site worker limit up to ai_site_max.
 * See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

extern void AiWorkSiteAdvance(Unit *u);        /* 0x29778 */

/* @0x29818 */
void AiWorkSiteRelease(int site)
{
    Unit *u = unit_array;
    int i;

    for (i = 0; i < 200; i++) {
        if ((u->work_site & 0x3fff) == site) {
            u->work_site &= 0xbfff;
            work_sites[site]--;
            AiWorkSiteAdvance(u);
        }
        u++;
    }
    ai_site_cycle++;
    if (ai_site_cycle == ai_site_reset) {
        ai_site_cycle = 0;
        if (ai_site_limit < ai_site_max)
            ai_site_limit++;
    }
}
