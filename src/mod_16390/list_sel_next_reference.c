/* codegen-compiler: 10.0a */
/* 0x1746c: next entry of a prev/next control. */
#include "mod_16390.h"

void ListSelNext(Dialog *d, DialogItem *item)
{
    int n = item->id;
    int *sel = d->params + n;

    if ((unsigned)item->text - 1 > *(unsigned *)sel) {
        (*sel)++;
        return;
    }
    if (item->flags & 1)
        *sel = 0;
}
