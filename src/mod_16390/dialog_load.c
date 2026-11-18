/* codegen-compiler: 10.0a */
/* 0x16694: load one dialog descriptor resource. */
#include "mod_16390.h"

Dialog *DialogLoad(unsigned int id)
{
    unsigned long size;
    Dialog *d;

    size = ResourceBegin((unsigned short)id, 0);
    d = GdsAlloc((unsigned short)size);
    ResourceRead(d, 0);
    return d;
}
