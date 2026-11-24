/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"
#include "mod_13b30_f1.h"

extern Unit *unit_array;
extern void DrawListInsert(void *u);

/* @0x2d058 */
void DrawListRebuild(void)
{
    Unit *p = unit_array;
    short i = 200;

    while (--i != -1) {
        if ((p->flags & 0x205) == 0) {
            DrawListInsert(p);
        }
        if ((p->flags & 0x207) == 0) {
            UnitCountAdd(p);
        }
        p++;
    }
}
