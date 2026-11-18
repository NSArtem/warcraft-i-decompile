/* codegen-compiler: 10.0a */
/* 0x16c58: event handler slot 0 - remember the pressed key. */
#include "mod_16390.h"

void DialogKeyHandler(Event *ev)
{
    short key = last_key;

    if (ev->sub != 2) {
        key = ev->key;
        if (key >= 'a' && key <= 'z')
            key -= 0x20;
    }
    last_key = key;
}
