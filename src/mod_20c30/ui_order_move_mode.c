/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern unsigned short pending_order;
extern void IssueOrderAt(short x, short y, Unit *target);

/* @0x20e98 */
void UiOrderMoveMode(void)
{
    pending_order = 2;
    IssueOrderAt(0, 0, 0);
}
