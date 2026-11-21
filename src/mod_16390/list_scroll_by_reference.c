/* codegen-compiler: 10.0a */
#include "mod_16390.h"

/* @0x17c4c */
void ListScrollBy(Dialog *d, int delta)
{
    DialogItem *it;
    int *p;
    int *pp;
    int n;
    int v;

    it = d->items;
    for (;;) {
        if (it->type == 5) {
            n = 0;
            p = (int *)it->text;
            while (*p != 0 && *p != -1) {
                n++;
                p++;
            }
            pp = d->params;
            pp[it->id] += delta;
            pp = &pp[it->id];
            v = *pp;
            if (v < 0) {
                *pp = 0;
            } else if (n <= v) {
                *pp = n - 1;
            }
            ListDraw(d, (DialogItem *)v);
            return;
        }
        if (it->type == 0xffff) {
            break;
        }
        it++;
    }
}
