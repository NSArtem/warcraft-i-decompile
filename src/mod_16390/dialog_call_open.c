/* codegen-compiler: 10.0a */
/* 0x16894: the dialog's 'opened' callback (slot +0xc), called with the dialog. */
#include "mod_16390.h"

void DialogCallOpen(Dialog *d)
{
    if (d->cb->open != 0)
        d->cb->open(d);
}
