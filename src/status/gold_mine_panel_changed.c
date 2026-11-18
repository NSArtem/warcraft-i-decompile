/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* 0x28360 - the gold mine panel (type 0x32): unit+0x54 is the amount of gold
 * left; a change of that dword forces a repaint. */
#include "status.h"

unsigned short GoldMinePanelChanged(void)
{
    unsigned short changed;

    changed = status_unit->target != status_progress_cache;
    status_progress_cache = status_unit->target;
    if (changed)
        return 1;
    if (UnitPanelStateChanged())
        return 1;
    return 0;
}
