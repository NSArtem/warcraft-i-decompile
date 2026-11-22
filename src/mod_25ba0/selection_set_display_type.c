/* codegen-compiler: 10.0a */
#include "mod_25ba0_f1.h"

/* 0x25d6c stores the low byte of type in each selected unit. */
void SelectionSetDisplayType(unsigned short type)
{
    Unit *u;

    for (u = SelectionFirst(); u != 0; u = SelectionNext()) {
        u->display_type = (unsigned char)type;
    }
}
