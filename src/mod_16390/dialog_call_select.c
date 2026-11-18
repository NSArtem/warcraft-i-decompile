/* codegen-compiler: 10.0a */
/* 0x174ac: the dialog's 'selection changed' callback (slot +8). */
#include "mod_16390.h"

void DialogCallSelect(Dialog *d)
{
    if (d->cb->select != 0)
        d->cb->select(d->params);
}
