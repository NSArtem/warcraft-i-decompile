/* codegen-compiler: 10.0a */
#include "mod_25ba0_c.h"

extern Unit *selected_units[2][4];
extern unsigned short selection_index;
extern unsigned short net_event_pending;

/* @0x25c50 */
Unit *SelectionNext(void)
{
    unsigned short i = selection_index;
    unsigned short p = net_event_pending;
    Unit *r = 0;

    while (i < 4) {
        if (selected_units[p][i] != 0) {
            r = selected_units[p][i++];
            break;
        }
        i++;
    }
    net_event_pending = p;
    selection_index = i;
    return r;
}
