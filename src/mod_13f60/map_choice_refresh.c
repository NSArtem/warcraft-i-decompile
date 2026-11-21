/* codegen-compiler: 10.0a */
#include "mod_13f60.h"

struct Dialog;
extern void fn_150f0(struct Dialog *d, int b);

/* @0x15158 */
void MapChoiceRefresh(struct Dialog *d)
{
    fn_150f0(d, *(unsigned short *)(*(char **)((char *)d + 6) + 0x14));
}
