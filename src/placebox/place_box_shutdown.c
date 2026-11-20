/* codegen-compiler: 10.0a */
#include "mod_20c30.h"

extern void GdsFree(void *p);

/* @0x2254c */
void PlaceBoxShutdown(void)
{
    void **pp = &((void **)&place_box_bm)[1];

    if (*pp != 0) {
        GdsFree(*pp);
        *pp = 0;
    }
}
