/* codegen-compiler: 10.0a */
/* 0x16c8c: idle event: count the auto-repeat delay down. */
#include "mod_16390.h"

void DialogIdleHandler(void)
{
    if (auto_repeat_delay != 0)
        auto_repeat_delay--;
}
