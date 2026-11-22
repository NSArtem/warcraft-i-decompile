/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

/* 0x25d86 and 0x25d89 copy the base type back to the display type. */
void SelectionRestoreDisplayTypes(void)
{
    Unit *u;

    for (u = SelectionFirst(); u != 0; u = SelectionNext()) {
        u->display_type = u->base_type;
    }
}
