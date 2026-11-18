/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x28400 - the peasant/peon panels: the carrying state byte unit+0x49 drives
 * the info line, so a change with it forces a repaint. */
#include "status.h"

unsigned short WorkerPanelChanged(void)
{
    unsigned short changed;

    if (status_unit->work.b.state != status_flags_cache || UnitPanelStateChanged())
        changed = 1;
    else
        changed = 0;
    status_flags_cache = status_unit->work.b.state;
    return changed;
}
