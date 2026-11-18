/* codegen-compiler: 10.0a */
/* 0x16f44: poll the dialog's 'finished' callback (slot +0x10). */
#include "mod_16390.h"

short DialogCheckDone(Dialog *d)
{
    if (d->cb->check != 0)
        return d->cb->check(d->params);
    return 0;
}
