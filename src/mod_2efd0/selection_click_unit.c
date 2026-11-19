/* codegen-flags: -s -ot -ol -4r -zp2 */
/* codegen-compiler: 10.0a */
/* SelectionClickUnit (0x2efd0), built from C: T3 under Watcom 10.0a.
 *
 * IssueOrderAt 0x2f0a8 is its neighbour and shares the epilogue (`jne
 * 0x2f0a7`); see src/mod_2efd0/issue_order_at_reference.c for why the two
 * cannot share one object here.  One function per object. */
#include "mod_2efd0.h"

/* @0x2efd0  a click on a unit: replace the selection with it, or - with one
 * of the (always-zero in v1.22h) modifiers set - extend the current local
 * creature selection with it. */
void SelectionClickUnit(Unit *u)
{
    Unit *list[4];
    Unit *p;
    unsigned short i;
    unsigned short n;
    short add;

    if (sel_mod_select_all != 0 || sel_mod_add != 0) {
        if (selection_local != 0 && u->owner == 0 &&
                type_is_creature[u->type] != 0)
            add = 1;
        else
            add = 0;
        n = 0;
        p = SelectionFirst();
        for (i = 0; i < 4; i++) {
            if (p == u)
                u = 0;
            else if (p != 0 && add)
                list[n++] = p;
            p = SelectionNext();
        }
        if (u != 0 && n < 4)
            list[n++] = u;
        SelectionSet(n, list);
    } else {
        SelectionSet(1, &u);
    }
}

