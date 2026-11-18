/* codegen-compiler: 10.0a */
/* 0x17430: previous entry of a prev/next control. */
#include "mod_16390.h"

void ListSelPrev(Dialog *d, DialogItem *item)
{
    int n = item->id;
    int *sel = d->params + n;

    if (*sel > 0) {
        (*sel)--;
        return;
    }
    if (item->flags & 1)
        *sel = (int)item->text - 1;
}
