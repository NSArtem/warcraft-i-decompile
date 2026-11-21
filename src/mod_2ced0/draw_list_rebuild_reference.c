/* codegen-compiler: 10.0a */
#include "mod_2ced0_c.h"

extern Unit *unit_array;
extern void DrawListInsert(void *u);
extern void fn_13c04(void *u);

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
            fn_13c04(p);
        }
        p++;
    }
}
