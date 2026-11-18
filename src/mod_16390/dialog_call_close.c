/* codegen-compiler: 10.0a */
/* 0x168a4: the dialog's 'closing' callback (slot +0x14). */
#include "mod_16390.h"

void DialogCallClose(Dialog *d)
{
    if (d->cb->close != 0)
        d->cb->close(d);
}
