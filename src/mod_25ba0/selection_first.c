/* codegen-compiler: 10.0a */
#include "mod_25ba0_c.h"

extern unsigned short selection_index;

/* @0x25cc4 */
Unit *SelectionFirst(void)
{
    selection_index = 0;
    return SelectionNext();
}
