/* codegen-compiler: 10.0a */
/* 0x16bdc: release a created dialog (layers, art, bitmap, descriptor). */
#include "mod_16390.h"

void DialogFree(Dialog *d)
{
    DialogArt *art;

    LayerInvalidate(d->layer);
    LayerInvalidate(d->layer + 1);
    layers[d->layer].active = 0;
    layers[d->layer + 1].active = 0;
    for (art = d->art; art->id != -1; art++)
        GdsFree(art->data);
    GdsFree(d->bitmap);
    GdsFree(d);
}
