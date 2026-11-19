/* codegen-compiler: 10.0a */
/* mod_295d0.  AiResetWorkSites 0x29954: release every AI worker from its work
 * site.  For every live unit of type < 0x20 (except the hero/wounded types
 * 0x0e..0x12) whose owner still has a site counter, clear the site state and
 * the owner's counter, then zero the five counters.  Called by AiTick 0x29a08
 * when the AI's wave timer expires.  See docs/subsystems/mod_295d0.md. */
#include "mod_295d0.h"

/* @0x29954 */
void AiResetWorkSites(void)
{
    unsigned short *sites = work_sites;
    Unit *u = unit_array;
    unsigned short i;

    for (i = 200; --i != (unsigned short)-1; ) {
        int type;
        if ((u->flags & 0x207) != 0)
            goto next;
        type = u->type;
        if (type > 0x1f)
            goto next;
        if (type >= 0xe && type <= 0x12)
            goto next;
        if (ai_site_count[u->owner] == 0)
            goto next;
        if ((u->work_site & 0x4000) != 0) {
            u->work_site &= 0x3fff;
            sites[u->work_site]--;
            u->work_site = 0;
        }
        ai_site_count[u->owner]--;
        u->order_flags = 4;
next:
        u++;
    }
    work_sites = sites;
    memset(ai_site_count, 0, 0xa);
    sites = work_sites;
}
